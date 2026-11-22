# Checklist da entrega final — C31 a C35 consolidados

Este documento permite registrar uma revisão final sem criar commits separados para cada subtarefa. É uma lista de **verificações a executar**, não uma afirmação de que todas já foram concluídas.

## Código e ciência

- [ ] Conferir a `main` atualizada, sem diferenças locais inesperadas.
- [ ] Confirmar que `ridge-v1` e os metadados são os originais do C23 (SHA-256 documentado).
- [ ] Preservar `reports/avaliacao_final_c30/`: não reavaliar o teste nem selecionar novas variantes com esses resultados.
- [ ] Executar `python -m pytest -q` e registrar data, contagem, aviso e commit.
- [ ] Verificar `python -m app.predictor` e `python -m scripts.verificar_deploy --url http://127.0.0.1:8000`.
- [ ] Revisar `README.md`, `docs/guia-reproducao.md` e `docs/implantacao.md`.

## Acessibilidade e usabilidade (verificação manual)

- [ ] Testar navegação com Tab/Shift+Tab e focos visíveis.
- [ ] Confirmar rótulos, mensagens de erro e status com leitor de tela quando possível.
- [ ] Testar 320 px, 375 px, 768 px e desktop; sem rolagem horizontal inesperada.
- [ ] Testar SMILES inválido, temperatura omitida, temperatura fora da faixa e backend indisponível.
- [ ] Conferir contraste, zoom de 200% e opção de movimento reduzido.
- [ ] Verificar que a página não exibe dados de outros usuários nem armazena histórico de SMILES.

## Publicação e licenças

- [ ] Verificar autorização para redistribuir o binário derivado `ridge-v1.joblib` e as condições de licença do BigSolDB. Se não houver autorização, **não publicar o binário em GitHub**.
- [ ] Definir licença do código com concordância da equipe, caso desejem atribuir uma licença; não presumir que um repositório público é automaticamente open source.
- [ ] Não incluir CSVs, `.env`, tokens ou dados brutos no Git.
- [ ] Testar `docker build` e `docker run` localmente (se Docker disponível).
- [ ] Criar serviço Render e confirmar domínio HTTPS, `/api/health`=200 e predição HTTP 200.
- [ ] Testar o site publicado em tela pequena e verificar logs sem expor entradas químicas.

## Vídeo ou demonstração para a banca

Roteiro recomendado de 3–5 minutos, sem promessa de duração obrigatória:

1. Mostrar o README e mencionar BigSolDB 2.0 e o recorte em metanol.
2. Mostrar o diagrama de arquitetura e explicar frontend → API → RDKit → Ridge.
3. Abrir `/frontend/`, inserir `CCO`, 25 °C e mostrar a estimativa real.
4. Mostrar `C1(` e a mensagem de validação; depois `CCO`, 100 °C e o aviso de extrapolação.
5. Abrir `/api/model-info`, citar validação interna vs teste final. Mostrar MAE 0,726303, RMSE 0,923927 e R² 0,255850, salientando as limitações.
6. Mostrar o resultado da suíte `pytest` e o commit de entrega.

Não afirmar que o modelo é validado universalmente ou adequado para decisões experimentais críticas.
