
"""C24: testes do predictor com artefato sintético confiável."""

import hashlib
import importlib
import json
import sys

import joblib
import numpy as np
import pandas as pd
import pytest
import rdkit
import sklearn
from fastapi.testclient import TestClient
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app import predictor as mod
from app.chemistry import FEATURE_NAMES, extrair_atributos
from app.schemas import PredictRequest


@pytest.fixture
def pasta_modelo(tmp_path):
    """Cria modelo sintético local para os testes."""

    moleculas = [
        "C", "CC", "CCC",
        "CO", "CCO", "CCN",
    ]

    temperaturas = [
        273.15, 298.15, 323.15,
    ]

    linhas = [
        extrair_atributos(s, t)
        for s in moleculas
        for t in temperaturas
    ]

    x = pd.DataFrame(
        linhas,
        columns=list(FEATURE_NAMES),
    )

    y = np.linspace(
        -2.0,
        1.0,
        len(x),
    )

    pipeline = Pipeline([
        ("escala", StandardScaler()),
        ("modelo", Ridge(alpha=1.0)),
    ])

    pipeline.fit(x, y)

    caminho = tmp_path / mod.NOME_MODELO
    joblib.dump(pipeline, caminho)

    meta = {
        "model_info": {
            "model_version": "ridge-v1",
            "dataset_name": "BigSolDB",
            "dataset_version": "2.0",
            "dataset_doi": (
                "10.5281/zenodo.15094979"
            ),
            "target": "LogS(mol/L)",
            "solvent": "methanol",
            "feature_names": list(FEATURE_NAMES),
            "trained_at": "2026-11-21",
            "metrics": {
                "mae": 0.7,
                "rmse": 0.9,
                "r2": 0.2,
            },
            "training_temperature_range_k": {
                "min": 273.15,
                "max": 323.15,
            },
            "software_versions": {
                "python": sys.version.split()[0],
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "rdkit": rdkit.__version__,
                "scikit-learn": sklearn.__version__,
                "joblib": joblib.__version__,
            },
        },
        "selection": {
            "selected_model": "Ridge",
        },
        "training": {
            "source_filename": "treino.csv",
            "artifact_filename": mod.NOME_MODELO,
            "artifact_sha256": hashlib.sha256(
                caminho.read_bytes()
            ).hexdigest(),
            "test_final_used": False,
        },
    }

    (
        tmp_path / mod.NOME_METADADOS
    ).write_text(
        json.dumps(meta),
        encoding="utf-8",
    )

    return tmp_path


def test_carregamento_e_inferencia(pasta_modelo):
    modelo = mod.carregar_predictor(
        pasta_modelo
    )

    resultado = modelo.prever(
        PredictRequest(
            smiles="CCO",
            temperature_c=25.0,
        )
    )

    assert np.isfinite(
        resultado.log_s_mol_l
    )

    assert resultado.temperature_k == pytest.approx(
        298.15
    )

    assert resultado.model_version == "ridge-v1"
    assert resultado.solvent == "methanol"
    assert len(resultado.warnings) == 1


def test_temperatura_omitida_falha(pasta_modelo):
    modelo = mod.carregar_predictor(pasta_modelo)

    with pytest.raises(
        mod.EntradaInvalida,
        match="temperature_c",
    ):
        modelo.prever(
            PredictRequest(smiles="CCO")
        )


def test_temperatura_fora_da_faixa_gera_aviso(
    pasta_modelo,
):
    modelo = mod.carregar_predictor(pasta_modelo)

    resultado = modelo.prever(
        PredictRequest(
            smiles="CCO",
            temperature_c=100,
        )
    )

    assert any(
        "extrapolação" in aviso
        for aviso in resultado.warnings
    )


def test_sem_artefato_falha(tmp_path):
    with pytest.raises(
        mod.ModeloIndisponivel
    ):
        mod.carregar_predictor(tmp_path)


def test_artefato_alterado_nao_chega_ao_joblib(
    pasta_modelo,
    monkeypatch,
):
    arquivo = pasta_modelo / mod.NOME_MODELO

    arquivo.write_bytes(
        arquivo.read_bytes() + b"alterado"
    )

    def nao_carregar(*args, **kwargs):
        raise AssertionError(
            "joblib.load não pode ser executado"
        )

    monkeypatch.setattr(
        mod.joblib,
        "load",
        nao_carregar,
    )

    with pytest.raises(
        mod.ModeloIndisponivel,
        match="SHA-256",
    ):
        mod.carregar_predictor(pasta_modelo)


