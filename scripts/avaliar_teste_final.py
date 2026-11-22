"""C30 — Avaliação ÚNICA do ridge-v1 no teste agrupado reservado do C14.

Executar SOMENTE após congelar a seleção e a configuração do modelo.
Não retreina, não otimiza hiperparâmetros nem grava previsões individuais.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.predictor import carregar_predictor
from app.schemas import PredictRequest

RAIZ = Path(__file__).resolve().parents[1]
ALVO = "LogS(mol/L)"
COLUNAS = {"Source_Row", "SMILES_Canonico", "Temperature_K", ALVO}
VERSAO = "ridge-v1"


def sha256(caminho: Path) -> str:
    resumo = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def conferir_dados(dados: pd.DataFrame, identificacao: str) -> None:
    faltantes = COLUNAS.difference(dados.columns)
    if faltantes:
        raise ValueError(f"Colunas ausentes em {identificacao}: {sorted(faltantes)}")
    if dados.empty:
        raise ValueError(f"{identificacao} está vazio")
    grupos = dados["SMILES_Canonico"]
    if grupos.isna().any() or grupos.astype(str).str.strip().eq("").any():
        raise ValueError(f"SMILES canônico vazio em {identificacao}")
    ids = dados["Source_Row"]
    if ids.isna().any() or not ids.is_unique:
        raise ValueError(f"Source_Row não é único em {identificacao}")
    for coluna in ("Temperature_K", ALVO):
        valores = pd.to_numeric(dados[coluna], errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(valores).all():
            raise ValueError(f"Valores não finitos em {identificacao}/{coluna}")
        if coluna == "Temperature_K" and (valores <= 0).any():
            raise ValueError(f"Temperatura não positiva em {identificacao}")


def calcular_metricas(reais: np.ndarray, previstos: np.ndarray) -> dict:
    if reais.size < 2 or previstos.shape != reais.shape:
        raise ValueError("São necessárias pelo menos duas previsões alinhadas")
    if not np.isfinite(reais).all() or not np.isfinite(previstos).all():
        raise ValueError("Valores não finitos na avaliação")
    return {
        "mae": float(mean_absolute_error(reais, previstos)),
        "rmse": float(np.sqrt(mean_squared_error(reais, previstos))),
        "r2": float(r2_score(reais, previstos)),
    }


def analise_erros(dados: pd.DataFrame, previstos: np.ndarray, minimo_k: float, maximo_k: float) -> dict:
    reais = dados[ALVO].to_numpy(dtype=float)
    abs_erro = np.abs(reais - previstos)
    residuo = reais - previstos
    por_molecula = pd.DataFrame({
        "grupo": dados["SMILES_Canonico"].to_numpy(),
        "erro_absoluto": abs_erro,
    }).groupby("grupo", sort=False)["erro_absoluto"].mean()

    temp = dados["Temperature_K"].to_numpy(dtype=float)
    mascaras = {
        "abaixo_do_treino": temp < minimo_k,
        "dentro_da_faixa_do_treino": (temp >= minimo_k) & (temp <= maximo_k),
        "acima_do_treino": temp > maximo_k,
    }
    faixas = {}
    for nome, mascara in mascaras.items():
        quantidade = int(mascara.sum())
        faixas[nome] = {
            "registros": quantidade,
            "mae": float(abs_erro[mascara].mean()) if quantidade else None,
        }
    return {
        "vies_medio_observado_menos_predito": float(residuo.mean()),
        "mediana_erro_absoluto": float(np.median(abs_erro)),
        "percentil_90_erro_absoluto": float(np.percentile(abs_erro, 90)),
        "mae_media_por_molecula": float(por_molecula.mean()),
        "faixas_temperatura": faixas,
    }


def salvar_graficos(dados: pd.DataFrame, previstos: np.ndarray, pasta: Path) -> None:
    reais = dados[ALVO].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(reais, previstos, s=12, alpha=0.35)
    limites = [min(reais.min(), previstos.min()), max(reais.max(), previstos.max())]
    ax.plot(limites, limites, "--", color="black", linewidth=1)
    ax.set(title="Teste final: observado vs. predito", xlabel="LogS observado (mol/L)", ylabel="LogS predito (mol/L)")
    fig.tight_layout()
    fig.savefig(pasta / "observado_predito_teste.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(dados["Temperature_K"], reais - previstos, s=12, alpha=0.35)
    ax.axhline(0, linestyle="--", color="black", linewidth=1)
    ax.set(title="Teste final: resíduos por temperatura", xlabel="Temperatura (K)", ylabel="Resíduo: observado − predito (LogS)")
    fig.tight_layout()
    fig.savefig(pasta / "residuos_temperatura_teste.png", dpi=150)
    plt.close(fig)


def montar_relatorio(dados: dict) -> str:
    m = dados["metricas_teste_final"]
    erros = dados["analise_de_erros"]
    val = dados["metricas_validacao_interna_c23"]
    faixas = erros["faixas_temperatura"]
    tabela = "\n".join(
        f"| {nome.replace('_', ' ')} | {v['registros']} | "
        + (f"{v['mae']:.6f}" if v["mae"] is not None else "não calculável") + " |"
        for nome, v in faixas.items()
    )
    return f"""# C30 — Avaliação final independente por molécula

