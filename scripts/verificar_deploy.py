"""Smoke test HTTP de uma implantação existente (sem alterar dados)."""

import argparse
import json
import math
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def chamada(base: str, caminho: str, payload: dict | None = None, timeout: float = 30):
    headers = {"Accept": "application/json"}
    corpo = None
    if payload is not None:
        corpo = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(base.rstrip("/") + caminho, data=corpo, headers=headers, method="POST" if corpo is not None else "GET")
    with urlopen(req, timeout=timeout) as resposta:
        bruto = resposta.read()
        tipo = resposta.headers.get("Content-Type", "")
        return resposta.status, json.loads(bruto) if "json" in tipo else bruto.decode("utf-8")


def executar(base: str, timeout: float = 30) -> None:
    status, pagina = chamada(base, "/frontend/", timeout=timeout)
    assert status == 200 and 'id="predict-form"' in pagina, "Frontend não foi entregue"
    status, health = chamada(base, "/api/health", timeout=timeout)
    assert status == 200 and health.get("model_available") is True, "Health não está pronto"
    assert health.get("model_version") == "ridge-v1", "Versão de modelo inesperada"
    status, info = chamada(base, "/api/model-info", timeout=timeout)
    assert status == 200 and len(info.get("feature_names", [])) == 10, "Metadados indisponíveis"
    status, pred = chamada(base, "/api/predict", {"smiles": "CCO", "temperature_c": 25}, timeout=timeout)
    assert status == 200 and pred.get("model_version") == "ridge-v1", "Predição indisponível"
    assert math.isfinite(pred.get("log_s_mol_l", math.nan)), "Predição não finita"
    assert abs(pred["log_s_mol_l"] - 0.1574631425041294) < 1e-5, "Resultado difere da referência do Ridge original"
    print("PASSOU: frontend, health, metadados e predição CCO/25 °C")
    print("LogS(mol/L):", pred["log_s_mol_l"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="URL base (http://127.0.0.1:8000 ou https://...)")
    parser.add_argument("--timeout", type=float, default=30)
    argumentos = parser.parse_args()
    if not argumentos.url.startswith(("http://", "https://")):
        parser.error("--url precisa começar com http:// ou https://")
    try:
        executar(argumentos.url, argumentos.timeout)
    except (HTTPError, URLError, TimeoutError, AssertionError, ValueError, KeyError, TypeError) as erro:
        print(f"Falha no teste de implantação: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
