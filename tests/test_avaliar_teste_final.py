"""C30 — testes com partições e artefato SINTÉTICOS, nunca o teste real."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from scripts import avaliar_teste_final as c30


class ModeloSintetico:
    """Modelo determinístico do teste, sem artefato Joblib e sem fit()."""

    info = SimpleNamespace(
        model_version="ridge-v1",
        training_temperature_range_k=SimpleNamespace(min=273.15, max=320.15),
        metrics=SimpleNamespace(mae=0.8, rmse=1.0, r2=0.2),
    )

    def prever(self, pedido):
        return SimpleNamespace(
            model_version="ridge-v1",
            log_s_mol_l=-0.5 + 0.1 * len(pedido.smiles),
        )


@pytest.fixture
def cenario(tmp_path, monkeypatch):
    particoes = tmp_path / "split"
    particoes.mkdir()
    treino = particoes / "treino.csv"
    teste = particoes / "teste.csv"
    artefatos = tmp_path / "artifacts"
    artefatos.mkdir()
    saida = tmp_path / "reports" / "avaliacao_final_c30"

    pd.DataFrame({
        "Source_Row": [1, 2, 3, 4],
        "SMILES_Canonico": ["C", "CC", "CCC", "CO"],
        "Temperature_K": [280.15, 298.15, 310.15, 315.15],
        c30.ALVO: [-1.0, -0.8, -0.6, -0.5],
    }).to_csv(treino, index=False)
    pd.DataFrame({
        "Source_Row": [11, 12, 13],
        "SMILES_Canonico": ["CCO", "CCN", "O"],
        "Temperature_K": [260.15, 298.15, 400.15],
        c30.ALVO: [-0.4, -0.2, 0.0],
    }).to_csv(teste, index=False)
    (artefatos / "ridge-v1.joblib").write_bytes(b"modelo_sintetico_nao_desserializar")
    (artefatos / "ridge-v1.metadata.json").write_text(
        json.dumps({"training": {
            "source_sha256": c30.sha256(treino),
            "records": 4,
            "molecules": 4,
        }}), encoding="utf-8",
    )
    monkeypatch.setattr(c30, "carregar_predictor", lambda _: ModeloSintetico())
    return {"treino": treino, "teste": teste, "artefatos": artefatos, "saida": saida}


def executar(c):
    return c30.avaliar_teste_final(c["treino"], c["teste"], c["artefatos"], c["saida"])


def test_calcula_metricas_e_analise_sem_vazamento(cenario):
    r = executar(cenario)
    assert r["particao"]["registros_teste"] == 3
    assert r["particao"]["moleculas_teste"] == 3
    assert r["particao"]["moleculas_compartilhadas"] == 0
    assert r["metricas_teste_final"]["mae"] == pytest.approx(.2)
    assert r["metricas_teste_final"]["rmse"] == pytest.approx(np.sqrt(.2 / 3))
    assert r["metricas_teste_final"]["r2"] == pytest.approx(-1.5)
    assert r["analise_de_erros"]["vies_medio_observado_menos_predito"] == pytest.approx(1 / 15)


def test_relatorios_arquivos_e_hashes(cenario):
    r = executar(cenario)
    pasta = cenario["saida"]
    assert sorted(p.name for p in pasta.iterdir()) == sorted([
        "resumo.json", "relatorio.md", "observado_predito_teste.png", "residuos_temperatura_teste.png",
    ])
    assert json.loads((pasta / "resumo.json").read_text(encoding="utf-8")) == r
    assert r["entradas_sha256"]["teste"] == hashlib.sha256(cenario["teste"].read_bytes()).hexdigest()
    assert r["entradas_sha256"]["joblib"] == c30.sha256(cenario["artefatos"] / "ridge-v1.joblib")
    assert (pasta / "observado_predito_teste.png").stat().st_size > 1000


def test_nao_divulga_linhas_smiles_nem_predicoes(cenario):
    executar(cenario)
    resumo = (cenario["saida"] / "resumo.json").read_text(encoding="utf-8")
    relatorio = (cenario["saida"] / "relatorio.md").read_text(encoding="utf-8")
    assert '"CCO"' not in resumo
    assert '"SMILES_Canonico"' not in resumo
    assert "CCO" not in relatorio
    assert '"predicoes"' not in resumo


def test_faixas_predefinidas_e_tres_grupos(cenario):
    r = executar(cenario)
    faixas = r["analise_de_erros"]["faixas_temperatura"]
    assert [x["registros"] for x in faixas.values()] == [1, 1, 1]
    assert faixas["abaixo_do_treino"]["mae"] == pytest.approx(.2)
    assert faixas["dentro_da_faixa_do_treino"]["mae"] == pytest.approx(0)
    assert faixas["acima_do_treino"]["mae"] == pytest.approx(.4)


def test_segunda_execucao_nao_sobrescreve(cenario):
    executar(cenario)
    with pytest.raises(FileExistsError, match="não repetir"):
        executar(cenario)


def test_bloqueia_molecula_compartilhada(cenario):
    t = pd.read_csv(cenario["teste"])
    t.loc[0, "SMILES_Canonico"] = "C"
    t.to_csv(cenario["teste"], index=False)
    with pytest.raises(ValueError, match="Vazamento"):
        executar(cenario)
    assert not cenario["saida"].exists()


def test_bloqueia_source_row_compartilhado(cenario):
    t = pd.read_csv(cenario["teste"])
    t.loc[0, "Source_Row"] = 2
    t.to_csv(cenario["teste"], index=False)
    with pytest.raises(ValueError, match="Vazamento"):
        executar(cenario)


def test_rejeita_csv_treino_adulterado(cenario):
    t = pd.read_csv(cenario["treino"])
    t.loc[0, c30.ALVO] = 200
    t.to_csv(cenario["treino"], index=False)
    with pytest.raises(ValueError, match="hash"):
        executar(cenario)


def test_rejeita_teste_vazio(cenario):
    t = pd.read_csv(cenario["teste"]).iloc[0:0]
    t.to_csv(cenario["teste"], index=False)
    with pytest.raises(ValueError, match="vazio"):
        executar(cenario)


def test_rejeita_duplicatas_source_row(cenario):
    t = pd.read_csv(cenario["teste"])
    t.loc[0, "Source_Row"] = t.loc[1, "Source_Row"]
    t.to_csv(cenario["teste"], index=False)
    with pytest.raises(ValueError, match="Source_Row"):
        executar(cenario)


def test_rejeita_valor_alvo_nao_finito(cenario):
    t = pd.read_csv(cenario["teste"])
    t.loc[0, c30.ALVO] = np.nan
    t.to_csv(cenario["teste"], index=False)
    with pytest.raises(ValueError, match="não finitos"):
        executar(cenario)


def test_rejeita_saida_nao_finita(cenario, monkeypatch):
    class ModeloRuim(ModeloSintetico):
        def prever(self, pedido):
            return SimpleNamespace(model_version="ridge-v1", log_s_mol_l=float("nan"))
    monkeypatch.setattr(c30, "carregar_predictor", lambda _: ModeloRuim())
    with pytest.raises(ValueError, match="não finitos"):
        executar(cenario)
    assert not cenario["saida"].exists()


def test_exige_nomes_corretos(cenario):
    with pytest.raises(ValueError, match="treino.csv e teste.csv"):
        c30.avaliar_teste_final(
            cenario["teste"], cenario["treino"], cenario["artefatos"], cenario["saida"]
        )


def test_rejeita_modelo_versao_diferente(cenario, monkeypatch):
    class ModeloOutraVersao(ModeloSintetico):
        info = SimpleNamespace(model_version="ridge-v2")
    monkeypatch.setattr(c30, "carregar_predictor", lambda _: ModeloOutraVersao())
    with pytest.raises(ValueError, match="congelado"):
        executar(cenario)


def test_cli_requer_confirmacao(monkeypatch):
    monkeypatch.setattr("sys.argv", ["avaliar_teste_final"])
    with pytest.raises(SystemExit) as saida:
        c30.main()
    assert saida.value.code == 2


def test_metricas_rejeitam_amostra_invalida():
    with pytest.raises(ValueError, match="duas previsões"):
        c30.calcular_metricas(np.array([1.0]), np.array([1.0]))
    with pytest.raises(ValueError, match="não finitos"):
        c30.calcular_metricas(np.array([1.0, 2.0]), np.array([float("inf"), 3.0]))
