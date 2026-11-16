
"""Testes isolados da primeira rota FastAPI."""

import pytest

from fastapi.testclient import TestClient

from app.main import app, consultar_estado_modelo


@pytest.fixture
def client():
    """Cria cliente HTTP de teste e limpa substituições."""
    with TestClient(app) as cliente:
        yield cliente

    app.dependency_overrides.clear()


def test_health_degradado_sem_modelo(client):
    """Sem artefato integrado, deve responder HTTP 503."""

    resposta = client.get("/api/health")

    assert resposta.status_code == 503

    assert resposta.json() == {
        "status": "degraded",
        "model_available": False,
        "model_version": None,
    }


def test_health_ok_somente_em_simulacao_de_teste(client):
    """Simula modelo disponível somente neste teste."""

    app.dependency_overrides[
        consultar_estado_modelo
    ] = lambda: (True, "teste-simulado")

    resposta = client.get("/api/health")

    assert resposta.status_code == 200

    assert resposta.json() == {
        "status": "ok",
        "model_available": True,
        "model_version": "teste-simulado",
    }


def test_health_nao_declara_pronto_sem_versao(client):
    """Disponibilidade sem versão não significa modelo pronto."""

    app.dependency_overrides[
        consultar_estado_modelo
    ] = lambda: (True, None)

    resposta = client.get("/api/health")

    assert resposta.status_code == 503
    assert resposta.json()["model_available"] is False
    assert resposta.json()["model_version"] is None


def test_health_nao_declara_pronto_com_versao_vazia(client):
    """Versão contendo apenas espaços é inválida."""

    app.dependency_overrides[
        consultar_estado_modelo
    ] = lambda: (True, "   ")

    resposta = client.get("/api/health")

    assert resposta.status_code == 503
    assert resposta.json()["status"] == "degraded"


def test_metodo_post_no_health_nao_e_permitido(client):
    """O contrato define apenas GET para /api/health."""

    resposta = client.post("/api/health")

    assert resposta.status_code == 405


def test_openapi_documenta_health_e_503(client):
    """Confere a documentação automática da API."""

    resposta = client.get("/openapi.json")

    assert resposta.status_code == 200

    rotas = resposta.json()["paths"]

    assert "/api/health" in rotas

    assert (
        "503"
        in rotas["/api/health"]["get"]["responses"]
    )

    # Essas rotas pertencem a commits posteriores.
    assert "/api/predict" not in rotas
    assert "/api/model-info" not in rotas
