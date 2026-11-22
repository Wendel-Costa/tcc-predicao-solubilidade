
"use strict";

// C27: frontend e API compartilham a mesma origem HTTP.
// A validação química definitiva continua no backend com RDKit.

const formulario = document.getElementById("predict-form");
const smiles = document.getElementById("smiles");
const temperatura = document.getElementById("temperature_c");
const botao = document.getElementById("predict-button");
const estado = document.getElementById("form-status");
const painelErro = document.getElementById("error-panel");
const mensagemErro = document.getElementById("error-message");
const painelResultado = document.getElementById("result-panel");
const painelCarregamento = document.getElementById("loading-state");
const resultadoLogS = document.getElementById("result-log-s");
const resultadoTemperaturaC = document.getElementById("result-temperature-c");
const resultadoTemperaturaK = document.getElementById("result-temperature-k");
const resultadoModelo = document.getElementById("result-model-version");
const listaAvisos = document.getElementById("result-warnings");

let enviando = false;
let controladorAtual = null;


function verificarEntradas() {
  const smilesPreenchido = smiles.value.trim().length > 0;
  const textoTemperatura = temperatura.value.trim();
  const valor = Number(textoTemperatura);

  const temperaturaValida = (
    textoTemperatura !== "" &&
    !temperatura.validity.badInput &&
    temperatura.checkValidity() &&
    Number.isFinite(valor) &&
    valor > -273.15
  );

  return { smilesPreenchido, temperaturaValida, valor };
}


function limparResultado() {
  painelResultado.hidden = true;
  resultadoLogS.textContent = "";
  resultadoTemperaturaC.textContent = "";
  resultadoTemperaturaK.textContent = "";
  resultadoModelo.textContent = "";
  listaAvisos.replaceChildren();
}


function mostrarErro(mensagem) {
  painelErro.hidden = false;
  mensagemErro.textContent = mensagem;
  estado.textContent = "Não foi possível calcular a estimativa.";
}


function atualizarFormulario() {
  const { smilesPreenchido, temperaturaValida } = verificarEntradas();

  botao.disabled = enviando || !(smilesPreenchido && temperaturaValida);
  botao.textContent = enviando ? "Calculando..." : "Calcular estimativa";

  smiles.setAttribute(
    "aria-invalid",
    String(smiles.value !== "" && !smilesPreenchido)
  );

  temperatura.setAttribute(
    "aria-invalid",
    String(temperatura.value.trim() !== "" && !temperaturaValida)
  );
}


function entradasAlteradas() {
  // Cancela a requisição anterior para evitar resultado desatualizado.
  if (controladorAtual !== null) {
    controladorAtual.abort();
    controladorAtual = null;
  }

  enviando = false;
  painelCarregamento.hidden = true;
  painelErro.hidden = true;
  mensagemErro.textContent = "";
  limparResultado();

  estado.textContent =
    "Preencha os campos e clique em Calcular estimativa.";

  atualizarFormulario();
}


const formatar = (valor) => new Intl.NumberFormat("pt-BR", {
  maximumFractionDigits: 6,
}).format(valor);


function mostrarResultado(dados) {
  if (
    !dados ||
    !Number.isFinite(dados.log_s_mol_l) ||
    !Number.isFinite(dados.temperature_c) ||
    !Number.isFinite(dados.temperature_k) ||
    typeof dados.model_version !== "string" ||
    !dados.model_version.trim() ||
    dados.solvent !== "methanol" ||
    !Array.isArray(dados.warnings) ||
    !dados.warnings.every((aviso) => typeof aviso === "string")
  ) {
    throw new Error(
      "A API retornou uma resposta de predição inválida."
    );
  }

  resultadoLogS.textContent = formatar(dados.log_s_mol_l);
  resultadoTemperaturaC.textContent =
    formatar(dados.temperature_c) + " °C";
  resultadoTemperaturaK.textContent =
    formatar(dados.temperature_k) + " K";
  resultadoModelo.textContent = dados.model_version;

  listaAvisos.replaceChildren();

  for (const aviso of dados.warnings) {
    const item = document.createElement("li");
    item.textContent = aviso;
    listaAvisos.appendChild(item);
  }

  painelResultado.hidden = false;
  estado.textContent = "Estimativa calculada com sucesso.";
}


async function enviarFormulario(evento) {
  evento.preventDefault();

  if (enviando) return;

  const {
    smilesPreenchido,
    temperaturaValida,
    valor
  } = verificarEntradas();

  limparResultado();

  if (!smilesPreenchido || !temperaturaValida) {
    mostrarErro(
      !smilesPreenchido
        ? "Informe um SMILES não vazio."
        : "Informe uma temperatura numérica acima de -273,15 °C."
    );

    (!smilesPreenchido ? smiles : temperatura).focus();
    atualizarFormulario();
    return;
  }

  painelErro.hidden = true;
  mensagemErro.textContent = "";
  painelCarregamento.hidden = false;
  estado.textContent = "Calculando estimativa...";

  enviando = true;
  const controlador = new AbortController();
  controladorAtual = controlador;

  atualizarFormulario();

  try {
    const resposta = await fetch("/api/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        smiles: smiles.value.trim(),
        temperature_c: valor,
      }),
      signal: controlador.signal,
    });

    let dados;

    try {
      dados = await resposta.json();
    } catch {
      throw new Error(
        "A API retornou uma resposta inválida."
      );
    }

    if (controladorAtual !== controlador) return;

    if (!resposta.ok) {
      const mensagem = (
        typeof dados?.error?.message === "string" &&
        dados.error.message.trim() !== ""
      )
        ? dados.error.message
        : "Não foi possível realizar a predição.";

      throw new Error(mensagem);
    }

    mostrarResultado(dados);

  } catch (erro) {
    if (
      controladorAtual !== controlador ||
      erro.name === "AbortError"
    ) {
      return;
    }

    if (erro instanceof TypeError) {
      mostrarErro(
        "Não foi possível conectar à API. " +
        "Confira se o servidor está funcionando."
      );
    } else {
      mostrarErro(
        erro.message || "Não foi possível realizar a predição."
      );
    }

  } finally {
    if (controladorAtual === controlador) {
      controladorAtual = null;
      enviando = false;
      painelCarregamento.hidden = true;
      atualizarFormulario();
    }
  }
}


smiles.addEventListener("input", entradasAlteradas);
temperatura.addEventListener("input", entradasAlteradas);
formulario.addEventListener("submit", enviarFormulario);

atualizarFormulario();
