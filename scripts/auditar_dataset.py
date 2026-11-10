import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger


RAIZ_PROJETO = Path(__file__).resolve().parents[1]

ARQUIVO_PADRAO = RAIZ_PROJETO / "data" / "raw" / "BigSolDBv2.0.csv"

DENSIDADES_PADRAO = RAIZ_PROJETO / "data" / "raw" / "BigSolDBv2.0_densities.csv"

COLUNAS_OBRIGATORIAS = {
    "SMILES_Solute",
    "Temperature_K",
    "Solvent",
    "LogS(mol/L)",
}

COLUNAS_NUMERICAS = [
    "Temperature_K",
    "Solubility(mole_fraction)",
    "Solubility(mol/L)",
    "LogS(mol/L)",
]

COLUNAS_DENSIDADE = {
    "Solvent",
    "Temperature_K",
    "Density_g/cm^3",
    "Source",
}


def carregar_csv(caminho: Path) -> pd.DataFrame:
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    return pd.read_csv(caminho, low_memory=False)


def verificar_colunas(df: pd.DataFrame) -> None:
    ausentes = COLUNAS_OBRIGATORIAS - set(df.columns)

    if ausentes:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {sorted(ausentes)}"
        )


def imprimir_estrutura(df: pd.DataFrame) -> None:
    print("\n" + "=" * 65)
    print("1. ESTRUTURA DO DATASET")
    print("=" * 65)

    print(f"Total de registros: {len(df):,}")
    print(f"Total de colunas: {len(df.columns)}")

    print("\nColunas e tipos identificados:")

    for coluna, tipo in df.dtypes.items():
        print(f"  - {coluna}: {tipo}")


def imprimir_valores_ausentes(df: pd.DataFrame) -> None:
    print("\n" + "=" * 65)
    print("2. VALORES AUSENTES")
    print("=" * 65)

    ausentes = df.isna().sum()

    for coluna, quantidade in ausentes.items():
        percentual = quantidade / len(df) * 100

        print(
            f"{coluna}: {quantidade:,} "
            f"({percentual:.2f}%)"
        )


def imprimir_distribuicao_numerica(
    df: pd.DataFrame,
    coluna: str
) -> None:
    if coluna not in df.columns:
        return

    print(f"\n{coluna}")

    original = df[coluna]
    numerico = pd.to_numeric(original, errors="coerce")

    valores = numerico.to_numpy(
        dtype="float64",
        na_value=np.nan
    )

    finitos = np.isfinite(valores)

    vazios = (
        original.isna()
        | original.astype("string").str.strip().eq("").fillna(False)
    )

    invalidos = (~vazios) & numerico.isna()

    nao_finitos = numerico.notna() & ~pd.Series(
        finitos,
        index=df.index
    )

    validos = numerico[finito_mask := pd.Series(finitos, index=df.index)]

    print(f"  Valores ausentes: {vazios.sum():,}")
    print(f"  Valores não numéricos: {invalidos.sum():,}")
    print(f"  Valores não finitos: {nao_finitos.sum():,}")
    print(f"  Valores numéricos finitos: {len(validos):,}")

    if not validos.empty:
        print(f"  Mínimo: {validos.min():.6f}")
        print(f"  Máximo: {validos.max():.6f}")
        print(f"  Média: {validos.mean():.6f}")
        print(f"  Mediana: {validos.median():.6f}")
        print(f"  Desvio padrão: {validos.std():.6f}")
        print(f"  Q1: {validos.quantile(0.25):.6f}")
        print(f"  Q3: {validos.quantile(0.75):.6f}")


def auditar_colunas_numericas(df: pd.DataFrame) -> None:
    print("\n" + "=" * 65)
    print("3. DISTRIBUIÇÕES NUMÉRICAS")
    print("=" * 65)

    for coluna in COLUNAS_NUMERICAS:
        imprimir_distribuicao_numerica(df, coluna)


