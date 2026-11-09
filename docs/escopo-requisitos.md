
# Escopo do Projeto e Restrições Científicas

**Projeto:** Predição de Solubilidade em Metanol

**Título provisório:** Desenvolvimento e Avaliação de Modelos de Aprendizado de Máquina e Protótipo Web para a Predição de Solubilidade de Compostos Orgânicos em Metanol utilizando Descritores Moleculares.

**Versão do documento:** 1.0

**Data:** 07/11/2026

**Status:** Escopo definido; decisões metodológicas específicas pendentes de auditoria dos dados.

---

## 1. Contextualização

Este projeto de Trabalho de Conclusão de Curso investiga a utilização de técnicas de aprendizado de máquina supervisionado para estimar a solubilidade de pequenas moléculas orgânicas em metanol.

A proposta envolve a análise de dados experimentais, o cálculo de descritores moleculares bidimensionais e o treinamento de modelos de regressão capazes de estimar a solubilidade de moléculas a partir de suas estruturas químicas e da temperatura.

Além da investigação científica, será desenvolvido um protótipo de aplicação web para disponibilizar as estimativas produzidas pelo modelo selecionado.

## 2. Problema de pesquisa

Qual é a solubilidade de diferentes pequenas moléculas orgânicas em metanol, e quais técnicas de aprendizado de máquina conseguem estimá-la melhor?

A investigação busca compreender a capacidade dos modelos de regressão de identificar relações entre características estruturais das moléculas, temperatura e solubilidade experimental em metanol.

## 3. Objetivos

### 3.1. Objetivo geral

Desenvolver e avaliar modelos de aprendizado de máquina para estimar a solubilidade de pequenas moléculas orgânicas em metanol, utilizando descritores moleculares bidimensionais e temperatura como variáveis de entrada.

### 3.2. Objetivos específicos

- Obter e auditar os registros experimentais da base BigSolDB 2.0.
- Identificar e selecionar exclusivamente os registros referentes ao metanol puro.
- Validar as estruturas moleculares e os valores experimentais utilizados.
- Extrair descritores moleculares bidimensionais por meio do RDKit.
- Investigar a influência da temperatura nas estimativas.
- Treinar e comparar diferentes modelos de regressão.
- Avaliar os modelos utilizando métricas estatísticas adequadas.
- Desenvolver uma aplicação web para disponibilizar as estimativas.
- Documentar os procedimentos, resultados e limitações da investigação.

## 4. Delimitação científica

### 4.1. Substâncias estudadas

O estudo será restrito a pequenas moléculas orgânicas.

A definição operacional de pequena molécula ainda deverá ser discutida pela equipe. Caso seja necessário estabelecer um critério quantitativo, como um limite de massa molar, ele deverá ser justificado e definido antes da avaliação final dos modelos.

Não será permitido escolher esse limite retrospectivamente apenas para melhorar os resultados.

### 4.2. Solvente

O único solvente considerado no modelo principal será o metanol puro (CH₃OH).

Serão excluídos do escopo:

- Registros de solubilidade em água.
- Registros de solubilidade em etanol.
- Registros de solubilidade em outros solventes.
- Misturas de metanol com outros solventes.

Não serão utilizados registros de outros solventes como substitutos de dados experimentais de metanol.

### 4.3. Fonte dos dados

A fonte prioritária será:

**BigSolDB 2.0**

DOI: https://doi.org/10.5281/zenodo.15094979

A base será utilizada como fonte de dados experimentais para a construção e avaliação dos modelos.

Antes do treinamento, será necessário confirmar:

- A versão efetivamente obtida.
- A estrutura e os nomes das colunas.
- A identificação dos registros de metanol puro.
- A definição da variável de solubilidade.
- As unidades utilizadas.
- A origem e a rastreabilidade dos registros.
- As condições de uso e redistribuição dos dados.

Os arquivos originais não deverão ser versionados no GitHub por padrão.

### 4.4. Variável-alvo

A variável-alvo proposta é:

**LogS (mol/L)**

Ela representa o logaritmo decimal da solubilidade expressa em concentração molar.

A relação matemática correspondente é:

LogS = log10(S)

Onde:

- LogS representa o valor na escala logarítmica.
- S representa a solubilidade em mol/L.

Quando necessária, a transformação inversa será:

S = 10^LogS

A coluna correspondente no BigSolDB 2.0, sua definição, unidade e eventuais transformações deverão ser confirmadas na documentação e nos arquivos reais da base.

