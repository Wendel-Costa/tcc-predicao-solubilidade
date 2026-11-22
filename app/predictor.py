
"""C24: carregamento local controlado e inferência sem treinamento."""

import hashlib
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import rdkit
import sklearn
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils.validation import check_is_fitted

from app.chemistry import FEATURE_NAMES, extrair_atributos
from app.schemas import (
    ModelInfoResponse,
    PredictRequest,
    PredictResponse,
)

RAIZ = Path(__file__).resolve().parents[1]
ARTEFATOS = RAIZ / "artifacts"

NOME_MODELO = "ridge-v1.joblib"
NOME_METADADOS = "ridge-v1.metadata.json"


class ModeloIndisponivel(RuntimeError):
    """O artefato não existe ou não pode ser utilizado."""


class EntradaInvalida(ValueError):
    """A entrada não atende ao protocolo de inferência."""


class PredicaoFalhou(RuntimeError):
    """Não foi possível gerar uma estimativa válida."""


def _sha256(caminho: Path) -> str:
    resumo = hashlib.sha256()

    with caminho.open("rb") as arquivo:
        for bloco in iter(
            lambda: arquivo.read(1024 * 1024),
            b"",
        ):
            resumo.update(bloco)

    return resumo.hexdigest()


def _conferir_versoes(
    versoes: dict[str, str],
) -> None:
    """Evita carregar um pipeline em ambiente incompatível."""

    atuais = {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "rdkit": rdkit.__version__,
        "scikit-learn": sklearn.__version__,
        "joblib": joblib.__version__,
    }

    for biblioteca, atual in atuais.items():
        registrado = versoes.get(biblioteca)

        if biblioteca == "python":
            # Aceita diferenças na versão patch,
            # mas não entre Python 3.14 e 3.15.
            compativel = (
                isinstance(registrado, str)
                and registrado.split(".")[:2]
                == atual.split(".")[:2]
            )
        else:
            compativel = registrado == atual

        if not compativel:
            raise ModeloIndisponivel(
                f"Versão incompatível para {biblioteca}: "
                f"artefato={registrado!r}, "
                f"ambiente={atual!r}"
            )


class Predictor:
    """Executa inferências com um pipeline já treinado."""

    def __init__(
        self,
        pipeline: Pipeline,
        info: ModelInfoResponse,
    ):
        self._pipeline = pipeline
        self.info = info

    def prever(
        self,
        pedido: PredictRequest,
    ) -> PredictResponse:
        """Estima LogS(mol/L) sem treinar o modelo."""

        temperatura_k = pedido.temperature_k

        if temperatura_k is None:
            raise EntradaInvalida(
                "Informe temperature_c; ainda não há "
                "temperatura padrão."
            )

        try:
            atributos = extrair_atributos(
                pedido.smiles,
                temperatura_k,
            )

            x = pd.DataFrame(
                [atributos],
                columns=list(FEATURE_NAMES),
            )

            saida = np.asarray(
                self._pipeline.predict(x)
            )

            if saida.size != 1:
                raise ValueError(
                    "O modelo retornou um número "
                    "inesperado de valores"
                )

            log_s = float(
                saida.reshape(-1)[0]
            )

            if not math.isfinite(log_s):
                raise ValueError(
                    "Predição não finita"
                )

        except ValueError as erro:
            raise PredicaoFalhou(
                "Não foi possível obter uma "
                "estimativa finita"
            ) from erro

        except Exception as erro:
            raise PredicaoFalhou(
                "Falha interna na execução do modelo"
            ) from erro

        faixa = (
            self.info.training_temperature_range_k
        )

        avisos = [
            "Estimativa estatística; não substitui "
            "medição experimental."
        ]

        if not (
            faixa.min <= temperatura_k <= faixa.max
        ):
            avisos.append(
                "Temperatura fora da faixa observada "
                "no treinamento "
                f"({faixa.min:g}–{faixa.max:g} K): "
                "extrapolação."
            )

        return PredictResponse(
            log_s_mol_l=log_s,
            temperature_c=pedido.temperature_c,
            temperature_k=temperatura_k,
            solvent="methanol",
            model_version=self.info.model_version,
            warnings=avisos,
        )


