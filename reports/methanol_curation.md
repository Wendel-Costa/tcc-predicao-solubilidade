# Relatório de Curadoria — Registros de Metanol do BigSolDB 2.0

## 1. Identificação

- **Projeto:** Predição de Solubilidade de Compostos Orgânicos em Metanol
- **Fonte:** BigSolDB 2.0
- **DOI:** 10.5281/zenodo.15094979
- **Data da execução:12/11/2026
- **Responsável:** Erika
- **Script utilizado:** `scripts/preparar_dados.py`
- **Arquivo original:** `data/raw/BigSolDBv2.0.csv`
- **SHA-256 do original:** 879f55f39db977e295c705e304d011d89d6e10da1daaa3f069181108c1de38b0
- **Arquivo produzido:** `data/processed/metanol_curado.csv`

## 2. Objetivo

Selecionar e validar registros experimentais de solubilidade referentes exclusivamente ao metanol puro, preservando a rastreabilidade dos dados e preparando o conjunto para as próximas etapas de quimioinformática e aprendizado de máquina.

## 3. Metodologia de curadoria

A identificação do metanol exige concordância entre a nomenclatura textual do solvente e a estrutura molecular representada por SMILES.

A curadoria aplica as seguintes regras:

1. Verificação das colunas obrigatórias.
2. Normalização do nome do solvente.
3. Canonicalização do SMILES do solvente com RDKit.
4. Identificação de metanol pela concordância entre nome e estrutura.
5. Canonicalização do SMILES do soluto, preservando estereoquímica.
6. Exclusão de solutos com SMILES ausente ou inválido.
7. Validação de temperatura finita e maior que zero Kelvin.
8. Validação da variável-alvo `LogS(mol/L)`.
9. Preservação da linha original por `Source_Row`.
10. Diagnóstico de duplicatas e medições repetidas, sem remoção automática.

A temperatura permanece expressa em Kelvin e a variável-alvo permanece na escala logarítmica decimal.

## 4. Resultados da identificação do metanol

| Indicador | Resultado |
|---|---|
| Registros originais | 103,944 |
| Registros com nome methanol | 8,220 |
| Registros com estrutura de metanol | 8,220 |
| Concordância entre nome e estrutura | 8,220 |
| Somente nome correspondente | 0 |
| Somente estrutura correspondente | 0 |
| SMILES de solvente inválidos ou ausentes | 299 |

## 5. Resultados da curadoria

| Indicador | Resultado |
|---|---|
| Candidatos confirmados como metanol | 8,220 |
| SMILES de soluto inválidos ou ausentes | 0 |
| Temperaturas inválidas ou ausentes | 0 |
| Valores LogS inválidos ou ausentes | 0 |
| Registros finais preparados | 8,220 |
| Moléculas canônicas distintas | 848 |
| Fontes científicas distintas | 874 |

As exclusões são sequenciais, de modo que cada contagem corresponde aos registros eliminados na respectiva etapa.

## 6. Duplicatas e observações repetidas

| Indicador | Resultado |
|---|---|
| Duplicatas exatas | 0 |
| Grupos repetidos por molécula e temperatura | 351 |
| Registros pertencentes aos grupos repetidos | 740 |

As observações repetidas foram diagnosticadas, mas não removidas ou agregadas automaticamente. Sua influência deverá ser considerada durante a avaliação experimental.

## 7. Distribuição da temperatura

| Indicador | Resultado |
|---|---|
| Temperatura mínima | 248.200000 K |
| Temperatura máxima | 354.150000 K |
| Média | 302.052157 K |
| Mediana | 303.150000 K |
| Temperaturas distintas | 745 |
| Registros a 298,15 ± 1 K | 829 |
| Moléculas distintas a 298,15 ± 1 K | 760 |
| Registros a 298,15 ± 5 K | 2,546 |
| Moléculas distintas a 298,15 ± 5 K | 843 |

### Análise de 25 °C