Não será considerada suficiente a simples existência de uma coluna cujo nome contenha LogS.

Todos os resultados dos modelos deverão ser avaliados na escala LogS (mol/L).

### 4.5. Temperatura

A temperatura será considerada uma variável numérica de entrada dos modelos.

Os dados de origem utilizam Kelvin (K), enquanto a interface web receberá valores em graus Celsius (°C).

A conversão deverá respeitar a seguinte relação:

K = °C + 273,15

A temperatura padrão inicialmente prevista para a aplicação é 25 °C, equivalente a 298,15 K.

Entretanto, essa configuração dependerá da auditoria dos registros de metanol.

Antes de estabelecer 25 °C como padrão definitivo, a equipe deverá:

- Identificar a faixa de temperaturas dos registros de metanol.
- Verificar a quantidade de observações próximas a 25 °C.
- Analisar a distribuição de temperaturas.
- Avaliar se existe cobertura suficiente nessa região.

A faixa global de temperaturas do BigSolDB não deverá ser utilizada como evidência da cobertura específica de metanol.

Caso a cobertura seja insuficiente ou 25 °C esteja fora da faixa observada, a questão deverá ser documentada e discutida pela equipe.

Não serão ocultadas extrapolações de temperatura.

## 5. Abordagem computacional

### 5.1. Representação molecular

As moléculas serão fornecidas à aplicação por meio de estruturas químicas representadas em formato SMILES.

A interpretação e validação dessas estruturas serão realizadas com o RDKit.

Será utilizada uma representação canônica para identificação e agrupamento das moléculas.

Informações estruturais relevantes, como estereoquímica e presença de sais, não deverão ser removidas indiscriminadamente.

### 5.2. Descritores moleculares

Serão utilizados descritores moleculares bidimensionais calculados pelo RDKit.

Entre os descritores inicialmente considerados estão:

- Massa molecular.
- LogP calculado.
- Área de superfície polar topológica (TPSA).
- Doadores de ligações de hidrogênio.
- Aceitadores de ligações de hidrogênio.
- Ligações rotacionáveis.
- Quantidade de átomos pesados.
- Quantidade de anéis.
- Fração Csp3.

A temperatura também integrará o conjunto de atributos dos modelos.

A seleção definitiva dos descritores deverá ser documentada e aplicada de maneira consistente no treinamento e na inferência.

Os descritores calculados não deverão ser confundidos com a variável-alvo experimental.

### 5.3. Modelos de aprendizado de máquina

O estudo começará com os seguintes modelos de regressão:

1. DummyRegressor, utilizando a estratégia de mediana.
2. Ridge.
3. RandomForestRegressor.

O DummyRegressor será utilizado como modelo de referência para avaliar se os demais algoritmos conseguem aprender relações úteis nos dados.

A implementação de modelos adicionais dependerá da conclusão e estabilidade do MVP.

Não serão priorizadas redes neurais ou arquiteturas excessivamente complexas.

### 5.4. Separação dos dados

A divisão entre treinamento e teste deverá ser agrupada por molécula, utilizando sua representação canônica.

Uma mesma molécula não poderá aparecer simultaneamente nos conjuntos de treinamento e teste, mesmo quando houver diferentes registros experimentais ou temperaturas.

Essa restrição busca evitar vazamento de informações e tornar a avaliação mais próxima do objetivo de estimar a solubilidade de moléculas não utilizadas durante o treinamento.

O conjunto de teste final deverá permanecer separado durante a seleção de atributos, ajuste dos modelos e escolha da configuração final.

### 5.5. Avaliação

Os modelos serão avaliados inicialmente utilizando:

- MAE — Erro Absoluto Médio.
- RMSE — Raiz do Erro Quadrático Médio.
- R² — Coeficiente de determinação.

As métricas serão calculadas na escala LogS (mol/L).

Quando houver dados suficientes, também serão produzidos gráficos de distribuição, comparação entre valores observados e preditos e análise de resíduos.

Não será estabelecido antecipadamente um desempenho mínimo obrigatório.

Um modelo que não superar a baseline também poderá representar um resultado científico válido, desde que sua avaliação e suas limitações sejam adequadamente documentadas.

## 6. Delimitação do software

O produto de software será um protótipo web de estimativa de solubilidade em metanol.

O fluxo geral previsto será:

