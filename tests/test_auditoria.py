
import pandas as pd
import pytest

from scripts import auditar_dataset as auditoria


def test_carregar_csv_le_arquivo(tmp_path):
    arquivo = tmp_path / "dados.csv"

    pd.DataFrame({
        "SMILES_Solute": ["CCO"],
        "Temperature_K": [298.15],
    }).to_csv(arquivo, index=False)

    resultado = auditoria.carregar_csv(arquivo)

    assert len(resultado) == 1
    assert resultado.loc[0, "SMILES_Solute"] == "CCO"
    assert resultado.loc[0, "Temperature_K"] == 298.15


def test_carregar_csv_rejeita_arquivo_inexistente(tmp_path):
    arquivo = tmp_path / "inexistente.csv"

    with pytest.raises(FileNotFoundError):
        auditoria.carregar_csv(arquivo)


def test_verificar_colunas_aceita_estrutura_valida():
    df = pd.DataFrame({
        "SMILES_Solute": ["CCO"],
        "Temperature_K": [298.15],
        "Solvent": ["methanol"],
        "LogS(mol/L)": [-1.0],
    })

    auditoria.verificar_colunas(df)


def test_verificar_colunas_rejeita_coluna_ausente():
    df = pd.DataFrame({
        "SMILES_Solute": ["CCO"],
        "Temperature_K": [298.15],
        "Solvent": ["methanol"],
    })

    with pytest.raises(ValueError, match="LogS"):
        auditoria.verificar_colunas(df)


def test_distribuicao_numerica_identifica_valores_invalidos(capsys):
    df = pd.DataFrame({
        "Temperature_K": [
            298.15,
            None,
            "texto",
            float("inf"),
            "",
        ]
    })

    auditoria.imprimir_distribuicao_numerica(
        df,
        "Temperature_K"
    )

    saida = capsys.readouterr().out

    assert "Valores ausentes: 2" in saida
    assert "Valores não numéricos: 1" in saida
    assert "Valores não finitos: 1" in saida
    assert "Valores numéricos finitos: 1" in saida


def test_auditar_smiles_identifica_validos_invalidos_e_canonicos(capsys):
    df = pd.DataFrame({
        "SMILES_Solute": [
            "CCO",
            "OCC",
            "C1(",
            None,
            "",
        ]
    })

    canonicos = auditoria.auditar_smiles(df)

    saida = capsys.readouterr().out

    assert saida.find("SMILES válidos: 2") != -1
    assert "SMILES inválidos: 1" in saida
    assert "SMILES ausentes: 2" in saida

    assert canonicos[0] == canonicos[1]
    assert canonicos[2] is None
    assert canonicos[3] is None
    assert canonicos[4] is None


def test_auditar_solventes_mostra_nomenclaturas_sem_classificacao_automatica(
    capsys
):
    df = pd.DataFrame({
        "Solvent": [
            "methanol",
            "methanol",
            "diisobutyl methanol",
            "water",
        ]
    })

    auditoria.auditar_solventes(df)

    saida = capsys.readouterr().out

    assert "Total de nomenclaturas distintas: 3" in saida
    assert "methanol: 2" in saida
    assert "diisobutyl methanol: 1" in saida


def test_auditar_repeticoes_identifica_molecula_em_temperaturas_diferentes(
    capsys
):
    df = pd.DataFrame({
        "SMILES_Solute": [
            "CCO",
            "OCC",
            "CC",
        ],
        "Temperature_K": [
            298.15,
            303.15,
            298.15,
        ],
    })

    canonicos = [
        "CCO",
        "CCO",
        "CC",
    ]

    auditoria.auditar_repeticoes(df, canonicos)

    saida = capsys.readouterr().out

    assert "Duplicatas exatas: 0" in saida
    assert (
        "Moléculas com medições em mais de uma temperatura: 1"
        in saida
    )


def test_auditar_densidades_aceita_arquivo_completo(tmp_path, capsys):
    arquivo = tmp_path / "densidades.csv"

    pd.DataFrame({
        "Solvent": ["methanol"],
        "Temperature_K": [298.15],
        "Density_g/cm^3": ["0.7918"],
        "Source": ["10.1000/exemplo"],
    }).to_csv(arquivo, index=False)

    auditoria.auditar_densidades(arquivo)

    saida = capsys.readouterr().out

    assert "Total de registros: 1" in saida
    assert "Density_g/cm^3" in saida


def test_auditar_densidades_rejeita_coluna_ausente(tmp_path):
    arquivo = tmp_path / "densidades.csv"

    pd.DataFrame({
        "Solvent": ["methanol"],
        "Temperature_K": [298.15],
        "Density_g/cm^3": ["0.7918"],
    }).to_csv(arquivo, index=False)

    with pytest.raises(ValueError, match="Source"):
        auditoria.auditar_densidades(arquivo)


def test_main_executa_auditoria_com_arquivos_temporarios(
    tmp_path,
    monkeypatch,
    capsys,
):
    arquivo_principal = tmp_path / "dataset.csv"
    arquivo_densidades = tmp_path / "densidades.csv"

    df = pd.DataFrame({
        "SMILES_Solute": ["CCO", "OCC", "CC"],
        "Temperature_K": [298.15, 303.15, 298.15],
        "Solvent": [
            "methanol",
            "diisobutyl methanol",
            "water",
        ],
        "SMILES_Solvent": ["CO", "CO", "O"],
        "Solubility(mole_fraction)": [0.1, 0.2, 0.3],
        "Solubility(mol/L)": [1.0, None, 2.0],
        "LogS(mol/L)": [0.0, None, 0.30103],
        "Compound_Name": ["Etanol", "Etanol", "Etano"],
        "CAS": ["1", "2", "3"],
        "PubChem_CID": [1, 2, 3],
        "FDA_Approved": ["No", "No", "No"],
        "Source": [
            "10.1000/a",
            "10.1000/b",
            "10.1000/c",
        ],
    })

    densidades = pd.DataFrame({
        "Solvent": ["methanol"],
        "Temperature_K": [298.15],
        "Density_g/cm^3": ["0.7918"],
        "Source": ["10.1000/d"],
    })

    df.to_csv(arquivo_principal, index=False)
    densidades.to_csv(arquivo_densidades, index=False)

    monkeypatch.setattr(
        "sys.argv",
        [
            "auditar_dataset.py",
            "--csv",
            str(arquivo_principal),
            "--densities",
            str(arquivo_densidades),
        ],
    )

    resultado = auditoria.main()

    saida = capsys.readouterr().out

    assert resultado == 0
    assert "AUDITORIA INICIAL CONCLUÍDA" in saida


def test_main_rejeita_dataset_sem_colunas_obrigatorias(
    tmp_path,
    monkeypatch,
    capsys,
):
    arquivo_principal = tmp_path / "dataset_invalido.csv"

    pd.DataFrame({
        "SMILES_Solute": ["CCO"],
        "Temperature_K": [298.15],
        "Solvent": ["methanol"],
    }).to_csv(arquivo_principal, index=False)

    monkeypatch.setattr(
        "sys.argv",
        [
            "auditar_dataset.py",
            "--csv",
            str(arquivo_principal),
        ],
    )

    resultado = auditoria.main()

    saida = capsys.readouterr().out

    assert resultado == 1
    assert "ERRO NA AUDITORIA" in saida
    assert "LogS(mol/L)" in saida
