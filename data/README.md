
# Dados do Projeto — BigSolDB 2.0

## 1. Origem dos dados

O projeto utiliza como fonte prioritária de dados experimentais o BigSolDB 2.0, uma base pública de valores de solubilidade de compostos orgânicos em diferentes solventes e temperaturas.

**Nome:** BigSolDB 2.0

**Autores:** Lev Krasnov, Dmitry Malikov, Marina Kiseleva, Sergei Tatarin e Stanislav Bezzubov.

**Repositório:** Zenodo.

**DOI:** https://doi.org/10.5281/zenodo.15094979

**Página de obtenção:** https://zenodo.org/records/15094979

**Publicação científica:** https://doi.org/10.1038/s41597-025-05559-8

**Data de publicação do registro:** 27/03/2025.

**Versão utilizada:** BigSolDB 2.0.

O projeto deverá utilizar a versão 2.0 especificada acima, sem substituí-la automaticamente por versões posteriores.

## 2. Referência bibliográfica

KRASNOV, Lev; MALIKOV, Dmitry; KISELEVA, Marina; TATARIN, Sergei; SOSNIN, Sergey; BEZZUBOV, Stanislav.

BigSolDB 2.0, dataset of solubility values for organic compounds in different solvents at various temperatures.

Scientific Data, v. 12, artigo 1236, 2025.

DOI: https://doi.org/10.1038/s41597-025-05559-8

A publicação deverá ser citada nos trabalhos acadêmicos que utilizarem os dados.

## 3. Características gerais da base

De acordo com a descrição original, o BigSolDB 2.0 contém:

- 103.944 registros experimentais de solubilidade.
- 1.448 compostos orgânicos.
- 213 solventes.
- 1.595 artigos científicos revisados por pares.

Esses valores representam a base completa, não o subconjunto selecionado para o projeto.

Os registros apresentam informações sobre estruturas moleculares, temperaturas, solventes, valores experimentais de solubilidade e referências das fontes originais.

## 4. Arquivos disponibilizados

O registro do Zenodo disponibiliza dois arquivos CSV relevantes.

| Arquivo | Descrição | Tamanho informado |
|---|---|---|
| BigSolDBv2.0.csv | Dados experimentais de solubilidade | 18,3 MB |
| BigSolDBv2.0_densities.csv | Densidades dos solventes utilizadas nos recálculos | 120 KB |

### 4.1. Arquivo principal

O arquivo `BigSolDBv2.0.csv` contém as seguintes colunas:

| Coluna | Descrição |
|---|---|
| SMILES_Solute | Estrutura molecular do composto dissolvido. |
| Temperature_K | Temperatura da medição em Kelvin. |
| Solvent | Nome do solvente. |
| SMILES_Solvent | Estrutura molecular do solvente. |
| Solubility(mole_fraction) | Solubilidade expressa em fração molar. |
| Solubility(mol/L) | Solubilidade recalculada em mol/L. |
| LogS(mol/L) | Logaritmo decimal da solubilidade recalculada em mol/L. |
| Compound_Name | Nome do composto. |
| CAS | Identificador CAS. |
| PubChem_CID | Identificador PubChem. |
| FDA_Approved | Indicação de aprovação do composto pela FDA. |
| Source | DOI da publicação que originou o registro experimental. |

### 4.2. Arquivo de densidades

O arquivo `BigSolDBv2.0_densities.csv` contém:

| Coluna | Descrição |
|---|---|
| Solvent | Nome do solvente. |
| Temperature_K | Temperatura da densidade em Kelvin. |
| Density_g/cm^3 | Densidade do solvente em g/cm³. |
| Source | DOI da fonte dos valores de densidade. |

### 4.3. Observação sobre a variável-alvo

A coluna `LogS(mol/L)` não corresponde diretamente aos valores de fração molar publicados nos artigos originais.

Segundo os autores, os valores de `Solubility(mol/L)` e `LogS(mol/L)` foram recalculados a partir da coluna `Solubility(mole_fraction)`, utilizando informações de densidade dos solventes disponíveis no arquivo complementar.

Essa distinção deverá ser considerada na interpretação dos resultados científicos.

## 5. Versão e controle de integridade

A versão de referência do projeto é o registro específico BigSolDB 2.0, identificado pelo DOI:

`10.5281/zenodo.15094979`

O Zenodo apresenta os seguintes checksums MD5 para os arquivos da versão consultada:

| Arquivo | MD5 informado pelo Zenodo |
|---|---|
| BigSolDBv2.0.csv | `1e6d8a510387746e9faab5f39dc46317` |
| BigSolDBv2.0_densities.csv | `059ae2deadb2ad1523fd4e24b2c88133` |

Esses valores servem como referência para conferência dos arquivos baixados.

### 5.2. Registro de obtenção

| Informação | Registro |
|---|---|
| Data de obtenção | 09/11/2026 |
| Versão | BigSolDB 2.0 |
| SHA-256 do arquivo principal | 879f55f39db977e295c705e304d011d89d6e10da1daaa3f069181108c1de38b0 |
| SHA-256 do arquivo de densidades | 02226420d9fb3294cb32211dac7f6ff7fa067511924afdb9f1893af1e334aac6|
| Integrante responsável pela obtenção | Erika |

## 6. Licença e condições de utilização

A publicação científica associada ao BigSolDB 2.0 declara licença Creative Commons Attribution 4.0 International (CC BY 4.0).

**Estado da verificação:** Confirmado. A licença consta nos metadados do conjunto de dados,
e não apenas na publicação científica.

## 7. Procedimento para obtenção dos dados

1. Acessar o registro oficial do BigSolDB 2.0 no Zenodo.
2. Conferir o identificador DOI e a versão do registro.
3. Obter os arquivos `BigSolDBv2.0.csv` e `BigSolDBv2.0_densities.csv`.
4. Salvar os arquivos no diretório local `data/raw/`.
5. Registrar a data de obtenção.
6. Calcular os hashes SHA-256.
7. Conferir os MD5 com os valores apresentados no registro.
8. Documentar eventuais divergências.

Comandos para conferir os arquivos após o download:

```bash
sha256sum data/raw/BigSolDBv2.0.csv

sha256sum data/raw/BigSolDBv2.0_densities.csv
```

Para conferir os MD5:

```bash
md5sum data/raw/BigSolDBv2.0.csv

md5sum data/raw/BigSolDBv2.0_densities.csv
```

## 8. Organização e versionamento

Os arquivos de dados originais não deverão ser versionados no Git por padrão.

O diretório local deverá seguir a organização:

```text
data/
│
├── README.md
│
└── raw/
    ├── BigSolDBv2.0.csv
    └── BigSolDBv2.0_densities.csv
```

O `.gitignore` deverá impedir o envio automático dos arquivos armazenados em `data/raw/`.

O arquivo `data/README.md` deverá permanecer versionado, pois contém as informações necessárias para identificar e obter os dados.

## 9. Referências

- Zenodo — BigSolDB 2.0: https://doi.org/10.5281/zenodo.15094979
- Scientific Data — Publicação original: https://doi.org/10.1038/s41597-025-05559-8
- Creative Commons — CC BY 4.0: https://creativecommons.org/licenses/by/4.0/

---

**Projeto:** Predição de Solubilidade em Metanol.

**Versão de dados definida:** BigSolDB 2.0.

**Responsável pela documentação e obtenção dos dados:** Erika.