
# Relatório de Auditoria Inicial — BigSolDB 2.0

## 1. Identificação

**Projeto:** Predição de Solubilidade em Metanol.

**Fonte:** BigSolDB 2.0.

**DOI:** https://doi.org/10.5281/zenodo.15094979

**Data de obtenção:** 09/11/2026.

**Responsável pela obtenção:** Erika.

**Data da auditoria:** 09/11/2026.

**Script utilizado:** `scripts/auditar_dataset.py`.

**Arquivos analisados:**

- `BigSolDBv2.0.csv`
- `BigSolDBv2.0_densities.csv`

Este relatório apresenta os resultados da auditoria inicial dos arquivos originais, antes da aplicação de filtros ou procedimentos de curadoria.

## 2. Características gerais do dataset

A base BigSolDB 2.0 apresentou os seguintes resultados:

| Característica | Resultado |
|---|---:|
| Registros experimentais | 103.944 |
| Colunas | 12 |
| Nomenclaturas de solventes distintas | 213 |
| Moléculas canônicas distintas | 1.448 |
| Fontes científicas distintas | 1.595 |

A estrutura de colunas identificada foi compatível com a descrição do dataset.

### 2.1. Tipos das colunas

| Coluna | Tipo identificado |
|---|---|
| SMILES_Solute | str |
| Temperature_K | float64 |
| Solvent | str |
| SMILES_Solvent | str |
| Solubility(mole_fraction) | float64 |
| Solubility(mol/L) | float64 |
| LogS(mol/L) | float64 |
| Compound_Name | str |
| CAS | str |
| PubChem_CID | float64 |
| FDA_Approved | str |
| Source | str |

## 3. Análise de valores ausentes

A auditoria identificou os seguintes valores ausentes:

| Coluna | Ausentes | Percentual |
|---|---:|---:|
| SMILES_Solute | 0 | 0,00% |
| Temperature_K | 0 | 0,00% |
| Solvent | 0 | 0,00% |
| SMILES_Solvent | 0 | 0,00% |
| Solubility(mole_fraction) | 0 | 0,00% |
| Solubility(mol/L) | 2.961 | 2,85% |
| LogS(mol/L) | 2.961 | 2,85% |
| Compound_Name | 0 | 0,00% |
| CAS | 7.456 | 7,17% |
| PubChem_CID | 2.593 | 2,49% |
| FDA_Approved | 0 | 0,00% |
| Source | 0 | 0,00% |

Os campos relacionados à estrutura molecular, temperatura, solvente e fonte científica não apresentaram valores ausentes.

Entretanto, foram identificados registros sem solubilidade recalculada em mol/L e sem LogS.

A coincidência entre as quantidades de valores ausentes desses dois campos deverá ser investigada durante a curadoria.

Os valores ausentes de CAS e PubChem_CID não representam necessariamente problemas para o objetivo principal, pois a representação molecular SMILES está disponível em todos os registros.

## 4. Distribuições numéricas

### 4.1. Temperatura

A distribuição global de temperatura apresentou:

| Estatística | Temperatura (K) |
|---|---:|
| Mínimo | 243,150000 |
| Máximo | 425,770000 |
| Média | 303,630294 |
| Mediana | 303,150000 |
| Desvio padrão | 15,749350 |
| Primeiro quartil | 293,150000 |
| Terceiro quartil | 313,150000 |

Todos os 103.944 registros apresentaram valores numéricos finitos de temperatura.

**Limitação:** esses resultados representam toda a base e não devem ser utilizados para determinar a faixa de aplicação do modelo de metanol.

A cobertura específica de temperaturas do metanol ainda deverá ser calculada.

### 4.2. Solubilidade em fração molar

| Estatística | Resultado |
|---|---:|
| Registros válidos | 103.944 |
| Mínimo | 0,000000 |
| Máximo | 0,954500 |
| Média | 0,054204 |
| Mediana | 0,009540 |
| Desvio padrão | 0,106530 |
| Primeiro quartil | 0,001260 |
| Terceiro quartil | 0,051160 |

### 4.3. Solubilidade em mol/L

