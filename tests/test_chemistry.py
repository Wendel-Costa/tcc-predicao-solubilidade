
"""Testes unitários do contrato de atributos moleculares compartilhados."""

import math

import pytest

from app import chemistry
from app.chemistry import FEATURE_NAMES, extrair_atributos


# Contrato independente dos nomes e da ordem dos atributos.
NOMES_ESPERADOS = (
    "MolWt",
    "MolLogP",
    "TPSA",
    "NumHDonors",
    "NumHAcceptors",
    "NumRotatableBonds",
    "HeavyAtomCount",
    "RingCount",
    "FractionCSP3",
    "Temperature_K",
)


def test_contrato_de_nomes_e_ordem_dos_atributos():
    assert FEATURE_NAMES == NOMES_ESPERADOS
    assert len(FEATURE_NAMES) == len(set(FEATURE_NAMES)) == 10

    atributos = extrair_atributos("CCO", 298.15)

    assert tuple(atributos) == NOMES_ESPERADOS


def test_atributos_do_etanol_tem_valores_conhecidos():
    atributos = extrair_atributos("CCO", 298.15)

    assert atributos["MolWt"] == pytest.approx(46.069, abs=0.002)
    assert atributos["TPSA"] == pytest.approx(20.23, abs=0.01)
    assert atributos["NumHDonors"] == 1.0
    assert atributos["NumHAcceptors"] == 1.0
    assert atributos["NumRotatableBonds"] == 0.0
    assert atributos["HeavyAtomCount"] == 3.0
    assert atributos["RingCount"] == 0.0
    assert atributos["FractionCSP3"] == 1.0
    assert atributos["Temperature_K"] == pytest.approx(298.15)


def test_descritores_sao_deterministicos():
    primeiro = extrair_atributos("CCO", 298.15)
    segundo = extrair_atributos("CCO", 298.15)

    assert primeiro == segundo
    assert primeiro is not segundo


def test_smiles_equivalentes_geram_mesmos_atributos():
    primeiro = extrair_atributos("CCO", 298.15)
    segundo = extrair_atributos("OCC", 298.15)

    assert primeiro == segundo


def test_espacos_externos_no_smiles_sao_aceitos():
    primeiro = extrair_atributos("  CCO  ", 298.15)
    segundo = extrair_atributos("CCO", 298.15)

    assert primeiro == segundo


def test_estereoisomeros_validos_sao_aceitos_sem_promessa_de_distincao():
    primeiro = extrair_atributos("C[C@H](O)F", 298.15)
    segundo = extrair_atributos("C[C@@H](O)F", 298.15)

    assert tuple(primeiro) == NOMES_ESPERADOS
    assert tuple(segundo) == NOMES_ESPERADOS

    # Os descritores 2D selecionados podem coincidir
    # para moléculas que diferem apenas na estereoquímica.
    assert primeiro == segundo


def test_descritores_de_moleculas_distintas_refletem_estrutura():
    etanol = extrair_atributos("CCO", 298.15)
    metano = extrair_atributos("C", 298.15)

    assert etanol["MolWt"] > metano["MolWt"]
    assert etanol["HeavyAtomCount"] == 3.0
    assert metano["HeavyAtomCount"] == 1.0


def test_todos_os_atributos_sao_float_e_finitos():
    moleculas = (
        "C",
        "CCO",
        "c1ccccc1",
        "CC(=O)O",
    )

    for smiles in moleculas:
        atributos = extrair_atributos(smiles, 298.15)

        assert all(
            type(valor) is float
            for valor in atributos.values()
        )

        assert all(
            math.isfinite(valor)
            for valor in atributos.values()
        )


def test_temperatura_nao_altera_descritores_moleculares():
    fria = extrair_atributos("CCO", 273.15)
    quente = extrair_atributos("CCO", 323.15)

    assert fria["Temperature_K"] == 273.15
    assert quente["Temperature_K"] == 323.15

    descritores_frios = {
        chave: valor
        for chave, valor in fria.items()
        if chave != "Temperature_K"
    }

    descritores_quentes = {
        chave: valor
        for chave, valor in quente.items()
        if chave != "Temperature_K"
    }

    assert descritores_frios == descritores_quentes


@pytest.mark.parametrize(
    "smiles",
    [None, 123, "", "   ", [], {}],
)
def test_rejeita_smiles_ausente_ou_nao_textual(smiles):
    with pytest.raises(
        ValueError,
        match="SMILES deve ser uma string não vazia",
    ):
        extrair_atributos(smiles, 298.15)


@pytest.mark.parametrize(
    "smiles",
    ["C1(", "nao_e_smiles", "C1CC"],
)
def test_rejeita_smiles_sintaticamente_invalidos(smiles):
    with pytest.raises(
        ValueError,
        match="SMILES inválido",
    ):
        extrair_atributos(smiles, 298.15)


@pytest.mark.parametrize(
    "temperatura",
    [None, "298.15", True, False, [], {}],
)
def test_rejeita_temperatura_nao_numerica(temperatura):
    with pytest.raises(
        ValueError,
        match="Temperatura deve ser numérica em Kelvin",
    ):
        extrair_atributos("CCO", temperatura)


@pytest.mark.parametrize(
    "temperatura",
    [
        0,
        -1,
        float("nan"),
        float("inf"),
        -float("inf"),
    ],
)
def test_rejeita_temperatura_nao_fisica_ou_nao_finita(temperatura):
    with pytest.raises(
        ValueError,
        match="Temperatura deve ser finita e maior que zero Kelvin",
    ):
        extrair_atributos("CCO", temperatura)


def test_aceita_temperatura_inteira_positiva():
    atributos = extrair_atributos("CCO", 300)

    assert atributos["Temperature_K"] == 300.0


def test_detecta_descritor_nao_finito(monkeypatch):
    monkeypatch.setattr(
        chemistry.Descriptors,
        "MolWt",
        lambda _mol: float("nan"),
    )

    with pytest.raises(
        ValueError,
        match="Descritor molecular não finito",
    ):
        extrair_atributos("CCO", 298.15)
