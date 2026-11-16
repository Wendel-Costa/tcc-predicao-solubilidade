
"""Testes unitários dos schemas; nenhuma predição real é realizada."""

import pytest

from pydantic import ValidationError

from app.schemas import (
    ErrorResponse,
    PredictRequest,
    PredictResponse,
)


def test_aceita_smiles_valido_e_converte_celsius_para_kelvin():
    pedido = PredictRequest(
        smiles="CCO",
        temperature_c=25,
    )

    assert pedido.smiles == "CCO"
    assert pedido.temperature_c == 25.0
    assert pedido.temperature_k == pytest.approx(298.15)


def test_temperatura_omitida_nao_assume_padrao_cientifico():
    pedido = PredictRequest(smiles="CCO")

    assert pedido.temperature_c is None
    assert pedido.temperature_k is None

    assert pedido.model_dump() == {
        "smiles": "CCO",
        "temperature_c": None,
    }


def test_espacos_externos_sao_removidos():
    pedido = PredictRequest(smiles="  OCC  ")

    assert pedido.smiles == "OCC"


def test_preserva_estereoquimica_do_smiles():
    texto = "C[C@H](O)F"

    pedido = PredictRequest(smiles=texto)

    assert pedido.smiles == texto


def test_temperatura_acima_do_zero_absoluto_e_aceita():
    pedido = PredictRequest(
        smiles="C",
        temperature_c=-273.14,
    )

    assert pedido.temperature_k > 0


@pytest.mark.parametrize(
    "smiles",
    [
        None,
        123,
        "",
        "   ",
        "C1(",
        "C1CC",
        "notSMILES",
        [],
    ],
)
def test_rejeita_smiles_invalidos(smiles):
    with pytest.raises(ValidationError):
        PredictRequest.model_validate({
            "smiles": smiles,
            "temperature_c": 25,
        })


@pytest.mark.parametrize(
    "temperatura",
    [
        -273.15,
        -300,
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        False,
        "25",
        [],
        {},
    ],
)
def test_rejeita_temperaturas_invalidas(temperatura):
    with pytest.raises(ValidationError):
        PredictRequest.model_validate({
            "smiles": "CCO",
            "temperature_c": temperatura,
        })


def test_smiles_obrigatorio():
    with pytest.raises(ValidationError):
        PredictRequest.model_validate({
            "temperature_c": 25,
        })


@pytest.mark.parametrize(
    "campo",
    ["solvent", "model"],
)
def test_rejeita_campos_nao_permitidos(campo):
    with pytest.raises(ValidationError):
        PredictRequest.model_validate({
            "smiles": "CCO",
            campo: "other",
        })


def test_schema_de_resposta_tem_campos_previstos():
    # Valor artificial somente para validar tipos e estrutura.
    resposta = PredictResponse(
        log_s_mol_l=-0.5,
        temperature_c=25,
        temperature_k=298.15,
        model_version="teste-unitario",
        warnings=[
            "Exemplo sintético, não é uma medição."
        ],
    )

    assert resposta.model_dump() == {
        "log_s_mol_l": -0.5,
        "temperature_c": 25.0,
        "temperature_k": 298.15,
        "solvent": "methanol",
        "model_version": "teste-unitario",
        "warnings": [
            "Exemplo sintético, não é uma medição."
        ],
    }


def test_resposta_rejeita_predicao_nao_finita():
    with pytest.raises(ValidationError):
        PredictResponse(
            log_s_mol_l=float("nan"),
            temperature_c=25,
            temperature_k=298.15,
            model_version="teste-unitario",
            warnings=[],
        )


def test_schema_padronizado_de_erro():
    erro = ErrorResponse.model_validate({
        "error": {
            "code": "invalid_smiles",
            "message": (
                "A estrutura SMILES informada não é válida."
            ),
        }
    })

    assert erro.error.code == "invalid_smiles"
    assert "error" in erro.model_dump()