**Modelo congelado:** `{dados['modelo']['versao']}`. **Fonte:** BigSolDB 2.0, metanol puro.
**Data UTC:** {dados['data_utc']}. **Alvo:** LogS(mol/L).

> Esta é uma avaliação em **teste retido por molécula**, do mesmo banco de dados.
> Não é validação externa em outra fonte, nem prova de aplicabilidade universal.
> **Não reajustar o modelo nem escolher hiperparâmetros com base nestes resultados.**

## Rastreabilidade da partição e do artefato

- Treino C14: {dados['particao']['registros_treino']} registros / {dados['particao']['moleculas_treino']} moléculas.
- Teste final C14: {dados['particao']['registros_teste']} registros / {dados['particao']['moleculas_teste']} moléculas.
- Moléculas compartilhadas: {dados['particao']['moleculas_compartilhadas']}.
- Source_Row compartilhados: {dados['particao']['registros_origem_compartilhados']}.
- SHA-256 treino: `{dados['entradas_sha256']['treino']}`.
- SHA-256 teste: `{dados['entradas_sha256']['teste']}`.
- SHA-256 artefato: `{dados['entradas_sha256']['joblib']}`.

## Métricas no teste final (nunca usadas para seleção)

| Métrica | Teste final C30 | Validação interna C23 (referência, outra amostra) |
|---|---:|---:|
| MAE (LogS) | {m['mae']:.6f} | {val['mae']:.6f} |
| RMSE (LogS) | {m['rmse']:.6f} | {val['rmse']:.6f} |
| R² | {m['r2']:.6f} | {val['r2']:.6f} |

**Atenção:** as métricas da validação interna referem-se a outro ajuste
sobre uma partição interna do treino. Elas não são métricas do pipeline
reajustado no conjunto completo de treino.

## Resíduos e heterogeneidade

- Viés médio (observado − predito): {erros['vies_medio_observado_menos_predito']:.6f} LogS.
- Mediana do erro absoluto: {erros['mediana_erro_absoluto']:.6f} LogS.
- Percentil 90 do erro absoluto: {erros['percentil_90_erro_absoluto']:.6f} LogS.
- MAE médio por molécula (mesmo peso por molécula): {erros['mae_media_por_molecula']:.6f} LogS.

Faixas definidas **antes de observar o teste** a partir dos limites
mínimo e máximo de temperatura do treino do C23:

| Faixa | Registros | MAE (LogS) |
|---|---:|---:|
{tabela}

