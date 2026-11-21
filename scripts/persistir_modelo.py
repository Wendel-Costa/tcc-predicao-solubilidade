
"""C23: seleciona Ridge pela validação agrupada e persiste o reajuste final.

Não lê nem avalia teste.csv.
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import joblib
import numpy as np
import pandas as pd
import rdkit
import sklearn

from app.chemistry import FEATURE_NAMES, extrair_atributos
from app.schemas import ModelInfoResponse
from scripts.treinar_modelos import (
    ALVO, COLUNAS, comparar_modelos, construir_atributos, criar_modelos,
)

RAIZ = Path(__file__).resolve().parents[1]
VERSAO_MODELO = "ridge-v1"
SEMENTE = 42


def sha256_arquivo(caminho: Path) -> str:
    resumo = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def validar_treino(dados: pd.DataFrame) -> None:
    ausentes = COLUNAS.difference(dados.columns)

    if ausentes:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {sorted(ausentes)}"
        )

    if dados.empty:
        raise ValueError("O CSV de treino está vazio")

    if dados["SMILES_Canonico"].isna().any() or (
        dados["SMILES_Canonico"].astype(str).str.strip() == ""
    ).any():
        raise ValueError("Existem SMILES canônicos vazios")

    if (
        dados["Source_Row"].isna().any()
        or not dados["Source_Row"].is_unique
    ):
        raise ValueError("Source_Row deve ser único e não nulo")

    if dados["SMILES_Canonico"].nunique() < 3:
        raise ValueError(
            "São necessárias pelo menos três moléculas distintas"
        )

    for coluna in ("Temperature_K", ALVO):
        valores = pd.to_numeric(
            dados[coluna], errors="coerce"
        ).to_numpy(dtype=float)

        if not np.isfinite(valores).all():
            raise ValueError(
                f"Valores não finitos ou não numéricos em {coluna}"
            )

        if coluna == "Temperature_K" and (valores <= 0).any():
            raise ValueError(
                "Temperature_K deve ser maior que zero"
            )


def treinar_e_salvar(origem: Path, saida: Path) -> dict:
    origem = Path(origem).resolve()
    saida = Path(saida).resolve()

    if origem.name != "treino.csv":
        raise ValueError(
            "A entrada precisa ser treino.csv do C14; nunca teste.csv"
        )

    if not origem.is_file():
        raise FileNotFoundError(
            f"CSV de treino não encontrado: {origem}"
        )

    artefato = saida / f"{VERSAO_MODELO}.joblib"
    meta = saida / f"{VERSAO_MODELO}.metadata.json"

    if artefato.exists() or meta.exists():
        raise FileExistsError(
            "Artefato/metadados já existem; não serão sobrescritos"
        )

    dados = pd.read_csv(origem, low_memory=False)
    validar_treino(dados)

    # Reproduz a comparação agrupada do C16/C17.
    comparacao = comparar_modelos(
        dados, semente=SEMENTE
    )

    metricas = comparacao["modelos"]

    vencedor = min(
        metricas,
        key=lambda nome: metricas[nome]["MAE"]
    )

    if vencedor != "Ridge":
        raise RuntimeError(
            f"Seleção divergente: {vencedor}; "
            "revisar protocolo antes de persistir"
        )

    # Reajusta em TODO o treino do C14.
    # O conjunto final teste.csv permanece intocado.
    x = construir_atributos(dados)

    if list(x.columns) != list(FEATURE_NAMES):
        raise RuntimeError(
            "Ordem dos atributos diverge de FEATURE_NAMES"
        )

    y = dados[ALVO].to_numpy(dtype=float)

    pipeline = criar_modelos(SEMENTE)["Ridge"]
    pipeline.fit(x, y)

    # Teste técnico de finitude, NÃO uma avaliação de acurácia.
    amostra = pd.DataFrame(
        [extrair_atributos("CCO", 298.15)],
        columns=list(FEATURE_NAMES),
    )

    predito = float(pipeline.predict(amostra)[0])

    if not np.isfinite(predito):
        raise RuntimeError(
            "O pipeline produziu predição não finita"
        )

    versoes = {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "rdkit": rdkit.__version__,
        "scikit-learn": sklearn.__version__,
        "joblib": joblib.__version__,
    }

    info = {
        "model_version": VERSAO_MODELO,
        "dataset_name": "BigSolDB",
        "dataset_version": "2.0",
        "dataset_doi": "10.5281/zenodo.15094979",
        "target": ALVO,
        "solvent": "methanol",
        "feature_names": list(FEATURE_NAMES),
        "trained_at": (
            datetime.now(timezone.utc).date().isoformat()
        ),
        "metrics": {
            "mae": float(metricas["Ridge"]["MAE"]),
            "rmse": float(metricas["Ridge"]["RMSE"]),
            "r2": float(metricas["Ridge"]["R2"]),
        },
        "training_temperature_range_k": {
            "min": float(dados["Temperature_K"].min()),
            "max": float(dados["Temperature_K"].max()),
        },
        "software_versions": versoes,
    }

    # Confere compatibilidade com o schema do C20.
    ModelInfoResponse.model_validate(info)

    saida.mkdir(parents=True, exist_ok=True)

    # Grava inicialmente em pasta temporária.
    with TemporaryDirectory(
        prefix="c23_", dir=saida
    ) as temporaria:
        temporario = Path(temporaria)
        artefato_tmp = temporario / artefato.name
        meta_tmp = temporario / meta.name

        joblib.dump(
            pipeline, artefato_tmp, compress=3
        )

        metadados = {
            "model_info": info,
            "selection": {
                "criterion": (
                    "menor MAE em validação interna "
                    "agrupada por molécula"
                ),
                "selected_model": "Ridge",
                "seed": SEMENTE,
                "comparison": comparacao,
                "metrics_context": (
                    "validação interna anterior ao "
                    "reajuste completo"
                ),
            },
            "training": {
                "source_filename": origem.name,
                "source_sha256": sha256_arquivo(origem),
                "records": int(len(dados)),
                "molecules": int(
                    dados["SMILES_Canonico"].nunique()
                ),
                "artifact_filename": artefato.name,
                "artifact_sha256": sha256_arquivo(
                    artefato_tmp
                ),
                "estimator": (
                    "Pipeline(StandardScaler, "
                    "Ridge(alpha=1.0))"
                ),
                "feature_builder": (
                    "app.chemistry.extrair_atributos"
                ),
                "test_final_used": False,
            },
        }

        meta_tmp.write_text(
            json.dumps(
                metadados,
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            ) + "\n",
            encoding="utf-8",
        )

        artefato_tmp.replace(artefato)
        meta_tmp.replace(meta)

    return metadados


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=(
            RAIZ / "data/processed/split/treino.csv"
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RAIZ / "artifacts",
    )

    args = parser.parse_args()

    try:
        metadados = treinar_e_salvar(
            args.input, args.output_dir
        )
    except (
        ValueError,
        FileNotFoundError,
        FileExistsError,
        RuntimeError,
    ) as erro:
        parser.error(str(erro))

    print(
        "Modelo salvo:",
        args.output_dir / f"{VERSAO_MODELO}.joblib",
    )
    print(
        "Metadados salvos:",
        args.output_dir / f"{VERSAO_MODELO}.metadata.json",
    )
    print(
        "Registros de treino:",
        metadados["training"]["records"],
    )
    print(
        "Moléculas de treino:",
        metadados["training"]["molecules"],
    )
    print("Teste final: NÃO UTILIZADO")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
