
"""Verificações estáticas do CSS e JS; sem dependências novas."""

from html.parser import HTMLParser
from pathlib import Path

import pytest


FRONTEND = (
    Path(__file__).resolve().parents[1]
    / "frontend"
)


class Coletor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elementos = []

    def handle_starttag(self, tag, attrs):
        self.elementos.append(
            (tag, dict(attrs))
        )


@pytest.fixture
def arquivos():
    html = (
        FRONTEND / "index.html"
    ).read_text(encoding="utf-8")

    css = (
        FRONTEND / "styles.css"
    ).read_text(encoding="utf-8")

    js = (
        FRONTEND / "app.js"
    ).read_text(encoding="utf-8")

    parser = Coletor()
    parser.feed(html)

    return parser.elementos, css, js


def test_css_e_js_sao_referenciados_localmente(arquivos):
    elementos, _, _ = arquivos

    assert any(
        tag == "link"
        and a.get("rel") == "stylesheet"
        and a.get("href") == "styles.css"
        for tag, a in elementos
    )

    assert any(
        tag == "script"
        and a.get("src") == "app.js"
        and "defer" in a
        for tag, a in elementos
    )


def test_formulario_e_elementos_necessarios_existem(arquivos):
    elementos, _, js = arquivos

    ids = {
        a["id"]
        for _, a in elementos
        if "id" in a
    }

    esperados = {
        "predict-form",
        "smiles",
        "temperature_c",
        "predict-button",
        "form-status",
        "error-panel",
        "error-message",
        "result-panel",
        "loading-state",
    }

    assert esperados <= ids

    for identificador in esperados:
        assert (
            f'getElementById("{identificador}")'
            in js
        )


def test_botao_inicialmente_desabilitado(arquivos):
    elementos, _, js = arquivos

    botoes = [
        a
        for tag, a in elementos
        if tag == "button"
        and a.get("id") == "predict-button"
    ]

    assert len(botoes) == 1
    assert "disabled" in botoes[0]

    assert (
        'botao.textContent = "Verificar entradas"'
        in js
    )


def test_validacao_local_sem_predicao_ou_requisicao_http(arquivos):
    _, _, js = arquivos

    assert "Number.isFinite" in js
    assert "valor > -273.15" in js
    assert "preventDefault()" in js

    assert "fetch(" not in js
    assert "XMLHttpRequest" not in js
    assert "localStorage" not in js


def test_resultado_e_carregamento_permanecem_ocultos(arquivos):
    _, _, js = arquivos

    assert "painelResultado.hidden = true" in js
    assert "painelCarregamento.hidden = true" in js

    assert "painelResultado.hidden = false" not in js
    assert "painelCarregamento.hidden = false" not in js


def test_mensagens_de_erro_sem_injecao_html(arquivos):
    _, _, js = arquivos

    assert "mensagemErro.textContent" in js
    assert "innerHTML" not in js


def test_css_responsivo(arquivos):
    _, css, _ = arquivos

    assert "@media (max-width: 600px)" in css
    assert "width: 100%" in css
    assert "clamp(" in css


def test_css_preserva_hidden_e_foco(arquivos):
    _, css, _ = arquivos

    assert "[hidden]" in css
    assert "display: none !important" in css
    assert ":focus-visible" in css


def test_status_acessivel_e_sem_resultado_ficticio(arquivos):
    elementos, _, js = arquivos

    assert any(
        a.get("id") == "form-status"
        and a.get("aria-live") == "polite"
        for _, a in elementos
    )

    assert "predição serão feitas pela API" in js
