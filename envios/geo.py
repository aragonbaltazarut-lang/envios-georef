"""Distancias y zonas de entrega, medidas desde un punto de origen."""

from math import asin, cos, radians, sin, sqrt

# El kilómetro cero de las rutas nacionales, en Plaza del Congreso (CABA).
# Para medir desde otro depósito, se cambia acá.
ORIGEN = (-34.6092, -58.3926)

RADIO_TIERRA_KM = 6371


def distancia_km(origen, destino):
    """Distancia en línea recta entre dos puntos (lat, lon), por haversine."""
    lat1, lon1 = map(radians, origen)
    lat2, lon2 = map(radians, destino)
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * RADIO_TIERRA_KM * asin(sqrt(a))


def zona(km):
    """Zona de entrega según la distancia al origen."""
    if km <= 60:
        return "AMBA"
    if km <= 400:
        return "Regional"
    return "Larga distancia"