| Estatística | Resultado |
|---|---:|
| Registros válidos | 100.983 |
| Valores ausentes | 2.961 |
| Mínimo | 0,000000 |
| Máximo | 309,792576 |
| Média | 1,185702 |
| Mediana | 0,127638 |
| Desvio padrão | 4,587850 |
| Primeiro quartil | 0,016946 |
| Terceiro quartil | 0,706480 |

### 4.4. LogS (mol/L)

| Estatística | Resultado |
|---|---:|
| Registros válidos | 100.983 |
| Valores ausentes | 2.961 |
| Mínimo | -9,128883 |
| Máximo | 2,491071 |
| Média | -1,029982 |
| Mediana | -0,894021 |
| Desvio padrão | 1,226869 |
| Primeiro quartil | -1,770935 |
| Terceiro quartil | -0,150900 |

Os resultados representam a distribuição global do dataset.

A auditoria não identificou valores não finitos nas colunas numéricas analisadas.

A presença de valores ausentes em LogS exige atenção, pois esse é o atributo que será utilizado como variável-alvo.

## 5. Distribuição dos solventes

Foram identificadas 213 nomenclaturas distintas de solventes.

Os oito solventes com maior frequência foram:

| Solvente | Registros |
|---|---:|
| ethanol | 10.271 |
| methanol | 8.220 |
| isopropanol | 7.298 |
| water | 6.814 |
| ethyl acetate | 6.802 |
| n-propanol | 6.616 |
| acetone | 6.062 |
| n-butanol | 5.613 |

### 5.1. Registros identificados como metanol

A nomenclatura exata `methanol` apareceu em 8.220 registros, correspondendo a aproximadamente 7,91% da base total.

A busca textual por nomenclaturas contendo `methanol` também encontrou:

| Nomenclatura | Registros |
|---|---:|
| methanol | 8.220 |
| diisobutyl methanol | 9 |

A segunda nomenclatura não deverá ser considerada automaticamente uma variante de metanol.

Por isso, a filtragem posterior deverá considerar a identidade química do solvente, utilizando a informação estrutural disponível em `SMILES_Solvent` e regras documentadas de curadoria.

Os 8.220 registros representam uma contagem preliminar baseada no campo `Solvent`, não a confirmação definitiva de todos os registros do subconjunto científico.

## 6. Validação das estruturas moleculares

A validação dos registros utilizando RDKit apresentou:

| Característica | Resultado |
|---|---:|
| SMILES válidos | 103.944 |
| SMILES inválidos | 0 |
| SMILES ausentes | 0 |
| Moléculas canônicas distintas | 1.448 |

Todas as estruturas da coluna `SMILES_Solute` foram interpretadas com sucesso pelo RDKit.

As estruturas canônicas foram geradas preservando a estereoquímica.

Esse resultado demonstra que a representação molecular da base está disponível para o processamento químico previsto no projeto.

Entretanto, a validade sintática de um SMILES não representa, isoladamente, uma validação experimental ou química completa.

## 7. Duplicatas e medições repetidas

Foram identificadas:

| Característica | Resultado |
|---|---:|
| Duplicatas exatas | 0 |
| Moléculas distintas com temperatura válida | 1.448 |
| Moléculas com registros em mais de uma temperatura | 1.386 |

A presença de múltiplas medições para uma mesma molécula reforça a necessidade de utilizar uma estratégia de divisão agrupada.

Uma mesma molécula não deverá aparecer simultaneamente nos conjuntos de treinamento e teste, mesmo quando os registros apresentarem temperaturas diferentes.

A auditoria inicial não realizou agregação ou exclusão dessas medições.

## 8. Rastreabilidade das fontes científicas

A coluna `Source` apresentou:

| Característica | Resultado |
|---|---:|
| Registros com fonte informada | 103.944 |
| Fontes científicas distintas | 1.595 |

As dez fontes mais frequentes foram:

