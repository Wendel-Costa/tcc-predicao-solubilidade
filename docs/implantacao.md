# Implantação — FastAPI + RDKit + Ridge + frontend (C31–C35)

## Objetivo e arquitetura

Publicar uma só aplicação FastAPI, incluindo `/frontend/`, `/api/predict`, `/api/health`, `/api/model-info` e `/docs`. O navegador utiliza `fetch('/api/predict')` na mesma origem, sem configurar CORS. A aplicação apenas carrega o pipeline congelado do C23 e **não treina em produção**.

**Opção recomendada:** Render Web Service com Docker. Railway com Docker é alternativa. Vercel suporta FastAPI/Python, mas seu runtime de funções exige uma verificação específica de dependências nativas, empacotamento e inicialização; não é a configuração principal entregue aqui.

## Pré-requisitos e integridade

O arquivo `artifacts/ridge-v1.joblib` **não está presente em um clone novo**: `.gitignore` o exclui por padrão. O Dockerfile espera esse binário no contexto de build. O arquivo `artifacts/ridge-v1.metadata.json` já está versionado.

Somente utilize o Joblib original **gerado pela equipe e confiável**, após avaliar permissões de redistribuição do artefato derivado do BigSolDB. Para uma implantação pública baseada no GitHub, a opção direta é **versionar conscientemente só esse arquivo**, após autorização e revisão; isso não é obrigatório para desenvolvimento local. Se a distribuição pública não for autorizada, **não o adicione** e não faça o deploy desse pacote; utilize solução privada de entrega do artefato ou mantenha a demonstração local.

Antes de qualquer inclusão no Git:

```bash
sha256sum artifacts/ridge-v1.joblib
python -m app.predictor
```

Hash do artefato C23, imutável:

```text
f362ca5d4b01e834901bb446a5029b1f9fb7a1636c7e87374dfd1fbb5e96bf5f
```

O SHA-256 confirma identidade de bytes, **não assegura autenticidade**. Joblib utiliza desserialização potencialmente executável; jamais carregue arquivos de origem desconhecida. `requirements-deploy.txt` contém as mesmas versões de NumPy, Pandas, RDKit, scikit-learn e Joblib registradas no C23. O Dockerfile usa Python 3.14.8; o carregador compara versão Python principal/secundária e versões exatas das bibliotecas.

**Nunca versione** `data/raw/`, `data/processed/`, tokens, `.env` nem CSVs experimentais. Não altere metadados ou modelo para contornar divergências.

## Teste com Docker no Fedora (antes de publicar)

O Docker precisa estar instalado e habilitado localmente. Para testar:

```bash
docker build -t tcc-metanol:final .
docker run --rm -p 10000:10000 tcc-metanol:final
```

Em outro terminal:

```bash
python -m scripts.verificar_deploy --url http://127.0.0.1:10000
```

Também abra `http://127.0.0.1:10000/frontend/` e verifique manualmente a interface em largura de celular, navegação por teclado, mensagens de erro e aviso de extrapolação. Se falhar o build por ausência do Joblib, não gere outro modelo usando o teste final; providencie o binário C23 original.

## Publicação no Render — um único serviço

1. Confirme que a equipe autorizou a distribuição pública do artefato pequeno e que a licença dos dados/derivados permite essa distribuição. Não deduza permissão somente por o repositório ser público.
2. Se autorizado, e **somente após conferir o hash**, execute `git add -f artifacts/ridge-v1.joblib`. A regra geral de `.gitignore` continua ativa para outros modelos.
3. Inclua os arquivos de documentação, teste e Docker no mesmo commit de finalização e publique na branch `main` sincronizada.
4. No [Render Dashboard](https://dashboard.render.com/), escolha **New → Blueprint** (Infrastructure as Code) e conecte o repositório `Wendel-Costa/tcc-predicao-solubilidade`. O Render lerá `render.yaml` e construirá a imagem a partir do `Dockerfile`.
5. Confirme o plano gratuito caso disponível (pode ter suspensão por inatividade), o health check `/api/health` e o domínio público gerado. Não marque implantação como bem-sucedida até que o deploy esteja **Live** e health check aprovado.
6. Abra a URL gerada com `/frontend/` e execute, do seu Fedora:

```bash
python -m scripts.verificar_deploy --url https://SEU-SERVICO.onrender.com
```

7. Teste também erros HTTP 422 e resultado de `CCO` a 25 °C; na versão original espera-se aproximadamente `0,1574631425 LogS(mol/L)` (estimativa, não valor experimental). Se aparecer 503, confira logs de compatibilidade e integridade do modelo antes de tentar refazer treinamento.

O filesystem da instância gratuita do Render é efêmero, mas o modelo é empacotado na **imagem Docker**, então ele estará novamente disponível depois de reinicializações. Free web services podem suspender após período de inatividade e demorar para despertar; antes da apresentação à banca, abra o link e teste a predição com antecedência. Não use planos gratuitos como garantia de disponibilidade contínua.

## Vercel e Railway

A Vercel oferece runtime Python com suporte a FastAPI e infraestrutura serverless. Também há suporte a pacotes grandes em modalidade beta; ainda é preciso conferir limites do projeto, binários RDKit e carregamento do `ridge-v1` original. Para usar Vercel, será necessário adaptar a configuração da função e testar cuidadosamente o bundling dos arquivos em `frontend/` e `artifacts/`. **Não presuma que o arquivo `render.yaml` pode ser usado na Vercel.**

O Railway permite deploy de projetos FastAPI com Docker a partir do GitHub. Uma migração normalmente aproveita o mesmo `Dockerfile` e acrescenta ajustes de configuração da plataforma (porta, plano e serviços).

Links oficiais: [Render FastAPI](https://render.com/docs/deploy-fastapi), [Render Blueprints](https://render.com/docs/infrastructure-as-code), [Vercel FastAPI](https://vercel.com/docs/frameworks/backend/fastapi), [Railway FastAPI](https://railway.com/guides/fastapi).

## Diagnóstico de problemas

- **Erro no COPY do Joblib:** o arquivo ainda está excluído do repositório remoto; confirme distribuição autorizada ou use outra entrega privada.
- **HTTP 503 em `/api/health`:** modelo ausente, hash divergente ou versão incompatível.
- **Erro em build do pip:** confira se as versões fixas em `requirements-deploy.txt` possuem wheels compatíveis com a imagem e arquitetura selecionadas. Não relaxe as versões silenciosamente.
- **HTTP 200 com resultado diferente:** não substitua o artefato original sem novo processo científico. Confirme arquivo, hash e versões.
- **503/timeout após inatividade no plano gratuito:** serviço pode estar acordando; teste novamente depois que estiver ativo.
- **JavaScript não carrega:** confirme acesso a `/frontend/app.js`, status 200 e que o site foi aberto via FastAPI, não `file://`.

## Observações acadêmicas

Os valores de desempenho publicados no C30 são de teste retido **por molécula no mesmo BigSolDB**, não validação externa. MAE=0,726303, RMSE=0,923927 e R²=0,255850 no teste final. A aplicação é demonstrativa e não substitui ensaios de solubilidade nem oferece estimativa formal de incerteza. O teste final **não deverá ser repetido** para escolher hiperparâmetros.
