"""C29: integração CSV sintético -> Ridge salvo -> predictor -> FastAPI.

Não utiliza dados reais de treino, nem o arquivo reservado teste.csv.
A seleção comparativa é simulada; o ajuste Ridge é verdadeiro.
"""

import hashlib
import importlib
import json
import shutil
from pathlib import Path
from unittest.mock import patch

import joblib
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.pipeline import Pipeline

from app import predictor as servico
from app.predictor import carregar_predictor as carregar_predictor_original
from app.chemistry import FEATURE_NAMES, extrair_atributos
from app.schemas import ModelInfoResponse, PredictRequest
from scripts import persistir_modelo as persistencia
from scripts.treinar_modelos import construir_atributos

api = importlib.import_module("app.main")


@pytest.fixture(scope="module")
def cenario_sintetico(tmp_path_factory):
    """Persiste de verdade um Ridge com registros fictícios.

    Somente a comparação C16 é controlada para garantir seleção estável.
    """
    raiz = tmp_path_factory.mktemp("c29_integracao")
    dados_dir = raiz / "dados"
    dados_dir.mkdir()
    treino = dados_dir / "treino.csv"
    teste_reservado = dados_dir / "teste.csv"
    artefatos = raiz / "artefatos"

    moleculas = (
        "C", "CC", "CCC", "CCCC", "CCO", "CO",
        "CCN", "N", "O", "COC", "CCCl", "CCBr",
    )
    linhas = []
    for indice, smiles in enumerate(moleculas):
        for temp_k in (273.15, 298.15, 320.15):
            linhas.append({
                "Source_Row": len(linhas),
                "SMILES_Canonico": smiles,
                "Temperature_K": temp_k,
                "LogS(mol/L)": (
                    -0.3 * indice + 0.012 * (temp_k - 298.15)
                ),
            })
    pd.DataFrame(linhas).to_csv(treino, index=False)

    # Sentinela deliberadamente ilegível como CSV científico válido.
    teste_reservado.write_bytes(b"C29_TESTE_FINAL_RESERVADO_NAO_LER\n")
    teste_sha_antes = hashlib.sha256(teste_reservado.read_bytes()).hexdigest()

    selecao_ficticia = {
        "semente": 42,
        "modelos": {
            "DummyRegressor": {"MAE": 1.1, "RMSE": 1.4, "R2": -0.1},
            "Ridge": {"MAE": 0.7, "RMSE": 0.9, "R2": 0.2},
            "RandomForest": {"MAE": 0.8, "RMSE": 1.0, "R2": 0.1},
        },
    }

    leituras = []
    leitura_original = pd.read_csv

    def ler_espiao(caminho, *args, **kwargs):
        leituras.append(Path(caminho).resolve())
        return leitura_original(caminho, *args, **kwargs)

    with (
        patch.object(persistencia, "comparar_modelos", return_value=selecao_ficticia) as comparar,
        patch.object(pd, "read_csv", side_effect=ler_espiao),
    ):
        meta = persistencia.treinar_e_salvar(treino, artefatos)

    comparar.assert_called_once()
    assert comparar.call_args.kwargs == {"semente": 42}

    return {
        "treino": treino,
        "teste_reservado": teste_reservado,
        "teste_sha": teste_sha_antes,
        "artefatos": artefatos,
        "metadata": meta,
        "leituras": leituras,
        "dados": pd.DataFrame(linhas),
    }


@pytest.fixture
def cliente_integrado(cenario_sintetico, monkeypatch):
    """A API carrega um Joblib real do diretório temporário, sem fake predictor."""
    carregar_original = servico.carregar_predictor
    diretorio = cenario_sintetico["artefatos"]

    monkeypatch.setattr(
        servico,
        "carregar_predictor",
        lambda: carregar_original(diretorio),
    )
    api.app.dependency_overrides.clear()
    servico.obter_predictor.cache_clear()

    try:
        with TestClient(api.app) as cliente:
            modelo = servico.obter_predictor()
            assert modelo is not None
            yield cliente, modelo
    finally:
        api.app.dependency_overrides.clear()
        servico.obter_predictor.cache_clear()


def test_treinamento_le_apenas_treino(cenario_sintetico):
    c = cenario_sintetico
    assert c["leituras"] == [c["treino"].resolve()]
    assert hashlib.sha256(
        c["teste_reservado"].read_bytes()
    ).hexdigest() == c["teste_sha"]
    assert c["metadata"]["training"]["test_final_used"] is False


