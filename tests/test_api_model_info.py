
"""Testes do endpoint /api/model-info.

Os metadados artificiais existem exclusivamente nos testes.
Nenhum artefato real é carregado.
"""

import pytest

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.chemistry import FEATURE_NAMES
from app.main import (
    app,
    consultar_metadados_modelo,
)
from app.schemas import ModelInfoResponse


@pytest.fixture
def client():
    """Cria cliente de teste e limpa dependências simuladas."""

    app.dependency_overrides.clear()

    with TestClient(app) as cliente:
        yield cliente

    app.dependency_overrides.clear()


def metadados_sinteticos():
    """Constrói metadados fictícios apenas para os testes."""

    return ModelInfoResponse.model_validate({
        "model_version": "simulado-apenas-teste",
        "dataset_name": "BigSolDB",
        "dataset_version": "2.0",
        "dataset_doi": "10.5281/zenodo.15094979",
        "target": "LogS(mol/L)",
        "solvent": "methanol",
        "feature_names": list(FEATURE_NAMES),
        "trained_at": "2026-11-16",
        "metrics": {
            "mae": 0.5,
            "rmse": 0.7,
            "r2": -0.1,
        },
        "training_temperature_range_k": {
            "min": 250.0,
            "max": 340.0,
        },
        "software_versions": {
            "python": "versao-simulada",
        },
    })


def test_model_info_sem_artefato_retorna_503(client):
    resposta = client.get("/api/model-info")

    assert resposta.status_code == 503

    assert resposta.json() == {
        "error": {
            "code": "model_unavailable",
            "message": "Metadados do modelo indisponíveis.",
        }
    }


def test_model_info_simulado_apenas_em_teste(client):
    esperado = metadados_sinteticos()

    app.dependency_overrides[
        consultar_metadados_modelo
    ] = lambda: esperado

    resposta = client.get("/api/model-info")

    assert resposta.status_code == 200

    assert resposta.json() == esperado.model_dump(
        mode="json"
    )


def test_health_permanece_degradado(client):
    resposta = client.get("/api/health")

    assert resposta.json()["model_available"] is False


def test_model_info_so_aceita_get(client):
    resposta = client.post("/api/model-info")

    assert resposta.status_code == 405


def test_openapi_documenta_200_e_503(client):
    resposta = client.get("/openapi.json")

    assert resposta.status_code == 200

    rotas = resposta.json()["paths"]

    assert "/api/model-info" in rotas

    respostas = rotas[
        "/api/model-info"
    ]["get"]["responses"]

    assert {"200", "503"}.issubset(respostas)


def test_metadados_rejeitam_campo_obrigatorio_ausente():
    dados = metadados_sinteticos().model_dump()

    del dados["metrics"]

    with pytest.raises(ValidationError):
        ModelInfoResponse.model_validate(dados)


def test_metricas_rejeitam_valores_nao_finitos():
    dados = metadados_sinteticos().model_dump()

    dados["metrics"]["rmse"] = float("inf")

    with pytest.raises(ValidationError):
        ModelInfoResponse.model_validate(dados)


def test_intervalo_temperatura_invertido_nao_e_aceito():
    dados = metadados_sinteticos().model_dump()

    dados["training_temperature_range_k"] = {
        "min": 350.0,
        "max": 250.0,
    }

    with pytest.raises(ValidationError):
        ModelInfoResponse.model_validate(dados)


def test_atributos_repetidos_nao_sao_aceitos():
    dados = metadados_sinteticos().model_dump()

    dados["feature_names"] = [
        "MolWt",
        "MolWt",
    ]

    with pytest.raises(ValidationError):
        ModelInfoResponse.model_validate(dados)
