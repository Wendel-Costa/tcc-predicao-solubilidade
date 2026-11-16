
"""Entrada da API de solubilidade em metanol (C18)."""

from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Response, status
from pydantic import BaseModel

from fastapi.responses import JSONResponse

from app.schemas import (
    ErrorDetail,
    ErrorResponse,
    ModelInfoResponse,
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


class HealthStatus(BaseModel):
    """Estrutura da resposta do endpoint health."""

    status: Literal["ok", "degraded"]
    model_available: bool
    model_version: str | None


def consultar_estado_modelo() -> tuple[bool, str | None]:
    """Ponto de integração com o predictor, previsto para C24.

    Até a integração, não existe um artefato carregado
    pela API. A existência de scripts de treinamento
    não significa que um modelo esteja disponível.
    """
    return False, None


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
    """Consulta os metadados do modelo integrado.

    Integração real prevista para o C24.

    Enquanto não existir um artefato carregado e validado,
    a API não disponibiliza informações fictícias.
    """
    return None


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