def auditar_solventes(df: pd.DataFrame) -> None:
    print("\n" + "=" * 65)
    print("4. SOLVENTES IDENTIFICADOS")
    print("=" * 65)

    contagem = (
        df["Solvent"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .value_counts()
    )

    print(f"Total de nomenclaturas distintas: {len(contagem)}")

    print("\nDistribuição das nomenclaturas:")

    for solvente, quantidade in contagem.items():
        print(f"  - {solvente}: {quantidade:,}")

    candidatos = [
        solvente
        for solvente in contagem.index
        if "methanol" in solvente.casefold()
        or "methyl alcohol" in solvente.casefold()
    ]

    print("\nNomenclaturas contendo 'methanol' ou 'methyl alcohol':")

    if candidatos:
        for solvente in candidatos:
            print(f"  - {solvente}: {contagem[solvente]:,}")
    else:
        print("  Nenhuma nomenclatura encontrada.")


def auditar_smiles(df: pd.DataFrame) -> list:
    print("\n" + "=" * 65)
    print("5. VALIDAÇÃO DAS ESTRUTURAS SMILES")
    print("=" * 65)

    RDLogger.DisableLog("rdApp.error")

    canonicos = []
    validos = 0
    invalidos = 0
    ausentes = 0

    try:
        for smiles in df["SMILES_Solute"]:
            if pd.isna(smiles) or not str(smiles).strip():
                ausentes += 1
                canonicos.append(None)
                continue

            molecula = Chem.MolFromSmiles(str(smiles).strip())

            if molecula is None:
                invalidos += 1
                canonicos.append(None)
                continue

            canonico = Chem.MolToSmiles(
                molecula,
                canonical=True,
                isomericSmiles=True
            )

            validos += 1
            canonicos.append(canonico)

    finally:
        RDLogger.EnableLog("rdApp.error")

    print(f"SMILES válidos: {validos:,}")
    print(f"SMILES inválidos: {invalidos:,}")
    print(f"SMILES ausentes: {ausentes:,}")

    distintos = {
        smiles for smiles in canonicos
        if smiles is not None
    }

    print(f"Moléculas canônicas distintas: {len(distintos):,}")

    return canonicos


def auditar_repeticoes(
    df: pd.DataFrame,
    canonicos: list
) -> None:
    print("\n" + "=" * 65)
    print("6. DUPLICATAS E MEDIÇÕES REPETIDAS")
    print("=" * 65)

    duplicatas = df.duplicated().sum()

    print(f"Duplicatas exatas: {duplicatas:,}")

    temperaturas = pd.to_numeric(
        df["Temperature_K"],
        errors="coerce"
    )

    valores_temperatura = temperaturas.to_numpy(
        dtype="float64",
        na_value=np.nan
    )

    mascara = (
        pd.Series(canonicos, index=df.index).notna()
        & np.isfinite(valores_temperatura)
    )

    registros = pd.DataFrame({
        "SMILES_Canonico": pd.Series(canonicos, index=df.index),
        "Temperature_K": temperaturas,
    }).loc[mascara]

    repetidas = (
        registros
        .groupby("SMILES_Canonico")["Temperature_K"]
        .nunique()
    )

    repetidas = repetidas[repetidas > 1]

    print(
        "Moléculas com medições em mais de uma temperatura: "
        f"{len(repetidas):,}"
    )

    print(f"Moléculas distintas com temperatura válida: {len(registros['SMILES_Canonico'].unique()):,}")


def auditar_fontes(df: pd.DataFrame) -> None:
    print("\n" + "=" * 65)
    print("7. FONTES CIENTÍFICAS")
    print("=" * 65)

    if "Source" not in df.columns:
        print("Coluna Source não encontrada.")
        return

    fontes = df["Source"].dropna()

    print(f"Registros com fonte informada: {len(fontes):,}")
    print(f"Fontes distintas: {fontes.nunique():,}")

    print("\nDez fontes mais frequentes:")

    for fonte, quantidade in fontes.value_counts().head(10).items():
        print(f"  - {fonte}: {quantidade:,}")


def auditar_densidades(caminho: Path) -> None:
    print("\n" + "=" * 65)
    print("8. ARQUIVO COMPLEMENTAR DE DENSIDADES")
    print("=" * 65)

    densidades = carregar_csv(caminho)

    ausentes = COLUNAS_DENSIDADE - set(densidades.columns)

    if ausentes:
        raise ValueError(
            f"Colunas ausentes no arquivo de densidades: {sorted(ausentes)}"
        )

    print(f"Total de registros: {len(densidades):,}")

    print("\nColunas:")

    for coluna, tipo in densidades.dtypes.items():
        print(f"  - {coluna}: {tipo}")

    print("\nValores ausentes:")

    for coluna, quantidade in densidades.isna().sum().items():
        print(f"  - {coluna}: {quantidade:,}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Auditoria inicial do BigSolDB 2.0."
    )

    parser.add_argument(
        "--csv",
        type=Path,
        default=ARQUIVO_PADRAO,
        help="Caminho do CSV principal."
    )

    parser.add_argument(
        "--densities",
        type=Path,
        default=DENSIDADES_PADRAO,
        help="Caminho do CSV complementar de densidades."
    )

    args = parser.parse_args()

    try:
        print("Carregando BigSolDB 2.0...")

        df = carregar_csv(args.csv)

        verificar_colunas(df)

        imprimir_estrutura(df)
        imprimir_valores_ausentes(df)
        auditar_colunas_numericas(df)
        auditar_solventes(df)

        canonicos = auditar_smiles(df)

        auditar_repeticoes(df, canonicos)
        auditar_fontes(df)
        auditar_densidades(args.densities)

        print("\n" + "=" * 65)
        print("AUDITORIA INICIAL CONCLUÍDA")
        print("=" * 65)

        return 0

    except (FileNotFoundError, ValueError, pd.errors.ParserError) as erro:
        print(f"\nERRO NA AUDITORIA: {erro}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())