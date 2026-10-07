"""La base SQLite: envíos, localidades ya consultadas e incidencias."""

import sqlite3
from datetime import datetime, timezone

ESQUEMA = """
CREATE TABLE IF NOT EXISTS localidades (
    clave      TEXT PRIMARY KEY,  -- 'localidad|provincia' tal como vino en el CSV
    georef_id  TEXT NOT NULL,
    localidad  TEXT NOT NULL,
    provincia  TEXT NOT NULL,
    lat        REAL NOT NULL,
    lon        REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS envios (
    id            TEXT PRIMARY KEY,
    cliente       TEXT NOT NULL,
    localidad     TEXT NOT NULL,
    provincia     TEXT NOT NULL,
    peso_kg       REAL NOT NULL,
    estado        TEXT NOT NULL DEFAULT 'pendiente',
    distancia_km  REAL,           -- NULL mientras el destino no se pudo normalizar
    zona          TEXT,
    actualizado   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS incidencias (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    envio_id  TEXT NOT NULL REFERENCES envios(id),
    tipo      TEXT NOT NULL,      -- 'api_caida' | 'localidad_no_encontrada'
    detalle   TEXT NOT NULL,
    creada    TEXT NOT NULL,
    resuelta  INTEGER NOT NULL DEFAULT 0
);
"""


def conectar(ruta="envios.db"):
    conn = sqlite3.connect(ruta, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(ESQUEMA)
    return conn


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
