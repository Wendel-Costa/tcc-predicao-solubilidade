"""C31 — verificações estáticas da documentação de uso e reprodução.

Não requer rede, arquivos CSV ou artefatos Joblib.
"""

from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
README = RAIZ / "README.md"
GUIA = RAIZ / "docs" / "guia-reproducao.md"


@pytest.fixture(scope="module")
def textos():
    return (
        README.read_text(encoding="utf-8"),
        GUIA.read_text(encoding="utf-8"),
    )


def test_documentos_existem():
    assert README.is_file()
    assert GUIA.is_file()


def test_titulo_e_escopo(textos):
    readme, _ = textos
    assert readme.startswith("# Predição de Solubilidade")
    assert "metanol" in readme.casefold()
    assert "SMILES" in readme
    assert "LogS(mol/L)" in readme


def test_documenta_comandos_da_aplicacao(textos):
    readme, guia = textos
    for documento in (readme, guia):
        assert "python -m pip install -r requirements.txt" in documento
        assert "python -m uvicorn app.main:app --reload" in documento
        assert "http://127.0.0.1:8000/frontend/" in documento


def test_documenta_tres_endpoints(textos):
    readme, guia = textos
    for endpoint in ("/api/health", "/api/model-info", "/api/predict"):
        assert endpoint in readme
        assert endpoint in guia


def test_entrada_sem_temperatura_padrao(textos):
    readme, guia = textos
    assert "temperatura é obrigatória" in readme
    assert "temperature_c" in guia
    assert "273,15" in readme


def test_fonte_doi_e_dataset(textos):
    readme, guia = textos
    for documento in (readme, guia):
        assert "BigSolDB" in documento
    assert "10.5281/zenodo.15094979" in readme
    assert "BigSolDBv2.0.csv" in guia


def test_descreve_particao_agrupada(textos):
    readme, guia = textos
    for documento in (readme, guia):
        assert "6.619" in documento
        assert "1.601" in documento
        assert "170" in documento
    assert "GroupShuffleSplit" in readme


def test_resultados_sao_identificados_como_teste_final(textos):
    readme, guia = textos
    for documento in (readme, guia):
        assert "0,726303" in documento
        assert "0,923927" in documento
        assert "0,255850" in documento
        assert "validação externa" in documento


def test_explicita_ausencia_do_joblib_no_git(textos):
    readme, guia = textos
    for documento in (readme, guia):
        assert "ridge-v1.joblib" in documento
        assert "não" in documento.casefold()
    assert "f362ca5d4b01e834901bb446a5029b1f9fb7a1636c7e87374dfd1fbb5e96bf5f" in guia


def test_separa_reproducao_e_artefato_original(textos):
    _, guia = textos
    assert "Modo A" in guia and "Modo B" in guia
    assert "--output-dir ../modelo-reproduzido-c31" in guia
    assert "não altera os metadados históricos" in guia


def test_nao_orienta_repetir_avaliacao_final(textos):
    _, guia = textos
    assert "não deve ser repetida" in guia
    assert "--confirmar-avaliacao-final" in guia
    assert "não é um passo da reprodução rotineira" in guia


def test_readme_atualizado_sem_promessa_futura(textos):
    readme, _ = textos
    assert "Em desenvolvimento." not in readme
    assert "ainda serão realizados" not in readme
    assert "0.157463" not in readme  # Referência usa vírgula, não formato inconsistente.


def test_links_documentais_basicos(textos):
    readme, _ = textos
    assert "(docs/guia-reproducao.md)" in readme
    assert "(data/README.md)" in readme
    assert "(reports/avaliacao_final_c30/relatorio.md)" in readme
    assert "(docs/contrato-api.md)" in readme


def test_blocos_de_codigo_fechados(textos):
    for documento in textos:
        assert documento.count("```") % 2 == 0
