"""Las pruebas corren sin API (modo simulado) y escriben registro y estado en carpetas temporales."""
import os

os.environ["LLM_PROVEEDOR"] = "simulado"

import pytest  # noqa: E402

from src import config  # noqa: E402


@pytest.fixture(autouse=True)
def carpetas_temporales(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "REGISTRO", tmp_path / "eventos.jsonl")
    monkeypatch.setattr(config, "ESTADO", tmp_path / "estado")
