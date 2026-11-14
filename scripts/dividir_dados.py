
"""Divisão reproduzível dos dados curados por molécula canônica."""

import argparse
from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit


COLUNAS_OBRIGATORIAS = {
    "SMILES_Canonico",
    "Temperature_K",
    "LogS(mol/L)",
    "Source_Row",
}

SEMENTE_PADRAO = 42
FRACAO_TESTE = 0.20


def dividir_dataset(
    dados: pd.DataFrame,
    fracao_teste: float = FRACAO_TESTE,
    semente: int = SEMENTE_PADRAO,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa todas as observações de uma molécula na mesma partição."""

    ausentes = COLUNAS_OBRIGATORIAS.difference(dados.columns)

    if ausentes:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {sorted(ausentes)}"
        )

    if not 0 < fracao_teste < 1:
        raise ValueError("fracao_teste deve estar entre 0 e 1")

    if dados.empty:
        raise ValueError("O dataset está vazio")

    if dados["SMILES_Canonico"].isna().any() or (
        dados["SMILES_Canonico"].astype(str).str.strip() == ""
    ).any():
        raise ValueError(
            "Existem SMILES canônicos ausentes ou vazios"
        )

    if (
        dados["Source_Row"].isna().any()
        or not dados["Source_Row"].is_unique
    ):
        raise ValueError(
            "Source_Row deve identificar cada registro unicamente"
        )

    if dados["SMILES_Canonico"].nunique() < 2:
        raise ValueError(
            "São necessárias ao menos duas moléculas distintas"
        )

    divisor = GroupShuffleSplit(
        n_splits=1,
        test_size=fracao_teste,
        random_state=semente,
    )

    indices_treino, indices_teste = next(
        divisor.split(
            dados,
            groups=dados["SMILES_Canonico"],
        )
    )

    treino = (
        dados.iloc[indices_treino]
        .copy()
        .reset_index(drop=True)
    )

    teste = (
        dados.iloc[indices_teste]
        .copy()
        .reset_index(drop=True)
    )

    grupos_treino = set(treino["SMILES_Canonico"])
    grupos_teste = set(teste["SMILES_Canonico"])

    if grupos_treino.intersection(grupos_teste):
        raise RuntimeError(
            "Vazamento: molécula presente em treino e teste"
        )

    if len(treino) + len(teste) != len(dados):
        raise RuntimeError("A divisão perdeu registros")

    return treino, teste


def main() -> int:
    raiz = Path(__file__).resolve().parents[1]

    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=raiz / "data/processed/metanol_curado.csv",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=raiz / "data/processed/split",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=SEMENTE_PADRAO,
    )

    argumentos = parser.parse_args()

    origem = argumentos.input.resolve()
    pasta = argumentos.output_dir.resolve()

    if not origem.is_file():
        parser.error(
            f"CSV curado não encontrado: {origem}"
        )

    if origem in (
        pasta / "treino.csv",
        pasta / "teste.csv",
    ):
        parser.error(
            "O arquivo de entrada não pode ser sobrescrito"
        )

    if (
        (pasta / "treino.csv").exists()
        or (pasta / "teste.csv").exists()
    ):
        parser.error(
            "Arquivos de partição já existem; "
            "não serão sobrescritos"
        )

    dados = pd.read_csv(
        origem,
        low_memory=False,
    )

    try:
        treino, teste = dividir_dataset(
            dados,
            semente=argumentos.seed,
        )
    except ValueError as erro:
        parser.error(str(erro))

    pasta.mkdir(
        parents=True,
        exist_ok=True,
    )

    treino.to_csv(
        pasta / "treino.csv",
        index=False,
    )

    teste.to_csv(
        pasta / "teste.csv",
        index=False,
    )

    print(
        f"Semente: {argumentos.seed}; "
        f"fração-alvo de grupos no teste: "
        f"{FRACAO_TESTE:.0%}"
    )

    print(
        f"Treino: {len(treino)} registros, "
        f"{treino['SMILES_Canonico'].nunique()} moléculas"
    )

    print(
        f"Teste: {len(teste)} registros, "
        f"{teste['SMILES_Canonico'].nunique()} moléculas"
    )

    print("Moléculas compartilhadas: 0")
    print(f"Saída: {pasta}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
