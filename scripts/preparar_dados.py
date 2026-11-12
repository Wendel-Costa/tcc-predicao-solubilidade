
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger


RAIZ_PROJETO = Path(__file__).resolve().parents[1]

ARQUIVO_ENTRADA_PADRAO = (
    RAIZ_PROJETO / "data" / "raw" / "BigSolDBv2.0.csv"
)

ARQUIVO_SAIDA_PADRAO = (
    RAIZ_PROJETO / "data" / "processed" / "metanol_curado.csv"
)

SMILES_METANOL = "CO"

COLUNAS_OBRIGATORIAS = {
    "SMILES_Solute",
    "Temperature_K",
    "Solvent",
    "SMILES_Solvent",
    "LogS(mol/L)",
}


def carregar_dataset(caminho: Path) -> pd.DataFrame:
    if not caminho.is_file():
        raise FileNotFoundError(
            f"Dataset não encontrado: {caminho}"
        )

    return pd.read_csv(caminho, low_memory=False)


def validar_colunas(df: pd.DataFrame) -> None:
    ausentes = COLUNAS_OBRIGATORIAS - set(df.columns)

    if ausentes:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {sorted(ausentes)}"
        )


def obter_smiles_canonico(valor) -> str | None:
    if pd.isna(valor) or not str(valor).strip():
        return None

    try:
        molecula = Chem.MolFromSmiles(str(valor).strip())

        if molecula is None:
            return None

        return Chem.MolToSmiles(
            molecula,
            canonical=True,
            isomericSmiles=True,
        )

    except Exception:
        return None


def canonicalizar_coluna(serie: pd.Series) -> pd.Series:
    RDLogger.DisableLog("rdApp.error")

    try:
        return serie.map(obter_smiles_canonico)
    finally:
        RDLogger.EnableLog("rdApp.error")


def mascara_valores_finitos(serie: pd.Series) -> pd.Series:
    valores = pd.to_numeric(serie, errors="coerce")

    array = valores.to_numpy(
        dtype="float64",
        na_value=np.nan,
    )

    return pd.Series(
        np.isfinite(array),
        index=serie.index,
    )


