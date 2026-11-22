"""C32–C35: verificações estáticas de entrega, sem uso de CSV experimental."""
from pathlib import Path
import hashlib
import json
import re
import pytest
from scripts import verificar_deploy

RAIZ = Path(__file__).resolve().parents[1]


def ler(caminho):
    return (RAIZ / caminho).read_text(encoding="utf-8")


def test_dockerfile_copia_apenas_necessario():
    texto = ler("Dockerfile")
    for item in ("FROM python:3.14.8-slim-bookworm", "requirements-deploy.txt", "app/", "frontend/", "ridge-v1.joblib", "ridge-v1.metadata.json", "uvicorn app.main:app"):
        assert item in texto
    for proibido in ("COPY . .", "COPY data/", "scripts.persistir_modelo", "scripts.avaliar_teste_final"):
        assert proibido not in texto


def test_dockerignore_exclui_dados_e_segredos():
    texto = ler(".dockerignore")
    for item in (".git", ".venv", "data/", "tests/", "scripts/", ".env", "reports/"):
        assert item in texto


def test_versoes_runtime_c23():
    texto = ler("requirements-deploy.txt")
    versoes = json.loads(ler("artifacts/ridge-v1.metadata.json"))["model_info"]["software_versions"]
    for nome, pacote in (("numpy", "numpy"), ("pandas", "pandas"), ("rdkit", "rdkit"), ("scikit-learn", "scikit-learn"), ("joblib", "joblib")):
        # Pip normaliza 2026.09.2 -> 2026.9.2; comparamos versões numéricas.
        fixada = next(linha.split("==", 1)[1] for linha in texto.splitlines() if linha.startswith(pacote + "=="))
        assert tuple(map(int, fixada.split("."))) == tuple(map(int, versoes[nome].split(".")))


def test_render_blueprint_aponta_para_health():
    texto = ler("render.yaml")
    for item in ("type: web", "runtime: docker", "healthCheckPath: /api/health", "plan: free"):
        assert item in texto


def test_readme_descreve_deploy_e_resultados():
    readme = ler("README.md")
    for termo in ("docs/implantacao.md", "docs/checklist-entrega.md", "0,726303", "0,923927", "0,255850", "validação externa"):
        assert termo in readme


def test_guia_nao_manda_repetir_avaliacao_final():
    texto = ler("docs/guia-reproducao.md")
    assert "não deve ser repetida" in texto
    assert "../modelo-reproduzido-c31" in texto


def test_licenca_nao_e_inventada():
    guia = ler("docs/checklist-entrega.md")
    assert "licença" in guia
    assert "concordância da equipe" in guia


def test_interface_basica_acessivel_e_responsiva():
    html = ler("frontend/index.html")
    css = ler("frontend/styles.css")
    for parte in ('lang="pt-BR"', 'aria-live="polite"', 'role="alert"', 'id="predict-form"'):
        assert parte in html
    for parte in (":focus-visible", "@media (max-width: 600px)", "prefers-reduced-motion"):
        assert parte in css


def test_workflow_nao_tenta_preencher_teste_final():
    texto = ler(".github/workflows/testes.yml")
    assert "pytest -q" in texto
    assert "avaliar_teste_final --confirmar" not in texto


def test_smoke_script_nao_retreina():
    texto = ler("scripts/verificar_deploy.py")
    for item in ("/frontend/", "/api/health", "/api/model-info", "/api/predict", "0.1574631425041294"):
        assert item in texto
    assert "joblib.load" not in texto
    assert "read_csv" not in texto


def test_documentacao_nao_inclui_tokens():
    texto = ler("docs/implantacao.md")
    assert "nunca" in texto.lower()
    assert "token" in texto.lower()
    assert "SHA-256" in texto


def test_smoke_rejeita_modelo_invalido(monkeypatch):
    class Resposta:
        def __init__(self, status, payload, tipo="application/json"):
            self.status = status
            self.payload = payload
            self.headers = {"Content-Type": tipo}
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return json.dumps(self.payload).encode("utf-8")
    def falso(req, timeout):
        url = req.full_url
        if url.endswith("/frontend/"):
            return Resposta(200, '<form id="predict-form">', 'text/html')
        if url.endswith("/api/health"):
            return Resposta(200, {"model_available": False, "model_version": None})
        raise AssertionError("Não deveria prosseguir")
    # Finge a entrega de HTML por cliente HTTP, sem rede externa.
    # A função verifica primeiro o estado Health.
    import io
    class HtmlResposta(Resposta):
        def read(self): return self.payload.encode("utf-8")
    def cliente(req, timeout):
        if req.full_url.endswith("/frontend/"):
            return HtmlResposta(200, '<form id="predict-form">', 'text/html')
        return Resposta(200, {"model_available": False, "model_version": None})
    monkeypatch.setattr(verificar_deploy, "urlopen", cliente)
    with pytest.raises(AssertionError, match="Health"):
        verificar_deploy.executar("http://localhost", timeout=1)
