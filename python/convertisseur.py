#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convertit une sauvegarde d'un format à un autre.

Dans un premier temps, celui-ci ne sait réaliser que la conversion du
format 1 au 2.

Format n°1 : informations de grille + informations de bordure
Format n°2 : informations de grille
"""

import sys

from tectonic.serial2 import Codec
from tectonic.fichier1 import Lecteur
from tectonic.fichier1 import Écrivain


def convertir(chemin):
    """Produit un fichier suffixé «.out» contenant les conversions ligne à ligne
    """
    entrée = Lecteur(chemin)
    sortie = Écrivain(chemin + ".out")

    codec = Codec()
    for ancien_code in entrée:
        # Cette ligne fonctionne, car l'ancien encodage ajoutait des
        # informations qui ne sont plus lues.
        grille = codec.décoder(ancien_code)
        code_actuel = codec.encoder(grille)
        sortie.ajouter(str(code_actuel))

        # Le temps de valider que le format n°2 est réellement
        # rétro-compatible…
        # assert codec.décoder(code_actuel) == grille


if __name__ == "__main__":
    for CHEMIN in sys.argv[1:]:
        print(f"Traitement de {CHEMIN}… ", end="")
        convertir(CHEMIN)
        print("achevé")
