
"""Testes sintéticos da baseline sem acessar o teste final do C14."""

import numpy as np
import pandas as pd
import pytest

from scripts.treinar_baseline import (
    avaliar_baseline,
    main,
)


def dados_exemplo():
    """Cria seis moléculas com duas medições por molécula."""
    return pd.DataFrame({
        "Source_Row": list(range(2, 14)),
        "SMILES_Canonico": [
            "C", "C",
            "CC", "CC",
            "CCC", "CCC",
            "CO", "CO",
            "CCO", "CCO",
            "O", "O",
        ],
        "Temperature_K": [298.15, 310.0] * 6,
        "LogS(mol/L)": [
            -1.0, -2.0,
            0.0, -1.0,
            1.0, 0.0,
            -2.0, -3.0,
            -0.5, -1.5,
            0.5, 1.5,
        ],
    })


def test_baseline_e_validacao_agrupada():
    dados = dados_exemplo()

    resultado = avaliar_baseline(dados)

    assert resultado["moleculas_compartilhadas"] == 0

    assert (
        resultado["registros_ajuste"]
        + resultado["registros_validacao"]
        == len(dados)
    )

    assert (
        resultado["moleculas_ajuste"]
        + resultado["moleculas_validacao"]
        == dados["SMILES_Canonico"].nunique()
    )

    assert np.isfinite(
        resultado["mediana_ajuste"]
    )

    assert resultado["mae_validacao"] >= 0
    assert resultado["rmse_validacao"] >= 0

    assert np.isfinite(
        resultado["r2_validacao"]
    )


def test_resultado_reproduzivel():
    primeiro = avaliar_baseline(
        dados_exemplo(),
        semente=42,
    )

    segundo = avaliar_baseline(
        dados_exemplo(),
        semente=42,
    )

    assert primeiro == segundo


def test_nao_modifica_o_dataframe_original():
    dados = dados_exemplo()
    copia = dados.copy(deep=True)

    avaliar_baseline(dados)

    pd.testing.assert_frame_equal(
        dados,
        copia,
    )


@pytest.mark.parametrize(
    "coluna",
    [
        "Source_Row",
        "SMILES_Canonico",
        "Temperature_K",
        "LogS(mol/L)",
    ],
)
def test_rejeita_colunas_ausentes(coluna):
    dados = dados_exemplo().drop(
        columns=coluna
    )

    with pytest.raises(
        ValueError,
        match="Colunas obrigatórias ausentes",
    ):
        avaliar_baseline(dados)


@pytest.mark.parametrize(
    "valor",
    [
        None,
        "invalido",
        float("nan"),
        float("inf"),
    ],
)
def test_rejeita_valores_de_logs_invalidos(valor):
    dados = dados_exemplo()
    dados["LogS(mol/L)"] = dados[
        "LogS(mol/L)"
    ].astype(object)

    dados.loc[0, "LogS(mol/L)"] = valor

    with pytest.raises(
        ValueError,
        match="LogS",
    ):
        avaliar_baseline(dados)


def test_rejeita_temperatura_invalida():
    dados = dados_exemplo()

    dados.loc[0, "Temperature_K"] = -1

    with pytest.raises(
        ValueError,
        match="Temperature_K",
    ):
        avaliar_baseline(dados)


def test_rejeita_arquivo_inexistente(
    tmp_path,
    monkeypatch,
):
    import sys

    arquivo = tmp_path / "ausente.csv"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "treinar_baseline.py",
            "--input",
            str(arquivo),
        ],
    )

    with pytest.raises(SystemExit) as erro:
        main()

    assert erro.value.code == 2
