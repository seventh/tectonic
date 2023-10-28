#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Charge et résout une grille de Tectonic

Le but n'est pas de faire une recherche brute mais d'utiliser des
techniques habituelles afin d'évaluer la difficulté

https://sudoku.megastar.fr/accueil/techniques-de-tectonic/
"""

import collections
import logging
import getopt
import random
import sys

from tectonic.serial2 import Codec
from tectonic.fichier1 import Lecteur


class CaseNavigable:
    def __init__(self, valeur, région):
        self.région = région
        if valeur > 0:
            self.valeurs = [valeur]
        else:
            self.valeurs = list()

        # Dans les huit directions
        self.voisins = list()


class RégionNavigable:
    """Ensemble des cases d'un bloc
    """
    def __init__(self):
        self.cases = list()

    def __len__(self):
        return len(self.cases)

    def forcés(self):
        """Valeurs fixées
        """
        return set([c.valeur for c in self.cases if c.valeur > 0])

    def libres(self):
        """Valeurs non encore fixées
        """
        return set(range(1, len(self) + 1)).difference(self.forcés())


class GrilleNavigable:
    def __init__(self, grille):
        self.base = grille.base
        self.régions = collections.defaultdict(RégionNavigable)
        self.cases = [None] * len(grille.cases)
        for i, case in enumerate(grille.cases):
            région = self.régions[case.région]
            self.cases[i] = CaseNavigable(case.valeur, région)
            région.cases.append(self.cases[i])

        # Voisinages
        for i, case in enumerate(self.cases):
            h, l = self.base.en_position(i)
            self._ajouter_voisin(case, h + 1, l)
            self._ajouter_voisin(case, h + 1, l + 1)
            self._ajouter_voisin(case, h + 1, l - 1)
            self._ajouter_voisin(case, h, l + 1)
            self._ajouter_voisin(case, h, l - 1)
            self._ajouter_voisin(case, h - 1, l)
            self._ajouter_voisin(case, h - 1, l + 1)
            self._ajouter_voisin(case, h - 1, l - 1)

        # Initialisation des possibles
        for case in self.cases:
            if len(case.valeurs) == 0:
                possibles = set(range(len(case.région)))
                for v in case.voisins:
                    if len(v.valeurs) == 1:
                        possibles.discard(v.valeurs[0])
                for m in case.régions.cases:
                    if m is not case and len(m.valeurs) == 1:
                        possibles.discard(m.valeurs[0])
                case.valeurs[:] = sorted(possibles)

    def _ajouter_voisin(self, case, h, l):
        """Ajoute la case de coordonnées (h, l) aux voisins de la case
        si ces coordonnées sont valides
        """
        if (0 <= h < self.base.hauteur and 0 <= l < self.base.largeur):
            case.voisins.append(self[(h, l)])


class Traitement:
    def __init__(self):
        self.codes = list()
        self.lots = list()

    @staticmethod
    def from_sys_argv():
        retour = Traitement()

        opts, args = getopt.getopt(sys.argv[1:], "f:")
        for opt, val in opts:
            if opt == "-f":
                retour.lots.append(val)
        retour.codes[:] = [int(c) for c in args]

        return retour

    def effectuer(self):
        codec = Codec()

        for code in self.codes:
            grille = codec.décoder(code)
            self.gérer_grille(grille)

        for lot in self.lots:
            lecteur = Lecteur(lot)
            for code in lecteur:
                grille = codec.décoder(code)
                self.gérer_grille(grille)

    def gérer_grille(self, grille):
        # D'abord, on supprime des valeurs
        n = random.randint(1, grille.base.nb_cases() // 2)
        indices = random.sample(range(grille.base.nb_cases()), n)
        for i in indices:
            grille.cases[i].valeur = 0
        logging.info("Grille à résoudre :\n" + str(grille))

        # Maintenant, on cherche à résoudre
        self.résoudre(grille)

    def résoudre(self, grille):
        # Modification du modèle Entité-Association
        grille = GrilleNavigable(grille)

        # On applique itérativement les techniques
        difficulté = -1
        techniques = [self.technique_1_1]
        modification = True
        while modification:
            modification = False
            for i, t in enumerate(techniques):
                if t(self, grille):
                    modification = True
                    if i > difficulté:
                        difficulté = i
                    break
        print(grille)

    def technique_1_1(self, grille):
        """Full block

        Dans un bloc donné, il ne reste qu’une seule case non résolue.

        https://sudoku.megastar.fr/full-block/
        """
        pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    random.seed(1977)

    T = Traitement.from_sys_argv()
    T.effectuer()