def test_metadados_e_hashes_do_pipeline(cenario_sintetico):
    c = cenario_sintetico
    info = c["metadata"]["model_info"]
    treino_meta = c["metadata"]["training"]
    arquivo_modelo = c["artefatos"] / servico.NOME_MODELO
    arquivo_meta = c["artefatos"] / servico.NOME_METADADOS

    assert arquivo_modelo.is_file()
    assert json.loads(arquivo_meta.read_text(encoding="utf-8")) == c["metadata"]
    assert treino_meta["source_sha256"] == hashlib.sha256(
        c["treino"].read_bytes()
    ).hexdigest()
    assert treino_meta["artifact_sha256"] == hashlib.sha256(
        arquivo_modelo.read_bytes()
    ).hexdigest()
    assert treino_meta["records"] == 36
    assert treino_meta["molecules"] == 12
    assert info["feature_names"] == list(FEATURE_NAMES)
    assert c["metadata"]["selection"]["selected_model"] == "Ridge"
    ModelInfoResponse.model_validate(info)


def test_descritores_consistentes_entre_treino_e_inferencia(cenario_sintetico):
    c = cenario_sintetico
    x_treino = construir_atributos(c["dados"])
    assert list(x_treino.columns) == list(FEATURE_NAMES)
    posicao = c["dados"].index[
        (c["dados"]["SMILES_Canonico"] == "CCO")
        & (c["dados"]["Temperature_K"] == 298.15)
    ][0]
    atributos = extrair_atributos("CCO", 298.15)
    assert list(atributos) == list(FEATURE_NAMES)
    np.testing.assert_allclose(
        x_treino.loc[posicao].to_numpy(dtype=float),
        np.array(list(atributos.values())),
        rtol=0,
        atol=1e-10,
    )


def test_pipeline_salvo_e_predictor_concordam(cliente_integrado):
    _, modelo = cliente_integrado
    pedido = PredictRequest(smiles="CCO", temperature_c=25.0)
    valores = pd.DataFrame(
        [extrair_atributos(pedido.smiles, pedido.temperature_k)],
        columns=list(FEATURE_NAMES),
    )
    estimativa_direta = float(modelo._pipeline.predict(valores)[0])
    resultado = modelo.prever(pedido)
    assert np.isfinite(estimativa_direta)
    assert resultado.log_s_mol_l == pytest.approx(estimativa_direta, abs=1e-12)


def test_health_e_metadados_usam_modelo_salvo(cliente_integrado):
    cliente, modelo = cliente_integrado
    health = cliente.get("/api/health")
    info = cliente.get("/api/model-info")
    assert health.status_code == 200
    assert health.json() == {
        "status": "ok", "model_available": True, "model_version": "ridge-v1"
    }
    assert info.status_code == 200
    assert info.json()["feature_names"] == list(FEATURE_NAMES)
    assert info.json()["metrics"]["mae"] == pytest.approx(0.7)
    assert info.json()["model_version"] == modelo.info.model_version


def test_http_prediz_igual_ao_predictor(cliente_integrado):
    cliente, modelo = cliente_integrado
    resposta = cliente.post(
        "/api/predict", json={"smiles": "CCO", "temperature_c": 25.0}
    )
    assert resposta.status_code == 200
    dados = resposta.json()
    esperado = modelo.prever(PredictRequest(smiles="CCO", temperature_c=25.0))
    assert dados["log_s_mol_l"] == pytest.approx(esperado.log_s_mol_l, abs=1e-12)
    assert dados["temperature_k"] == pytest.approx(298.15)
    assert dados["solvent"] == "methanol"
    assert dados["model_version"] == "ridge-v1"
    assert dados["warnings"] == esperado.warnings


def test_smiles_equivalentes_geram_mesmo_resultado(cliente_integrado):
    cliente, _ = cliente_integrado
    respostas = [
        cliente.post(
            "/api/predict",
            json={"smiles": smiles, "temperature_c": 25},
        )
        for smiles in ("CCO", "OCC")
    ]
    assert all(r.status_code == 200 for r in respostas)
    assert respostas[0].json()["log_s_mol_l"] == pytest.approx(
        respostas[1].json()["log_s_mol_l"], abs=1e-12
    )


def test_temperatura_fora_da_faixa_sinaliza_extrapolacao(cliente_integrado):
    cliente, _ = cliente_integrado
    resposta = cliente.post(
        "/api/predict", json={"smiles": "CCO", "temperature_c": 100}
    )
    assert resposta.status_code == 200
    assert resposta.json()["temperature_k"] == pytest.approx(373.15)
    assert any("extrapolação" in aviso for aviso in resposta.json()["warnings"])


