"""Reportes operativos, escritos en SQL."""

POR_ZONA = """
SELECT zona,
       COUNT(*)                    AS envios,
       ROUND(SUM(peso_kg), 1)      AS kg,
       ROUND(AVG(distancia_km), 0) AS km_promedio
FROM envios
WHERE zona IS NOT NULL
GROUP BY zona
ORDER BY km_promedio
"""

POR_PROVINCIA = """
SELECT provincia, COUNT(*) AS envios, ROUND(SUM(peso_kg), 1) AS kg
FROM envios
WHERE zona IS NOT NULL
GROUP BY provincia
ORDER BY envios DESC, provincia
"""

POR_ESTADO = """
SELECT estado, COUNT(*) AS envios
FROM envios
GROUP BY estado
ORDER BY envios DESC
"""

INCIDENCIAS_ABIERTAS = """
SELECT i.envio_id, e.cliente, i.tipo, i.detalle, i.creada
FROM incidencias i
JOIN envios e ON e.id = i.envio_id
WHERE i.resuelta = 0
ORDER BY i.creada
"""

REPORTES = {
    "Envíos por zona": POR_ZONA,
    "Envíos por provincia": POR_PROVINCIA,
    "Envíos por estado": POR_ESTADO,
    "Incidencias abiertas": INCIDENCIAS_ABIERTAS,
}


def tabla(conn, sql):
    """Corre la consulta y la devuelve como texto en columnas."""
    cursor = conn.execute(sql)
    columnas = [c[0] for c in cursor.description]
    filas = [[("" if v is None else str(v)) for v in fila] for fila in cursor.fetchall()]
    if not filas:
        return "(sin datos)"
    anchos = [max(len(c), *(len(f[i]) for f in filas)) for i, c in enumerate(columnas)]
    linea = lambda valores: "  ".join(v.ljust(a) for v, a in zip(valores, anchos))
    return "\n".join([linea(columnas), linea(["-" * a for a in anchos]), *map(linea, filas)])
