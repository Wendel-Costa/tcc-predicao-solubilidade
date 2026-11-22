# Guia de reprodução e execução — C31

Este guia distingue duas atividades que **não devem ser confundidas**: (A) **executar o protótipo com o artefato original** do C23 e (B) **refazer a cadeia de preparação/treinamento em outro diretório** para verificar o processo. A avaliação do teste final do C30 já ocorreu em 22/11/2026 e **não deve ser repetida ou utilizada para ajuste do modelo publicado**.

## 1. Requisitos

- Fedora/Linux (ambiente utilizado pela equipe); outros sistemas podem exigir ajustes de instalação.
- Python **3.14**; a máquina que gerou o Joblib original usou **3.14.8**.
- Git, conexão para instalar dependências, acesso aos arquivos de dados permitidos e, para a demonstração original, ao Joblib confiável gerado pela equipe.
- Executar todos os comandos a partir da raiz do repositório.

```bash
git clone https://github.com/Wendel-Costa/tcc-predicao-solubilidade.git
cd tcc-predicao-solubilidade
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

O arquivo `requirements.txt` define faixas, não um lockfile. **Para utilizar o Joblib original**, conferir o `software_versions` em `artifacts/ridge-v1.metadata.json`. O carregador exige correspondência exata das versões registradas para NumPy, Pandas, RDKit, scikit-learn e Joblib; para Python, exige mesma versão principal e secundária.

Versões do ambiente original:

| Dependência | Versão no C23 |
|---|---|
| Python | 3.14.8 |
| NumPy | 2.5.4 |
| Pandas | 3.1.1 |
| RDKit | 2026.09.2 |
| scikit-learn | 1.9.1 |
| Joblib | 1.6.0 |

Se necessário, ajuste as versões do ambiente para essas versões registradas antes de carregar o Joblib. Não edite o JSON apenas para fazer o teste passar.

## 2. Modo A — executar a aplicação com o modelo original

O repositório contém `artifacts/ridge-v1.metadata.json`, mas **não** o binário `artifacts/ridge-v1.joblib` (`.gitignore`). Solicite o Joblib original por um canal interno **confiável**, garantindo correspondência com os metadados versionados.

```bash
ls -lh artifacts/ridge-v1.metadata.json
sha256sum artifacts/ridge-v1.joblib
python -m app.predictor
```

SHA-256 do Joblib originalmente gerado:

```text
f362ca5d4b01e834901bb446a5029b1f9fb7a1636c7e87374dfd1fbb5e96bf5f
```

O checksum confere a identidade dos bytes em relação ao registro original, mas **não autentica o produtor**: o Joblib usa mecanismos de desserialização que podem executar código. **Nunca carregue um arquivo Joblib recebido de uma fonte desconhecida.**

Se `python -m app.predictor` imprimir `Modelo carregado: ridge-v1` e `Descritores: 10`, inicie:

```bash
python -m uvicorn app.main:app --reload
```

Abra `http://127.0.0.1:8000/frontend/` ou `http://127.0.0.1:8000/docs`. Verifique a API:

```bash
curl -i http://127.0.0.1:8000/api/health
curl -i http://127.0.0.1:8000/api/model-info
curl -i -X POST http://127.0.0.1:8000/api/predict \
  -H 'Content-Type: application/json' \
  -d '{"smiles":"CCO","temperature_c":25}'
```

Com o modelo original, a última requisição deve produzir uma estimativa de cerca de **0,1574631425 LogS(mol/L)**, e `health` deve devolver HTTP 200. Quando o artefato não pode ser carregado, os endpoints dependentes do modelo retornam HTTP 503. SMILES inválidos, campos adicionais e temperaturas fisicamente inválidas retornam HTTP 422. O valor numérico de predição é uma referência **técnica**, não uma medição experimental.

A faixa de temperatura registrada no treino foi **248,2–354,15 K**. Um valor fora dessa faixa provoca aviso de extrapolação, não uma proibição automática. Estar dentro da faixa não garante confiabilidade para uma molécula estruturalmente diferente.

## 3. Modo B — reproduzir a preparação e o treinamento offline

