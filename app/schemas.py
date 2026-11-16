
"""Contratos Pydantic de entrada e saída da predição.

Não executa inferência e não define a faixa de aplicação do modelo.
"""
from datetime import date, datetime
import math
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
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


class ModelMetrics(BaseModel):
    """Métricas reais registradas no experimento."""

    model_config = ConfigDict(extra="forbid")

    mae: float = Field(ge=0, allow_inf_nan=False)
    rmse: float = Field(ge=0, allow_inf_nan=False)
    r2: float = Field(allow_inf_nan=False)


class TrainingTemperatureRangeK(BaseModel):
    """Faixa observada no treinamento, expressa em Kelvin."""

    model_config = ConfigDict(extra="forbid")

    min: float = Field(gt=0, allow_inf_nan=False)
    max: float = Field(gt=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def validar_intervalo(self):
        if self.max < self.min:
            raise ValueError(
                "Temperatura máxima deve ser maior ou igual à mínima"
            )

        return self


class ModelInfoResponse(BaseModel):
    """Contrato de metadados do modelo disponível na API."""

    model_config = ConfigDict(extra="forbid")

    model_version: str = Field(min_length=1)
    dataset_name: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    dataset_doi: str = Field(min_length=1)

    target: Literal["LogS(mol/L)"]
    solvent: Literal["methanol"]

    feature_names: list[str] = Field(min_length=1)

    trained_at: date | datetime

    metrics: ModelMetrics

    training_temperature_range_k: TrainingTemperatureRangeK

    software_versions: dict[str, str] = Field(
        min_length=1
    )

    @model_validator(mode="after")
    def validar_features(self):
        if any(
            not nome.strip()
            for nome in self.feature_names
        ):
            raise ValueError(
                "Nomes de atributos não podem ser vazios"
            )

        if len(set(self.feature_names)) != len(
            self.feature_names
        ):
            raise ValueError(
                "Nomes de atributos não podem se repetir"
            )

        return self
