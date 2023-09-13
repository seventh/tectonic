# -*- coding: utf-8 -*-
"""Format de fichier

Le format est assez simple pour l'instant :
«
code n°1
code n°2
…
-1

Le marqueur terminal permet d'assurer l'intégrité du contenu.
»
"""

import io
import logging
import sys


def lire(chemin):
    """Lit un fichier de grilles encodées
    """
    retour = list()
    with open(chemin, "rt") as entrée:
        for ligne in entrée:
            code = int(ligne)
            if code == -1:
                break
            retour.append(code)
        else:
            logging.warning("Fin de fichier prématurée")
    return retour


def enregistrer(chemin, codes):
    """Enregistre les grilles encodées dans un fichier

    La marque de fin de fichier est automatiquement ajoutée pour assurer
    l'intégrité du fichier
    """
    with open(chemin, "wt") as sortie:
        for code in codes:
            sortie.write(str(code) + "\n")
        sortie.write("-1\n")


def convertir(chemin):
    """Ajoute une marque de fin de fichier aux fichiers n'en présentant pas
    """
    with open(chemin, "r+t") as fichier:
        taille = -200
        fin = None
        while True:
            fichier.seek(taille, io.SEEK_END)
            fin = fichier.read()
            if fin.count("\n") >= 2:
                break
            else:
                taille *= 2
        lignes = fin.split("\n")
        if lignes[-1] != "-1":
            fichier.write("-1\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for CHEMIN in sys.argv[1:]:
        convertir(CHEMIN)
