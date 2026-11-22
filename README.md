# Predição de Solubilidade de Compostos Orgânicos em Metanol

[![Python](https://img.shields.io/badge/Python-3.14-blue)](https://www.python.org/)

Protótipo acadêmico de Trabalho de Conclusão de Curso (TCC) para estimar a solubilidade de compostos orgânicos em **metanol puro**, usando uma estrutura molecular em **SMILES** e uma **temperatura em graus Celsius**. O backend FastAPI calcula descritores com RDKit, aplica um pipeline de regressão Ridge previamente treinado e apresenta uma estimativa em uma interface HTML/CSS/JavaScript.

> **Limitação:** a saída é uma **estimativa estatística**, não uma medição experimental. O projeto é de caráter acadêmico e não deve ser usado isoladamente para decisões de segurança ou processos químicos críticos.

## Estado do projeto

- Aplicação web e API integradas: **implementadas** (C27).
- Modelo selecionado: **`ridge-v1`**, um `Pipeline(StandardScaler, Ridge(alpha=1.0))`, ajustado somente com o conjunto de treino do C14 (C23).
- Testes de software: **284 aprovados** no C30, em 22/11/2026. A finalização acrescenta testes de documentação e de entrega; execute `python -m pytest -q` para verificar a contagem no seu ambiente.
- Avaliação final reservada por molécula: **realizada uma única vez** no C30. Veja [o relatório científico](reports/avaliacao_final_c30/relatorio.md).

## Início rápido — executar a aplicação

Os comandos devem ser executados **na raiz do repositório**. Para demonstrar a API com o mesmo `ridge-v1` publicado, é necessário obter **separadamente um arquivo Joblib original, confiável e compatível**: por padrão, ele não é distribuído pelo Git. Para a implantação em nuvem há uma exceção opcional, consciente e limitada ao artefato `ridge-v1.joblib`, descrita no guia de implantação.

```bash
git clone https://github.com/Wendel-Costa/tcc-predicao-solubilidade.git
cd tcc-predicao-solubilidade
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Para carregar o **artefato original do C23**, reproduza as versões das bibliotecas registradas em `artifacts/ridge-v1.metadata.json`. A execução original usou Python **3.14.8**, NumPy **2.5.4**, Pandas **3.1.1**, RDKit **2026.09.2**, scikit-learn **1.9.1** e Joblib **1.6.0**. `requirements.txt` expressa faixas de versões e, sozinho, não fixa esse ambiente.

Coloque o Joblib original, obtido de fonte interna confiável, em `artifacts/ridge-v1.joblib` (não substitua o JSON versionado). Confira a integridade:

```bash
sha256sum artifacts/ridge-v1.joblib
python -m app.predictor
```

O SHA-256 esperado para o **Joblib do experimento C23** é:

```text
f362ca5d4b01e834901bb446a5029b1f9fb7a1636c7e87374dfd1fbb5e96bf5f
```

O hash confirma correspondência com o artefato registrado; **não prova que um arquivo de origem desconhecida é seguro**. Não carregue Joblib/Pickle de terceiros. Se as versões do ambiente não forem compatíveis, o serviço recusará o carregamento.

Para executar:

```bash
python -m uvicorn app.main:app --reload
```

Abra **http://127.0.0.1:8000/frontend/** (ou a raiz `/`, que redireciona para a interface). A documentação interativa da API fica em **http://127.0.0.1:8000/docs**. `--reload` é apropriado para desenvolvimento local, não para produção.

Exemplo de requisição em outro terminal:

```bash
curl -i -X POST http://127.0.0.1:8000/api/predict \
  -H 'Content-Type: application/json' \
  -d '{"smiles":"CCO","temperature_c":25}'
```

Com o artefato original, a predição técnica registrada para `CCO` a 25 °C foi aproximadamente **0,157463 LogS(mol/L)**; ela **não é um valor experimental**. A temperatura é obrigatória para realizar a predição, sem valor padrão automático. Erros de entrada são devolvidos em JSON, geralmente com HTTP 422. Sem modelo carregável, a API responde HTTP 503.

## API e interface

| Endpoint | Método | Finalidade |
|---|---|---|
| `/` | GET | Redirecionar para a interface |
| `/frontend/` | GET | Formulário web |
| `/api/health` | GET | Estado do serviço e do modelo |
| `/api/model-info` | GET | Metadados do modelo e métricas de **validação interna** |
| `/api/predict` | POST | Estimativa de `LogS(mol/L)` |
| `/docs` | GET | Swagger/OpenAPI |

O solvente é fixo: **metanol**. Não envie outro solvente no JSON. O backend usa temperatura em Kelvin internamente (`°C + 273,15`) e dez atributos na mesma ordem do treinamento. A validação da estrutura SMILES é feita com RDKit; a interface mostra avisos de extrapolação térmica quando aplicável. Consulte o [contrato detalhado da API](docs/contrato-api.md).

## Dados e metodologia

- **Fonte:** BigSolDB 2.0, [Zenodo DOI 10.5281/zenodo.15094979](https://doi.org/10.5281/zenodo.15094979).
- **Recorte:** registros experimentais associados a metanol puro; não se aplica filtro fixo de temperatura na curadoria.
- **Alvo:** `LogS(mol/L)`.
- **Partição:** agrupamento por SMILES canônico (`GroupShuffleSplit`, semente 42), sem moléculas comuns entre treino e teste.
- **Treino:** 6.619 registros de 678 moléculas; **teste final:** 1.601 registros de 170 moléculas.
- **Seleção:** comparação entre DummyRegressor, Ridge e Random Forest, na validação interna restrita ao treino; o Ridge foi escolhido por menor MAE.
- **Treinamento final:** reajuste do Ridge no treino completo, com padronização integrada ao pipeline.
- **Teste final:** uso único no C30, **sem retreinamento e sem seleção de hiperparâmetros**.

### Resultados científicos

| Métrica | Validação interna C23 | Teste final C30 |
|---|---:|---:|
| MAE (LogS) | 0,797167 | **0,726303** |
| RMSE (LogS) | 0,978122 | **0,923927** |
| R² | 0,213921 | **0,255850** |

O teste final foi separado por molécula, mas **dentro do próprio BigSolDB**: não é validação externa independente em outra fonte. O valor de R² indica desempenho explicativo limitado. As métricas da validação interna pertencem a um **ajuste e amostra diferentes**; a diferença numérica não comprova melhoria do modelo. O viés médio (observado − predito) do teste foi **0,023091 LogS**, e o MAE médio atribuindo peso igual a cada molécula foi **0,753855 LogS**.

As 1.601 observações do teste estavam dentro da faixa de temperatura observada no treino; isso **não valida extrapolação térmica**, nem garante generalização a novas classes químicas.

Detalhes: [relatório C30](reports/avaliacao_final_c30/relatorio.md), [resumo estruturado](reports/avaliacao_final_c30/resumo.json) e [protocolo previamente definido](docs/protocolo-avaliacao-final-c30.md).

## Testes

Com o ambiente virtual ativo:

```bash
python -m pytest -q
```

Os testes majoritariamente utilizam amostras sintéticas e fixtures; o teste opcional do C29 que compara o artefato original é ignorado quando o Joblib não está presente. A ausência do arquivo original pode impedir a **demonstração real**, mas não deve impedir a maioria dos testes de software. Avisos de depreciação do Starlette podem aparecer sem reprovar a suíte.

## Reprodução e estrutura do projeto

Para obter o BigSolDB, preparar os dados, entender a separação entre artefato original e treinamento reproduzido, e verificar os hashes, consulte o **[guia de reprodução](docs/guia-reproducao.md)**. Consulte também [a documentação dos dados](data/README.md), [os diagramas](docs/diagramas/01-diagrama-contexto.md) e [os testes de integração](docs/testes-integracao-c29.md).

```text
app/               # Schemas, descritores RDKit, predictor e FastAPI
frontend/          # HTML, CSS e JavaScript
scripts/           # Curadoria, partição, treino e avaliações offline
tests/             # Testes unitários, de contrato e de integração
docs/              # Contrato, protocolo, diagramas e guia de reprodução
data/              # Orientações; CSVs reais locais excluídos do Git
artifacts/         # Metadados; Joblib ignorado por padrão (exceção opcional para deploy)
reports/           # Relatórios científicos agregados e gráficos
```

## Equipe e referência

Projeto desenvolvido por **Wendel, Erika e Gabriel**, com contribuições distribuídas entre dados e aprendizado de máquina, API, frontend, documentação e validação.

Ao utilizar o BigSolDB, cite o conjunto de dados e a publicação científica associados, conforme a [documentação da fonte](data/README.md). Verifique separadamente as licenças dos dados e do código antes de redistribuição ou uso externo.


## Implantação na nuvem e entrega final

O aplicativo pode ser publicado com **FastAPI + frontend no mesmo endereço**. A opção documentada para o TCC é **Render com Docker**; também é possível avaliar Vercel ou Railway, respeitando as limitações de runtime e das dependências científicas.

- [Guia de implantação no Render e alternativas](docs/implantacao.md)
- [Checklist de validação e demonstração final](docs/checklist-entrega.md)
- Dependências exatas do modelo para contêiner: `requirements-deploy.txt`
- Execute `python -m scripts.verificar_deploy --url http://127.0.0.1:8000` após iniciar a API localmente; use a URL publicada depois da implantação.

**Atenção à redistribuição:** o modelo original é excluído do Git por padrão. Publicá-lo no repositório exige decisão expressa da equipe sobre direitos/licenças de distribuição. Jamais publique CSVs, tokens ou segredos. A verificação de integridade SHA-256 não substitui a verificação da origem confiável de um arquivo Joblib.

Antes de apresentar resultados científicos, distinga a validação interna (C23) da avaliação final retida por molécula (C30). A avaliação final **já ocorreu uma vez** e não deve ser refeita para selecionar novas variantes do modelo.