A avaliação deve considerar a quantidade de observações, o número de moléculas distintas, a distribuição de temperaturas e a representatividade do conjunto próximo de 298,15 K.

As janelas diagnósticas não foram utilizadas como filtros de treinamento.

## 8. Distribuição da solubilidade

| Indicador | Resultado |
|---|---|
| LogS mínimo | -6.865999 |
| LogS máximo | 2.391134 |
| LogS médio | -0.787865 |
| LogS mediano | -0.733187 |

A variável-alvo corresponde a `LogS(mol/L)`, o logaritmo decimal da concentração molar, recalculado pelos autores do BigSolDB 2.0 a partir dos dados de fração molar e informações de densidade.

## 9. Limitações e decisões

**Identificação do solvente.** Não houve divergência entre nome e estrutura: os 8.220 registros identificados como metanol satisfazem os dois critérios, e nenhum foi identificado por apenas um deles. Os 299 SMILES de solvente inválidos ou ausentes não correspondem a registros com nome "methanol", portanto não representam perda de dados de metanol.

**Cobertura de temperatura.** As medições abrangem de 248,2 K a 354,15 K, com mediana de 303,15 K e 745 temperaturas distintas. A janela de 298,15 ± 1 K contém 829 registros (10,1%) e 760 moléculas; a de ± 5 K contém 2.546 registros (31,0%) e 843 moléculas. A maioria dos registros está, portanto, fora de 25 °C, e um modelo restrito a essa temperatura usaria uma fração pequena dos dados. Decisão: manter todas as temperaturas e tratar a temperatura como variável de entrada. As janelas foram usadas apenas como diagnóstico.

**Medições repetidas.** Há 351 grupos de repetição por molécula e temperatura, somando 740 registros (9,0%), sem duplicatas exatas. Foram preservados, sem remoção nem agregação. Como a divisão entre treino e teste será agrupada por SMILES canônico, todas as repetições de uma molécula ficarão no mesmo subconjunto, o que evita vazamento de dados. Em contrapartida, moléculas com mais repetições pesam mais no treino e nas métricas. Essas repetições, vindas de fontes diferentes, também permitem estimar a variabilidade experimental.

**Representatividade das moléculas.** O conjunto tem 848 moléculas distintas (média de cerca de 9,7 registros por molécula) e 874 fontes. Na divisão agrupada, o que limita a generalização é o número de moléculas, não o de registros: uma divisão 80/20 deixaria cerca de 680 moléculas para treino e 170 para teste. A diversidade química (massa molar, grupos funcionais, esqueletos) ainda não foi avaliada. A heterogeneidade entre 874 fontes também implica variabilidade entre métodos e laboratórios.

**Variável-alvo.** O LogS foi recalculado pelos autores do BigSolDB 2.0 a partir da fração molar e da densidade, de modo que incertezas de densidade se propagam para o alvo. O valor máximo (2,39) equivale a cerca de 245 mol/L, muito acima da concentração molar do metanol puro (cerca de 24,7 mol/L). 

Dessa forma, a base não é considerada suficiente apenas pelo número de registros; a avaliação leva em conta também as 848 moléculas e a divisão agrupada.

## 10. Conclusão

A curadoria identificou 8.220 registros de metanol puro, com concordância total entre nome e estrutura, e nenhum registro foi excluído por soluto, temperatura ou LogS inválidos. O conjunto final tem 848 moléculas distintas e 874 fontes, com temperaturas de 248,2 K a 354,15 K. As medições repetidas (740 registros em 351 grupos) foram preservadas e serão tratadas pela divisão agrupada por SMILES canônico.

O conjunto é adequado como entrada para a próxima etapa (divisão agrupada e modelos de referência), com as ressalvas de que a cobertura química e a distribuição de temperatura ainda precisam ser avaliadas e de que os valores extremos de LogS precisam ser verificados.

O conjunto preparado será utilizado como entrada das próximas etapas somente após a verificação de sua integridade e adequação ao protocolo experimental.