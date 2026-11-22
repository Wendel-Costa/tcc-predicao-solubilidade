"""C28 — Testes leves de integridade documental dos diagramas Mermaid."""

import re
from pathlib import Path

import pytest


RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / "docs" / "diagramas"
ARQUIVOS = (
    "01-diagrama-contexto.md",
    "02-diagrama-conteineres.md",
    "03-diagrama-componentes.md",
    "04-diagrama-sequencia.md",
    "05-fluxo-cientifico.md",
)


@pytest.mark.parametrize("nome", ARQUIVOS)
def test_diagrama_existe_e_tem_mermaid_fechado(nome):
    texto = (PASTA / nome).read_text(encoding="utf-8")
    blocos = re.findall(r"```mermaid\n(.*?)\n```", texto, re.DOTALL)
    assert texto.startswith("# ")
    assert blocos
    assert texto.count("```mermaid") == len(blocos)
    assert texto.count("```") == len(blocos) * 2
    assert all(
        bloco.startswith(("flowchart ", "sequenceDiagram"))
        for bloco in blocos
    )


@pytest.mark.parametrize("nome", ARQUIVOS)
def test_links_markdown_relativos_apontam_para_arquivos(nome):
    texto = (PASTA / nome).read_text(encoding="utf-8")
    links = re.findall(r"\[[^\]]+\]\(([^)]+\.md|[^)]+\.py|[^)]+\.js)\)", texto)
    assert links, "O diagrama precisa conter ao menos uma referência cruzada"
    for link in links:
        assert (PASTA / link).is_file(), f"Link quebrado: {nome} -> {link}"


def test_componentes_identificam_modulos_reais():
    conteudo = (PASTA / "03-diagrama-componentes.md").read_text(encoding="utf-8")
    for modulo in (
        "app/main.py", "app/schemas.py", "app/predictor.py",
        "app/chemistry.py", "frontend/app.js",
    ):
        assert modulo in conteudo


def test_sequencia_documenta_contratos_de_erro():
    conteudo = (PASTA / "04-diagrama-sequencia.md").read_text(encoding="utf-8")
    for termo in (
        "POST /api/predict", "HTTP 200", "HTTP 422", "HTTP 503", "HTTP 500",
        "invalid_temperature", "model_unavailable", "prediction_failed",
        "AbortController",
    ):
        assert termo in conteudo


def test_fluxo_identifica_teste_reservado_e_validacao_interna():
    conteudo = (PASTA / "05-fluxo-cientifico.md").read_text(encoding="utf-8")
    for termo in (
        "treino.csv", "teste.csv", "RESERVADO", "validação interna",
        "ridge-v1.joblib", "BigSolDB 2.0", "GroupShuffleSplit",
    ):
        assert termo in conteudo
    assert "**Não realizada**" in conteudo


def test_conteineres_documentam_mesma_origem_sem_treino_online():
    conteudo = (PASTA / "02-diagrama-conteineres.md").read_text(encoding="utf-8")
    assert "mesma origem HTTP" in conteudo
    assert "offline" in conteudo
    assert "POST /api/predict" in conteudo
    assert "ridge-v1.joblib" in conteudo