def test_incompatibilidade_de_versao_bloqueia(
    pasta_modelo,
):
    caminho = pasta_modelo / mod.NOME_METADADOS

    dados = json.loads(
        caminho.read_text(encoding="utf-8")
    )

    dados["model_info"]["software_versions"][
        "scikit-learn"
    ] = "0.0.0"

    caminho.write_text(
        json.dumps(dados),
        encoding="utf-8",
    )

    with pytest.raises(
        mod.ModeloIndisponivel,
        match="Versão incompatível",
    ):
        mod.carregar_predictor(pasta_modelo)


def test_atributos_fora_de_ordem_bloqueia(
    pasta_modelo,
):
    caminho = pasta_modelo / mod.NOME_METADADOS

    dados = json.loads(
        caminho.read_text(encoding="utf-8")
    )

    dados["model_info"][
        "feature_names"
    ].reverse()

    caminho.write_text(
        json.dumps(dados),
        encoding="utf-8",
    )

    with pytest.raises(
        mod.ModeloIndisponivel,
        match="Metadados incompatíveis",
    ):
        mod.carregar_predictor(pasta_modelo)


def test_rejeita_metadados_corrompidos(
    pasta_modelo,
):
    caminho = pasta_modelo / mod.NOME_METADADOS

    caminho.write_text(
        "{json quebrado",
        encoding="utf-8",
    )

    with pytest.raises(
        mod.ModeloIndisponivel,
        match="Metadados inválidos",
    ):
        mod.carregar_predictor(pasta_modelo)


def test_rejeita_symlink(
    pasta_modelo,
    tmp_path,
):
    nova_pasta = tmp_path / "links"
    nova_pasta.mkdir()

    (
        nova_pasta / mod.NOME_MODELO
    ).symlink_to(
        pasta_modelo / mod.NOME_MODELO
    )

    (
        nova_pasta / mod.NOME_METADADOS
    ).write_bytes(
        (
            pasta_modelo / mod.NOME_METADADOS
        ).read_bytes()
    )

    with pytest.raises(
        mod.ModeloIndisponivel,
        match="Arquivo ausente ou não permitido",
    ):
        mod.carregar_predictor(nova_pasta)


def test_cache_uma_vez(monkeypatch):
    mod.obter_predictor.cache_clear()

    chamadas = []

    def fake():
        chamadas.append("chamada")
        raise mod.ModeloIndisponivel(
            "ausente"
        )

    monkeypatch.setattr(
        mod,
        "carregar_predictor",
        fake,
    )

    assert mod.obter_predictor() is None
    assert mod.obter_predictor() is None
    assert len(chamadas) == 1

    mod.obter_predictor.cache_clear()


def test_api_health_e_model_info_com_artefato(
    pasta_modelo,
    monkeypatch,
):
    api = importlib.import_module(
        "app.main"
    )

    modelo = mod.carregar_predictor(
        pasta_modelo
    )

    monkeypatch.setattr(
        api,
        "obter_predictor",
        lambda: modelo,
    )

    api.app.dependency_overrides.clear()

    with TestClient(api.app) as cliente:
        resposta_health = cliente.get(
            "/api/health"
        )

        resposta_info = cliente.get(
            "/api/model-info"
        )

    assert resposta_health.status_code == 200

    assert resposta_health.json() == {
        "status": "ok",
        "model_available": True,
        "model_version": "ridge-v1",
    }

    assert resposta_info.status_code == 200

    assert resposta_info.json()[
        "feature_names"
    ] == list(FEATURE_NAMES)


def test_api_degradada_quando_artefato_ausente(
    monkeypatch,
):
    api = importlib.import_module(
        "app.main"
    )

    monkeypatch.setattr(
        api,
        "obter_predictor",
        lambda: None,
    )

    api.app.dependency_overrides.clear()

    with TestClient(api.app) as cliente:
        assert (
            cliente.get("/api/health").status_code
            == 503
        )

        assert (
            cliente.get("/api/model-info").status_code
            == 503
        )
