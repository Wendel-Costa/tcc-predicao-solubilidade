
"""Testes da estrutura HTML inicial do frontend."""

from html.parser import HTMLParser
from pathlib import Path

import pytest


ARQUIVO_HTML = (
    Path(__file__).resolve().parents[1]
    / "frontend"
    / "index.html"
)


class EstruturaHTML(HTMLParser):
    """Coleta elementos e atributos sem dependências externas."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elementos = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        self.elementos.append((tag, atributos))

        if "id" in atributos:
            self.ids.append(atributos["id"])

    def buscar_id(self, identificador):
        encontrados = [
            (tag, attrs)
            for tag, attrs in self.elementos
            if attrs.get("id") == identificador
        ]

        assert len(encontrados) == 1, (
            f"ID ausente ou duplicado: {identificador}"
        )

        return encontrados[0]


@pytest.fixture
def pagina():
    conteudo = ARQUIVO_HTML.read_text(
        encoding="utf-8"
    )

    estrutura = EstruturaHTML()
    estrutura.feed(conteudo)
    estrutura.close()

    return conteudo, estrutura


def test_documento_html_em_portugues_com_viewport(pagina):
    html, estrutura = pagina

    assert html.lstrip().lower().startswith(
        "<!doctype html>"
    )

    assert any(
        tag == "html" and a.get("lang") == "pt-BR"
        for tag, a in estrutura.elementos
    )

    assert any(
        tag == "meta" and a.get("name") == "viewport"
        for tag, a in estrutura.elementos
    )

    assert any(
        tag == "title"
        for tag, _ in estrutura.elementos
    )


def test_conteudo_principal_e_titulos(pagina):
    _, estrutura = pagina

    assert estrutura.buscar_id("conteudo")[0] == "main"

    assert sum(
        tag == "h1"
        for tag, _ in estrutura.elementos
    ) == 1

    assert any(
        tag == "a" and a.get("href") == "#conteudo"
        for tag, a in estrutura.elementos
    )


def test_formulario_possui_rotulos_associados(pagina):
    _, estrutura = pagina

    assert estrutura.buscar_id("predict-form")[0] == "form"

    for campo in ("smiles", "temperature_c"):
        assert any(
            tag == "label" and a.get("for") == campo
            for tag, a in estrutura.elementos
        )

        assert estrutura.buscar_id(campo)[0] == "input"


def test_smiles_obrigatorio_com_ajuda(pagina):
    _, estrutura = pagina

    _, campo = estrutura.buscar_id("smiles")

    assert campo["name"] == "smiles"
    assert campo["type"] == "text"
    assert "required" in campo

    assert campo["aria-describedby"] == "ajuda-smiles"

    assert estrutura.buscar_id("ajuda-smiles")[0] == "p"



def test_temperatura_obrigatoria_sem_padrao_automatico(pagina):
    _, estrutura = pagina

    _, campo = estrutura.buscar_id("temperature_c")

    assert campo["name"] == "temperature_c"
    assert campo["type"] == "number"
    assert campo["step"] == "any"

    # Exigida pela interface, mas sem valor assumido.
    assert "required" in campo
    assert "value" not in campo



def test_botao_desabilitado_ate_integracao(pagina):
    _, estrutura = pagina

    tag, attrs = estrutura.buscar_id("predict-button")

    assert tag == "button"
    assert attrs["type"] == "submit"
    assert "disabled" in attrs


def test_areas_de_resultado_erro_e_carregamento(pagina):
    _, estrutura = pagina

    for identificador in (
        "result-panel",
        "error-panel",
        "loading-state",
    ):
        _, attrs = estrutura.buscar_id(identificador)
        assert "hidden" in attrs

    assert estrutura.buscar_id(
        "result-log-s"
    )[0] == "output"

    for identificador in (
        "result-temperature-c",
        "result-temperature-k",
        "result-model-version",
        "result-warnings",
        "error-message",
    ):
        estrutura.buscar_id(identificador)

    assert estrutura.buscar_id(
        "error-panel"
    )[1]["role"] == "alert"

    assert estrutura.buscar_id(
        "form-status"
    )[1]["aria-live"] == "polite"


def test_identificadores_html_nao_sao_duplicados(pagina):
    _, estrutura = pagina

    assert len(estrutura.ids) == len(
        set(estrutura.ids)
    )
