#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import getopt

from tectonic.fichier1 import Lecteur
from tectonic.fichier1 import Écrivain
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


def identifier_sorties(nom):
    if nom is None:
        sortie_ok = "log.ok"
        sortie_ko = "log.ko"
    else:
        sortie_ok = nom + ".ok"
        sortie_ko = nom + ".ko"

    return (sortie_ok, sortie_ko)


def filtrer(nom, itérateur):
    nom_ok, nom_ko = identifier_sorties(nom)
    sortie_ok = Écrivain(nom_ok)
    sortie_ko = Écrivain(nom_ko)

    codec = Codec()
    for code in itérateur:
        grille = codec.décoder(code)
        if grille.est_canonique():
            sortie_ok.ajouter(code)
        else:
            sortie_ko.ajouter(code)

    sortie_ko.clore()
    sortie_ok.clore()


if __name__ == "__main__":
    CONF = Configuration.charger()

    if len(CONF.codes) > 0:
        filtrer(None, CONF.codes)

    for LOT in CONF.lots:
        LECTEUR = Lecteur(LOT)
        filtrer(LOT, LECTEUR)
