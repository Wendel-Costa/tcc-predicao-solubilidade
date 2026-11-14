
"""Testes sintéticos da divisão agrupada; não dependem do BigSolDB."""

import pandas as pd
import pytest

from scripts.dividir_dados import dividir_dataset


def exemplo():
    return pd.DataFrame({
        "Source_Row": [2, 3, 4, 5, 6, 7, 8, 9],
        "SMILES_Canonico": [
            "CCO", "CCO", "CCO", "CO",
            "CO", "C", "CC", "CC",
        ],
        "Temperature_K": [
            298.15, 303.15, 298.15, 298.15,
            310, 298.15, 299, 300,
        ],
        "LogS(mol/L)": [
            -1, -1.1, -1, -0.2,
            -0.3, -0.4, -1.2, -1.4,
        ],
    })


def test_sem_vazamento_e_sem_perda_de_registros():
    dados = exemplo()
    antes = dados.copy(deep=True)

    treino, teste = dividir_dataset(dados)

    assert set(treino.SMILES_Canonico).isdisjoint(
        set(teste.SMILES_Canonico)
    )

    assert set(treino.Source_Row).isdisjoint(
        set(teste.Source_Row)
    )

    assert sorted(
        pd.concat([treino, teste]).Source_Row
    ) == sorted(dados.Source_Row)

    pd.testing.assert_frame_equal(dados, antes)


def test_mesma_semente_reproduz_mesmas_particoes():
    dados = exemplo()

    a, b = dividir_dataset(dados, semente=42)
    c, d = dividir_dataset(dados, semente=42)

    pd.testing.assert_frame_equal(a, c)
    pd.testing.assert_frame_equal(b, d)


def test_repeticoes_e_temperaturas_da_mesma_molecula_ficam_juntas():
    treino, teste = dividir_dataset(exemplo())

    for smiles in exemplo().SMILES_Canonico.unique():
        linhas_treino = treino.loc[
            treino.SMILES_Canonico == smiles
        ]

        linhas_teste = teste.loc[
            teste.SMILES_Canonico == smiles
        ]

        assert linhas_treino.empty != linhas_teste.empty


@pytest.mark.parametrize(
    "coluna",
    [
        "Source_Row",
        "SMILES_Canonico",
        "Temperature_K",
        "LogS(mol/L)",
    ],
)
def test_coluna_obrigatoria_ausente(coluna):
    dados = exemplo().drop(columns=coluna)

    with pytest.raises(
        ValueError,
        match="Colunas obrigatórias ausentes",
    ):
        dividir_dataset(dados)


@pytest.mark.parametrize(
    "fracao",
    [-0.1, 0, 1, 1.2],
)
def test_fracao_invalida(fracao):
    with pytest.raises(
        ValueError,
        match="fracao_teste",
    ):
        dividir_dataset(
            exemplo(),
            fracao_teste=fracao,
        )


def test_dataset_vazio():
    with pytest.raises(
        ValueError,
        match="vazio",
    ):
        dividir_dataset(exemplo().iloc[:0])


def test_uma_unica_molecula():
    dados = exemplo()
    dados["SMILES_Canonico"] = "CCO"

    with pytest.raises(
        ValueError,
        match="duas moléculas",
    ):
        dividir_dataset(dados)


@pytest.mark.parametrize(
    "valor",
    [None, "", "   "],
)
def test_smiles_ausente_ou_vazio(valor):
    dados = exemplo()
    dados.loc[0, "SMILES_Canonico"] = valor

    with pytest.raises(
        ValueError,
        match="SMILES canônicos",
    ):
        dividir_dataset(dados)


def test_source_row_duplicado():
    dados = exemplo()

    dados.loc[1, "Source_Row"] = dados.loc[
        0, "Source_Row"
    ]

    with pytest.raises(
        ValueError,
        match="Source_Row",
    ):
        dividir_dataset(dados)