| DOI | Registros |
|---|---:|
| 10.1021/je100341q | 568 |
| 10.1016/j.molliq.2018.12.081 | 392 |
| 10.1021/je1009812 | 340 |
| 10.1016/j.jct.2013.12.031 | 324 |
| 10.1016/j.jct.2014.05.009 | 288 |
| 10.1016/j.molliq.2022.120365 | 247 |
| 10.1016/j.molliq.2016.08.074 | 245 |
| 10.1021/acs.jced.7b00316 | 236 |
| 10.1021/acs.jced.3c00237 | 234 |
| 10.1021/acs.jced.9b00842 | 215 |

A presença de referências científicas em todos os registros possibilita a rastreabilidade das fontes experimentais.

## 9. Auditoria do arquivo complementar de densidades

O arquivo `BigSolDBv2.0_densities.csv` apresentou:

| Característica | Resultado |
|---|---:|
| Registros | 2.210 |
| Colunas | 4 |
| Valores ausentes | 0 |

As colunas identificadas foram:

- Solvent.
- Temperature_K.
- Density_g/cm^3.
- Source.

Foi identificada uma particularidade: a coluna `Density_g/cm^3` foi carregada pelo Pandas como texto (`str`).

Embora não existam valores ausentes, ainda será necessário verificar se todos os registros podem ser convertidos em valores numéricos finitos.

Essa verificação deverá ocorrer antes de qualquer utilização do arquivo em procedimentos de cálculo.

## 10. Integridade e procedência dos arquivos

Os arquivos utilizados correspondem à versão BigSolDB 2.0, obtida em 09/11/2026.

DOI: 10.5281/zenodo.15094979

### 10.1. Checksums MD5

| Arquivo | MD5 de referência |
|---|---|
| BigSolDBv2.0.csv | 1e6d8a510387746e9faab5f39dc46317 |
| BigSolDBv2.0_densities.csv | 059ae2deadb2ad1523fd4e24b2c88133 |

### 10.2. Hashes SHA-256

| Arquivo | SHA-256 |
|---|---|
| BigSolDBv2.0.csv | 879f55f39db977e295c705e304d011d89d6e10da1daaa3f069181108c1de38b0 |
| BigSolDBv2.0_densities.csv | 02226420d9fb3294cb32211dac7f6ff7fa067511924afdb9f1893af1e334aac6 |

A responsável pela obtenção informou que os arquivos foram obtidos e tiveram sua integridade conferida.

A licença específica do dataset deverá ser consultada no documento `data/README.md`, que mantém o registro da verificação realizada pela equipe.

## 11. Limitações da auditoria inicial

Esta etapa teve como objetivo caracterizar a base original, sem executar procedimentos de curadoria.

Portanto, ainda existem questões que precisam ser investigadas:

1. Distribuição de LogS especificamente para metanol.
2. Quantidade de registros de metanol sem variável-alvo.
3. Distribuição de temperatura do subconjunto de metanol.
4. Cobertura de observações próximas a 25 °C.
5. Confirmação da identidade química do solvente por meio de `SMILES_Solvent`.
6. Integridade numérica da coluna de densidade.
7. Distribuição de medições repetidas por molécula e temperatura.
8. Identificação de possíveis conflitos experimentais.

Os resultados apresentados neste relatório não devem ser interpretados como resultados da base já curada para treinamento.

## 12. Conclusão

A auditoria inicial confirmou que o BigSolDB 2.0 contém 103.944 registros experimentais distribuídos entre 213 nomenclaturas de solventes, com 1.448 moléculas canônicas distintas.

Foram identificados 8.220 registros com a nomenclatura exata `methanol`, constituindo o ponto de partida para a investigação específica do projeto.

Todas as estruturas SMILES do soluto foram interpretadas com sucesso pelo RDKit, e foram identificadas 1.595 fontes científicas.

Entretanto, ainda não é possível determinar o tamanho definitivo do conjunto de dados utilizável no treinamento, pois precisamos realizar a filtragem específica de metanol, verificar a disponibilidade da variável-alvo e analisar a distribuição de temperatura.

A próxima etapa deverá investigar essas questões antes da construção dos modelos de aprendizado de máquina.

---

**Responsável pela auditoria:** Erika.

**Projeto:** Predição de Solubilidade em Metanol.

**Versão do dataset:** BigSolDB 2.0.