@pytest.mark.parametrize(
    ("corpo", "codigo"),
    [
        ({"smiles": "C1(", "temperature_c": 25}, "invalid_smiles"),
        ({"smiles": "CCO", "temperature_c": -300}, "invalid_temperature"),
        ({"smiles": "CCO"}, "invalid_temperature"),
        ({"smiles": "CCO", "temperature_c": 25, "solvent": "water"}, "invalid_request"),
    ],
)
def test_erros_http_padronizados(cliente_integrado, corpo, codigo):
    cliente, _ = cliente_integrado
    resposta = cliente.post("/api/predict", json=corpo)
    assert resposta.status_code == 422
    assert resposta.json()["error"]["code"] == codigo
    assert "detail" not in resposta.json()


def test_requisicoes_nao_treinam_nem_leem_csv(cliente_integrado):
    cliente, _ = cliente_integrado  # Predictor já está carregado.
    with (
        patch.object(Pipeline, "fit", side_effect=AssertionError("fit na API")),
        patch.object(pd, "read_csv", side_effect=AssertionError("CSV na API")),
        patch.object(joblib, "dump", side_effect=AssertionError("dump na API")),
    ):
        for _ in range(2):
            assert cliente.post(
                "/api/predict", json={"smiles": "CCO", "temperature_c": 25}
            ).status_code == 200
        assert cliente.get("/api/health").status_code == 200
        assert cliente.get("/api/model-info").status_code == 200


def test_cache_evitar_carregamento_repetido(cliente_integrado, monkeypatch):
    cliente, _ = cliente_integrado
    original = servico.carregar_predictor
    chamadas = []

    def contar():
        chamadas.append(True)
        return original()

    monkeypatch.setattr(servico, "carregar_predictor", contar)
    servico.obter_predictor.cache_clear()

    assert cliente.get("/api/health").status_code == 200
    assert cliente.get("/api/model-info").status_code == 200
    assert cliente.post(
        "/api/predict", json={"smiles": "CCO", "temperature_c": 25}
    ).status_code == 200
    assert len(chamadas) == 1


def test_artefato_corrompido_degrada_api(cliente_integrado, cenario_sintetico, tmp_path):
    cliente, _ = cliente_integrado
    pasta_ruim = tmp_path / "corrompido"
    pasta_ruim.mkdir()
    for nome in (servico.NOME_MODELO, servico.NOME_METADADOS):
        shutil.copy2(cenario_sintetico["artefatos"] / nome, pasta_ruim / nome)

    with (pasta_ruim / servico.NOME_MODELO).open("ab") as arquivo:
        arquivo.write(b"modificado")

    # Redireciona o carregamento para uma cópia corrompida.
    with patch.object(
        servico, "carregar_predictor",
        side_effect=lambda: _carregar_integro(pasta_ruim),
    ):
        servico.obter_predictor.cache_clear()
        assert cliente.get("/api/health").status_code == 503
        assert cliente.get("/api/model-info").status_code == 503
        resposta = cliente.post(
            "/api/predict", json={"smiles": "CCO", "temperature_c": 25}
        )
        assert resposta.status_code == 503
        assert resposta.json()["error"]["code"] == "model_unavailable"


def _carregar_integro(diretorio):
    """Evita duplicar o algoritmo de integridade; usa a função original."""
    return carregar_predictor_original(diretorio)


def test_regressao_artefato_real_quando_disponivel():
    """Teste opcional: verifica artefato do C23, sem ler os CSVs reais."""
    caminho = servico.ARTEFATOS / servico.NOME_MODELO
    if not caminho.is_file():
        pytest.skip("Joblib real não está disponível neste ambiente")

    try:
        modelo = _carregar_integro(servico.ARTEFATOS)
    except servico.ModeloIndisponivel as erro:
        if "Versão incompatível" in str(erro):
            pytest.skip("Versões de execução incompatíveis com o Joblib do C23")
        raise

    resultado = modelo.prever(PredictRequest(smiles="CCO", temperature_c=25.0))
    assert resultado.model_version == "ridge-v1"
    assert resultado.temperature_k == pytest.approx(298.15)
    # Regressão numérica observada no C24/C25 para o Joblib original do C23.
    assert resultado.log_s_mol_l == pytest.approx(0.1574631425041294, abs=1e-9)
