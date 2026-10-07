# envios-georef

> Proyecto de aprendizaje: mi primer acercamiento a Python, FastAPI y SQLite.

Una integración chica para envíos a cualquier punto de la Argentina. Toma envíos de un CSV y normaliza cada destino contra la [API Georef](https://datosgobar.github.io/georef-ar-api/) del Estado argentino. Después calcula la distancia desde el kilómetro cero de las rutas nacionales (Plaza del Congreso, CABA), asigna una zona de entrega y guarda todo en SQLite para sacar reportes con SQL. Los transportistas avisan los cambios de estado por un webhook.

Los datos de `datos/envios_ejemplo.csv` son inventados.

## Qué hace

- **Consume una API REST pública** con timeout y reintentos con espera creciente. Solo reintenta lo que puede andar en un segundo intento: la red caída o un error 5xx. Un 4xx es un pedido mal armado y no se reintenta.
- **Guarda las respuestas en caché** en la base: cada localidad se consulta una sola vez, aunque aparezca en cien envíos.
- **Registra lo que falla en vez de frenar.** Si la API se cae o no encuentra un destino, el envío se guarda igual y queda una incidencia abierta. En la corrida siguiente, si ya se puede normalizar, la incidencia se cierra sola.
- **Se puede correr dos veces.** Reimportar el mismo archivo actualiza los envíos y no duplica ni envíos ni incidencias.
- **Reportes en SQL**: envíos y kilos por zona, por provincia y por estado, e incidencias abiertas.
- **API con FastAPI**: consultar un envío, ver las incidencias abiertas y recibir el webhook de cambio de estado. Ese webhook valida el estado y rechaza los que no conoce.

## Cómo correrlo

Necesita Python 3.11 o más nuevo.

```bash
python -m venv .venv
.venv\Scripts\activate          # en Linux o macOS: source .venv/bin/activate
pip install -r requirements.txt

python -m envios importar datos/envios_ejemplo.csv
python -m envios reporte
```

```
11 normalizados, 1 con incidencia

Envíos por zona

zona             envios  kg     km_promedio
---------------  ------  -----  -----------
AMBA             3       79.8   30.0
Regional         3       45.5   313.0
Larga distancia  5       100.5  883.0
...

Incidencias abiertas

envio_id  cliente    tipo                     detalle
--------  ---------  -----------------------  ------------------------
ENV-0011  Cliente C  localidad_no_encontrada  Villa Inventada, Córdoba
```

La API:

```bash
uvicorn envios.api:app --reload
# http://127.0.0.1:8000/docs tiene la documentación interactiva

curl -X POST http://127.0.0.1:8000/webhooks/estado \
     -H "Content-Type: application/json" \
     -d '{"envio_id": "ENV-0001", "estado": "en_transito"}'
```

Los tests usan una API falsa, así que no salen a internet:

```bash
pytest
```

## Cómo está armado

| Archivo | Qué hace |
| --- | --- |
| `envios/georef.py` | El cliente de la API Georef: arma el pedido, reintenta y devuelve la localidad normalizada. |
| `envios/geo.py` | La distancia entre dos puntos (fórmula de haversine) y la zona según los kilómetros. |
| `envios/db.py` | El esquema SQLite: `envios`, `localidades` (la caché) e `incidencias`. |
| `envios/importar.py` | Del CSV a la base: normaliza, calcula, guarda y abre o cierra incidencias. |
| `envios/reportes.py` | Las consultas SQL de los reportes. |
| `envios/api.py` | La API HTTP y el webhook. |
| `tests/` | 11 tests: distancias, importación con la API caída y webhook. |

Las zonas se miden en línea recta desde el kilómetro cero: AMBA hasta 60 km, Regional hasta 400 km y Larga distancia más allá. Para medir desde un depósito propio alcanza con cambiar `ORIGEN` en `envios/geo.py`.

---

Desarrollado con Claude Code como asistente de programación.
