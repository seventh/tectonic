#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convertit une sauvegarde d'un format à un autre.

Par défaut, réalise la conversion du format n°0 au format n°1.
"""

import getopt
import logging
import sys

from tectonic import fichier_000
from tectonic import fichier_001


class Convertisseur:

    FORMATS = [fichier_000, fichier_001]

    def __init__(self, nid=0, but=1, chemins=list(), suffixe=".out"):
        self.nid = nid
        self.but = but
        self.chemins = chemins
        self.suffixe = suffixe

    @staticmethod
    def charger():
        retour = Convertisseur()
        opts, args = getopt.getopt(sys.argv[1:], "b:n:o:")
        for opt, val in opts:
            if opt == "-o":
                retour.suffixe = val
            else:
                if not val.isdecimal():
                    logging.warning(f"Option «{opt} {val}» ignorée")
                    continue
                else:
                    val = int(val)
                    if not (0 <= val < len(Convertisseur.FORMATS)):
                        logging.warning(f"Option «{opt} {val}» ignorée")
                        continue
                    elif opt == "-b":
                        retour.but = val
                    elif opt == "-n":
                        retour.nid = val
        retour.chemins[:] = args

        retour.lecteur = Convertisseur.FORMATS[retour.nid].Lecteur
        retour.écrivain = Convertisseur.FORMATS[retour.but].Écrivain

        return retour

    def convertir(self, chemin):
        lecteur = self.lecteur(chemin)
        écrivain = self.écrivain(chemin + self.suffixe, lecteur.base)

        for code in lecteur:
            écrivain.ajouter(code)
        écrivain.clore()

    def lancer(self):
        for chemin in self.chemins:
            print(f"Traitement de {chemin}… ", end="")
            self.convertir(chemin)
            print("achevé")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    CONV = Convertisseur.charger()
    CONV.lancer()
