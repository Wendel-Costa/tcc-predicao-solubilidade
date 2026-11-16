
"""Entrada da API de solubilidade em metanol (C18)."""

from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Response, status
from pydantic import BaseModel


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
