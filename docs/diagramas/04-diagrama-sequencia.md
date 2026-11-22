# Diagrama de sequência — predição HTTP (C28)

## Fluxo bem-sucedido

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuário
    participant N as Navegador / app.js
    participant A as FastAPI / main.py
    participant S as schemas.py
    participant P as predictor.py
    participant C as chemistry.py / RDKit
    participant M as Ridge / Joblib
    U->>N: Informa CCO e temperatura 25 °C
    N->>A: POST /api/predict com JSON
    A->>S: Valida PredictRequest (FastAPI)
    S-->>A: SMILES válido e temperatura 298,15 K
    A->>P: obter_predictor() (cache)
    Note over P,M: No primeiro acesso: confere metadados, hash e versões e carrega artefato local confiável
    P-->>A: Predictor disponível
    A->>P: prever(pedido)
    P->>C: extrair_atributos(SMILES, temperatura_k)
    C-->>P: Dez atributos em ordem FEATURE_NAMES
    P->>M: pipeline.predict(uma linha)
    M-->>P: Estimativa de LogS(mol/L)
    P-->>A: PredictResponse e avisos
    A-->>N: HTTP 200 com JSON
    N-->>U: Exibe LogS, temperatura, versão e avisos
```

O valor numérico obtido depende do **artefato local**. O backend não consulta BigSolDB nem executa `fit()` durante essa sequência. A validação inicial de SMILES no schema também utiliza RDKit.

## Caminhos de erro e comportamento de interface

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuário
    participant N as Navegador / app.js
    participant A as FastAPI / main.py
    participant P as predictor.py
    U->>N: Envia formulário
    N->>A: POST /api/predict
    alt SMILES, JSON ou temperatura inválidos
        A-->>N: HTTP 422 com error.code estruturado
    else Temperatura omitida
        A-->>N: HTTP 422 / invalid_temperature
    else Artefato indisponível ou incompatível
        A->>P: obter_predictor()
        P-->>A: None
        A-->>N: HTTP 503 / model_unavailable
    else Falha durante inferência
        A->>P: prever(pedido)
        P-->>A: PredicaoFalhou
        A-->>N: HTTP 500 / prediction_failed
    else Temperatura fora da faixa observada
        A->>P: prever(pedido)
        P-->>A: Estimativa e aviso de extrapolação
        A-->>N: HTTP 200 com warnings
    end
    N-->>U: Exibe erro ou resultado, sem criar valor fictício
```

A interface bloqueia campos vazios/temperatura impossível antes de enviar; SMILES sintaticamente inválidos podem chegar à API e são rejeitados pelo schema. Ao editar os campos enquanto há uma chamada pendente, `AbortController` cancela a requisição anterior e impede mostrar resultados desatualizados.

| HTTP | Significado |
|---|---|
| 200 | Estimativa e avisos, incluindo extrapolação quando aplicável |
| 422 | `invalid_smiles`, `invalid_temperature` ou `invalid_request` |
| 503 | `model_unavailable` |
| 500 | `prediction_failed` |

O exemplo `CCO` é uma verificação funcional, **não uma avaliação de acurácia experimental**.

## Referências

- [Componentes da API](03-diagrama-componentes.md)
- [Contrato da API](../contrato-api.md)
