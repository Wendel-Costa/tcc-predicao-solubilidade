
"""C25 — Testes HTTP da API de predição.

Os valores simulados não representam resultados do BigSolDB.
"""

import pytest

from fastapi.testclient import TestClient

from app.main import app
from app.predictor import (
    EntradaInvalida,
    PredicaoFalhou,
    obter_predictor,
)
from app.schemas import PredictRequest, PredictResponse


class ModeloFalso:
    """Substitui o predictor real somente durante os testes."""

    def __init__(self):
        self.chamadas = []

    def prever(self, pedido):
        self.chamadas.append(pedido)

        avisos = [
            "Resultado sintético apenas para teste."
        ]

        if pedido.temperature_c >= 100:
            avisos.append(
                "Extrapolação simulada."
            )

        return PredictResponse(
            log_s_mol_l=-0.321,
            temperature_c=pedido.temperature_c,
            temperature_k=pedido.temperature_k,
            solvent="methanol",
            model_version="versao-teste",
            warnings=avisos,
        )


@pytest.fixture
def client():
    """Isola as dependências FastAPI entre os testes."""

    app.dependency_overrides.clear()

    try:
        with TestClient(app) as cliente:
            yield cliente
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def modelo_fake():
    return ModeloFalso()


def test_predicao_200(client, modelo_fake):
    app.dependency_overrides[
        obter_predictor
    ] = lambda: modelo_fake

    resposta = client.post(
        "/api/predict",
        json={
            "smiles": " CCO ",
            "temperature_c": 25,
        },
    )

    assert resposta.status_code == 200

    assert resposta.json() == {
        "log_s_mol_l": -0.321,
        "temperature_c": 25.0,
        "temperature_k": 298.15,
        "solvent": "methanol",
        "model_version": "versao-teste",
        "warnings": [
            "Resultado sintético apenas para teste."
        ],
    }

    assert len(modelo_fake.chamadas) == 1

    recebido = modelo_fake.chamadas[0]

    assert isinstance(
        recebido,
        PredictRequest,
    )

    assert recebido.smiles == "CCO"


def test_modelo_indisponivel_503(client):
    app.dependency_overrides[
        obter_predictor
    ] = lambda: None

    resposta = client.post(
        "/api/predict",
        json={
            "smiles": "CCO",
            "temperature_c": 25,
        },
    )

    assert resposta.status_code == 503

    assert resposta.json() == {
        "error": {
            "code": "model_unavailable",
            "message": "Modelo de predição indisponível.",
        }
    }


@pytest.mark.parametrize(
    "dados",
    [
        {"smiles": "CCO"},
        {
            "smiles": "CCO",
            "temperature_c": None,
        },
    ],
)
def test_temperatura_omitida_422(
    client,
    modelo_fake,
    dados,
):
    app.dependency_overrides[
        obter_predictor
    ] = lambda: modelo_fake

    resposta = client.post(
        "/api/predict",
        json=dados,
    )

    assert resposta.status_code == 422

    assert resposta.json()[
        "error"
    ]["code"] == "invalid_temperature"

    assert modelo_fake.chamadas == []


@pytest.mark.parametrize(
    "dados",
    [
        {
            "smiles": "C1(",
            "temperature_c": 25,
        },
        {
            "smiles": "",
            "temperature_c": 25,
        },
        {
            "smiles": "CCO",
            "temperature_c": -273.15,
        },
        {
            "smiles": "CCO",
            "temperature_c": 25,
            "solvent": "water",
        },
    ],
)
def test_campos_invalidos_422(
    client,
    modelo_fake,
    dados,
):
    app.dependency_overrides[
        obter_predictor
    ] = lambda: modelo_fake

    resposta = client.post(
        "/api/predict",
        json=dados,
    )

    assert resposta.status_code == 422

    # Até C26, campos inválidos seguem o padrão FastAPI.
    assert "detail" in resposta.json()

    assert modelo_fake.chamadas == []


def test_get_nao_permitido(client):
    resposta = client.get("/api/predict")

    assert resposta.status_code == 405


def test_falha_de_predicao_500(client):
    class ModeloComFalha:
        def prever(self, pedido):
            raise PredicaoFalhou(
                "dados internos sensiveis"
            )

    app.dependency_overrides[
        obter_predictor
    ] = lambda: ModeloComFalha()

    resposta = client.post(
        "/api/predict",
        json={
            "smiles": "CCO",
            "temperature_c": 25,
        },
    )

    assert resposta.status_code == 500

    assert resposta.json()[
        "error"
    ]["code"] == "prediction_failed"

    assert "sensiveis" not in str(
        resposta.json()
    )


def test_entrada_rejeitada_pelo_predictor_422(client):
    class ModeloComFalha:
        def prever(self, pedido):
            raise EntradaInvalida(
                "Temperatura recusada pelo serviço"
            )

    app.dependency_overrides[
        obter_predictor
    ] = lambda: ModeloComFalha()

    resposta = client.post(
        "/api/predict",
        json={
            "smiles": "CCO",
            "temperature_c": 25,
        },
    )

    assert resposta.status_code == 422

    assert resposta.json()[
        "error"
    ]["code"] == "invalid_temperature"


def test_falha_inesperada_500(client):
    class ModeloComFalha:
        def prever(self, pedido):
            raise RuntimeError(
                "erro interno"
            )

    app.dependency_overrides[
        obter_predictor
    ] = lambda: ModeloComFalha()

    resposta = client.post(
        "/api/predict",
        json={
            "smiles": "CCO",
            "temperature_c": 25,
        },
    )

    assert resposta.status_code == 500

    assert resposta.json()[
        "error"
    ]["code"] == "prediction_failed"


def test_avisos_do_predictor_sao_preservados(
    client,
    modelo_fake,
):
    app.dependency_overrides[
        obter_predictor
    ] = lambda: modelo_fake

    resposta = client.post(
        "/api/predict",
        json={
            "smiles": "CCO",
            "temperature_c": 100,
        },
    )

    assert resposta.status_code == 200

    assert (
        resposta.json()["warnings"][-1]
        == "Extrapolação simulada."
    )


def test_openapi_documenta_predict(client):
    resposta = client.get("/openapi.json")

    assert resposta.status_code == 200

    rotas = resposta.json()["paths"]

    assert "/api/predict" in rotas
    assert "post" in rotas["/api/predict"]

    respostas = rotas[
        "/api/predict"
    ]["post"]["responses"]

    assert {
        "200",
        "422",
        "503",
        "500",
    }.issubset(respostas)
