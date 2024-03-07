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


class Chercheur:

    def __init__(self, conf):
        self.conf = conf

    def trouver(self):
        base = self.conf.base()

        producteurs = list()
        enregistreurs = list()
        for palier in range(base.nb_cases() + 1):
            progrès = Progrès(base.hauteur, base.largeur, base.maximum, palier)

            if palier < base.nb_cases():
                producteurs.append(ProducteurProgrès(progrès))

            chemin = os.path.join(self.conf.chemin, str(progrès) + ".gle")
            enregistreurs.append(get_écrivain(chemin, base))

        itérateurs = [iter(GénérateurGrilleVide(base))]
        while len(itérateurs) != 0:
            k = len(itérateurs) - 1
            it = itérateurs[-1]
            try:
                # Code appartenent au palier 'k'
                code = next(it)
                if k < len(producteurs):
                    enregistreurs[k].ajouter(code)
                    itérateurs.append(producteurs[k].itérer(code))
                else:
                    grille = producteurs[-1].codec.décoder(code)
                    analyse = Analyseur(grille)
                    for r in analyse.régions.values():
                        if r.est_anormal():
                            break
                    else:
                        logging.info(code)
                        enregistreurs[-1].ajouter(code)
            except StopIteration:
                itérateurs.pop()

        for e in enregistreurs:
            e.clore()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    CONF = Configuration.charger()
    logging.info(CONF)

    CHERCHEUR = Chercheur(CONF)
    CHERCHEUR.trouver()
