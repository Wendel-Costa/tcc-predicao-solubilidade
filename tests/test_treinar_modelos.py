
"""Testes sintéticos de treino e validação; nunca leem teste.csv."""

import math
import re

import pandas as pd
import pytest

from scripts.dividir_dados import dividir_dataset
from scripts.treinar_modelos import (
    construir_atributos,
    comparar_modelos,
    main,
)
from app.chemistry import FEATURE_NAMES


def dados_exemplo():
    smiles = [
        "C", "CC", "CCC", "CCCC", "CO",
        "CCO", "CCCO", "O", "CC(=O)O", "CCN",
    ]

    linhas = []

    for indice, s in enumerate(smiles):
        for temp in (298.15, 303.15):
            linhas.append({
                "Source_Row": len(linhas) + 2,
                "SMILES_Canonico": s,
                "Temperature_K": temp,
                "LogS(mol/L)": (
                    indice * -0.25
                    + (temp - 298.15) * 0.02
                ),
            })

    return pd.DataFrame(linhas)


def test_colunas_matriz_na_ordem_definida():
    x = construir_atributos(dados_exemplo())

    assert tuple(x.columns) == FEATURE_NAMES
    assert x.shape == (20, 10)
    assert x.iloc[0]["Temperature_K"] == 298.15


def test_compara_tres_modelos_sem_vazamento():
    r = comparar_modelos(dados_exemplo())

    assert r["moleculas_compartilhadas"] == 0

    assert (
        r["moleculas_ajuste"]
        + r["moleculas_validacao"]
        == 10
    )

    assert (
        r["registros_ajuste"]
        + r["registros_validacao"]
        == 20
    )

    assert set(r["modelos"]) == {
        "DummyRegressor",
        "Ridge",
        "RandomForest",
    }

    for metricas in r["modelos"].values():
        assert set(metricas) == {
            "MAE", "RMSE", "R2",
        }

        assert all(
            math.isfinite(v)
            for v in metricas.values()
        )

        assert metricas["MAE"] >= 0
        assert metricas["RMSE"] >= 0


def test_mesma_semente_reproduz_resultados():
    assert comparar_modelos(
        dados_exemplo(),
        42,
    ) == comparar_modelos(
        dados_exemplo(),
        42,
    )


def test_nao_modifica_entrada():
    dados = dados_exemplo()
    original = dados.copy(deep=True)

    comparar_modelos(dados)

    pd.testing.assert_frame_equal(
        dados,
        original,
    )


def test_baseline_reproduz_mediana_do_ajuste():
    dados = dados_exemplo()

    ajuste, validacao = dividir_dataset(
        dados,
        fracao_teste=0.20,
        semente=42,
    )

    mediana = ajuste["LogS(mol/L)"].median()

    erro = (
        validacao["LogS(mol/L)"] - mediana
    ).abs().mean()

    resultado = comparar_modelos(dados)

    assert (
        resultado["modelos"]["DummyRegressor"]["MAE"]
        == pytest.approx(erro)
    )


@pytest.mark.parametrize(
    "coluna",
    [
        "SMILES_Canonico",
        "Source_Row",
        "Temperature_K",
        "LogS(mol/L)",
    ],
)
def test_coluna_ausente(coluna):
    with pytest.raises(
        ValueError,
        match="Colunas obrigatórias ausentes",
    ):
        comparar_modelos(
            dados_exemplo().drop(columns=coluna)
        )


@pytest.mark.parametrize(
    "coluna,valor",
    [
        ("Temperature_K", 0),
        ("Temperature_K", float("nan")),
        ("LogS(mol/L)", float("inf")),
    ],
)
def test_rejeita_valores_invalidos(coluna, valor):
    dados = dados_exemplo()
    dados.loc[0, coluna] = valor

    with pytest.raises(
        ValueError,
        match=re.escape(coluna),
    ):
        comparar_modelos(dados)


def test_cli_recusa_teste_final(
    tmp_path,
    monkeypatch,
):
    import sys

    arquivo = tmp_path / "teste.csv"
    dados_exemplo().to_csv(arquivo, index=False)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "treinar_modelos.py",
            "--input",
            str(arquivo),
        ],
    )

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 2
