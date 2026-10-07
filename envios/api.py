"""API HTTP: consulta de envíos y el webhook por el que avisan los transportistas."""

import os
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from .db import ahora, conectar

app = FastAPI(title="Envíos")


def get_conn():
    conn = conectar(os.environ.get("ENVIOS_DB", "envios.db"))
    try:
        yield conn
    finally:
        conn.close()


class CambioDeEstado(BaseModel):
    envio_id: str
    estado: Literal["pendiente", "en_transito", "entregado", "devuelto"]


@app.get("/envios/{envio_id}")
def ver_envio(envio_id: str, conn=Depends(get_conn)):
    fila = conn.execute("SELECT * FROM envios WHERE id = ?", (envio_id,)).fetchone()
    if not fila:
        raise HTTPException(404, f"No existe el envío {envio_id}")
    return dict(fila)


@app.post("/webhooks/estado")
def cambiar_estado(cambio: CambioDeEstado, conn=Depends(get_conn)):
    """El transportista avisa que un envío cambió de estado."""
    cursor = conn.execute(
        "UPDATE envios SET estado = ?, actualizado = ? WHERE id = ?",
        (cambio.estado, ahora(), cambio.envio_id),
    )
    if cursor.rowcount == 0:
        raise HTTPException(404, f"No existe el envío {cambio.envio_id}")
    conn.commit()
    return {"ok": True, "envio_id": cambio.envio_id, "estado": cambio.estado}


@app.get("/incidencias")
def incidencias_abiertas(conn=Depends(get_conn)):
    filas = conn.execute(
        "SELECT * FROM incidencias WHERE resuelta = 0 ORDER BY creada"
    ).fetchall()
    return [dict(f) for f in filas]
