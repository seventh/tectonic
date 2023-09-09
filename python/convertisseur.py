#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Convertit une sauvegarde d'un format à un autre.

Dans un premier temps, celui-ci ne sait réaliser que la conversion du
format 1 au 2.

Format n°1 : informations de grille + informations de bordure
Format n°2 : informations de grille
"""

import sys

import serial


def convertir(chemin):
    """Produit un fichier suffixé «.out» contenant les conversions ligne à ligne
    """
    chemin_sortie = chemin + ".out"
    with (open(chemin, "rt") as entrée,
          open(chemin_sortie, "wt") as sortie):
        for ligne in entrée:
            ancien_code = int(ligne.strip())
            # Cette ligne fonctionne, car l'ancien encodage ajoutait des
            # informations qui ne sont plus lues.
            grille = serial.décoder(ancien_code)
            code_actuel = serial.encoder(grille)
            sortie.write(str(code_actuel) + "\n")

            # Le temps de valider que le format n°2 est réellement
            # rétro-compatible…
            # assert serial.décoder(code_actuel) == grille


if __name__ == "__main__":
    for CHEMIN in sys.argv[1:]:
        print(f"Traitement de {CHEMIN}… ", end="")
        convertir(CHEMIN)
        print("achevé")
