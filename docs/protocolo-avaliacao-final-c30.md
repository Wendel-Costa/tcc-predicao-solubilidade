# C30 — Protocolo pré-especificado da avaliação final

## Objetivo e decisão congelada

Avaliar uma única vez, no teste reservado do C14, o pipeline **ridge-v1**
(`StandardScaler` + `Ridge(alpha=1.0)`), escolhido no C23 pela validação
interna agrupada por molécula (semente 42). O modelo já foi treinado com o
`treino.csv` completo do C14. Não há novo treinamento, busca de hiperparâmetros,
seleção de modelos, correção de dados ou escolha de subconjuntos com base no teste.

O código da API e sua integração foram verificados nos commits C24–C29.
Os testes de software não são medidas de desempenho preditivo.

## Dados e controles contra vazamento

- Fonte: BigSolDB 2.0, DOI 10.5281/zenodo.15094979.
- Escopo: metanol puro; alvo experimental `LogS(mol/L)`.
- Divisão C14 por `SMILES_Canonico`, semente 42, 20% dos grupos no teste.
- Valores anteriormente registrados: treino 6.619 registros / 678 moléculas;
  teste 1.601 registros / 170 moléculas. Conferir esses números antes de publicar.
- O teste não foi usado para seleção do Ridge, ajuste de hiperparâmetros ou criação
  do artefato C23.
- O script verifica ausência de interseção de SMILES canônicos e de `Source_Row`,
  além do SHA-256 do treino contra os metadados do C23.
- O SHA-256 do teste avaliado será registrado no resultado agregado.
- O artefato carregado deve ser o arquivo local **confiável** gerado pela equipe;
  Joblib usa desserialização insegura para arquivos de terceiros.

## Métricas predefinidas

1. **MAE** de LogS por registro, menor é melhor.
2. **RMSE** de LogS por registro, menor é melhor.
3. **R²** no conjunto final retido, maior é melhor; pode ser negativo.
4. **Viés médio** (experimental − previsto).
5. **Mediana e percentil 90** do erro absoluto.
6. **MAE médio por molécula**: calcula o MAE de cada grupo e faz a média
   entre grupos, reduzindo o domínio de moléculas com muitas observações.
7. Descrição por **temperatura** em três faixas estabelecidas pelos extremos
   do treinamento: abaixo, dentro e acima do intervalo. Reportar quantidade de
   registros e MAE; sem observações, marcar `null`, não substituir por zero.
8. Gráficos de **observado versus predito** e **resíduos versus temperatura**.

Os gráficos, análises descritivas e grupos são apenas diagnósticos.
Não escolher novo modelo/descritores/hiperparâmetros após observá-los.

## Execução única deliberada

1. Revisar o código `scripts/avaliar_teste_final.py` **sem abrir o teste final**.
2. Executar apenas os testes sintéticos: `python -m pytest tests/test_avaliar_teste_final.py -q`.
3. Executar a suíte completa: `python -m pytest -q`.
4. Conferir `artifacts/ridge-v1.joblib`, `artifacts/ridge-v1.metadata.json`,
   `data/processed/split/treino.csv` e `data/processed/split/teste.csv`.
5. Confirmar que não existe `reports/avaliacao_final_c30/` de uma avaliação anterior.
6. Executar **uma única vez**:

```bash
python -m scripts.avaliar_teste_final --confirmar-avaliacao-final
```

7. Conferir `reports/avaliacao_final_c30/resumo.json` e
   `reports/avaliacao_final_c30/relatorio.md`, os dois gráficos e a comparação
   com as contagens do C14.
8. Revisar e **interpretar** os resultados em linguagem científica antes do commit.
   Um teste final desfavorável também deve ser relatado, sem mudar `ridge-v1`.

O script rejeita automaticamente a substituição de uma pasta de resultados
já existente. Se falhar antes de gerar o diretório, corrija apenas erros de
infraestrutura/protocolo; não modifique o modelo com base nos valores do teste.

## O que poderá entrar no Git

- Script e testes automatizados.
- Este protocolo e o relatório Markdown de avaliação final, após revisão.
- JSON agregado de métricas/hashes e dois gráficos gerados (sem previsões por linha).

**Não versionar:** `data/processed/split/*.csv`, SMILES individualizados,
previsões por registro, arquivos Joblib, arquivo de dados original.

## Limitações científicas importantes

O teste C14 é um **holdout por molécula dentro do mesmo banco de dados**, não
uma validação externa em laboratório, em outras fontes ou séries temporais.
Mesmo sem SMILES canônicos repetidos entre treino e teste, pode haver
similaridade estrutural entre as moléculas, viés de seleção da base e medições
correlacionadas. Não há garantia de confiança para moléculas fora do domínio
químico do treino ou para temperaturas extremas. Ausência de observações numa
faixa não significa erro zero. Resultados são estimativas em escala LogS,
não medições experimentais produzidas pelo modelo.

Não usar o teste final novamente para retreinar, ajustar ou selecionar e ainda
chamar suas métricas de avaliação independente. Alterações posteriores do modelo
exigem outra estratégia de validação e novos dados de teste independentes.
