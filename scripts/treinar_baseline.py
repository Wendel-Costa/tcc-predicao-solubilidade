
"""Baseline mediana com validação agrupada apenas no treino do C14."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

from scripts.dividir_dados import dividir_dataset


RAIZ = Path(__file__).resolve().parents[1]

ALVO = "LogS(mol/L)"

COLUNAS = {
    "SMILES_Canonico",
    "Source_Row",
    "Temperature_K",
    ALVO,
}


def avaliar_baseline(
    dados: pd.DataFrame,
    semente: int = 42,
) -> dict:
    """Avalia a baseline com moléculas separadas para validação."""

    # 1. Conferir as colunas obrigatórias.
    ausentes = COLUNAS - set(dados.columns)

    if ausentes:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {sorted(ausentes)}"
        )

    if dados.empty:
        raise ValueError(
            "O conjunto de treinamento está vazio"
        )

    # 2. Validar as variáveis numéricas.
    for nome in ("Temperature_K", ALVO):
        valores = pd.to_numeric(
            dados[nome],
            errors="coerce",
        )

        if not np.isfinite(
            valores.to_numpy(dtype=float)
        ).all():
            raise ValueError(
                f"Valores inválidos ou não finitos em {nome}"
            )

    if (
        pd.to_numeric(dados["Temperature_K"]) <= 0
    ).any():
        raise ValueError(
            "Temperature_K deve ser maior que zero"
        )

    # 3. Reutilizar a divisão agrupada do C14.
    # Nenhuma observação do teste final é utilizada aqui.
    ajuste, validacao = dividir_dataset(
        dados,
        fracao_teste=0.20,
        semente=semente,
    )

    grupos_ajuste = set(
        ajuste["SMILES_Canonico"]
    )

    grupos_validacao = set(
        validacao["SMILES_Canonico"]
    )

    # 4. Conferir ausência de vazamento.
    if grupos_ajuste & grupos_validacao:
        raise RuntimeError(
            "Moléculas compartilhadas entre ajuste e validação"
        )

    if len(ajuste) + len(validacao) != len(dados):
        raise RuntimeError(
            "Registros perdidos na divisão"
        )

    # 5. Criar e ajustar a baseline.
    modelo = DummyRegressor(
        strategy="median"
    )

    # DummyRegressor ignora os valores de X ao calcular
    # a mediana. Temperature_K mantém a interface
    # padrão do scikit-learn.
    modelo.fit(
        ajuste[["Temperature_K"]],
        ajuste[ALVO],
    )

    # 6. Predizer somente a validação interna.
    y_real = validacao[ALVO].to_numpy(
        dtype=float
    )

    y_previsto = modelo.predict(
        validacao[["Temperature_K"]]
    )

    # 7. Calcular métricas na escala LogS(mol/L).
    return {
        "registros_ajuste": len(ajuste),
        "registros_validacao": len(validacao),
        "moleculas_ajuste": len(grupos_ajuste),
        "moleculas_validacao": len(grupos_validacao),
        "moleculas_compartilhadas": len(
            grupos_ajuste & grupos_validacao
        ),
        "mediana_ajuste": float(
            modelo.constant_[0, 0]
        ),
        "mae_validacao": float(
            mean_absolute_error(
                y_real,
                y_previsto,
            )
        ),
        "rmse_validacao": float(
            np.sqrt(
                mean_squared_error(
                    y_real,
                    y_previsto,
                )
            )
        ),
        "r2_validacao": (
            float(r2_score(y_real, y_previsto))
            if len(y_real) >= 2
            else None
        ),
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

    dados = pd.read_csv(
        args.input,
        low_memory=False,
    )

    resultados = avaliar_baseline(
        dados,
        semente=args.seed,
    )

    print(
        "Baseline: DummyRegressor(strategy='median')"
    )

    print(
        "Avaliação: validação agrupada interna ao treino do C14"
    )

    for chave, valor in resultados.items():
        print(f"{chave}: {valor}")

    print(
        "O arquivo teste.csv do C14 NÃO foi utilizado."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
