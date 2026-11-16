
"""Testes da avaliação científica usando dados sintéticos."""

import json
import math
import sys

import pandas as pd
import pytest

from scripts.avaliar_modelos import (
    calcular_metricas,
    executar_avaliacao,
    salvar_graficos,
    main,
)
from scripts.treinar_modelos import comparar_modelos


def dados_exemplo():
    smiles = (
        "C", "CC", "CCC", "CCCC", "CO",
        "CCO", "CCCO", "O", "CC(=O)O", "CCN",
    )

    linhas = []

    for indice, smiles_mol in enumerate(smiles):
        for temperatura in (298.15, 303.15):
            linhas.append({
                "Source_Row": len(linhas) + 2,
                "SMILES_Canonico": smiles_mol,
                "Temperature_K": temperatura,
                "LogS(mol/L)": (
                    -0.25 * indice
                    + 0.02 * (temperatura - 298.15)
                ),
            })

    return pd.DataFrame(linhas)


def test_metricas_perfeitas():
    resultado = calcular_metricas(
        [1.0, 2.0, 3.0],
        [1.0, 2.0, 3.0],
    )

    assert resultado["MAE"] == 0.0
    assert resultado["RMSE"] == 0.0
    assert resultado["R2"] == 1.0


def test_avaliacao_agrupada_sem_vazamento():
    resumo, validacao, predicoes = executar_avaliacao(
        dados_exemplo()
    )

    assert resumo["moleculas_compartilhadas"] == 0
    assert resumo["registros_ajuste"] + len(validacao) == 20
    assert resumo["moleculas_ajuste"] + resumo[
        "moleculas_validacao"
    ] == 10

    assert set(predicoes) == {
        "DummyRegressor",
        "Ridge",
        "RandomForest",
    }

    for valores in resumo["metricas"].values():
        assert all(math.isfinite(v) for v in valores.values())



def test_metricas_coincidem_com_c16():
    dados = dados_exemplo()

    anterior = comparar_modelos(dados)
    atual, _, _ = executar_avaliacao(dados)

    # Verifica se os mesmos modelos foram avaliados.
    assert set(atual["metricas"]) == set(anterior["modelos"])

    # Compara as métricas individualmente.
    for nome_modelo in anterior["modelos"]:
        metricas_anteriores = anterior["modelos"][nome_modelo]
        metricas_atuais = atual["metricas"][nome_modelo]

        assert metricas_atuais == pytest.approx(
            metricas_anteriores
        )


def test_avaliacao_e_reproduzivel():
    a, _, pred_a = executar_avaliacao(dados_exemplo(), 42)
    b, _, pred_b = executar_avaliacao(dados_exemplo(), 42)

    assert a == b

    for nome in pred_a:
        assert pred_a[nome].tolist() == pytest.approx(
            pred_b[nome].tolist()
        )


def test_gera_quatro_graficos(tmp_path):
    dados = dados_exemplo()
    _, validacao, predicoes = executar_avaliacao(dados)

    salvar_graficos(
        dados,
        validacao,
        predicoes,
        tmp_path,
    )

    nomes = [
        "distribuicao_logs.png",
        "distribuicao_temperatura.png",
        "observado_predito.png",
        "residuos.png",
    ]

    for nome in nomes:
        arquivo = tmp_path / nome
        assert arquivo.is_file()
        assert arquivo.stat().st_size > 0


def test_cli_rejeita_teste_final(tmp_path, monkeypatch):
    arquivo = tmp_path / "teste.csv"
    dados_exemplo().to_csv(arquivo, index=False)

    monkeypatch.setattr(
        sys,
        "argv",
        ["avaliar_modelos.py", "--input", str(arquivo)],
    )

    with pytest.raises(SystemExit) as erro:
        main()

    assert erro.value.code == 2


def test_cli_grava_metricas(tmp_path, monkeypatch):
    entrada = tmp_path / "treino.csv"
    saida = tmp_path / "relatorio"

    dados_exemplo().to_csv(entrada, index=False)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "avaliar_modelos.py",
            "--input", str(entrada),
            "--output-dir", str(saida),
        ],
    )

    assert main() == 0

    with (saida / "metricas.json").open(
        encoding="utf-8"
    ) as arquivo:
        conteudo = json.load(arquivo)

    assert conteudo["moleculas_compartilhadas"] == 0
    assert len(conteudo["sha256_entrada"]) == 64
    assert "Ridge" in conteudo["metricas"]
