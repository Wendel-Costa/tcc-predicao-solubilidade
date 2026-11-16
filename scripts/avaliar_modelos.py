
"""Avaliação comparativa dos modelos na validação agrupada interna.
"""

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

from scripts.dividir_dados import dividir_dataset
from scripts.treinar_modelos import (
    ALVO,
    COLUNAS,
    construir_atributos,
    criar_modelos,
)


RAIZ = Path(__file__).resolve().parents[1]


def calcular_metricas(y_real, y_previsto):
    """Calcula MAE, RMSE e R² na escala LogS."""

    return {
        "MAE": float(mean_absolute_error(y_real, y_previsto)),
        "RMSE": float(
            np.sqrt(mean_squared_error(y_real, y_previsto))
        ),
        "R2": float(r2_score(y_real, y_previsto)),
    }


def executar_avaliacao(dados, semente=42):
    """Treina e avalia modelos na mesma divisão interna."""

    ausentes = COLUNAS.difference(dados.columns)

    if ausentes:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {sorted(ausentes)}"
        )

    if dados.empty:
        raise ValueError("O dataset está vazio")

    for coluna in ("Temperature_K", ALVO):
        numeros = pd.to_numeric(
            dados[coluna], errors="coerce"
        ).to_numpy(dtype=float)

        if not np.isfinite(numeros).all():
            raise ValueError(
                f"Valores inválidos em {coluna}"
            )

    if (pd.to_numeric(dados["Temperature_K"]) <= 0).any():
        raise ValueError("Temperature_K deve ser maior que zero")

    ajuste, validacao = dividir_dataset(
        dados,
        fracao_teste=0.20,
        semente=semente,
    )

    if len(validacao) < 2:
        raise ValueError("Validação insuficiente para R²")

    grupos_ajuste = set(ajuste["SMILES_Canonico"])
    grupos_validacao = set(validacao["SMILES_Canonico"])

    if grupos_ajuste & grupos_validacao:
        raise RuntimeError("Vazamento entre ajuste e validação")

    x_ajuste = construir_atributos(ajuste)
    x_validacao = construir_atributos(validacao)

    y_ajuste = ajuste[ALVO].to_numpy(dtype=float)
    y_validacao = validacao[ALVO].to_numpy(dtype=float)

    metricas = {}
    predicoes = {}

    for nome, modelo in criar_modelos(semente).items():
        modelo.fit(x_ajuste, y_ajuste)

        previsto = np.asarray(
            modelo.predict(x_validacao),
            dtype=float,
        )

        if not np.isfinite(previsto).all():
            raise RuntimeError(
                f"Predições inválidas no modelo {nome}"
            )

        metricas[nome] = calcular_metricas(
            y_validacao,
            previsto,
        )

        predicoes[nome] = previsto

    resumo = {
        "semente": semente,
        "fracao_validacao_grupos": 0.20,
        "registros_ajuste": len(ajuste),
        "registros_validacao": len(validacao),
        "moleculas_ajuste": len(grupos_ajuste),
        "moleculas_validacao": len(grupos_validacao),
        "moleculas_compartilhadas": len(
            grupos_ajuste & grupos_validacao
        ),
        "escala": "LogS(mol/L)",
        "metricas": metricas,
    }

    return resumo, validacao, predicoes


def salvar_graficos(dados, validacao, predicoes, pasta):
    """Gera gráficos para a análise científica."""

    pasta.mkdir(parents=True, exist_ok=True)

    # 1. Distribuição de LogS no treino do C14.
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.hist(dados[ALVO], bins=40)
    ax.set_title("Distribuição de LogS — treino C14")
    ax.set_xlabel("LogS(mol/L)")
    ax.set_ylabel("Número de registros")

    fig.tight_layout()
    fig.savefig(
        pasta / "distribuicao_logs.png", dpi=160
    )
    plt.close(fig)

    # 2. Distribuição de temperatura no treino do C14.
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.hist(dados["Temperature_K"], bins=40)
    ax.set_title("Distribuição das temperaturas — treino C14")
    ax.set_xlabel("Temperatura (K)")
    ax.set_ylabel("Número de registros")

    fig.tight_layout()
    fig.savefig(
        pasta / "distribuicao_temperatura.png", dpi=160
    )
    plt.close(fig)

    reais = validacao[ALVO].to_numpy(dtype=float)

    # 3. Observado versus predito.
    fig, ax = plt.subplots(figsize=(8, 6))

    for nome, previsto in predicoes.items():
        ax.scatter(
            reais,
            previsto,
            alpha=0.4,
            s=14,
            label=nome,
        )

    limites = [
        float(min(reais.min(), *(p.min() for p in predicoes.values()))),
        float(max(reais.max(), *(p.max() for p in predicoes.values()))),
    ]

    ax.plot(
        limites,
        limites,
        linestyle="--",
        color="black",
        label="Predição perfeita",
    )

    ax.set_xlabel("LogS observado")
    ax.set_ylabel("LogS predito")
    ax.set_title("Observado versus predito — validação")
    ax.legend()
    fig.tight_layout()

    fig.savefig(
        pasta / "observado_predito.png", dpi=160
    )
    plt.close(fig)

    # 4. Resíduos versus predição.
    # Resíduo = observado - predito.
    fig, ax = plt.subplots(figsize=(8, 6))

    for nome, previsto in predicoes.items():
        residuos = reais - previsto

        ax.scatter(
            previsto,
            residuos,
            alpha=0.4,
            s=14,
            label=nome,
        )

    ax.axhline(
        0,
        linestyle="--",
        color="black",
    )

    ax.set_xlabel("LogS predito")
    ax.set_ylabel("Resíduo (observado - predito)")
    ax.set_title("Resíduos — validação")
    ax.legend()
    fig.tight_layout()

    fig.savefig(
        pasta / "residuos.png", dpi=160
    )
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--input",
        type=Path,
        default=RAIZ / "data/processed/split/treino.csv",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RAIZ / "reports/model_comparison",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    args = parser.parse_args()

    origem = args.input.resolve()

    if not origem.is_file():
        parser.error(f"CSV não encontrado: {origem}")

    if origem.name.casefold() == "teste.csv":
        parser.error(
            "teste.csv está reservado para avaliação final"
        )

    dados = pd.read_csv(origem, low_memory=False)

    resumo, validacao, predicoes = executar_avaliacao(
        dados,
        semente=args.seed,
    )

    resumo["data_execucao"] = date.today().isoformat()
    resumo["arquivo_entrada"] = str(origem)
    resumo["sha256_entrada"] = hashlib.sha256(
        origem.read_bytes()
    ).hexdigest()

    pasta = args.output_dir.resolve()
    pasta.mkdir(parents=True, exist_ok=True)

    salvar_graficos(
        dados,
        validacao,
        predicoes,
        pasta,
    )

    with (pasta / "metricas.json").open(
        "w", encoding="utf-8"
    ) as arquivo:
        json.dump(
            resumo,
            arquivo,
            indent=2,
            ensure_ascii=False,
        )

    print("AVALIAÇÃO COMPARATIVA — VALIDAÇÃO INTERNA")

    for chave, valor in resumo.items():
        if chave != "metricas":
            print(f"{chave}: {valor}")

    for nome, m in resumo["metricas"].items():
        print(
            f"{nome}: "
            f"MAE={m['MAE']:.6f}; "
            f"RMSE={m['RMSE']:.6f}; "
            f"R2={m['R2']:.6f}"
        )

    print(f"Relatórios e gráficos: {pasta}")
    print("O teste.csv do C14 não foi utilizado.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