1. O usuário informa a estrutura molecular em formato SMILES.
2. O usuário informa a temperatura em graus Celsius.
3. O frontend envia os dados para a API.
4. A API valida as informações recebidas.
5. O módulo químico utiliza o RDKit para interpretar a estrutura e extrair os descritores.
6. O serviço de predição organiza os atributos e utiliza o pipeline previamente treinado.
7. A API devolve a estimativa de LogS (mol/L).
8. O frontend apresenta o resultado e os avisos pertinentes.

O treinamento será executado offline por meio de scripts específicos.

A API não deverá treinar modelos durante as requisições.

O processamento utilizado na inferência deverá ser consistente com aquele utilizado durante o treinamento.

### 6.1. Tecnologias previstas

- Python.
- Pandas e NumPy.
- RDKit.
- scikit-learn.
- FastAPI.
- Pydantic.
- HTML.
- CSS.
- JavaScript.
- Pytest.
- Matplotlib.
- Git e GitHub.

### 6.2. Limitações do produto

A aplicação apresentará estimativas estatísticas baseadas em dados experimentais e em um modelo de aprendizado de máquina previamente treinado.

Portanto, ela:

- Não realizará simulações termodinâmicas de primeiros princípios.
- Não substituirá medições experimentais.
- Não garantirá precisão para moléculas fora do domínio de aplicação.
- Não deverá ocultar limitações ou extrapolações.
- Não deverá apresentar valores fictícios como predições reais.

## 7. Itens fora do escopo

Para manter o projeto viável dentro do prazo, não serão implementados como parte do MVP:

- Predição de solubilidade em múltiplos solventes.
- Predição de solubilidade em misturas de solventes.
- Banco de dados.
- Cadastro e autenticação de usuários.
- Histórico persistente de predições.
- Treinamento de modelos durante as requisições da API.
- Microsserviços.
- Infraestrutura complexa de implantação.
- Frontend baseado em frameworks como React, Vue ou Angular.
- Redes neurais como prioridade inicial.

Docker poderá ser considerado posteriormente somente se resolver um problema concreto de execução ou instalação.

## 8. Restrições metodológicas

Durante todo o desenvolvimento, deverão ser respeitados os seguintes princípios:

1. Utilizar exclusivamente registros experimentais de metanol puro no modelo principal.
2. Não misturar unidades ou escalas de solubilidade.
3. Confirmar a definição da variável-alvo antes do treinamento.
4. Não presumir cobertura de temperatura sem auditar os registros.
5. Não remover informações químicas indiscriminadamente.
6. Impedir a presença da mesma molécula nos conjuntos de treinamento e teste.
7. Utilizar procedimentos consistentes de extração de atributos.
8. Não escolher modelos com base em resultados obtidos repetidamente no conjunto de teste.
9. Não inventar resultados, métricas, contagens ou evidências experimentais.
10. Documentar as decisões de curadoria e as limitações dos modelos.

## 9. Decisões pendentes de validação

As questões abaixo deverão ser resolvidas durante o desenvolvimento:

| Questão | Etapa prevista |
|---|---|
| Identificação exata da coluna LogS e confirmação da unidade | Auditoria do BigSolDB |
| Critério operacional para pequenas moléculas | Antes da avaliação final |
| Cobertura de temperatura do metanol | Auditoria do BigSolDB |
| Adequação de 25 °C como temperatura padrão | Após auditoria |
| Tratamento de duplicatas e conflitos experimentais | Curadoria |
| Seleção definitiva dos descritores | Preparação dos dados |
| Faixa de aplicação do modelo | Após análise dos dados e experimentos |
| Condições de redistribuição dos dados e artefatos | Verificação de licença |

Nenhuma dessas questões deverá ser resolvida por suposição quando depender de evidências dos dados reais.

## 10. Critérios gerais de conclusão

O projeto será considerado tecnicamente concluído quando:

- O procedimento de obtenção e preparação dos dados estiver documentado.
- O subconjunto de metanol tiver sido auditado.
- Os descritores forem extraídos de maneira reproduzível.
- Os modelos tiverem sido treinados e avaliados.
- Os resultados reais estiverem documentados.
- O pipeline final puder ser carregado para realizar predições.
- A API estiver integrada ao serviço de predição.
- A interface web estiver funcional.
- Os testes previstos estiverem implementados e executados.
- A documentação permitir reproduzir a execução do sistema.
- As limitações científicas e computacionais estiverem explícitas.

A ausência de desempenho superior à baseline não invalida automaticamente o trabalho, desde que a investigação tenha sido conduzida e documentada adequadamente.


## 11. Requisitos funcionais

