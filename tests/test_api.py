import pytest
from fastapi.testclient import TestClient

from envios.api import app, get_conn
from envios.db import ahora, conectar


@pytest.fixture
def cliente(tmp_path):
    conn = conectar(tmp_path / "test.db")
    conn.execute(
        "INSERT INTO envios (id, cliente, localidad, provincia, peso_kg, actualizado) "
        "VALUES ('ENV-1', 'Cliente A', 'Rosario', 'Santa Fe', 10, ?)",
        (ahora(),),
    )
    conn.commit()
    app.dependency_overrides[get_conn] = lambda: conn
    yield TestClient(app)
    app.dependency_overrides.clear()
    conn.close()


def test_ver_envio(cliente):
    respuesta = cliente.get("/envios/ENV-1")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "pendiente"


def test_envio_inexistente(cliente):
    assert cliente.get("/envios/ENV-999").status_code == 404


def test_webhook_cambia_el_estado(cliente):
    respuesta = cliente.post("/webhooks/estado", json={"envio_id": "ENV-1", "estado": "entregado"})
    assert respuesta.status_code == 200
    assert cliente.get("/envios/ENV-1").json()["estado"] == "entregado"


def test_webhook_rechaza_un_estado_desconocido(cliente):
    respuesta = cliente.post("/webhooks/estado", json={"envio_id": "ENV-1", "estado": "perdido"})
    assert respuesta.status_code == 422


def test_webhook_de_un_envio_inexistente(cliente):
    respuesta = cliente.post("/webhooks/estado", json={"envio_id": "ENV-999", "estado": "entregado"})
    assert respuesta.status_code == 404
