import json
import shutil

import pytest

from controles.acceso_por_rol import AccesoPorRol
from controles.permisos_herramientas import PermisosHerramientas
from evaluacion.metricas import wilson
from src import config, llm
from src.agente import agente
from src.asistente import responder
from src.clasificador import predecir as modulo_predecir
from src.clasificador.predecir import ModeloAlterado, predecir
from src.rag.recuperador import recuperar
from src.sesion import iniciar_sesion


def sesion(usuario):
    claves = {"cperez": "demo-cperez", "mrojas": "demo-mrojas", "secretaria1": "demo-secret1"}
    return iniciar_sesion(usuario, claves[usuario])


def test_clave_incorrecta_no_inicia_sesion():
    with pytest.raises(PermissionError):
        iniciar_sesion("cperez", "otra-clave")


def test_el_rol_sale_de_la_sesion():
    assert sesion("cperez").rol == "colegiado"
    assert sesion("secretaria1").rol == "personal"


def test_acceso_por_rol_quita_fragmentos_internos_al_colegiado():
    fragmentos = recuperar("criterios internos del Tribunal para sancionar")
    permitidos, descartados = AccesoPorRol().filtrar_fragmentos(fragmentos, sesion("cperez"))
    assert descartados and all(f.nivel == "publico" for f, _ in permitidos)
    _, descartados_personal = AccesoPorRol().filtrar_fragmentos(fragmentos, sesion("secretaria1"))
    assert descartados_personal == []


def test_permisos_fuerzan_el_codigo_de_la_sesion():
    args, motivo = PermisosHerramientas().autorizar_herramienta("consultar_estado", {"colegiado_id": "C-2041"}, sesion("cperez"))
    assert motivo is None and args["colegiado_id"] == "C-1043"


def test_permisos_bloquean_constancia_a_no_habil():
    _, motivo = PermisosHerramientas().autorizar_herramienta("emitir_constancia", {"colegiado_id": "C-1043"}, sesion("cperez"))
    assert motivo and "no está hábil" in motivo
    _, motivo = PermisosHerramientas().autorizar_herramienta("emitir_constancia", {"colegiado_id": "C-2041"}, sesion("mrojas"))
    assert motivo is None


def test_personal_no_emite_constancias():
    _, motivo = PermisosHerramientas().autorizar_herramienta("emitir_constancia", {"colegiado_id": "C-2041"}, sesion("secretaria1"))
    assert motivo


def _agente_que_obedece(monkeypatch):
    """Simula un modelo que obedeció una orden escondida: pide emitir la constancia de C-1043."""
    turnos = iter([
        {"texto": "", "llamadas": [{"id": "1", "nombre": "emitir_constancia", "argumentos": '{"colegiado_id": "C-1043"}'}],
         "mensaje": {"role": "assistant", "content": None, "tool_calls": []}},
        {"texto": "Listo.", "llamadas": [], "mensaje": {"role": "assistant", "content": "Listo."}},
    ])
    monkeypatch.setattr(llm, "conversar", lambda mensajes, herramientas: next(turnos))


def test_sin_control_el_agente_ejecuta_lo_que_pide_el_modelo(monkeypatch):
    _agente_que_obedece(monkeypatch)
    _, traza = agente.ejecutar("constancia", sesion("cperez"), "", controles=())
    assert traza[0]["ejecutada"] is True


def test_con_permisos_la_orden_escondida_se_bloquea(monkeypatch):
    _agente_que_obedece(monkeypatch)
    _, traza = agente.ejecutar("constancia", sesion("cperez"), "", controles=[PermisosHerramientas()])
    assert traza[0]["ejecutada"] is False and traza[0]["bloqueada_por"] == "permisos_herramientas"
    assert not (config.ESTADO / "constancias.jsonl").exists()


def test_clasificador_separa_rutas():
    assert predecir("Necesito mi constancia de habilitación para una licitación")["ruta"] == "automatica"
    assert predecir("Quiero que se levante mi suspensión")["ruta"] == "revision"


def test_modelo_alterado_no_se_carga(tmp_path, monkeypatch):
    copia = tmp_path / "modelo.joblib"
    shutil.copy(config.MODELO_CLASIFICADOR, copia)
    with open(copia, "ab") as f:
        f.write(b"alterado")
    monkeypatch.setattr(config, "MODELO_CLASIFICADOR", copia)
    modulo_predecir._modelo.cache_clear()
    try:
        with pytest.raises(ModeloAlterado):
            predecir("hola")
    finally:
        modulo_predecir._modelo.cache_clear()


def test_el_registro_guarda_la_ingesta_del_adjunto():
    ev = responder("Adjunto mi comprobante, ¿quedó registrado mi pago?", sesion("mrojas"),
                   adjunto={"nombre": "comprobante.txt", "texto": "pago de cuota"})
    linea = json.loads(config.REGISTRO.read_text(encoding="utf-8").splitlines()[-1])
    assert linea["id"] == ev["id"]
    assert linea["adjunto"]["subido_por"] == "mrojas" and len(linea["adjunto"]["sha256"]) == 64
    assert linea["clasificacion"]["clase"]


def test_wilson():
    p, bajo, alto = wilson(10, 20)
    assert p == 0.5 and round(bajo, 3) == 0.299 and round(alto, 3) == 0.701