**Não é necessário executar o modo B para demonstrar a aplicação com o modelo original.** Para reconstituir a preparação, baixe o BigSolDB 2.0 do [Zenodo](https://zenodo.org/records/15094979) e confira origem, licença e hashes conforme [`data/README.md`](../data/README.md).

O arquivo principal esperado é **`BigSolDBv2.0.csv`**; ele não é versionado. Guarde-o no diretório abaixo:

```bash
mkdir -p data/raw
# Coloque aqui, manualmente, o CSV original obtido do Zenodo:
ls -lh data/raw/BigSolDBv2.0.csv
sha256sum data/raw/BigSolDBv2.0.csv
```

O SHA-256 do arquivo original utilizado pela equipe foi registrado em `data/README.md`; confira-o antes de reproduzir os números. O arquivo de densidades do Zenodo é documentado como dado de origem, mas **não é consumido diretamente por esses scripts**: a variável-alvo LogS já vem no CSV original.

**Executar somente em um diretório onde os arquivos de saída do split ainda não existam.** Os scripts recusam algumas sobrescritas para preservar a rastreabilidade.

```bash
python -m scripts.preparar_dados
python -m scripts.dividir_dados
python -m scripts.treinar_modelos
python -m scripts.avaliar_modelos
```

Arquivos esperados (não versionados):

```text
data/processed/metanol_curado.csv
data/processed/split/treino.csv
data/processed/split/teste.csv
reports/model_comparison/metricas.json
```

A divisão por molécula canônica utiliza semente 42 e proporção-alvo de 20% dos **grupos** para teste; isso não significa 20% exatos das linhas. Na execução documentada: 6.619 registros de 678 moléculas no treino e 1.601 registros de 170 moléculas no teste, com **zero moléculas compartilhadas**.

Conferência do `treino.csv` utilizado no C23:

```bash
sha256sum data/processed/split/treino.csv
```

SHA-256 esperado para o treino histórico:

```text
0f272a13c2a7c5f0469abf64f098cceec2c82a0c586eae6def1c7491752178d9
```

### Reajustar o modelo em diretório separado (sem sobrescrever o original)

O JSON `artifacts/ridge-v1.metadata.json` **já é versionado**. O script `scripts.persistir_modelo` recusa sobrescrever `ridge-v1.metadata.json` e `ridge-v1.joblib`. Portanto, **NÃO** execute novamente a persistência no diretório padrão do C23.

Use uma pasta separada **fora do repositório**, que não exista ou não contenha os artefatos:

```bash
python -m scripts.persistir_modelo --output-dir ../modelo-reproduzido-c31
```

Esse comando produz **novos arquivos** em `../modelo-reproduzido-c31/` e não altera os metadados históricos na raiz de `artifacts/`. Para conferir o arquivo resultante, use o carregador com caminho explícito:

```bash
python - <<'PY'
from pathlib import Path
from app.predictor import carregar_predictor
modelo = carregar_predictor(Path('../modelo-reproduzido-c31'))
print('Modelo reproduzido:', modelo.info.model_version)
print('Atributos:', len(modelo.info.feature_names))
PY
```

Uma nova execução pode gerar **bytes e hash diferentes**, especialmente em outras versões de bibliotecas. A compatibilidade de versões é conferida pelo carregador. Esse modelo reproduzido **não substitui o artefato original `ridge-v1`**, nem autoriza reinterpretar o teste final já conhecido como um conjunto independente para ele.

**Nota:** essa pasta de saída fica fora do repositório precisamente para não incluir artefatos de treinamento acidentalmente no Git. Não versionar arquivos Joblib ou CSVs de reprodução.

## 4. Avaliação científica publicada (C30)

Os relatórios de avaliação final já foram gerados em **22/11/2026**, utilizando o teste reservado do C14 uma única vez e o Ridge fixado previamente:

- [Relatório narrativo](../reports/avaliacao_final_c30/relatorio.md)
- [Resumo JSON](../reports/avaliacao_final_c30/resumo.json)
- [Protocolo predefinido](protocolo-avaliacao-final-c30.md)

Resultados: MAE = **0,726303 LogS**, RMSE = **0,923927 LogS**, R² = **0,255850**. Esses valores não são métricas da validação interna e não demonstram generalização universal. O teste por molécula ocorreu na mesma fonte de dados: não constitui validação externa independente. A avaliação **não deve ser repetida**, e o modelo **não deve ser reajustado** com base nas métricas observadas.

O comando `python -m scripts.avaliar_teste_final --confirmar-avaliacao-final` descreve a execução histórica do C30, não é um passo da reprodução rotineira. Consulte os resultados já documentados em vez de criar um novo conjunto de métricas após conhecer o teste.

## 5. Diagnóstico de problemas comuns

| Sintoma | Verificação / ação |
|---|---|
| `python3.14: command not found` | Instalar Python 3.14 ou escolher ambiente compatível antes de criar `.venv`. |
| `ModuleNotFoundError` | Ativar `.venv` e executar `python -m pip install -r requirements.txt` da raiz do projeto. |
| `/api/health` devolve HTTP 503 | Verificar presença do Joblib **original**, seu SHA-256, metadados e versões das bibliotecas. |
| `Modelo indisponível: Versão incompatível` | Reproduzir as versões do ambiente original; não alterar metadados históricos. |
| Erro de sobrescrita no split ou na persistência | Preservar arquivos históricos e usar pasta nova para experimentos reproduzidos. |
| `/` não abre a interface | Testar `/frontend/` e conferir se a API foi iniciada na porta 8000. |
| Aviso de extrapolação | Temperatura está fora da faixa observada no treino; estimativa pode ser ainda menos confiável. |
| Aviso `StarletteDeprecationWarning` | Aviso de dependência, não uma falha de teste. Registrar e tratar futuramente. |

## 6. Organização e segurança

Arquivos locais que **não** devem ser publicados em commits de reprodução: CSVs brutos/processados, Joblib/Pickle e quaisquer credenciais. Versionar código, metadados revisados, hashes, documentação, testes e métricas agregadas autorizadas. Evitar registrar SMILES individuais de usuários em logs sem necessidade.

A aplicação é um protótipo acadêmico, sem autenticação e sem infraestrutura de produção. Para publicação na internet, seria necessária uma revisão adicional de exposição do serviço, recursos e segurança.


## 5. Publicação em nuvem

A execução local e a implantação pública têm requisitos de distribuição distintos. Consulte o [guia de implantação](implantacao.md) para o Render com Docker e para o procedimento opcional de versionamento autorizado do único Joblib. Os dados experimentais brutos e processados permanecem excluídos do Git.
