
# ADR-001 — Arquitetura inicial do sistema

## Status

Aceita.

## Data

08/11/2026.

## Contexto

O projeto consiste no desenvolvimento de um protótipo web para estimar a solubilidade de pequenas moléculas orgânicas em metanol, utilizando descritores moleculares e modelos de aprendizado de máquina.

A equipe possui três integrantes e prazo de entrega definido para 01/12/2026.

O sistema precisa permitir o processamento científico dos dados, o treinamento offline de modelos e a disponibilização de estimativas por meio de uma aplicação web.

É necessário manter a arquitetura simples, modular e reproduzível, evitando funcionalidades que não contribuam diretamente para os objetivos do TCC.

## Decisão

Adotar inicialmente uma arquitetura monolítica modular, utilizando Python no backend e tecnologias web nativas no frontend.

### 1. Backend

Utilizar:

- Python.
- FastAPI.
- Pydantic.
- RDKit.
- scikit-learn.

A API será responsável pela validação das requisições, coordenação do processamento químico e execução das predições.

Os módulos internos deverão possuir responsabilidades separadas, evitando concentrar toda a implementação em um único arquivo.

### 2. Frontend

Utilizar exclusivamente:

- HTML.
- CSS.
- JavaScript puro.

Não serão utilizados frameworks frontend como React, Vue ou Angular.

A interface deverá consumir os endpoints da API por meio de requisições HTTP.

A estratégia definitiva de disponibilização dos arquivos do frontend será definida durante a implementação e integração.

### 3. Treinamento offline

O treinamento dos modelos será executado por scripts Python independentes do ciclo de execução da API.

Os scripts serão responsáveis pela preparação dos dados, extração dos atributos, divisão dos conjuntos, treinamento e avaliação.

A API deverá utilizar um pipeline previamente treinado e armazenado.

Não será permitido treinar modelos durante as requisições de predição.

### 4. Consistência do processamento químico

A geração dos descritores deverá possuir uma implementação compartilhada entre o treinamento e a inferência.

A equipe deverá evitar a duplicação da lógica de extração de atributos em scripts e módulos diferentes.

Os nomes, a quantidade e a ordem dos atributos deverão ser consistentes com os utilizados durante o treinamento.

### 5. Armazenamento

Não será utilizado banco de dados.

Os dados experimentais e os arquivos processados serão armazenados localmente, respeitando as condições de uso e redistribuição do BigSolDB.

Os artefatos dos modelos serão armazenados em arquivos locais, acompanhados de metadados sobre sua origem e treinamento.

Arquivos de dados e artefatos binários não deverão ser versionados automaticamente pelo Git.

### 6. Dependências e ambiente

Utilizar ambiente virtual Python com `venv`.

As dependências do projeto serão documentadas em um arquivo centralizado `requirements.txt`.

Novas bibliotecas deverão ser introduzidas somente quando houver justificativa técnica.

### 7. Testes

Utilizar Pytest para testar os módulos científicos e a aplicação.

A API será testada com TestClient.

Os testes deverão contemplar tanto os comportamentos individuais quanto a integração dos componentes.

## Alternativas consideradas

### Arquitetura de microsserviços

Não adotada.

A divisão em múltiplos serviços adicionaria complexidade de comunicação, implantação e manutenção sem uma necessidade concreta para o escopo do MVP.

### Frontend com framework JavaScript

Não adotado.

O projeto não necessita de um framework frontend para implementar as funcionalidades previstas.

HTML, CSS e JavaScript são suficientes para o protótipo.

### Banco de dados

Não adotado.

O sistema não possui requisitos de persistência de usuários ou histórico de predições.

Os arquivos locais são suficientes para armazenar os dados e o artefato do modelo.

### Treinamento durante as requisições

Não adotado.

O treinamento é um procedimento experimental offline. A API deverá executar somente a inferência utilizando modelos previamente treinados.

## Consequências

### Benefícios

- Arquitetura mais simples de implementar e manter.
- Menor quantidade de dependências.
- Separação entre experimentação científica e utilização da aplicação.
- Facilidade de reprodução dos experimentos.
- Menor complexidade de implantação.
- Responsabilidades mais claras entre os integrantes.

### Limitações

- O sistema dependerá da disponibilidade local do artefato treinado.
- Alterações no pipeline poderão exigir um novo treinamento.
- A arquitetura não foi projetada para escalabilidade distribuída.
- A compatibilidade entre versões do Python e das bibliotecas precisará ser controlada.

## Decisões ainda pendentes

Este registro não define antecipadamente:

- O formato definitivo de serialização do modelo.
- A estratégia final de execução do frontend junto à API.
- A configuração de CORS, caso seja necessária.
- A faixa definitiva de aplicação do modelo.
- A configuração final de treinamento e avaliação.

Essas decisões deverão ser registradas em novos ADRs somente quando houver necessidade concreta.

## Responsáveis

- Wendel: arquitetura e integração.
- Erika: dados e aprendizado de máquina.
- Gabriel: API e frontend.
