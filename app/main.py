
"""Entrada da API de solubilidade em metanol (C18)."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from starlette.exceptions import (
    HTTPException as StarletteHTTPException,
)

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
            "model": ErrorResponse,
            "description": (
                "Requisição inválida, SMILES inválido "
                "ou temperatura inválida."
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

# C26 — Padronização dos erros HTTP da API.

def classificar_erro_validacao(erros: list[dict]) -> tuple[str, str]:
    """Classifica erros sem devolver valores enviados pelo usuário.

    Se vários campos estiverem incorretos ao mesmo tempo,
    utiliza invalid_request como classificação geral.
    """

    campos = set()

    for erro in erros:
        local = erro.get("loc", ())

        if len(local) >= 2 and local[0] == "body":
            campos.add(local[1])
        else:
            campos.add("outro")

    if campos == {"smiles"}:
        return (
            "invalid_smiles",
            "A estrutura SMILES informada não é válida.",
        )

    if campos == {"temperature_c"}:
        return (
            "invalid_temperature",
            "A temperatura informada não é válida.",
        )

    return (
        "invalid_request",
        "Requisição inválida. Verifique os campos enviados.",
    )


@app.exception_handler(RequestValidationError)
async def tratar_erro_validacao(
    request: Request,
    exc: RequestValidationError,
):
    """Padroniza erros de validação do POST /api/predict."""

    # Não altera a documentação nem outras rotas.
    if request.url.path != "/api/predict":
        return await request_validation_exception_handler(
            request,
            exc,
        )

    codigo, mensagem = classificar_erro_validacao(
        exc.errors()
    )

    return resposta_erro_predict(
        codigo=codigo,
        mensagem=mensagem,
        codigo_http=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


@app.exception_handler(StarletteHTTPException)
async def tratar_erro_http(
    request: Request,
    exc: StarletteHTTPException,
):
    """Padroniza rotas inexistentes e métodos inválidos da API."""

    # Não modifica as respostas padrão fora de /api/.
    if not request.url.path.startswith("/api/"):
        return await http_exception_handler(
            request,
            exc,
        )

    if exc.status_code == 404:
        resposta = resposta_erro_predict(
            codigo="invalid_request",
            mensagem="Endpoint não encontrado.",
            codigo_http=404,
        )

    elif exc.status_code == 405:
        resposta = resposta_erro_predict(
            codigo="invalid_request",
            mensagem=(
                "Método HTTP não permitido "
                "para este endpoint."
            ),
            codigo_http=405,
        )

    else:
        return await http_exception_handler(
            request,
            exc,
        )

    # Preserva cabeçalhos HTTP importantes, como Allow.
    if exc.headers:
        resposta.headers.update(exc.headers)

    return resposta