def preparar_dataset(
    df_original: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    validar_colunas(df_original)

    dados = df_original.copy()

    colunas_originais = list(dados.columns)

    # Identificação da linha no CSV original, considerando o cabeçalho.
    dados.insert(
        0,
        "Source_Row",
        np.arange(2, len(dados) + 2),
    )

    # 1. Identificação textual do solvente.
    nome_metanol = (
        dados["Solvent"]
        .astype("string")
        .str.strip()
        .str.casefold()
        .eq("methanol")
        .fillna(False)
    )

    # 2. Identificação estrutural do solvente.
    smiles_solvente = canonicalizar_coluna(
        dados["SMILES_Solvent"]
    )

    molecula_metanol = Chem.MolFromSmiles(SMILES_METANOL)

    if molecula_metanol is None:
        raise RuntimeError("Não foi possível interpretar o metanol.")

    metanol_canonico = Chem.MolToSmiles(
        molecula_metanol,
        canonical=True,
        isomericSmiles=True,
    )

    estrutura_metanol = smiles_solvente.eq(metanol_canonico)

    # 3. Identificação de concordâncias e divergências.
    nome_e_estrutura = nome_metanol & estrutura_metanol

    somente_nome = nome_metanol & ~estrutura_metanol

    somente_estrutura = estrutura_metanol & ~nome_metanol

    # A inclusão exige concordância entre nome e estrutura química.
    candidatos = dados.loc[nome_e_estrutura].copy()

    resumo = {
        "registros_originais": len(dados),
        "nomenclaturas_methanol": int(nome_metanol.sum()),
        "estruturas_de_metanol": int(estrutura_metanol.sum()),
        "concordancia_nome_estrutura": int(nome_e_estrutura.sum()),
        "apenas_nome_methanol": int(somente_nome.sum()),
        "apenas_estrutura_metanol": int(somente_estrutura.sum()),
        "smiles_solvente_invalidos_ou_ausentes": int(
            smiles_solvente.isna().sum()
        ),
    }

    resumo["candidatos_metanol"] = len(candidatos)

    if candidatos.empty:
        raise ValueError(
            "Nenhum registro foi confirmado como metanol."
        )

    # 4. Canonicalização das moléculas dissolvidas.
    canonicos_soluto = canonicalizar_coluna(
        candidatos["SMILES_Solute"]
    )

    candidatos["SMILES_Canonico"] = canonicos_soluto

    validos_smiles = canonicos_soluto.notna()

    resumo["soluto_smiles_invalidos_ou_ausentes"] = int(
        (~validos_smiles).sum()
    )

    apos_smiles = candidatos.loc[validos_smiles].copy()

    # 5. Validação da temperatura.
    temperaturas = pd.to_numeric(
        apos_smiles["Temperature_K"],
        errors="coerce",
    )

    temperaturas_array = temperaturas.to_numpy(
        dtype="float64",
        na_value=np.nan,
    )

    temperaturas_validas = pd.Series(
        np.isfinite(temperaturas_array)
        & (temperaturas_array > 0),
        index=apos_smiles.index,
    )

    resumo["temperaturas_invalidas_ou_ausentes"] = int(
        (~temperaturas_validas).sum()
    )

    apos_temperatura = apos_smiles.loc[
        temperaturas_validas
    ].copy()

    apos_temperatura["Temperature_K"] = temperaturas.loc[
        temperaturas_validas
    ]

    # 6. Validação da variável-alvo.
    logs = pd.to_numeric(
        apos_temperatura["LogS(mol/L)"],
        errors="coerce",
    )

    logs_array = logs.to_numpy(
        dtype="float64",
        na_value=np.nan,
    )

    logs_validos = pd.Series(
        np.isfinite(logs_array),
        index=apos_temperatura.index,
    )

    resumo["logs_invalidos_ou_ausentes"] = int(
        (~logs_validos).sum()
    )

    preparados = apos_temperatura.loc[logs_validos].copy()

    preparados["LogS(mol/L)"] = logs.loc[logs_validos]

    if preparados.empty:
        raise ValueError(
            "Nenhum registro válido restou após a preparação."
        )

    # 7. Preservação da rastreabilidade.
    preparados = preparados.sort_values(
        "Source_Row"
    ).reset_index(drop=True)

    # 8. Diagnóstico de repetições, sem excluir medições.
    duplicatas_exatas = preparados.duplicated(
        subset=colunas_originais
    ).sum()

    grupos_molecula_temperatura = (
        preparados
        .groupby(
            ["SMILES_Canonico", "Temperature_K"]
        )
        .size()
    )

    grupos_repetidos = grupos_molecula_temperatura[
        grupos_molecula_temperatura > 1
    ]

    resumo.update({
        "registros_preparados": len(preparados),
        "moleculas_distintas": preparados[
            "SMILES_Canonico"
        ].nunique(),
        "fontes_distintas": (
            preparados["Source"].nunique()
            if "Source" in preparados.columns
            else None
        ),
        "duplicatas_exatas": int(duplicatas_exatas),
        "grupos_molecula_temperatura_repetidos": len(
            grupos_repetidos
        ),
        "registros_em_grupos_repetidos": int(
            grupos_repetidos.sum()
        ),
    })

    return preparados, resumo


def apresentar_resultados(
    dados: pd.DataFrame,
    resumo: dict,
) -> None:
    print("\n" + "=" * 65)
    print("1. IDENTIFICAÇÃO DO METANOL")
    print("=" * 65)

    for chave, valor in resumo.items():
        if chave in {
            "registros_originais",
            "nomenclaturas_methanol",
            "estruturas_de_metanol",
            "concordancia_nome_estrutura",
            "apenas_nome_methanol",
            "apenas_estrutura_metanol",
            "smiles_solvente_invalidos_ou_ausentes",
        }:
            print(f"{chave}: {valor:,}")

    print("\n" + "=" * 65)
    print("2. CURADORIA DOS REGISTROS")
    print("=" * 65)

    for chave in [
        "candidatos_metanol",
        "soluto_smiles_invalidos_ou_ausentes",
        "temperaturas_invalidas_ou_ausentes",
        "logs_invalidos_ou_ausentes",
        "registros_preparados",
    ]:
        print(f"{chave}: {resumo[chave]:,}")

    print("\n" + "=" * 65)
    print("3. CARACTERÍSTICAS DO CONJUNTO PREPARADO")
    print("=" * 65)

    print(
        "Moléculas distintas: "
        f"{resumo['moleculas_distintas']:,}"
    )

    if resumo["fontes_distintas"] is not None:
        print(
            "Fontes científicas distintas: "
            f"{resumo['fontes_distintas']:,}"
        )

    print(
        "Duplicatas exatas: "
        f"{resumo['duplicatas_exatas']:,}"
    )

    print(
        "Grupos com a mesma molécula e temperatura: "
        f"{resumo['grupos_molecula_temperatura_repetidos']:,}"
    )

    print(
        "Registros pertencentes a grupos repetidos: "
        f"{resumo['registros_em_grupos_repetidos']:,}"
    )

    temperaturas = dados["Temperature_K"]

    logs = dados["LogS(mol/L)"]

    print("\nDistribuição de temperatura:")

    print(f"  Mínimo: {temperaturas.min():.6f} K")
    print(f"  Máximo: {temperaturas.max():.6f} K")
    print(f"  Média: {temperaturas.mean():.6f} K")
    print(f"  Mediana: {temperaturas.median():.6f} K")

    referencia_25c = 298.15
    distancias = (temperaturas - referencia_25c).abs()

    print(
        "  Registros entre 298,15 ± 1 K: "
        f"{(distancias <= 1).sum():,}"
    )

    print(
        "  Registros entre 298,15 ± 5 K: "
        f"{(distancias <= 5).sum():,}"
    )

    print(
        "  Distância da medição mais próxima de 25 °C: "
        f"{distancias.min():.6f} K"
    )

    print("\nDistribuição de LogS:")

    print(f"  Mínimo: {logs.min():.6f}")
    print(f"  Máximo: {logs.max():.6f}")
    print(f"  Média: {logs.mean():.6f}")
    print(f"  Mediana: {logs.median():.6f}")

    print("\nObservação:")
    print(
        "As janelas de ±1 K e ±5 K são diagnósticas; "
        "não representam filtros de treinamento."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepara os registros experimentais de metanol."
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=ARQUIVO_ENTRADA_PADRAO,
        help="Caminho do CSV original do BigSolDB 2.0.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=ARQUIVO_SAIDA_PADRAO,
        help="Caminho para salvar o conjunto preparado.",
    )

    args = parser.parse_args()

    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError(
                "O arquivo de saída não pode sobrescrever o original."
            )

        print("Carregando BigSolDB 2.0...")

        df = carregar_dataset(args.input)

        print("Iniciando identificação e preparação...")

        preparados, resumo = preparar_dataset(df)

        args.output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        preparados.to_csv(
            args.output,
            index=False,
            encoding="utf-8",
        )

        apresentar_resultados(preparados, resumo)

        print("\n" + "=" * 65)
        print("PREPARAÇÃO CONCLUÍDA")
        print("=" * 65)

        print(f"Arquivo gerado: {args.output}")
        print(f"Registros salvos: {len(preparados):,}")

        return 0

    except (
        FileNotFoundError,
        ValueError,
        pd.errors.ParserError,
    ) as erro:
        print(f"\nERRO NA PREPARAÇÃO: {erro}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
