
"""C26 — Testes do tratamento padronizado de erros HTTP."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.predictor import obter_predictor


@pytest.fixture
def client():
    """Mantém os testes independentes do artefato real."""

    app.dependency_overrides.clear()

    app.dependency_overrides[
        obter_predictor
    ] = lambda: None

    try:
        with TestClient(app) as cliente:
            yield cliente
    finally:
        app.dependency_overrides.clear()


def conferir_erro(resposta, status, codigo, mensagem):
    """Verifica status e formato exato do contrato."""

    assert resposta.status_code == status
    assert resposta.json() == {
        "error": {
            "code": codigo,
            "message": mensagem,
        }
    }

    assert resposta.headers["content-type"].startswith(
        "application/json"
    )


@pytest.mark.parametrize(
    "dados",
    [
        {"smiles": "C1(", "temperature_c": 25},
        {"smiles": "", "temperature_c": 25},
        {"smiles": 123, "temperature_c": 25},
        {"temperature_c": 25},
    ],
)
def test_smiles_invalidos(client, dados):
    resposta = client.post(
        "/api/predict",
        json=dados,
    )

    conferir_erro(
        resposta,
        422,
        "invalid_smiles",
        "A estrutura SMILES informada não é válida.",
    )

    # Não retorna os dados submetidos pelo usuário.
    assert "C1(" not in resposta.text


@pytest.mark.parametrize(
    "temperatura",
    [
        -273.15,
        -300,
        True,
        "25",
    ],
)
def test_temperaturas_invalidas(client, temperatura):
    resposta = client.post(
        "/api/predict",
        json={
            "smiles": "CCO",
            "temperature_c": temperatura,
        },
    )

    conferir_erro(
        resposta,
        422,
        "invalid_temperature",
        "A temperatura informada não é válida.",
    )


@pytest.mark.parametrize(
    "dados",
    [
        {
            "smiles": "CCO",
            "temperature_c": 25,
            "solvent": "water",
        },
        [],
        {
            "smiles": "C1(",
            "temperature_c": -300,
        },
    ],
)
def test_requisicoes_invalidas(client, dados):
    resposta = client.post(
        "/api/predict",
        json=dados,
    )

    conferir_erro(
        resposta,
        422,
        "invalid_request",
        "Requisição inválida. Verifique os campos enviados.",
    )


def test_json_malformado(client):
    resposta = client.post(
        "/api/predict",
        content=b'{"smiles": ',
        headers={
            "Content-Type": "application/json",
        },
    )

    conferir_erro(
        resposta,
        422,
        "invalid_request",
        "Requisição inválida. Verifique os campos enviados.",
    )


def test_temperatura_omitida_mantem_contrato(client):
    resposta = client.post(
        "/api/predict",
        json={"smiles": "CCO"},
    )

    conferir_erro(
        resposta,
        422,
        "invalid_temperature",
        (
            "Informe temperature_c em graus Celsius; "
            "ainda não há padrão automático."
        ),
    )


def test_endpoint_inexistente_na_api(client):
    resposta = client.get(
        "/api/endpoint-inexistente"
    )

    conferir_erro(
        resposta,
        404,
        "invalid_request",
        "Endpoint não encontrado.",
    )


def test_metodo_invalido_e_cabecalho_allow(client):
    resposta = client.get(
        "/api/predict"
    )

    conferir_erro(
        resposta,
        405,
        "invalid_request",
        "Método HTTP não permitido para este endpoint.",
    )

    assert "POST" in resposta.headers["allow"]


def test_rotas_fora_da_api_mantem_comportamento(client):
    resposta = client.get(
        "/rota-inexistente"
    )

    assert resposta.status_code == 404

    assert resposta.json() == {
        "detail": "Not Found",
    }


def test_openapi_documenta_formato_422(client):
    resposta = client.get(
        "/openapi.json"
    )

    assert resposta.status_code == 200

    respostas = resposta.json()["paths"][
        "/api/predict"
    ]["post"]["responses"]

    assert "422" in respostas

    esquema = respostas["422"]["content"][
        "application/json"
    ]["schema"]

    assert esquema["$ref"].endswith(
        "/ErrorResponse"
    )
