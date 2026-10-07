"""Línea de comandos: python -m envios importar <csv> | python -m envios reporte"""

import argparse

from .db import conectar
from .importar import importar
from .reportes import REPORTES, tabla


def main():
    parser = argparse.ArgumentParser(prog="envios")
    parser.add_argument("--db", default="envios.db", help="archivo SQLite (envios.db)")
    sub = parser.add_subparsers(dest="comando", required=True)
    imp = sub.add_parser("importar", help="cargar envíos desde un CSV")
    imp.add_argument("csv")
    sub.add_parser("reporte", help="mostrar los reportes")
    args = parser.parse_args()

    conn = conectar(args.db)
    if args.comando == "importar":
        resumen = importar(conn, args.csv)
        print(", ".join(f"{n} {k}" for k, n in resumen.items()) or "Nada para importar")
    else:
        for titulo, sql in REPORTES.items():
            print(f"\n{titulo}\n")
            print(tabla(conn, sql))


if __name__ == "__main__":
    main()
