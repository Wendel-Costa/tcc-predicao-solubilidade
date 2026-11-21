
"""Testes do C23 com dados SINTÉTICOS e comparação controlada."""

import hashlib
import json

import joblib
import numpy as np
import pandas as pd
import pytest

from app.chemistry import FEATURE_NAMES, extrair_atributos
from app.schemas import ModelInfoResponse
from scripts import persistir_modelo as modulo


@pytest.fixture
def treino_csv(tmp_path):
    smiles = [
        "C", "CC", "CCC", "CCCC", "CCO", "CO",
        "CCN", "O", "N", "COC", "CCCl", "CCBr",
    ]

    linhas = []

    for indice, molecula in enumerate(smiles):
        for temperatura in (273.15, 298.15, 320.15):
            linhas.append({
                "Source_Row": len(linhas),
                "SMILES_Canonico": molecula,
                "Temperature_K": temperatura,
                "LogS(mol/L)": (
                    -0.2 * indice
                    + 0.001 * (temperatura - 298.15)
                ),
            })

    caminho = tmp_path / "treino.csv"

    pd.DataFrame(linhas).to_csv(
        caminho, index=False
    )

    return caminho


@pytest.fixture
def comparacao_controlada(monkeypatch):
    # Valores somente para os testes.
    # NÃO são métricas do TCC.
    comparacao = {
        "semente": 42,
        "modelos": {
            "DummyRegressor": {
                "MAE": 1.1, "RMSE": 1.3, "R2": -0.1,
            },
            "Ridge": {
                "MAE": 0.7, "RMSE": 0.9, "R2": 0.2,
            },
            "RandomForest": {
                "MAE": 0.8, "RMSE": 1.0, "R2": 0.1,
            },
        },
    }

    monkeypatch.setattr(
        modulo,
        "comparar_modelos",
        lambda dados, semente: comparacao,
    )

    return comparacao


def test_artefato_e_metadados_coerentes(
    treino_csv, tmp_path, comparacao_controlada
):
    saida = tmp_path / "models"

    meta = modulo.treinar_e_salvar(
        treino_csv, saida
    )

    binario = saida / "ridge-v1.joblib"
    json_path = saida / "ridge-v1.metadata.json"

    assert binario.is_file()
    assert json_path.is_file()

    assert json.loads(
        json_path.read_text(encoding="utf-8")
    ) == meta

    assert meta["training"]["source_sha256"] == (
        hashlib.sha256(
            treino_csv.read_bytes()
        ).hexdigest()
    )

    assert meta["training"]["artifact_sha256"] == (
        hashlib.sha256(
            binario.read_bytes()
        ).hexdigest()
    )

    assert meta["training"]["records"] == 36
    assert meta["training"]["molecules"] == 12
    assert meta["training"]["test_final_used"] is False
    assert meta["selection"]["selected_model"] == "Ridge"
    assert meta["model_info"]["metrics"]["mae"] == 0.7

    ModelInfoResponse.model_validate(
        meta["model_info"]
    )


def test_pipeline_salvo_prediz_finito_e_preserva_ordem(
    treino_csv, tmp_path, comparacao_controlada
):
    saida = tmp_path / "models"
    modulo.treinar_e_salvar(treino_csv, saida)

    # Apenas um artefato gerado pelo próprio teste.
    pipeline = joblib.load(
        saida / "ridge-v1.joblib"
    )

    assert list(pipeline.feature_names_in_) == list(
        FEATURE_NAMES
    )
    assert list(pipeline.named_steps) == [
        "escala", "modelo"
    ]

    amostra = pd.DataFrame(
        [extrair_atributos("CCO", 298.15)],
        columns=list(FEATURE_NAMES),
    )

    assert np.isfinite(
        pipeline.predict(amostra)
    ).all()


def test_nao_sobrescreve_artefato(
    treino_csv, tmp_path, comparacao_controlada
):
    saida = tmp_path / "models"
    modulo.treinar_e_salvar(treino_csv, saida)

    with pytest.raises(FileExistsError):
        modulo.treinar_e_salvar(treino_csv, saida)


@pytest.mark.parametrize(
    "nome",
    ["teste.csv", "metanol_curado.csv"],
)
def test_rejeita_entrada_que_nao_e_treino(
    nome, tmp_path
):
    caminho = tmp_path / nome
    caminho.write_text(
        "nada", encoding="utf-8"
    )

    with pytest.raises(
        ValueError, match="treino.csv"
    ):
        modulo.treinar_e_salvar(
            caminho, tmp_path / "models"
        )


def test_rejeita_arquivo_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        modulo.treinar_e_salvar(
            tmp_path / "treino.csv",
            tmp_path / "models",
        )


def test_rejeita_source_row_duplicado(
    treino_csv, tmp_path
):
    dados = pd.read_csv(treino_csv)

    dados.loc[1, "Source_Row"] = dados.loc[
        0, "Source_Row"
    ]

    dados.to_csv(treino_csv, index=False)

    with pytest.raises(
        ValueError, match="Source_Row"
    ):
        modulo.treinar_e_salvar(
            treino_csv, tmp_path / "models"
        )


def test_rejeita_temperatura_invalida(
    treino_csv, tmp_path
):
    dados = pd.read_csv(treino_csv)
    dados.loc[0, "Temperature_K"] = 0
    dados.to_csv(treino_csv, index=False)

    with pytest.raises(
        ValueError, match="Temperature_K"
    ):
        modulo.treinar_e_salvar(
            treino_csv, tmp_path / "models"
        )


def test_rejeita_alvo_ausente(
    treino_csv, tmp_path
):
    dados = pd.read_csv(treino_csv)

    dados = dados.drop(
        columns=["LogS(mol/L)"]
    )
    dados.to_csv(treino_csv, index=False)

    with pytest.raises(
        ValueError, match="Colunas obrigatórias"
    ):
        modulo.treinar_e_salvar(
            treino_csv, tmp_path / "models"
        )


def test_nao_salva_se_outra_tecnica_vencer(
    treino_csv,
    tmp_path,
    monkeypatch,
    comparacao_controlada,
):
    comparacao_controlada["modelos"][
        "RandomForest"
    ]["MAE"] = 0.1

    with pytest.raises(
        RuntimeError, match="Seleção divergente"
    ):
        modulo.treinar_e_salvar(
            treino_csv, tmp_path / "models"
        )

    assert not (
        tmp_path / "models" / "ridge-v1.joblib"
    ).exists()
