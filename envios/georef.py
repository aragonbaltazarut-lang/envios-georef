"""Cliente de la API Georef (datos.gob.ar), que normaliza localidades argentinas."""

import time

import requests

URL = "https://apis.datos.gob.ar/georef/api/localidades"


class GeorefError(Exception):
    """La API no respondió bien, ni siquiera después de reintentar."""


def buscar_localidad(nombre, provincia, intentos=3, espera=1.0):
    """Devuelve la localidad normalizada, o None si la API no la encuentra.

    Reintenta solo lo que puede andar en un segundo intento (la red caída,
    un error 5xx). Un 4xx es un pedido mal armado: reintentarlo no sirve.
    """
    params = {
        "nombre": nombre,
        "provincia": provincia,
        "max": 1,
        "campos": "id,nombre,provincia.nombre,centroide",
    }
    for intento in range(1, intentos + 1):
        try:
            respuesta = requests.get(URL, params=params, timeout=10)
            respuesta.raise_for_status()
            datos = respuesta.json()
            break
        except requests.HTTPError as e:
            if e.response.status_code < 500 or intento == intentos:
                raise GeorefError(f"{nombre}, {provincia}: {e}") from e
        except (requests.RequestException, ValueError) as e:
            if intento == intentos:
                raise GeorefError(f"{nombre}, {provincia}: {e}") from e
        time.sleep(espera * 2 ** (intento - 1))

    if not datos["localidades"]:
        return None
    loc = datos["localidades"][0]
    return {
        "georef_id": loc["id"],
        "localidad": loc["nombre"],
        "provincia": loc["provincia"]["nombre"],
        "lat": loc["centroide"]["lat"],
        "lon": loc["centroide"]["lon"],
    }
