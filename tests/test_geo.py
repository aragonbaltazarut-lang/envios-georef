from envios.geo import distancia_km, zona

OBELISCO = (-34.6037, -58.3816)
ROSARIO = (-32.9468, -60.6393)


def test_distancia_buenos_aires_rosario():
    assert 270 < distancia_km(OBELISCO, ROSARIO) < 290


def test_distancia_a_si_mismo_es_cero():
    assert distancia_km(ROSARIO, ROSARIO) == 0


def test_zonas():
    assert zona(10) == "AMBA"
    assert zona(60) == "AMBA"
    assert zona(61) == "Regional"
    assert zona(400) == "Regional"
    assert zona(1500) == "Larga distancia"
