# C29 — Integração entre pipeline, predictor e API

## Objetivo

Verificar a integração das implementações dos commits C12, C16, C23, C24,
C25 e C26, preservando a separação entre **ajuste offline** e **inferência HTTP**.

Este conjunto de testes verifica comportamento de software e **não constitui
avaliação de desempenho preditivo** nem validação científica externa.

## Escopo de teste

Arquivo de teste: `tests/test_integracao_pipeline_api.py`.

A suíte contém **16 casos** (13 funções; uma delas parametrizada em quatro
entradas). A infraestrutura utiliza um CSV de treino **inteiramente sintético**,
construído em um diretório temporário. Um segundo arquivo chamado `teste.csv`
contém uma sentinela e não deve ser aberto. Nenhum CSV real é utilizado nesses
casos.

O experimento de seleção de candidatos é **controlado** por valores fictícios:
essa parte da comparação não é reexecutada no C29. O script real
`scripts.persistir_modelo.treinar_e_salvar()` continua treinando um
`Pipeline(StandardScaler, Ridge(alpha=1.0))` real sobre os atributos produzidos
pelo RDKit, e salva o Joblib e os metadados em arquivos temporários.

O módulo `app.predictor` carrega os dois arquivos, verifica versões, ordem dos
atributos e hashes; o FastAPI atende `/api/health`, `/api/model-info` e
`POST /api/predict` usando o **predictor real** gerado para o teste.

### Aspectos cobertos

- Treinamento lê somente `treino.csv` sintético; `teste.csv` reservado intacto.
- SHA-256 do CSV e do Joblib conferidos contra metadados.
- Ordem, quantidade e valores dos dez atributos entre treino e inferência.
- Concordância numérica entre `Pipeline.predict()`, `Predictor.prever()` e HTTP.
- SMILES equivalentes (`CCO` e `OCC`) na mesma temperatura.
- Conversão Celsius → Kelvin e aviso de extrapolação.
- Erros HTTP 422 (`invalid_smiles`, `invalid_temperature`, `invalid_request`).
- Ausência de chamadas de treinamento, gravação do Joblib ou leitura de CSV
  durante as requisições.
- Reutilização do artefato em cache, sem carregamentos repetidos.
- Arquivo Joblib adulterado: API retorna HTTP 503 sem expor uma predição.

### Teste opcional com o artefato real do C23

Quando `artifacts/ridge-v1.joblib` existe e foi criado com versões compatíveis,
o último caso valida seu carregamento e a predição de regressão para etanol
(`CCO`) a 25 °C, aproximadamente `0.1574631425041294` LogS(mol/L).
O valor é uma referência técnica previamente observada, **não é a solubilidade
experimental do etanol**. O teste não abre arquivos de treino ou teste reais.

Em computadores sem o Joblib, ou com bibliotecas incompatíveis com o binário,
esse teste é pulado. Uma falha de integridade com versões compatíveis deve
reprovar o teste, não ser ignorada.

## Comandos de execução

Na raiz do repositório, com o ambiente virtual ativado:

```bash
python -m pytest tests/test_integracao_pipeline_api.py -q
python -m pytest -q
```

Se o arquivo Joblib original estiver presente e compatível, são esperados
**16 testes aprovados no novo arquivo**. Em ambientes sem ele, são esperados
**15 aprovados e 1 ignorado**. O total do projeto, partindo dos 252 testes do
C28, será respectivamente **268 aprovados**, ou **267 aprovados e 1 ignorado**.
Essas contagens precisam ser confirmadas no ambiente local.

## Limites científicos

1. Resultados de seleção e métricas sintéticas dos fixtures **não devem** ser
   citados como resultados do BigSolDB 2.0.
2. Os valores do `model_info` de arquivos sintéticos são fabricados
   intencionalmente para testar o contrato.
3. As métricas `MAE`, `RMSE` e `R²` do Ridge real publicadas no C23 se referem
   à validação interna agrupada antes do reajuste final.
4. `data/processed/split/teste.csv` continua reservado. Não deve ser
   utilizado ou inspecionado durante C29.
5. SHA-256 verifica integridade com relação ao registro, não autentica
   artefatos fornecidos por terceiros. Arquivos Joblib não confiáveis nunca
   devem ser carregados.
6. O desempenho científico e a análise de erros devem ser tratados na etapa
   científica subsequente, com protocolo de avaliação final explícito.
