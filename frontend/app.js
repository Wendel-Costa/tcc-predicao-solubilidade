
"use strict";

// validação básica no navegador.

const formulario = document.getElementById("predict-form");
const smiles = document.getElementById("smiles");
const temperatura = document.getElementById("temperature_c");
const botao = document.getElementById("predict-button");
const estado = document.getElementById("form-status");
const painelErro = document.getElementById("error-panel");
const mensagemErro = document.getElementById("error-message");
const painelResultado = document.getElementById("result-panel");
const painelCarregamento = document.getElementById("loading-state");


function verificarEntradas() {
  const smilesPreenchido = smiles.value.trim().length > 0;
  const textoTemperatura = temperatura.value.trim();

  let temperaturaValida = !temperatura.validity.badInput;

  if (textoTemperatura !== "") {
    const valor = Number(textoTemperatura);

    temperaturaValida = temperaturaValida &&
      Number.isFinite(valor) &&
      valor > -273.15;
  }

  return {
    smilesPreenchido,
    temperaturaValida
  };
}


function atualizarFormulario() {
  const {
    smilesPreenchido,
    temperaturaValida
  } = verificarEntradas();

  // Habilita o botão somente com campos adequados.
  botao.disabled = !(smilesPreenchido && temperaturaValida);

  smiles.setAttribute(
    "aria-invalid",
    String(!smilesPreenchido && smiles.value !== "")
  );

  temperatura.setAttribute(
    "aria-invalid",
    String(!temperaturaValida)
  );

  // Apresenta erros locais sem tentar realizar predições.
  const erroSmiles =
    !smilesPreenchido && smiles.value.length > 0;

  painelErro.hidden = !(erroSmiles || !temperaturaValida);

  mensagemErro.textContent = erroSmiles
    ? "Informe um SMILES não vazio."
    : !temperaturaValida
      ? "A temperatura deve ser numérica e maior que -273,15 °C."
      : "";

  painelResultado.hidden = true;
  painelCarregamento.hidden = true;

  estado.textContent =
    "Verificação local de campos; predição disponível " +
    "somente após a integração com a API.";
}


function enviarFormulario(evento) {
  // Impede o envio real antes da integração.
  evento.preventDefault();

  const {
    smilesPreenchido,
    temperaturaValida
  } = verificarEntradas();

  painelResultado.hidden = true;
  painelCarregamento.hidden = true;

  if (!smilesPreenchido || !temperaturaValida) {
    painelErro.hidden = false;

    mensagemErro.textContent = !smilesPreenchido
      ? "Informe um SMILES não vazio."
      : "Informe uma temperatura numérica acima de " +
        "-273,15 °C ou deixe o campo vazio.";

    (!smilesPreenchido ? smiles : temperatura).focus();

    return;
  }

  painelErro.hidden = true;

  estado.textContent =
    "Campos preenchidos. A validação química completa " +
    "e a predição serão feitas pela API em uma etapa " +
    "posterior (C27).";
}


// O HTML começa com o botão desabilitado.
// No C22, ele será usado apenas para verificar as entradas.

botao.textContent = "Verificar entradas";

smiles.addEventListener(
  "input",
  atualizarFormulario
);

temperatura.addEventListener(
  "input",
  atualizarFormulario
);

formulario.addEventListener(
  "submit",
  enviarFormulario
);

atualizarFormulario();
