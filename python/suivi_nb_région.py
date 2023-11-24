#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import getopt

from tectonic.fichier1 import Lecteur
from tectonic.serial2 import Codec


class Configuration:
    def __init__(self):
        self.codes = list()
        self.lots = list()

    @staticmethod
    def charger():
        retour = Configuration()
        opts, args = getopt.getopt(sys.argv[1:], "f:")
        for opt, val in opts:
            if opt == "-f":
                retour.lots.append(val)
        retour.codes[:] = [int(x) for x in args]

        return retour


def déterminer_nb_régions(conf):
    nb_régions = dict()
    codec = Codec()
    for code in conf.codes:
        grille = codec.décoder(code)
        n = grille.nb_régions()
        nb_régions[n] = nb_régions.get(n, 0) + 1

    for lot in conf.lots:
        lecteur = Lecteur(lot)
        for code in lecteur:
            grille = codec.décoder(code)
            n = grille.nb_régions()
            nb_régions[n] = nb_régions.get(n, 0) + 1

    for n in sorted(nb_régions):
        print(f"{n} régions : {nb_régions[n]}")


if __name__ == "__main__":
    CONF = Configuration.charger()
    déterminer_nb_régions(CONF)