def carregar_predictor(
    diretorio: Path = ARTEFATOS,
) -> Predictor:
    """Carrega somente o artefato local esperado do C23.

    SHA-256 verifica integridade, não autenticidade.
    Nunca carregar arquivos joblib de terceiros.
    """

    pasta = Path(diretorio)

    caminho = pasta / NOME_MODELO
    meta_path = pasta / NOME_METADADOS

    for arquivo in (caminho, meta_path):
        if (
            arquivo.is_symlink()
            or not arquivo.is_file()
        ):
            raise ModeloIndisponivel(
                f"Arquivo ausente ou não permitido: "
                f"{arquivo}"
            )

    try:
        if meta_path.stat().st_size > 1_000_000:
            raise ModeloIndisponivel(
                "Metadados excessivamente grandes"
            )

        dados = json.loads(
            meta_path.read_text(
                encoding="utf-8"
            )
        )

        info = ModelInfoResponse.model_validate(
            dados["model_info"]
        )

        treino = dados["training"]

        if (
            info.model_version != "ridge-v1"
            or list(info.feature_names)
            != list(FEATURE_NAMES)
            or dados["selection"]["selected_model"]
            != "Ridge"
            or treino["artifact_filename"]
            != NOME_MODELO
            or treino["source_filename"]
            != "treino.csv"
            or treino["test_final_used"] is not False
        ):
            raise ModeloIndisponivel(
                "Metadados incompatíveis "
                "com o modelo C23"
            )

        esperado = treino["artifact_sha256"]

        if (
            not isinstance(esperado, str)
            or len(esperado) != 64
            or any(
                c not in "0123456789abcdef"
                for c in esperado
            )
            or _sha256(caminho) != esperado
        ):
            raise ModeloIndisponivel(
                "SHA-256 do modelo não confere"
            )

        _conferir_versoes(
            info.software_versions
        )

    except ModeloIndisponivel:
        raise

    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
    ) as erro:
        raise ModeloIndisponivel(
            "Metadados inválidos ou ilegíveis"
        ) from erro

    # ATENÇÃO: joblib.load pode executar código.
    # Usar somente um artefato próprio e confiável.
    try:
        pipeline = joblib.load(caminho)

        if not isinstance(
            pipeline, Pipeline
        ):
            raise ModeloIndisponivel(
                "Objeto salvo não é um Pipeline"
            )

        if list(pipeline.named_steps) != [
            "escala",
            "modelo",
        ]:
            raise ModeloIndisponivel(
                "Etapas do pipeline incorretas"
            )

        escala = pipeline.named_steps["escala"]
        regressor = pipeline.named_steps["modelo"]

        if (
            type(escala) is not StandardScaler
            or type(regressor) is not Ridge
        ):
            raise ModeloIndisponivel(
                "Tipos de estimador inesperados"
            )

        if regressor.alpha != 1.0:
            raise ModeloIndisponivel(
                "Hiperparâmetro Ridge incompatível"
            )

        check_is_fitted(pipeline)

        if list(
            pipeline.feature_names_in_
        ) != list(FEATURE_NAMES):
            raise ModeloIndisponivel(
                "Ordem de atributos incompatível"
            )

        if pipeline.n_features_in_ != len(
            FEATURE_NAMES
        ):
            raise ModeloIndisponivel(
                "Quantidade de atributos incompatível"
            )

    except ModeloIndisponivel:
        raise

    except Exception as erro:
        raise ModeloIndisponivel(
            "Falha no carregamento do pipeline"
        ) from erro

    return Predictor(
        pipeline=pipeline,
        info=info,
    )


@lru_cache(maxsize=1)
def obter_predictor() -> Predictor | None:
    """Carrega uma vez por processo.

    Reiniciar o serviço após instalar um novo artefato.
    """

    try:
        return carregar_predictor()

    except ModeloIndisponivel:
        return None


if __name__ == "__main__":
    try:
        modelo = carregar_predictor()

    except ModeloIndisponivel as erro:
        print(
            f"Modelo indisponível: {erro}",
            file=sys.stderr,
        )
        raise SystemExit(1) from erro

    print(
        "Modelo carregado:",
        modelo.info.model_version,
    )

    print(
        "Descritores:",
        len(modelo.info.feature_names),
    )
