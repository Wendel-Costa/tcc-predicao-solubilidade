
"""Entrada da API de solubilidade em metanol (C18)."""

from app.predictor import (
    EntradaInvalida,
    PredicaoFalhou,
    Predictor,
    obter_predictor,
)

import logging

from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Response, status
from pydantic import BaseModel

from fastapi.responses import JSONResponse

from app.schemas import (
    ErrorDetail,
    ErrorResponse,
    ModelInfoResponse,
    PredictRequest,
    PredictResponse,
)

# Cria a aplicação FastAPI.
app = FastAPI(
    title="Predição de Solubilidade em Metanol",
    description=(
        "API do protótipo acadêmico; "
        "treinamento é executado offline."
    ),
    version="0.1.0",
)

logger = logging.getLogger(__name__)

class HealthStatus(BaseModel):
    """Estrutura da resposta do endpoint health."""

    status: Literal["ok", "degraded"]
    model_available: bool
    model_version: str | None


def consultar_estado_modelo() -> tuple[bool, str | None]:
    """Consulta a disponibilidade real do predictor."""

    modelo = obter_predictor()

    if modelo is None:
        return False, None

    return True, modelo.info.model_version

@app.get(
    "/api/health",
    response_model=HealthStatus,
    responses={
        503: {
            "model": HealthStatus,
            "description": "Modelo não disponível",
        }
    },
    tags=["sistema"],
)
def health(
    response: Response,
    estado: Annotated[
        tuple[bool, str | None],
        Depends(consultar_estado_modelo),
    ],
) -> HealthStatus:
    """Informa a disponibilidade do serviço de predição."""

    disponivel, versao = estado

    # Modelo só está pronto quando há disponibilidade
    # confirmada e uma versão não vazia.
    pronto = bool(
        disponivel
        and versao
        and versao.strip()
    )

    # A API funciona, mas não pode realizar predições.
    if not pronto:
        response.status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
        )

    return HealthStatus(
        status="ok" if pronto else "degraded",
        model_available=pronto,
        model_version=versao if pronto else None,
    )


def consultar_metadados_modelo() -> ModelInfoResponse | None:
    """Retorna os metadados do artefato carregado."""

    modelo = obter_predictor()

    if modelo is None:
        return None

    return modelo.info

@app.get(
    "/api/model-info",
    response_model=ModelInfoResponse,
    responses={
        503: {
            "model": ErrorResponse,
            "description": (
                "Metadados do modelo indisponíveis"
            ),
        },
    },
    tags=["modelo"],
)
def model_info(
    metadados: Annotated[
        ModelInfoResponse | None,
        Depends(consultar_metadados_modelo),
    ],
) -> ModelInfoResponse | JSONResponse:
    """Retorna os metadados reais ou HTTP 503."""

    if metadados is None:
        erro = ErrorResponse(
            error=ErrorDetail(
                code="model_unavailable",
                message=(
                    "Metadados do modelo indisponíveis."
                ),
            )
        )

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=erro.model_dump(),
        )

    return metadados

# C25 — Endpoint HTTP de predição.
# O pipeline já foi treinado offline no C23.

def resposta_erro_predict(
    codigo: str,
    mensagem: str,
    codigo_http: int,
) -> JSONResponse:
    """Produz resposta de erro conforme o contrato da API."""

    erro = ErrorResponse(
        error=ErrorDetail(
            code=codigo,
            message=mensagem,
        )
    )

    return JSONResponse(
        status_code=codigo_http,
        content=erro.model_dump(),
    )


@app.post(
    "/api/predict",
    response_model=PredictResponse,
    responses={
        422: {
            "description": (
                "Campos inválidos (validação FastAPI/Pydantic) "
                "ou temperatura ausente (ErrorResponse)."
            ),
        },
        503: {
            "model": ErrorResponse,
            "description": "Modelo de predição indisponível.",
        },
        500: {
            "model": ErrorResponse,
            "description": "Erro inesperado na predição.",
        },
    },
    tags=["predição"],
)
def predict(
    pedido: PredictRequest,
    modelo: Annotated[
        Predictor | None,
        Depends(obter_predictor),
    ],
) -> PredictResponse | JSONResponse:
    """Estima a solubilidade em metanol usando o modelo carregado."""

    # Ainda não há temperatura padrão aprovada.
    if pedido.temperature_c is None:
        return resposta_erro_predict(
            codigo="invalid_temperature",
            mensagem=(
                "Informe temperature_c em graus Celsius; "
                "ainda não há padrão automático."
            ),
            codigo_http=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    # Não tentamos treinar ou criar um modelo na requisição.
    if modelo is None:
        return resposta_erro_predict(
            codigo="model_unavailable",
            mensagem="Modelo de predição indisponível.",
            codigo_http=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:
        # Utiliza exclusivamente o predictor do C24.
        return modelo.prever(pedido)

    except EntradaInvalida as erro:
        return resposta_erro_predict(
            codigo="invalid_temperature",
            mensagem=str(erro),
            codigo_http=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    except PredicaoFalhou:
        # Não registra o SMILES nem detalhes internos na resposta.
        logger.exception(
            "Falha no processamento da predição"
        )

        return resposta_erro_predict(
            codigo="prediction_failed",
            mensagem="Não foi possível realizar a predição.",
            codigo_http=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    except Exception:
        # Evita expor stack traces ao cliente.
        logger.exception(
            "Falha inesperada no predictor"
        )

        return resposta_erro_predict(
            codigo="prediction_failed",
            mensagem="Não foi possível realizar a predição.",
            codigo_http=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
