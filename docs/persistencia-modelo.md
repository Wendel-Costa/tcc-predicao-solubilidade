
# C23 — Persistência do modelo selecionado

## Modelo

Modelo selecionado: Ridge.

Pipeline:
- StandardScaler
- Ridge(alpha=1.0)

Critério de seleção: menor MAE na validação interna
agrupada por molécula, com semente 42.

Modelos comparados:
- DummyRegressor(strategy="median")
- Ridge(alpha=1.0)
- RandomForestRegressor(n_estimators=200,
  min_samples_leaf=2, random_state=42, n_jobs=1)

## Dados

Fonte: BigSolDB 2.0.
DOI: 10.5281/zenodo.15094979.
Solvente: metanol puro.
Alvo: LogS(mol/L).

O ajuste final usa exclusivamente:
data/processed/split/treino.csv

O conjunto:
data/processed/split/teste.csv

permanece reservado para avaliação final.

## Execução

```bash
python -m scripts.persistir_modelo
```

Saídas:
- artifacts/ridge-v1.joblib
- artifacts/ridge-v1.metadata.json

## Significado das métricas

As métricas armazenadas em model_info são obtidas
da validação interna agrupada, antes do reajuste
com o treino completo.

Elas NÃO são métricas do teste final.
Elas NÃO medem o desempenho do pipeline reajustado
em dados externos.

## Rastreabilidade

O JSON registra:
- Nome e versão do modelo.
- Versão e DOI do dataset.
- Ordem dos atributos.
- Data do treinamento.
- Métricas da validação interna.
- Intervalo observado de temperatura no treino.
- Versões de Python e das bibliotecas.
- SHA-256 do CSV de treino.
- SHA-256 do artefato serializado.
- Quantidade de registros e moléculas do ajuste final.

## Segurança e reprodução

O arquivo joblib usa serialização baseada em pickle.
Não carregar arquivos recebidos de fontes não confiáveis.

O artefato binário não é versionado por padrão.
Em outro computador, é necessário disponibilizar
o arquivo de treino autorizado e executar novamente
o script offline para gerar o artefato.

Não reutilizar metadados de um artefato diferente:
o SHA-256 deve corresponder ao arquivo binário.

A API nunca deverá executar o treinamento
durante uma requisição HTTP.

## Limitações

Ridge é o melhor candidato entre os modelos
avaliados segundo o protocolo interno adotado.
Isso não demonstra generalização irrestrita.

O R² obtido na validação interna foi modesto.
A validade em moléculas inéditas ainda depende
da avaliação final reservada e da análise de erros.

A faixa de temperaturas de treinamento não deve
ser confundida com uma garantia de validade
preditiva em todo o intervalo.
