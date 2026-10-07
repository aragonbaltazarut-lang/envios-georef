"""Del CSV a la base: normaliza cada destino y deja registro de lo que falla."""

import csv
from collections import Counter

from .db import ahora
from .geo import ORIGEN, distancia_km, zona
from .georef import GeorefError, buscar_localidad


def localidad(conn, nombre, provincia, buscar):
    """Busca primero en la base y consulta la API solo la primera vez."""
    clave = f"{nombre.strip().lower()}|{provincia.strip().lower()}"
    fila = conn.execute("SELECT * FROM localidades WHERE clave = ?", (clave,)).fetchone()
    if fila:
        return dict(fila)
    loc = buscar(nombre, provincia)
    if loc:
        conn.execute(
            "INSERT INTO localidades VALUES (:clave, :georef_id, :localidad, :provincia, :lat, :lon)",
            {"clave": clave, **loc},
        )
    return loc


def abrir_incidencia(conn, envio_id, tipo, detalle):
    """Abre una incidencia, salvo que ya haya una igual sin resolver."""
    abierta = conn.execute(
        "SELECT 1 FROM incidencias WHERE envio_id = ? AND tipo = ? AND resuelta = 0",
        (envio_id, tipo),
    ).fetchone()
    if not abierta:
        conn.execute(
            "INSERT INTO incidencias (envio_id, tipo, detalle, creada) VALUES (?, ?, ?, ?)",
            (envio_id, tipo, detalle, ahora()),
        )


def importar(conn, ruta_csv, buscar=buscar_localidad):
    """Carga los envíos del CSV. Se puede correr dos veces sobre el mismo archivo.

    Un envío cuyo destino no se pudo normalizar se guarda igual, sin distancia
    ni zona, y queda una incidencia abierta: así no se pierde y se ve qué falta.
    Cuando una corrida posterior lo normaliza, sus incidencias se cierran solas.
    """
    resumen = Counter()
    with open(ruta_csv, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            envio = {
                "id": fila["id"],
                "cliente": fila["cliente"],
                "localidad": fila["localidad"],
                "provincia": fila["provincia"],
                "peso_kg": float(fila["peso_kg"]),
                "distancia_km": None,
                "zona": None,
                "actualizado": ahora(),
            }
            try:
                loc = localidad(conn, fila["localidad"], fila["provincia"], buscar)
            except GeorefError as e:
                abrir_incidencia(conn, envio["id"], "api_caida", str(e))
                resumen["con incidencia"] += 1
                loc = None
            else:
                if loc is None:
                    abrir_incidencia(
                        conn, envio["id"], "localidad_no_encontrada",
                        f"{fila['localidad']}, {fila['provincia']}",
                    )
                    resumen["con incidencia"] += 1

            if loc:
                km = distancia_km(ORIGEN, (loc["lat"], loc["lon"]))
                envio.update(
                    localidad=loc["localidad"], provincia=loc["provincia"],
                    distancia_km=round(km, 1), zona=zona(km),
                )
                conn.execute(
                    "UPDATE incidencias SET resuelta = 1 WHERE envio_id = ? AND resuelta = 0",
                    (envio["id"],),
                )
                resumen["normalizados"] += 1

            conn.execute(
                """
                INSERT INTO envios (id, cliente, localidad, provincia, peso_kg,
                                    distancia_km, zona, actualizado)
                VALUES (:id, :cliente, :localidad, :provincia, :peso_kg,
                        :distancia_km, :zona, :actualizado)
                ON CONFLICT (id) DO UPDATE SET
                    cliente = excluded.cliente, localidad = excluded.localidad,
                    provincia = excluded.provincia, peso_kg = excluded.peso_kg,
                    distancia_km = excluded.distancia_km, zona = excluded.zona,
                    actualizado = excluded.actualizado
                """,
                envio,
            )
    conn.commit()
    return resumen
