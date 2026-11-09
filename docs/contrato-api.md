
# Contrato da API — Predição de Solubilidade em Metanol

## 1. Objetivo

Definir a comunicação entre o frontend e o backend da aplicação de predição de solubilidade em metanol.

A API será implementada utilizando Python, FastAPI e Pydantic.

A comunicação utilizará HTTP e mensagens no formato JSON.

O contrato estabelece a estrutura das requisições, respostas e erros esperados.

**Versão inicial:** 1.0

**Status:** Contrato preliminar, sujeito a ajustes durante a implementação.

## 2. Convenções gerais

- Prefixo das rotas: `/api`.
- Formato de comunicação: JSON.
- Codificação: UTF-8.
- Temperatura recebida: graus Celsius.
- Temperatura utilizada internamente: Kelvin.
- Solvente: metanol, definido pelo próprio sistema.
- Variável-alvo: LogS (mol/L).

O cliente não deverá enviar o solvente ou escolher o modelo utilizado.

O sistema deverá utilizar exclusivamente o modelo configurado no backend.

## 3. Endpoints

| Método | Endpoint | Finalidade |
|---|---|---|
| GET | `/api/health` | Verificar a disponibilidade da API e do modelo. |
| GET | `/api/model-info` | Consultar informações e metadados do modelo. |
| POST | `/api/predict` | Realizar uma estimativa de solubilidade. |

---

## 4. GET /api/health

### Finalidade

Verificar se a API está disponível e se o pipeline de predição pode ser utilizado.

### Resposta de sucesso

**HTTP 200 OK**

| Campo | Tipo | Descrição |
|---|---|---|
| status | string | Estado geral do serviço. |
| model_available | boolean | Indica se o modelo está disponível para predição. |
| model_version | string ou null | Versão do modelo carregado. |

Quando a API estiver disponível e o modelo carregado, o estado deverá ser `ok`.

Se o processo da API estiver funcionando, mas o modelo não estiver disponível, o endpoint deverá informar a condição degradada e retornar HTTP 503.

---

## 5. GET /api/model-info

### Finalidade

Disponibilizar informações sobre o modelo utilizado pela aplicação.

### Resposta de sucesso

**HTTP 200 OK**

A resposta deverá apresentar:

| Campo | Tipo | Descrição |
|---|---|---|
| model_version | string | Versão do modelo. |
| dataset_name | string | Nome da base utilizada. |
| dataset_version | string | Versão do dataset. |
| dataset_doi | string | DOI da fonte de dados. |
| target | string | Variável-alvo. |
| solvent | string | Solvente utilizado. |
| feature_names | array de strings | Nomes dos atributos e sua ordem. |
| trained_at | string | Data do treinamento em formato ISO 8601. |
| metrics | object | Métricas reais do experimento. |
| training_temperature_range_k | object | Faixa de temperaturas observadas no treinamento, em Kelvin. |
| software_versions | object | Versões das bibliotecas e do Python utilizadas. |

O objeto `metrics` deverá conter:

- `mae`: erro absoluto médio.
- `rmse`: raiz do erro quadrático médio.
- `r2`: coeficiente de determinação.

As métricas deverão corresponder ao experimento documentado e não poderão ser preenchidas com valores fictícios.

Se o artefato ou seus metadados não estiverem disponíveis, a API deverá retornar HTTP 503.

**Observação:** a faixa de temperatura de treinamento descreve os dados utilizados no ajuste do modelo. Ela não deverá ser apresentada automaticamente como garantia de validade da predição em toda essa faixa.

---

## 6. POST /api/predict

### Finalidade

Receber uma estrutura molecular e uma temperatura e retornar uma estimativa de solubilidade em metanol.

### Requisição

**Content-Type:** `application/json`

Exemplo:

```json
{
  "smiles": "CC(=O)O",
  "temperature_c": 25.0
}
```

