
"Testes com dados sintéticos para a curadoria exclusiva de metanol."

import sys

import pandas as pd
import pytest

from scripts import preparar_dados as curadoria


def criar_dados(*alteracoes):
    """Cria linhas independentes com o schema mínimo mais Source."""
    base = {
        "SMILES_Solute": "CCO",
        "Temperature_K": 298.15,
        "Solvent": "methanol",
        "SMILES_Solvent": "CO",
        "LogS(mol/L)": -1.0,
        "Source": "fonte-a",
    }
    return pd.DataFrame([
        {**base, **alteracao}
        for alteracao in (alteracoes or ({},))
    ])


def test_aceita_colunas_obrigatorias_sem_source():
    dados = criar_dados().drop(columns="Source")

    preparados, resumo = curadoria.preparar_dataset(dados)

    assert len(preparados) == 1
    assert resumo["fontes_distintas"] is None


@pytest.mark.parametrize("coluna", [
    "SMILES_Solute",
    "Temperature_K",
    "Solvent",
    "SMILES_Solvent",
    "LogS(mol/L)",
])
def test_rejeita_cada_coluna_obrigatoria_ausente(coluna):
    dados = criar_dados().drop(columns=coluna)

    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes") as erro:
        curadoria.preparar_dataset(dados)

    assert coluna in str(erro.value)


def test_exige_concordancia_do_nome_e_estrutura_do_metanol():
    dados = criar_dados(
        {},
        {"Solvent": "  MeThAnOl  ", "SMILES_Solvent": "OC"},
        {"Solvent": "water", "SMILES_Solvent": "O"},
        {"Solvent": "diisobutyl methanol", "SMILES_Solvent": "CO"},
        {"Solvent": "methanol", "SMILES_Solvent": "O"},
        {"Solvent": "ethanol", "SMILES_Solvent": "CO"},
        {"Solvent": "methanol", "SMILES_Solvent": None},
        {"Solvent": "methanol", "SMILES_Solvent": "C1("},
        {"Solvent": None, "SMILES_Solvent": "CO"},
    )

    preparados, resumo = curadoria.preparar_dataset(dados)

    assert preparados["Source_Row"].tolist() == [2, 3]
    assert resumo["registros_originais"] == 9
    assert resumo["nomenclaturas_methanol"] == 5
    assert resumo["estruturas_de_metanol"] == 5
    assert resumo["concordancia_nome_estrutura"] == 2
    assert resumo["apenas_nome_methanol"] == 3
    assert resumo["apenas_estrutura_metanol"] == 3
    assert resumo["smiles_solvente_invalidos_ou_ausentes"] == 2
    assert resumo["candidatos_metanol"] == 2
    assert resumo["registros_preparados"] == 2


def test_canonicaliza_smiles_equivalentes_sem_alterar_coluna_original():
    dados = criar_dados({}, {"SMILES_Solute": "OCC"})

    preparados, resumo = curadoria.preparar_dataset(dados)

    assert preparados["SMILES_Solute"].tolist() == ["CCO", "OCC"]
    assert preparados["SMILES_Canonico"].tolist() == ["CCO", "CCO"]
    assert resumo["moleculas_distintas"] == 1


def test_preserva_diferenca_entre_estereoisomeros():
    dados = criar_dados(
        {"SMILES_Solute": "C[C@H](O)F"},
        {"SMILES_Solute": "C[C@@H](O)F"},
    )

    preparados, resumo = curadoria.preparar_dataset(dados)
    canonicos = preparados["SMILES_Canonico"].tolist()

    assert len(set(canonicos)) == 2
    assert all("@" in smiles for smiles in canonicos)
    assert resumo["moleculas_distintas"] == 2


def test_exclui_smiles_de_soluto_invalidos_e_ausentes():
    dados = criar_dados(
        {},
        {"SMILES_Solute": "C1("},
        {"SMILES_Solute": None},
        {"SMILES_Solute": ""},
    )

    preparados, resumo = curadoria.preparar_dataset(dados)

    assert preparados["Source_Row"].tolist() == [2]
    assert resumo["soluto_smiles_invalidos_ou_ausentes"] == 3
    assert resumo["registros_preparados"] == 1


def test_exclui_temperaturas_invalidas_e_preserva_kelvin():
    dados = criar_dados(
        {},
        {"Temperature_K": None},
        {"Temperature_K": "invalida"},
        {"Temperature_K": float("inf")},
        {"Temperature_K": float("-inf")},
        {"Temperature_K": 0},
        {"Temperature_K": -5},
        {"Temperature_K": "310.0"},
    )

    preparados, resumo = curadoria.preparar_dataset(dados)

    assert preparados["Source_Row"].tolist() == [2, 9]
    assert preparados["Temperature_K"].tolist() == pytest.approx([298.15, 310.0])
    assert resumo["temperaturas_invalidas_ou_ausentes"] == 6
    assert resumo["registros_preparados"] == 2


def test_exclui_logs_invalidos_sem_converter_a_escala():
    dados = criar_dados(
        {"LogS(mol/L)": -1.2},
        {"LogS(mol/L)": None},
        {"LogS(mol/L)": "invalido"},
        {"LogS(mol/L)": float("inf")},
        {"LogS(mol/L)": float("-inf")},
        {"LogS(mol/L)": float("nan")},
        {"LogS(mol/L)": "-0.1"},
    )

    preparados, resumo = curadoria.preparar_dataset(dados)

    assert preparados["Source_Row"].tolist() == [2, 8]
    assert preparados["LogS(mol/L)"].tolist() == pytest.approx([-1.2, -0.1])
    assert resumo["logs_invalidos_ou_ausentes"] == 5


