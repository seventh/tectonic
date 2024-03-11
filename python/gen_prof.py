#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Générateur de grille complète

À la différence du générateur original, celui-ci adopte une approche en
profondeur d'abord.
"""

import dataclasses
import getopt
import logging
import os.path
import sys

from tectonic import Base
from tectonic import Progrès
from tectonic.fichier import écrivain as get_écrivain
from générateur import Analyseur
from générateur import ProducteurProgrès
from générateur import GénérateurGrilleVide


@dataclasses.dataclass
class Configuration:

    hauteur: int = 5
    largeur: int = 4
    maximum: int = 5
    chemin: str = "../data"

    @staticmethod
    def charger():
        retour = Configuration()
        opts, args = getopt.getopt(sys.argv[1:], "h:l:m:")
        for opt, val in opts:
            if not val.isdecimal():
                logging.warning(f"Option «{opt} {val}» ignorée")
                continue
            else:
                val = int(val)
                if opt == "-h" and val > 0:
                    retour.hauteur = val
                elif opt == "-l" and val > 0:
                    retour.largeur = val
                elif opt == "-m" and val > 2:
                    retour.maximum = val
        if len(args) != 0:
            retour.chemin = args[0]

        return retour

    def base(self):
        return Base(hauteur=self.hauteur,
                    largeur=self.largeur,
                    maximum=self.maximum)


class Niveau:

    def __init__(self, producteur):
        self.producteur = producteur

        self.générateur = None
        self.index = -1
        self.code = -1

    def ajouter(self, code):
        pass

    def clore(self):
        pass


class NiveauÀEnregistreur(Niveau):

    def __init__(self, producteur, enregistreur):
        super().__init__(producteur)
        self.enregistreur = enregistreur

    def ajouter(self, code):
        self.enregistreur.ajouter(code)

    def clore(self):
        self.enregistreur.clore()


def construire_chemin(niveaux):
    return ",".join([str(n.index) for n in niveaux])


class Chercheur:

    def __init__(self, conf):
        self.conf = conf

    def trouver(self):
        base = self.conf.base()
        nb_cases = base.nb_cases()

        # Préparation des contexte de production/enregistrement
        # Pour chaque palier :
        #  - un producteur qui permet d'obtenir un itérateur à partir d'un code
        # du palier précédent
        #  - un enregistreur qui mémorise les codes de ce palier
        niveaux = list()
        for palier in range(nb_cases + 1):
            progrès = Progrès(base.hauteur, base.largeur, base.maximum, palier)

            if palier == 0:
                producteur = None
            else:
                producteur = ProducteurProgrès(progrès)

            if palier < base.nb_cases():
                niveau = Niveau(producteur)
            else:
                chemin = os.path.join(self.conf.chemin, str(progrès) + ".log")
                enregistreur = get_écrivain(chemin, base)
                niveau = NiveauÀEnregistreur(producteur, enregistreur)
            niveaux.append(niveau)

        # Pour le palier initial, on produit une grille vide ex-nihilo
        niveaux[0].générateur = enumerate(GénérateurGrilleVide(base))
        k = 0
        while k >= 0:
            it = niveaux[k].générateur
            try:
                # Code appartenent au palier 'k'
                index, code = next(it)
                niveaux[k].index = index
                niveaux[k].code = code

                if k < nb_cases:
                    niveaux[k].ajouter(code)
                    k += 1
                    niveaux[k].générateur = enumerate(
                        niveaux[k].producteur.itérer(code))
                else:
                    grille = niveaux[k].producteur.codec.décoder(code)
                    analyse = Analyseur(grille)
                    for r in analyse.régions.values():
                        if r.est_anormal():
                            break
                    else:
                        niveaux[k].ajouter(code)
                        logging.debug(construire_chemin(niveaux))
            except StopIteration:
                k -= 1

        # Enfin, on finalise tous les fichiers enregistrés
        for n in niveaux:
            n.clore()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    CONF = Configuration.charger()
    logging.info(CONF)

    CHERCHEUR = Chercheur(CONF)
    CHERCHEUR.trouver()