### Campos da requisição

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| smiles | string | Sim | Estrutura molecular no formato SMILES. |
| temperature_c | number | Não | Temperatura em graus Celsius. Padrão inicial de 25 °C. |

### Regras de validação

**SMILES:**

- Não poderá estar vazio.
- Deverá ser interpretável pelo RDKit.
- Estruturas inválidas deverão ser rejeitadas.
- Não deverão ser removidas informações estruturais indiscriminadamente.

**Temperatura:**

- Deverá ser um valor numérico finito.
- Não poderá representar uma temperatura igual ou inferior ao zero absoluto.
- O valor informado deverá ser convertido para Kelvin.
- Deverá respeitar a faixa de aplicação aprovada pelo protocolo científico.

A faixa definitiva de aplicação dependerá da auditoria e da análise do conjunto de dados de metanol.

### Conversão da temperatura

A API deverá utilizar:

`temperature_k = temperature_c + 273.15`

Exemplo de conversão:

- Entrada: 25 °C.
- Temperatura utilizada: 298,15 K.

### Resposta de sucesso

**HTTP 200 OK**

A resposta deverá possuir os seguintes campos:

| Campo | Tipo | Descrição |
|---|---|---|
| log_s_mol_l | number | Estimativa da solubilidade na escala LogS (mol/L). |
| temperature_c | number | Temperatura informada ou assumida como padrão. |
| temperature_k | number | Temperatura convertida para Kelvin. |
| solvent | string | Identificação do solvente: `methanol`. |
| model_version | string | Versão do modelo utilizado. |
| warnings | array de strings | Avisos sobre a estimativa e suas limitações. |

A resposta deverá incluir um aviso informando que a predição é uma estimativa estatística e não substitui uma medição experimental.

Não será apresentado um exemplo numérico de predição nesta documentação antes de existir um modelo efetivamente treinado.

---

## 7. Tratamento de erros

As respostas de erro deverão possuir estrutura uniforme.

Formato:

```json
{
  "error": {
    "code": "invalid_smiles",
    "message": "A estrutura SMILES informada não é válida."
  }
}
```

### Códigos HTTP previstos

| HTTP | Código interno | Situação |
|---|---|---|
| 422 | invalid_request | Requisição com campos ausentes ou inválidos. |
| 422 | invalid_smiles | Estrutura molecular inválida. |
| 422 | invalid_temperature | Temperatura inválida ou não finita. |
| 422 | temperature_out_of_range | Temperatura fora da faixa de aplicação definida. |
| 503 | model_unavailable | Artefato ausente ou modelo indisponível. |
| 500 | prediction_failed | Falha inesperada durante o processamento da predição. |

A API deverá apresentar mensagens compreensíveis e não deverá expor stack traces ao usuário.

Falhas internas poderão ser registradas nos logs do servidor para auxiliar a depuração.

---

## 8. Regras gerais de funcionamento

1. O solvente será sempre metanol puro.
2. O usuário não poderá escolher outro solvente.
3. O backend utilizará o pipeline de modelo previamente treinado.
4. Nenhuma requisição poderá iniciar um treinamento.
5. A extração dos descritores deverá utilizar a mesma implementação adotada nos scripts científicos.
6. Os atributos deverão respeitar os nomes e a ordem esperados pelo modelo.
7. A API deverá informar a versão do modelo utilizado.
8. Não haverá armazenamento persistente das predições.

## 9. Decisões pendentes

Os seguintes aspectos ainda dependerão da implementação e dos resultados científicos:

- Confirmação definitiva da temperatura padrão de 25 °C.
- Definição da faixa de aplicação do modelo.
- Seleção definitiva dos descritores.
- Estrutura final dos metadados.
- Formato de persistência do pipeline.
- Política definitiva de mensagens de advertência.

Essas decisões deverão ser incorporadas ao contrato antes da conclusão da integração.

---

**Projeto:** Predição de Solubilidade em Metanol.

**Tecnologia da API:** FastAPI e Pydantic.