# Implantação — FastAPI + RDKit + Ridge + frontend (Render)

## Estado publicado e arquitetura

**Aplicação pública:** <https://tcc-predicao-solubilidade.onrender.com/frontend/>
**Documentação interativa:** <https://tcc-predicao-solubilidade.onrender.com/docs>
**Health:** <https://tcc-predicao-solubilidade.onrender.com/api/health>
**Model Info:** <https://tcc-predicao-solubilidade.onrender.com/api/model-info>

Implantação no **Render**, usando um único Web Service com **Docker**. O FastAPI entrega o frontend (`/frontend/`) e os endpoints `/api/predict`, `/api/health` e `/api/model-info` na mesma origem. O navegador utiliza `fetch("/api/predict")`, sem necessidade de configurar CORS para esse fluxo. A API **apenas carrega** o Ridge congelado no C23: nunca treina em produção.

A equipe executou `python -m scripts.verificar_deploy --url https://tcc-predicao-solubilidade.onrender.com` e informou que a verificação passou. O teste confirma o funcionamento naquele momento; não equivale a garantia de disponibilidade contínua. A infraestrutura gratuita pode entrar em repouso após inatividade e acordar automaticamente no acesso seguinte.

## Artefato e integridade: Joblib fora do GitHub

O repositório **não contém** `artifacts/ridge-v1.joblib`. O `.gitignore` continua excluindo esse arquivo, enquanto `artifacts/ridge-v1.metadata.json` é versionado. **Não execute `git add -f artifacts/ridge-v1.joblib`** para reproduzir a implantação atual.

O `Dockerfile` publicado reconstrói o binário durante o build usando um **Secret File** do Render que contém a representação Base64 do Joblib original. O BuildKit apresenta o arquivo secreto temporariamente em `/run/secrets/ridge_v1_joblib_b64`; o Dockerfile decodifica o conteúdo, verifica o hash e ajusta as permissões. O `.dockerignore` deve impedir o envio de `*.joblib` e outros arquivos privados ao contexto da imagem.

**SHA-256 esperado do artefato congelado:**

```text
f362ca5d4b01e834901bb446a5029b1f9fb7a1636c7e87374dfd1fbb5e96bf5f
```

A verificação de SHA-256 confirma que os bytes coincidem com o registro da equipe, mas **não autentica o produtor de um arquivo desconhecido**. Joblib utiliza desserialização com potencial de executar código; carregue somente o artefato original proveniente de fonte confiável. O arquivo reconstruído fará parte da **imagem privada** do serviço. **Base64 não é criptografia**, e essa forma de distribuição não elimina as obrigações de licença e atribuição.

Não versione CSVs experimentais (`data/raw/`, `data/processed/`), `.env`, tokens, senhas, arquivos secretos ou o texto Base64. O `ridge_v1_joblib_b64` é um nome de arquivo configurado no painel, **nunca** um arquivo a ser enviado ao GitHub.

## Como configurar o arquivo secreto no Render

1. Na máquina autorizada da equipe, confira a integridade do arquivo original:

   ```bash
   sha256sum artifacts/ridge-v1.joblib
   ```

2. Gere uma cópia textual temporária, com permissões restritas:

   ```bash
   umask 077
   base64 -w 0 artifacts/ridge-v1.joblib > /tmp/ridge_v1_joblib_b64
   printf '\n' >> /tmp/ridge_v1_joblib_b64
   base64 -d /tmp/ridge_v1_joblib_b64 | sha256sum
   ```