![Observado versus predito](observado_predito_teste.png)

![Resíduos por temperatura](residuos_temperatura_teste.png)

## Limitações científicas e de interpretação

1. O teste foi separado por SMILES canônico, reduzindo vazamento de identidade
   molecular; isômeros, análogos e famílias químicas relacionadas ainda podem
   compartilhar padrões, e podem existir outras fontes de dependência dos dados.
2. Os registros podem representar medições repetidas; o MAE padrão pondera
   registros, enquanto o MAE médio por molécula pondera moléculas igualmente.
3. SMILES e descritores 2D, junto à temperatura, não capturam necessariamente
   todos os fatores experimentais que determinam a solubilidade.
4. A qualidade, cobertura química, unidades e condições de medição do BigSolDB
   limitam a generalização; resultados neste banco não equivalem a validação externa.
5. Erros por faixa de temperatura são descritivos; faixas com poucas observações
   não autorizam conclusões robustas. Dentro da faixa de treino também há
   possibilidade de extrapolação estrutural.
6. O algoritmo é Ridge linear com padronização; não há intervalos de incerteza
   preditiva individuais nem garantia de precisão para moléculas inéditas.
7. Inspecionar este teste **não autoriza reajustar** a versão `ridge-v1`.
   Uma nova avaliação após ajustes exigiria outro conjunto independente.

