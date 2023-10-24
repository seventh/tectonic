#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vérifie si un code identifie une grille en forme normale
"""

import getopt
import logging
import sys

from tectonic.fichier1 import Lecteur
from tectonic.serial2 import Codec


class Configuration:

    def __init__(self):
        self.codes = list()
        self.lots = list()

        self.codec = Codec()

    def afficher(self):
        for code in self.codes:
            self.tester(code)

        for lot in self.lots:
            lecteur = Lecteur(lot)
            for code in lecteur:
                self.tester(code)

    def tester(self, code):
        grille = self.codec.décoder(code)
        grille.normaliser()
        nouveau = self.codec.encoder(grille)
        if nouveau != code:
            self.afficher_code(code)

    def afficher_code(self, code):
        if self.saut_requis:
            print("")
        print(code)
        self.saut_requis = True


def charger_configuration():
    retour = Configuration()

    opts, args = getopt.getopt(sys.argv[1:], "f:")
    for opt, val in opts:
        if opt == "-f":
            retour.lots.append(val)
    retour.codes[:] = [int(c) for c in args]

    return retour


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    CONF = charger_configuration()
    CONF.afficher()
