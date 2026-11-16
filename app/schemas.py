
"""Contratos Pydantic de entrada e saída da predição.

Não executa inferência e não define a faixa de aplicação do modelo.
"""

import math
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)
from rdkit import Chem


class PredictRequest(BaseModel):
    """Entrada da predição; temperatura em Celsius, se informada."""

    model_config = ConfigDict(extra="forbid")

    smiles: str
    temperature_c: float | None = None

    @field_validator("smiles", mode="before")
    @classmethod
    def validar_smiles(cls, valor: object) -> str:
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(
                "SMILES deve ser uma string não vazia"
            )

        valor = valor.strip()
        molecula = Chem.MolFromSmiles(valor)

        if molecula is None or molecula.GetNumAtoms() == 0:
            raise ValueError("SMILES inválido")

        return valor

    @field_validator("temperature_c", mode="before")
    @classmethod
    def validar_temperatura(
        cls,
        valor: object,
    ) -> float | None:
        if valor is None:
            return None

        if isinstance(valor, bool) or not isinstance(
            valor, (int, float)
        ):
            raise ValueError(
                "Temperatura deve ser numérica em graus Celsius"
            )

        numero = float(valor)

        if not math.isfinite(numero):
            raise ValueError(
                "Temperatura deve ser finita"
            )

        if numero <= -273.15:
            raise ValueError(
                "Temperatura deve estar acima do zero absoluto"
            )

        return numero

    @property
    def temperature_k(self) -> float | None:
        """Converte para Kelvin sem assumir padrão não aprovado."""
        if self.temperature_c is None:
            return None

        return self.temperature_c + 273.15


class PredictResponse(BaseModel):
    """Formato da futura resposta de predição."""

    model_config = ConfigDict(extra="forbid")

    log_s_mol_l: float = Field(allow_inf_nan=False)
    temperature_c: float = Field(allow_inf_nan=False)
    temperature_k: float = Field(
        gt=0,
        allow_inf_nan=False,
    )
    solvent: Literal["methanol"] = "methanol"
    model_version: str = Field(min_length=1)
    warnings: list[str]


class ErrorDetail(BaseModel):
    """Código e mensagem de erro da API."""

    code: Literal[
        "invalid_request",
        "invalid_smiles",
        "invalid_temperature",
        "temperature_out_of_range",
        "model_unavailable",
        "prediction_failed",
    ]
    message: str


class ErrorResponse(BaseModel):
    """Estrutura uniforme para respostas de erro."""

    error: ErrorDetail