def test_contagens_seguem_a_ordem_de_exclusao():
    dados = criar_dados(
        {"Solvent": "water", "SMILES_Solvent": "O"},
        {"SMILES_Solute": None},
        {"SMILES_Solute": "C1("},
        {"Temperature_K": None},
        {"Temperature_K": -1},
        {"LogS(mol/L)": "invalido"},
        {},
        {"SMILES_Solute": "CC"},
    )

    preparados, resumo = curadoria.preparar_dataset(dados)

    assert preparados["Source_Row"].tolist() == [8, 9]
    assert resumo["registros_originais"] == 8
    assert resumo["candidatos_metanol"] == 7
    assert resumo["soluto_smiles_invalidos_ou_ausentes"] == 2
    assert resumo["temperaturas_invalidas_ou_ausentes"] == 2
    assert resumo["logs_invalidos_ou_ausentes"] == 1
    assert resumo["registros_preparados"] == 2


def test_diagnostica_duplicatas_sem_remover_ou_agregar_medicoes():
    dados = criar_dados(
        {},
        {},
        {"SMILES_Solute": "OCC", "Source": "fonte-b"},
        {"Temperature_K": 303.15},
        {"SMILES_Solute": "CC", "Source": "fonte-c"},
    )

    preparados, resumo = curadoria.preparar_dataset(dados)

    assert preparados["Source_Row"].tolist() == [2, 3, 4, 5, 6]
    assert resumo["registros_preparados"] == 5
    assert resumo["duplicatas_exatas"] == 1
    assert resumo["grupos_molecula_temperatura_repetidos"] == 1
    assert resumo["registros_em_grupos_repetidos"] == 3
    assert resumo["moleculas_distintas"] == 2
    assert resumo["fontes_distintas"] == 3


def test_nao_modifica_dataframe_de_entrada():
    dados = criar_dados(
        {"Solvent": "  METHANOL  ", "Temperature_K": "298.15"},
        {"Solvent": "water", "SMILES_Solvent": "O"},
    )
    original = dados.copy(deep=True)

    curadoria.preparar_dataset(dados)

    pd.testing.assert_frame_equal(dados, original)
    assert "Source_Row" not in dados.columns
    assert "SMILES_Canonico" not in dados.columns


def test_rejeita_base_sem_candidato_confirmado_de_metanol():
    dados = criar_dados({"Solvent": "water", "SMILES_Solvent": "O"})

    with pytest.raises(ValueError, match="Nenhum registro foi confirmado como metanol"):
        curadoria.preparar_dataset(dados)


def test_rejeita_base_sem_registros_validos_apos_curadoria():
    dados = criar_dados(
        {"SMILES_Solute": "C1("},
        {"Temperature_K": 0},
        {"LogS(mol/L)": None},
    )

    with pytest.raises(ValueError, match="Nenhum registro válido restou"):
        curadoria.preparar_dataset(dados)


def test_relatorio_de_temperatura_usa_janelas_apenas_como_diagnostico(capsys):
    dados = criar_dados(
        {"Temperature_K": 298.15},
        {"Temperature_K": 299.0},
        {"Temperature_K": 303.15},
        {"Temperature_K": 310.0},
    )
    preparados, resumo = curadoria.preparar_dataset(dados)

    curadoria.apresentar_resultados(preparados, resumo)
    saida = capsys.readouterr().out

    assert len(preparados) == 4
    assert "Registros entre 298,15 ± 1 K: 2" in saida
    assert "Registros entre 298,15 ± 5 K: 3" in saida
    assert "não representam filtros de treinamento" in saida


def test_cli_rejeita_caminho_de_entrada_inexistente(tmp_path, monkeypatch, capsys):
    entrada = tmp_path / "inexistente.csv"
    saida = tmp_path / "processado.csv"
    monkeypatch.setattr(sys, "argv", [
        "preparar_dados.py", "--input", str(entrada), "--output", str(saida),
    ])

    assert curadoria.main() == 1
    assert "Dataset não encontrado" in capsys.readouterr().out
    assert not saida.exists()


def test_cli_impede_sobrescrever_arquivo_de_entrada(tmp_path, monkeypatch, capsys):
    entrada = tmp_path / "dados.csv"
    criar_dados().to_csv(entrada, index=False)
    anterior = entrada.read_bytes()
    monkeypatch.setattr(sys, "argv", [
        "preparar_dados.py", "--input", str(entrada), "--output", str(entrada),
    ])

    assert curadoria.main() == 1
    assert "não pode sobrescrever o original" in capsys.readouterr().out
    assert entrada.read_bytes() == anterior


def test_cli_grava_csv_em_diretorio_novo_com_linhas_rastreaveis(
    tmp_path, monkeypatch, capsys,
):
    entrada = tmp_path / "entrada.csv"
    saida = tmp_path / "subpasta" / "processado.csv"
    criar_dados(
        {},
        {"Solvent": "water", "SMILES_Solvent": "O"},
        {"SMILES_Solute": "OCC", "Temperature_K": 303.15},
    ).to_csv(entrada, index=False)
    monkeypatch.setattr(sys, "argv", [
        "preparar_dados.py", "--input", str(entrada), "--output", str(saida),
    ])

    assert curadoria.main() == 0
    assert "PREPARAÇÃO CONCLUÍDA" in capsys.readouterr().out
    assert saida.is_file()
    gravados = pd.read_csv(saida)
    assert gravados["Source_Row"].tolist() == [2, 4]
    assert gravados["SMILES_Canonico"].tolist() == ["CCO", "CCO"]
    assert gravados["Temperature_K"].tolist() == pytest.approx([298.15, 303.15])
    assert gravados["LogS(mol/L)"].tolist() == [-1.0, -1.0]