3. No [painel do Render](https://dashboard.render.com/), abra o **Web Service** criado para o projeto. Em **Environment → Secret Files**, adicione (ou atualize) o arquivo de nome **exato** `ridge_v1_joblib_b64` e cole **somente** o conteúdo Base64, sem aspas, prompts do terminal ou marcadores Markdown. O valor de Base64 não é uma variável de ambiente comum.
4. Salve e faça uma implantação que **reconstrua a imagem**. Uma simples reinicialização de uma imagem já construída não incorpora mudanças no segredo usado durante o build.
5. Confira nos logs a verificação do checksum e o início do Uvicorn. Se falhar, examine a mensagem **antes** de `exit code: 1`, sem revelar o conteúdo completo do segredo em logs ou chats públicos.

> Após utilizar o arquivo temporário, remova-o com `rm -f /tmp/ridge_v1_joblib_b64` quando não for mais necessário. Se houver outra cópia legítima em local seguro, preserve o Joblib original e seu hash como registro científico, não o Base64 de implantação.

## Implantação e atualizações

O repositório possui `Dockerfile`, `.dockerignore`, `requirements-deploy.txt` e `render.yaml`. O serviço está ligado ao GitHub e utiliza a branch `main`. O arquivo `render.yaml` descreve o serviço Docker e o health check `/api/health`; a configuração real existente no painel do Render também deve ser conferida caso haja alterações.

O container usa **Python 3.14.8**, e o `requirements-deploy.txt` fixa as versões das bibliotecas científicas compatíveis com o C23. O predictor compara as versões informadas nos metadados. **Não modifique o Joblib ou o JSON para contornar incompatibilidades.**

Para uma nova implantação: publique apenas código, documentação e testes autorizados, confira o status do build no Render, verifique que o serviço fica **Live** e rode novamente o teste HTTP abaixo.

## Verificação da aplicação publicada

Na raiz do projeto, com o ambiente Python configurado:

```bash
python -m scripts.verificar_deploy \
  --url https://tcc-predicao-solubilidade.onrender.com
```

A saída positiva observada localmente na implantação foi:

```text
PASSOU: frontend, health, metadados e predição CCO/25 °C
LogS(mol/L): 0.1574631425041294
```

Também é útil abrir o site em celular e conferir formulários, avisos de extrapolação e erros HTTP 422. Não registre SMILES de usuários em logs sem necessidade. O resultado esperado acima é uma **referência técnica para o mesmo `ridge-v1`** e não uma medição experimental.

## Teste Docker (opcional, recomendado)

O BuildKit precisa receber o Secret File também no build local. **O comando antigo `docker build -t ... .` sem segredo não corresponde à configuração atual e deve falhar intencionalmente.**

```bash
umask 077
base64 -w 0 artifacts/ridge-v1.joblib > /tmp/ridge_v1_joblib_b64
printf '\n' >> /tmp/ridge_v1_joblib_b64
DOCKER_BUILDKIT=1 docker build \
  --secret id=ridge_v1_joblib_b64,src=/tmp/ridge_v1_joblib_b64 \
  -t tcc-metanol:final .
docker run --rm -p 10000:10000 tcc-metanol:final
```

Em outro terminal:

```bash
python -m scripts.verificar_deploy --url http://127.0.0.1:10000
```

Se o sistema acusar falta de permissão em `/var/run/docker.sock`, verifique os privilégios locais para Docker ou use Podman configurado adequadamente. Não é obrigatório repetir o teste local depois que o build real do Render e a verificação pública já tiverem sido aprovados. A imagem contém o modelo reconstruído; mantenha controle de acesso ao serviço e à imagem.

## Problemas comuns

| Sintoma | Verificação recomendada |
|---|---|
| `base64: invalid input` | Recriar o arquivo temporário e copiar somente Base64 no Secret File. |
| `sha256sum: ... FAILED` | O conteúdo reconstruído não corresponde ao artefato original; conferir hash e recadastrar segredo. |
| `No such file or directory` em `/run/secrets/` | Confirmar o nome exato do **Secret File**, a disponibilidade no build e reconstruir a imagem. |
| HTTP 503 em `/api/health` | Conferir modelo, metadados, hash e versões do ambiente. |
| Erro `pip` durante o build | Conferir wheels/versões fixadas; não modificar versões silenciosamente. |
| Resposta HTTP 200 com previsão divergente | Conferir binário, hash e versões; não retreinar após observar o teste final. |
| Primeiro acesso demorado | Em plano gratuito, o serviço pode estar acordando automaticamente após inatividade. |
| JS ou CSS ausente | Abrir `/frontend/` pela FastAPI e conferir arquivos estáticos com HTTP 200. |

## Alternativas e limites

A Vercel pode executar FastAPI/Python, mas exige adaptação de build, configuração e empacotamento das bibliotecas científicas; não é o deploy atualmente usado. Railway com Docker é uma alternativa. A publicação no Render não transforma o protótipo em sistema validado para decisões laboratoriais críticas.

## Referências científicas e restrições

- Fonte: BigSolDB 2.0, DOI <https://doi.org/10.5281/zenodo.15094979>.
- Métricas do teste final congelado C30: MAE **0,726303**, RMSE **0,923927**, R² **0,255850**.
- Avaliação realizada por **moléculas não compartilhadas**, mas no **mesmo BigSolDB**; não é validação externa.
- Não repetir a avaliação final retida para selecionar novas versões. Eventuais modelos futuros deverão ser avaliados com novas partições internas apenas do treino e, para alegações externas novas, dados realmente independentes.
- A licença e as condições de redistribuição de artefatos derivados devem ser revisadas separadamente; esconder o Joblib do GitHub não confere autorização de distribuição.

Referências técnicas: [Render — Docker Secrets](https://render.com/docs/docker-secrets), [Render — Environment and Secret Files](https://render.com/docs/configure-environment-variables), [Docker — Build secrets](https://docs.docker.com/build/building/secrets).
