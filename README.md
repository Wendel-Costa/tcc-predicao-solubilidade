
# Predição de Solubilidade em Metanol

Projeto de Trabalho de Conclusão de Curso dedicado ao desenvolvimento e à avaliação de modelos de aprendizado de máquina para estimar a solubilidade de pequenas moléculas orgânicas em metanol.

## Objetivo

Investigar quais técnicas de aprendizado de máquina conseguem estimar melhor a solubilidade de diferentes moléculas em metanol, utilizando descritores moleculares bidimensionais e temperatura como variáveis de entrada.

O projeto também contempla o desenvolvimento de uma aplicação web para disponibilizar as estimativas produzidas pelo modelo selecionado.

## Escopo

- Solvente: metanol (CH₃OH).
- Variável-alvo: LogS(mol/L).
- Representação molecular de entrada: SMILES.
- Temperatura: variável numérica expressa em Kelvin durante o processamento científico.
- Fonte de dados: BigSolDB 2.0.

## Fonte de dados

**BigSolDB 2.0**

DOI: https://doi.org/10.5281/zenodo.15094979

Serão utilizados exclusivamente registros experimentais referentes ao metanol puro.

Os arquivos originais do dataset não deverão ser versionados neste repositório por padrão. A obtenção, identificação, preparação e auditoria dos dados serão documentadas ao longo do desenvolvimento.

## Tecnologias previstas

| Área | Tecnologias |
|---|---|
| Linguagem | Python |
| Manipulação de dados | Pandas e NumPy |
| Quimioinformática | RDKit |
| Aprendizado de máquina | scikit-learn |
| Backend | FastAPI e Pydantic |
| Frontend | HTML, CSS e JavaScript |
| Testes | Pytest |
| Visualização | Matplotlib |
| Versionamento | Git e GitHub |

## Arquitetura prevista

O projeto será organizado em módulos com responsabilidades independentes:

- **Preparação dos dados:** auditoria, curadoria e processamento do BigSolDB.
- **Aprendizado de máquina:** extração de descritores, treinamento e avaliação dos modelos.
- **Backend:** API responsável pela validação das entradas e execução das predições.
- **Frontend:** interface web para envio das estruturas moleculares e apresentação dos resultados.

O treinamento será realizado offline. A aplicação utilizará um pipeline previamente treinado e salvo.

## Equipe

- Wendel
- Erika
- Gabriel

## Estado do projeto

Em desenvolvimento.

A auditoria dos dados, os experimentos de aprendizado de máquina e a implementação da aplicação ainda serão realizados. Portanto, não existem resultados de desempenho ou previsões validadas a apresentar nesta etapa.