O JSON inclui apenas métricas agregadas. CSVs, SMILES individuais e
predições linha a linha não são exportados.
"""


def avaliar_teste_final(treino: Path, teste: Path, artefatos: Path, saida: Path) -> dict:
    """Avalia uma única vez o pipeline congelado, sem chamar fit()."""
    treino, teste, artefatos, saida = (Path(x).resolve() for x in (treino, teste, artefatos, saida))
    if treino.name != "treino.csv" or teste.name != "teste.csv":
        raise ValueError("Entradas devem ser treino.csv e teste.csv do split C14")
    if treino == teste:
        raise ValueError("Treino e teste não podem ser o mesmo arquivo")
    if saida.exists():
        raise FileExistsError("Relatório final já existe: não repetir nem sobrescrever a avaliação")
    if not treino.is_file() or not teste.is_file():
        raise FileNotFoundError("É necessário disponibilizar treino.csv e teste.csv do C14")

    # O carregador valida o hash do Joblib e as versões de software antes de desserializar.
    modelo = carregar_predictor(artefatos)
    if modelo.info.model_version != VERSAO:
        raise ValueError("Somente o ridge-v1 congelado pode ser avaliado no C30")
    meta = json.loads((artefatos / "ridge-v1.metadata.json").read_text(encoding="utf-8"))
    hash_treino = sha256(treino)
    if hash_treino != meta["training"]["source_sha256"]:
        raise ValueError("Treino diverge do hash usado para gerar o artefato")

    dados_treino = pd.read_csv(treino, low_memory=False)
    conferir_dados(dados_treino, "treino")
    if len(dados_treino) != meta["training"]["records"] or (
        dados_treino["SMILES_Canonico"].nunique() != meta["training"]["molecules"]
    ):
        raise ValueError("Contagens do treino divergem dos metadados C23")

    dados_teste = pd.read_csv(teste, low_memory=False)
    conferir_dados(dados_teste, "teste")
    if len(dados_teste) < 2 or dados_teste["SMILES_Canonico"].nunique() < 2:
        raise ValueError("Teste insuficiente para métricas de generalização")

    moleculas_compartilhadas = len(set(dados_treino["SMILES_Canonico"]) & set(dados_teste["SMILES_Canonico"]))
    ids_compartilhados = len(set(dados_treino["Source_Row"]) & set(dados_teste["Source_Row"]))
    if moleculas_compartilhadas or ids_compartilhados:
        raise ValueError("Vazamento: moléculas ou Source_Row compartilhados entre treino e teste")

    previstos = []
    for smiles, kelvin in zip(dados_teste["SMILES_Canonico"], dados_teste["Temperature_K"]):
        pedido = PredictRequest(smiles=smiles, temperature_c=float(kelvin) - 273.15)
        resultado = modelo.prever(pedido)
        if resultado.model_version != VERSAO:
            raise ValueError("Resposta de predição com versão incompatível")
        previstos.append(resultado.log_s_mol_l)
    previstos = np.asarray(previstos, dtype=float)
    reais = dados_teste[ALVO].to_numpy(dtype=float)
    metricas = calcular_metricas(reais, previstos)
    limite = modelo.info.training_temperature_range_k
    erros = analise_erros(dados_teste, previstos, float(limite.min), float(limite.max))
    val = modelo.info.metrics

    resumo = {
        "protocolo": "C30_teste_final_unico_por_molecula",
        "data_utc": datetime.now(timezone.utc).date().isoformat(),
        "modelo": {"versao": VERSAO, "selecionado_antes_do_teste": True},
        "fonte": {"dataset": "BigSolDB", "versao": "2.0", "doi": "10.5281/zenodo.15094979", "solvente": "methanol", "alvo": ALVO},
        "entradas_sha256": {"treino": hash_treino, "teste": sha256(teste), "joblib": sha256(artefatos / "ridge-v1.joblib")},
        "particao": {
            "registros_treino": len(dados_treino), "moleculas_treino": int(dados_treino["SMILES_Canonico"].nunique()),
            "registros_teste": len(dados_teste), "moleculas_teste": int(dados_teste["SMILES_Canonico"].nunique()),
            "moleculas_compartilhadas": 0, "registros_origem_compartilhados": 0,
        },
        "metricas_teste_final": metricas,
        "metricas_validacao_interna_c23": {"mae": val.mae, "rmse": val.rmse, "r2": val.r2},
        "analise_de_erros": erros,
        "observacao": "Teste final usado uma única vez; não realizar seleção ou reajuste com estes resultados.",
    }

    saida.parent.mkdir(parents=True, exist_ok=True)
    # Produz todos os arquivos antes de publicar um diretório único.
    with TemporaryDirectory(prefix="c30_", dir=saida.parent) as temporaria:
        temporario = Path(temporaria) / "resultado"
        temporario.mkdir()
        (temporario / "resumo.json").write_text(
            json.dumps(resumo, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
        (temporario / "relatorio.md").write_text(montar_relatorio(resumo), encoding="utf-8")
        salvar_graficos(dados_teste, previstos, temporario)
        temporario.rename(saida)
    return resumo


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--treino", type=Path, default=RAIZ / "data/processed/split/treino.csv")
    parser.add_argument("--teste", type=Path, default=RAIZ / "data/processed/split/teste.csv")
    parser.add_argument("--artefatos", type=Path, default=RAIZ / "artifacts")
    parser.add_argument("--saida", type=Path, default=RAIZ / "reports/avaliacao_final_c30")
    parser.add_argument("--confirmar-avaliacao-final", action="store_true", help="Confirma abertura única do teste final, com modelo previamente congelado")
    args = parser.parse_args()
    if not args.confirmar_avaliacao_final:
        parser.error("Adicione --confirmar-avaliacao-final somente após congelar o modelo e o protocolo")
    try:
        resultado = avaliar_teste_final(args.treino, args.teste, args.artefatos, args.saida)
    except (OSError, ValueError, RuntimeError, KeyError) as erro:
        parser.error(str(erro))
    print("C30 — avaliação FINAL única concluída (sem retreinamento)")
    print("Registros de teste:", resultado["particao"]["registros_teste"])
    print("Moléculas de teste:", resultado["particao"]["moleculas_teste"])
    for nome, valor in resultado["metricas_teste_final"].items():
        print(f"{nome.upper()}: {valor:.6f}")
    print("Relatório:", args.saida / "relatorio.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
