#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import getopt
import sys

import serial


def charger_configuration():
    lots = list()
    codes = list()

    opts, args = getopt.getopt(sys.argv[1:], "f:")
    for opt, val in opts:
        if opt == "-f":
            lots.push(val)

    codes[:] = [int(c) for c in args]

    return codes, lots


def afficher_code(code):
    grille = serial.décoder(code)
    print("")
    print(grille)


def lire(chemin):
    with open(chemin, "rt") as entrée:
        for ligne in entrée:
            code = int(ligne.strip())
            afficher_code(code)


if __name__ == "__main__":
    CODES, LOTS = charger_configuration()

    for CODE in CODES:
        afficher_code(CODE)
    for LOT in LOTS:
        lire(LOT)