Os requisitos funcionais descrevem os serviços e comportamentos que o sistema deverá oferecer.

| ID | Requisito | Descrição |
|---|---|---|
| RF01 | Entrada molecular | O sistema deverá permitir o envio de uma estrutura molecular em formato SMILES. |
| RF02 | Entrada de temperatura | O sistema deverá permitir informar a temperatura em graus Celsius, utilizando inicialmente 25 °C como padrão quando não informada, sujeito à validação da cobertura experimental. |
| RF03 | Validação molecular | O sistema deverá validar as estruturas SMILES utilizando o RDKit e rejeitar estruturas inválidas. |
| RF04 | Extração de atributos | O sistema deverá calcular os descritores moleculares definidos pelo protocolo científico e incorporar a temperatura. |
| RF05 | Predição | O backend deverá utilizar o pipeline de aprendizado de máquina previamente treinado para estimar a solubilidade. |
| RF06 | Apresentação do resultado | O sistema deverá apresentar o resultado na escala LogS (mol/L), a temperatura utilizada, a versão do modelo e os avisos pertinentes. |
| RF07 | Verificação de disponibilidade | A API deverá disponibilizar um endpoint para verificar sua disponibilidade e a do modelo. |
| RF08 | Informações do modelo | A API deverá disponibilizar informações sobre o modelo utilizado, os dados de treinamento, os atributos e as métricas disponíveis. |
| RF09 | Tratamento de erros | O sistema deverá apresentar mensagens estruturadas e compreensíveis para entradas inválidas e falhas de processamento. |
| RF10 | Ausência de histórico | O sistema não deverá persistir o histórico das predições realizadas pelos usuários. |

## 12. Requisitos não funcionais

Os requisitos não funcionais estabelecem condições de qualidade e restrições que deverão ser respeitadas durante o desenvolvimento.

| ID | Requisito | Descrição |
|---|---|---|
| RNF01 | Consistência científica | O modelo principal deverá utilizar exclusivamente registros experimentais referentes ao metanol puro. |
| RNF02 | Consistência de atributos | A geração dos descritores deverá utilizar a mesma implementação durante o treinamento e a inferência, preservando os nomes, a quantidade e a ordem das características. |
| RNF03 | Integridade experimental | A divisão dos dados deverá impedir que a mesma molécula apareça simultaneamente nos conjuntos de treinamento e teste. |
| RNF04 | Reprodutibilidade | Os procedimentos de preparação, treinamento e avaliação deverão registrar suas configurações, versões e sementes aleatórias. |
| RNF05 | Separação de responsabilidades | O treinamento dos modelos deverá ocorrer offline, sem execução durante as requisições da API. |
| RNF06 | Manutenibilidade | Os módulos deverão possuir responsabilidades delimitadas, evitando duplicação de código e abstrações desnecessárias. |
| RNF07 | Acessibilidade | A interface deverá possuir navegação por teclado, identificação dos campos e contraste adequado. |
| RNF08 | Responsividade | A aplicação deverá funcionar em diferentes tamanhos de tela. |
| RNF09 | Tratamento de falhas | Mensagens de erro não deverão expor stack traces ou informações internas desnecessárias. |
| RNF10 | Reprodutibilidade do ambiente | A instalação deverá ser documentada e utilizar um ambiente virtual e um arquivo centralizado de dependências. |

## 13. Critérios iniciais de aceitação

O sistema deverá atender aos seguintes critérios para ser considerado funcional:

- Receber uma estrutura SMILES válida e uma temperatura.
- Rejeitar estruturas moleculares inválidas.
- Converter corretamente a temperatura de Celsius para Kelvin.
- Calcular os atributos moleculares de maneira consistente.
- Utilizar um pipeline previamente treinado.
- Retornar uma estimativa de LogS (mol/L).
- Informar a versão do modelo e a temperatura utilizada.
- Apresentar avisos sobre as limitações da estimativa.
- Tratar a indisponibilidade do artefato de modelo.
- Apresentar resultados por meio de uma interface web funcional.

A validação científica dependerá adicionalmente da auditoria dos dados, da prevenção de vazamento entre conjuntos e da avaliação dos modelos por métricas estatísticas.

Não será estabelecido um valor mínimo de desempenho como condição antecipada de aceitação.

Os critérios serão verificados por meio de testes automatizados e testes integrados, além da análise dos resultados científicos reais.


---

**Equipe:** Wendel, Erika e Gabriel.

**Data prevista para entrega:** 01/12/2026.
