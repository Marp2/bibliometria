import random

from src.estructuras_datos import (
    ConjuntoHash, ListaDinamica, Pila, TablaHashSimple, crear_matriz, mediana, menor_de_tres, ordenar_por_mezcla,
    potencia_modular, promedio,
)


def test_lista_dinamica_crece_y_extrae():
    lista = ListaDinamica(1)
    for i in range(100):
        lista.agregar(i)
    assert lista.tamano() == 100 and lista[99] == 99
    assert lista.extraer() == 99 and lista.tamano() == 99


def test_pila_lifo():
    p = Pila()
    p.apilar(1)
    p.apilar(2)
    assert p.desapilar() == 2 and p.desapilar() == 1 and p.esta_vacia()


def test_tabla_hash_con_redimension():
    t = TablaHashSimple(2)
    for i in range(500):
        t.poner("k%d" % i, i)
    assert t.tamano() == 500 and t.obtener("k123") == 123 and not t.contiene("zzz")
    t.poner("k1", 99)
    assert t.obtener("k1") == 99 and t.tamano() == 500


def test_conjunto_hash():
    c = ConjuntoHash()
    for x in "abracadabra":
        c.agregar(x)
    assert c.tamano() == 5 and c.contiene("r") and not c.contiene("z")


def test_matriz_independiente():
    m = crear_matriz(2, 3, 0)
    m[0][0] = 7
    assert m[1][0] == 0  # filas independientes


def test_ordenar_por_mezcla_correcto_y_estable():
    random.seed(3)
    datos = [random.randint(0, 20) for _ in range(300)]
    assert ordenar_por_mezcla(datos) == sorted(datos)
    assert ordenar_por_mezcla(datos, descendente=True) == sorted(datos, reverse=True)
    pares = [(1, "a"), (0, "b"), (1, "c"), (0, "d")]
    assert ordenar_por_mezcla(pares, clave=lambda p: p[0]) == [(0, "b"), (0, "d"), (1, "a"), (1, "c")]  # estable
    assert ordenar_por_mezcla([]) == [] and ordenar_por_mezcla([5]) == [5]


def test_potencia_modular_coincide_con_pow():
    for b, e, m in ((256, 0, 101), (256, 9, 1000000007), (31, 1000, 13), (2, 10, 1000)):
        assert potencia_modular(b, e, m) == pow(b, e, m)


def test_estadisticos():
    assert promedio([1, 2, 3, 4]) == 2.5 and promedio([]) == 0.0
    assert mediana([3, 1, 2]) == 2 and mediana([1, 2, 3, 4]) == 2.5
    assert menor_de_tres(3, 1, 2) == 1
