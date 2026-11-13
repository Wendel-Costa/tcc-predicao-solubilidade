
"""Extração compartilhada de atributos moleculares com RDKit.

Este módulo é utilizado tanto no treinamento offline quanto
na futura inferência pela API.
"""

import math
from numbers import Real

from rdkit import Chem
from rdkit.Chem import (
    Crippen,
    Descriptors,
    Lipinski,
    rdMolDescriptors,
)


# Contrato de nomes e ordem dos atributos.
# Esta ordem deverá ser preservada no treinamento e na API.
FEATURE_NAMES = (
    "MolWt",
    "MolLogP",
    "TPSA",
    "NumHDonors",
    "NumHAcceptors",
    "NumRotatableBonds",
    "HeavyAtomCount",
    "RingCount",
    "FractionCSP3",
    "Temperature_K",
)


def extrair_atributos(
    smiles: str,
    temperatura_k: float,
) -> dict[str, float]:
    """Calcula descritores 2D e inclui temperatura em Kelvin.

    Parâmetros
    ----------
    smiles : str
        Representação SMILES da molécula.

    temperatura_k : float
        Temperatura experimental em Kelvin.

    Retorno
    -------
    dict[str, float]
        Dicionário com os atributos na ordem de FEATURE_NAMES.

    Exceções
    --------
    ValueError
        Quando o SMILES ou a temperatura forem inválidos,
        ou algum atributo calculado não for finito.
    """

    # 1. Validar a entrada SMILES.
    if not isinstance(smiles, str) or not smiles.strip():
        raise ValueError(
            "SMILES deve ser uma string não vazia"
        )

    # 2. Interpretar a estrutura molecular.
    molecula = Chem.MolFromSmiles(smiles.strip())

    if molecula is None or molecula.GetNumAtoms() == 0:
        raise ValueError("SMILES inválido")

    # 3. Canonicalizar antes do cálculo.
    # Preserva a representação isomérica.
    canonico = Chem.MolToSmiles(
        molecula,
        canonical=True,
        isomericSmiles=True,
    )

    molecula = Chem.MolFromSmiles(canonico)

    # 4. Validar a temperatura.
    if (
        isinstance(temperatura_k, bool)
        or not isinstance(temperatura_k, Real)
    ):
        raise ValueError(
            "Temperatura deve ser numérica em Kelvin"
        )

    temperatura_k = float(temperatura_k)

    if (
        not math.isfinite(temperatura_k)
        or temperatura_k <= 0
    ):
        raise ValueError(
            "Temperatura deve ser finita e maior que zero Kelvin"
        )

    # 5. Calcular descritores moleculares 2D.
    valores = (
        Descriptors.MolWt(molecula),
        Crippen.MolLogP(molecula),
        rdMolDescriptors.CalcTPSA(molecula),
        Lipinski.NumHDonors(molecula),
        Lipinski.NumHAcceptors(molecula),
        Lipinski.NumRotatableBonds(molecula),
        molecula.GetNumHeavyAtoms(),
        rdMolDescriptors.CalcNumRings(molecula),
        rdMolDescriptors.CalcFractionCSP3(molecula),
        temperatura_k,
    )

    # 6. Converter todos os atributos para float.
    # A ordem segue FEATURE_NAMES.
    resultado = dict(
        zip(FEATURE_NAMES, map(float, valores))
    )

    # 7. Garantir que todos os valores sejam finitos.
    if not all(
        math.isfinite(valor)
        for valor in resultado.values()
    ):
        raise ValueError(
            "Descritor molecular não finito"
        )

    return resultado
