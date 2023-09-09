#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

import serial


def lire(chemin):
    with open(chemin, "rt") as entrée:
        for ligne in entrée:
            code = int(ligne.strip())
            grille = serial.décoder(code)
            print("")
            print(grille)


if __name__ == "__main__":
    lire(sys.argv[1])
