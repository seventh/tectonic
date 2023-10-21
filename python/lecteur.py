#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import getopt
import sys

from tectonic.fichier1 import Lecteur
from tectonic.serial2 import Codec


def charger_configuration():
    lots = list()

    opts, args = getopt.getopt(sys.argv[1:], "f:")
    for opt, val in opts:
        if opt == "-f":
            lots.append(val)
    codes = [int(c) for c in args]

    return codes, lots


def afficher(codes, lots):
    codec = Codec()

    affichage = False
    for code in codes:
        grille = codec.décoder(code)
        if affichage:
            print("")
        print(grille)
        affichage = True

    for lot in lots:
        lecteur = Lecteur(lot)
        for code in lecteur:
            grille = codec.décoder(code)
            if affichage:
                print("")
            print(grille)
            affichage = True


if __name__ == "__main__":
    CODES, LOTS = charger_configuration()

    afficher(CODES, LOTS)
