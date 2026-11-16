
"""Compara baseline, Ridge e Random Forest na validação interna do C14.

Não lê, treina nem avalia o conjunto final teste.csv.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.chemistry import FEATURE_NAMES, extrair_atributos
from scripts.dividir_dados import dividir_dataset


RAIZ = Path(__file__).resolve().parents[1]

ALVO = "LogS(mol/L)"

COLUNAS = {
    "Source_Row",
    "SMILES_Canonico",
    "Temperature_K",
    ALVO,
}


def construir_atributos(dados: pd.DataFrame) -> pd.DataFrame:
    """Aplica a mesma função de química prevista para a inferência."""

    linhas = [
        extrair_atributos(smiles, float(temperatura))
        for smiles, temperatura in zip(
            dados["SMILES_Canonico"],
            dados["Temperature_K"],
        )
    ]

    return pd.DataFrame(
        linhas,
        columns=list(FEATURE_NAMES),
    )


def comparar_modelos(
    dados: pd.DataFrame,
    semente: int = 42,
) -> dict:
    """Ajusta e compara modelos sem tocar no teste final do C14."""

    # 1. Conferir as colunas obrigatórias.
    ausentes = COLUNAS.difference(dados.columns)

    if ausentes:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {sorted(ausentes)}"
        )

    if dados.empty:
        raise ValueError(
            "O conjunto de treinamento está vazio"
        )

    # 2. Validar as variáveis numéricas.
    for coluna in ("Temperature_K", ALVO):
        numeros = pd.to_numeric(
            dados[coluna],
            errors="coerce",
        ).to_numpy(dtype=float)

        if not np.isfinite(numeros).all():
            raise ValueError(
                f"Valores inválidos ou não finitos em {coluna}"
            )

    if (
        pd.to_numeric(dados["Temperature_K"]) <= 0
    ).any():
        raise ValueError(
            "Temperature_K deve ser maior que zero"
        )

    # 3. Utilizar a mesma divisão interna do C15.
    ajuste, validacao = dividir_dataset(
        dados,
        fracao_teste=0.20,
        semente=semente,
    )

    if len(validacao) < 2:
        raise ValueError(
            "A validação precisa ter pelo menos duas observações"
        )

    grupos_a = set(ajuste["SMILES_Canonico"])
    grupos_v = set(validacao["SMILES_Canonico"])

    if grupos_a & grupos_v:
        raise RuntimeError(
            "Vazamento entre ajuste e validação"
        )

    # 4. Calcular os mesmos atributos de treinamento e inferência.
    x_ajuste = construir_atributos(ajuste)
    x_validacao = construir_atributos(validacao)

    y_ajuste = ajuste[ALVO].to_numpy(dtype=float)
    y_validacao = validacao[ALVO].to_numpy(dtype=float)

    # 5. Definir os modelos.
    modelos = {
        "DummyRegressor": DummyRegressor(
            strategy="median",
        ),
        "Ridge": Pipeline([
            ("escala", StandardScaler()),
            ("modelo", Ridge(alpha=1.0)),
        ]),
        "RandomForest": RandomForestRegressor(
            n_estimators=200,
            min_samples_leaf=2,
            random_state=semente,
            n_jobs=1,
        ),
    }

    # 6. Treinar e avaliar na mesma validação.
    resultados = {}

    for nome, modelo in modelos.items():
        modelo.fit(x_ajuste, y_ajuste)

        previsto = modelo.predict(x_validacao)

        if not np.isfinite(previsto).all():
            raise RuntimeError(
                f"Predições não finitas: {nome}"
            )

        resultados[nome] = {
            "MAE": float(
                mean_absolute_error(
                    y_validacao,
                    previsto,
                )
            ),
            "RMSE": float(
                np.sqrt(
                    mean_squared_error(
                        y_validacao,
                        previsto,
                    )
                )
            ),
            "R2": float(
                r2_score(
                    y_validacao,
                    previsto,
                )
            ),
        }

    # 7. Registrar as informações da divisão.
    return {
        "semente": semente,
        "registros_ajuste": len(ajuste),
        "registros_validacao": len(validacao),
        "moleculas_ajuste": len(grupos_a),
        "moleculas_validacao": len(grupos_v),
        "moleculas_compartilhadas": len(
            grupos_a & grupos_v
        ),
        "modelos": resultados,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=RAIZ / "data/processed/split/treino.csv",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(
            f"CSV de treino não encontrado: {args.input}"
        )

    if args.input.name.casefold() == "teste.csv":
        parser.error(
            "Não use teste.csv: o teste final está reservado"
        )

    dados = pd.read_csv(
        args.input,
        low_memory=False,
    )

    resultados = comparar_modelos(
        dados,
        semente=args.seed,
    )

    print(
        "Comparação na validação interna — sem uso de teste.csv"
    )

    for chave, valor in resultados.items():
        if chave != "modelos":
            print(f"{chave}: {valor}")

    for nome, metricas in resultados["modelos"].items():
        print(
            f"{nome}: "
            f"MAE={metricas['MAE']:.6f}; "
            f"RMSE={metricas['RMSE']:.6f}; "
            f"R2={metricas['R2']:.6f}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
