#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convertit une sauvegarde d'un format à un autre.

Par défaut, réalise la conversion du formats n°1 au format n°2.

Rappel des formats :
1) fichier1 + serial1
2) fichier1 + serial2
3) fichier2 + serial3
"""

import getopt
import logging
import sys

from tectonic import fichier1
from tectonic import fichier2
from tectonic import serial2
from tectonic import serial3


class Convertisseur:

    FORMATS = {
        1: (fichier1, serial2),
        2: (fichier1, serial2),
        3: (fichier2, serial3),
    }

    def __init__(self, nid=1, but=2, chemins=list(), suffixe=".out"):
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
                    if not (1 <= val <= 3):
                        logging.warning(f"Option «{opt} {val}» ignorée")
                        continue
                    elif opt == "-b":
                        retour.but = val
                    elif opt == "-n":
                        retour.nid = val
        retour.chemins[:] = args

        retour.lecteur = Convertisseur.FORMATS[retour.nid][0].Lecteur
        retour.décodeur = Convertisseur.FORMATS[retour.nid][1].Codec
        retour.écrivain = Convertisseur.FORMATS[retour.but][0].Écrivain
        retour.encodeur = Convertisseur.FORMATS[retour.but][1].Codec

        return retour

    def convertir(self, chemin):
        configuré = False
        lecteur = self.lecteur(chemin)
        écrivain = self.écrivain(chemin + self.suffixe)
        for ancien in lecteur:
            if not configuré:
                if hasattr(lecteur, "base"):
                    décodeur = self.décodeur(lecteur.base)
                    écrivain.configurer(lecteur.base)
                    encodeur = self.encodeur(lecteur.base)
                    configuré = True
                else:
                    décodeur = self.décodeur()

            grille = décodeur.décoder(ancien)

            if not configuré:
                écrivain.configurer(grille.base)
                encodeur = self.encodeur(grille.base)
                configuré = True

            nouveau = encodeur.encoder(grille)
            écrivain.ajouter(nouveau)

    def lancer(self):
        for chemin in self.chemins:
            print(f"Traitement de {chemin}… ", end="")
            self.convertir(chemin)
            print("achevé")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    CONV = Convertisseur.charger()
    CONV.lancer()
