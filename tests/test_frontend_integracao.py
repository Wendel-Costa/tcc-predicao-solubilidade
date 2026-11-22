
"""C27: integração entre entrega do frontend e API FastAPI."""

import pytest

from fastapi.testclient import TestClient

from app.main import app
from app.predictor import obter_predictor
from app.schemas import PredictResponse


@pytest.fixture
def client():
    app.dependency_overrides.clear()

    try:
        with TestClient(app) as cliente:
            yield cliente
    finally:
        app.dependency_overrides.clear()


def test_raiz_redireciona_para_frontend(client):
    resposta = client.get(
        "/",
        follow_redirects=False,
    )

    assert resposta.status_code == 307
    assert resposta.headers["location"] == "/frontend/"


def test_html_servido_pela_fastapi(client):
    resposta = client.get("/frontend/")

    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith(
        "text/html"
    )

    assert 'id="predict-form"' in resposta.text
    assert 'id="result-panel"' in resposta.text

    assert 'href="styles.css"' in resposta.text
    assert 'src="app.js"' in resposta.text


@pytest.mark.parametrize(
    ("caminho", "tipo"),
    [
        ("/frontend/styles.css", "text/css"),
        ("/frontend/app.js", "javascript"),
    ],
)
def test_arquivos_estaticos_servidos(
    client,
    caminho,
    tipo,
):
    resposta = client.get(caminho)

    assert resposta.status_code == 200
    assert tipo in resposta.headers["content-type"]
    assert resposta.content


def test_js_aponta_para_api_na_mesma_origem(client):
    resposta = client.get("/frontend/app.js")

    assert resposta.status_code == 200

    codigo = resposta.text

    assert 'fetch("/api/predict"' in codigo
    assert '"POST"' in codigo
    assert "JSON.stringify" in codigo
    assert "AbortController" in codigo

    # Resultados são inseridos como texto.
    assert "textContent" in codigo
    assert "innerHTML" not in codigo


def test_predicao_por_http_na_mesma_aplicacao(client):
    class ModeloSimulado:
        def prever(self, pedido):
            return PredictResponse(
                log_s_mol_l=-0.125,
                temperature_c=pedido.temperature_c,
                temperature_k=pedido.temperature_k,
                solvent="methanol",
                model_version="teste-c27",
                warnings=["Aviso sintético do teste."],
            )

    app.dependency_overrides[
        obter_predictor
    ] = lambda: ModeloSimulado()

    resposta = client.post(
        "/api/predict",
        json={
            "smiles": "CCO",
            "temperature_c": 25,
        },
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["log_s_mol_l"] == -0.125
    assert dados["temperature_k"] == pytest.approx(
        298.15
    )
    assert dados["model_version"] == "teste-c27"
    assert dados["solvent"] == "methanol"
    assert dados["warnings"] == [
        "Aviso sintético do teste."
    ]


def test_modelo_indisponivel_retorna_503(client):
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

    assert resposta.json()["error"]["code"] == (
        "model_unavailable"
    )


def test_erro_smiles_retorna_422(client):
    app.dependency_overrides[
        obter_predictor
    ] = lambda: None

    resposta = client.post(
        "/api/predict",
        json={
            "smiles": "C1(",
            "temperature_c": 25,
        },
    )

    assert resposta.status_code == 422

    assert resposta.json()["error"]["code"] == (
        "invalid_smiles"
    )


def test_arquivo_estatico_inexistente_retorna_404(client):
    resposta = client.get(
        "/frontend/arquivo-inexistente.js"
    )

    assert resposta.status_code == 404


def test_openapi_continua_documentando_api(client):
    resposta = client.get("/openapi.json")

    assert resposta.status_code == 200

    rotas = resposta.json()["paths"]

    assert "/api/predict" in rotas
    assert "/api/health" in rotas
    assert "/api/model-info" in rotas

    # O frontend não precisa aparecer como endpoint REST.
    assert "/frontend/" not in rotas
