"""El importador, con una API falsa: los tests no salen a internet."""

import pytest

from envios.db import conectar
from envios.georef import GeorefError
from envios.importar import importar

CSV = """id,cliente,localidad,provincia,peso_kg
ENV-1,Cliente A,Rosario,Santa Fe,10
ENV-2,Cliente B,Villa Inventada,Córdoba,5
ENV-3,Cliente C,Salta,Salta,2
ENV-4,Cliente A,Rosario,Santa Fe,3
"""

ROSARIO = {"georef_id": "82084270", "localidad": "Rosario", "provincia": "Santa Fe",
           "lat": -32.9472, "lon": -60.6332}
SALTA = {"georef_id": "66028050", "localidad": "Salta", "provincia": "Salta",
         "lat": -24.7859, "lon": -65.4117}


@pytest.fixture
def conn():
    return conectar(":memory:")


@pytest.fixture
def csv_envios(tmp_path):
    ruta = tmp_path / "envios.csv"
    ruta.write_text(CSV, encoding="utf-8")
    return ruta


class ApiFalsa:
    """Responde Rosario, no encuentra Villa Inventada y se cae con Salta."""

    def __init__(self, salta_caida=True):
        self.salta_caida = salta_caida
        self.consultas = []

    def __call__(self, nombre, provincia):
        self.consultas.append(nombre)
        if nombre == "Rosario":
            return ROSARIO
        if nombre == "Salta":
            if self.salta_caida:
                raise GeorefError("Salta, Salta: 503 Service Unavailable")
            return SALTA
        return None


def test_importa_y_registra_incidencias(conn, csv_envios):
    resumen = importar(conn, csv_envios, buscar=ApiFalsa())

    assert resumen == {"normalizados": 2, "con incidencia": 2}
    # Todos los envíos quedan guardados, también los que fallaron.
    assert conn.execute("SELECT COUNT(*) FROM envios").fetchone()[0] == 4
    tipos = {f["envio_id"]: f["tipo"] for f in conn.execute("SELECT * FROM incidencias")}
    assert tipos == {"ENV-2": "localidad_no_encontrada", "ENV-3": "api_caida"}
    rosario = conn.execute("SELECT * FROM envios WHERE id = 'ENV-1'").fetchone()
    assert rosario["zona"] == "Regional"


def test_cada_localidad_se_consulta_una_vez(conn, csv_envios):
    api = ApiFalsa()
    importar(conn, csv_envios, buscar=api)
    assert api.consultas.count("Rosario") == 1


def test_reimportar_no_duplica_y_cierra_lo_resuelto(conn, csv_envios):
    importar(conn, csv_envios, buscar=ApiFalsa(salta_caida=True))
    importar(conn, csv_envios, buscar=ApiFalsa(salta_caida=False))

    assert conn.execute("SELECT COUNT(*) FROM envios").fetchone()[0] == 4
    abiertas = conn.execute(
        "SELECT envio_id FROM incidencias WHERE resuelta = 0"
    ).fetchall()
    # Salta volvió a responder: su incidencia se cerró. Villa Inventada sigue
    # abierta, una sola vez aunque se haya importado dos veces.
    assert [f["envio_id"] for f in abiertas] == ["ENV-2"]
