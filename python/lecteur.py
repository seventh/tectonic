#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import getopt
import sys

from tectonic.fichier1 import Lecteur
from tectonic.serial2 import Codec


class Configuration:
    def __init__(self):
        self.codes = list()
        self.lots = list()
        self.debug = False
        self.saut_requis = False

    def afficher(self):
        codec = Codec()

        for code in self.codes:
            grille = codec.décoder(code)
            self.afficher_grille(grille)

        for lot in self.lots:
            lecteur = Lecteur(lot)
            for code in lecteur:
                grille = codec.décoder(code)
                self.afficher_grille(grille)

    def afficher_grille(self, grille):
        if self.saut_requis:
            print("")
        if self.debug:
            print(repr(grille))
        else:
            print(grille)
        self.saut_requis = True


def charger_configuration():
    retour = Configuration()

    opts, args = getopt.getopt(sys.argv[1:], "f:g")
    for opt, val in opts:
        if opt == "-f":
            retour.lots.append(val)
        elif opt == "-g":
            retour.debug = True
    retour.codes[:] = [int(c) for c in args]

    return retour


if __name__ == "__main__":
    CONF = charger_configuration()
    CONF.afficher()
