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
    def __init__(self, position, valeur, région):
        self.position = position
        self.région = région
        if valeur > 0:
            self.libres = None
            self.valeur = valeur
        else:
            self.libres = set()
            self.valeur = None

        # Dans les huit directions
        self.voisins = list()

    def fixer(self, valeur=None):
        if valeur is None:
            assert len(self.libres) == 1
            self.valeur = self.libres.pop()
        else:
            assert valeur in self.libres
            self.valeur = valeur

        self.libres = None


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
        return set([c.valeur for c in self.cases if c.valeur is not None])

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
            position = grille.base.en_position(i)
            self.cases[i] = CaseNavigable(position, case.valeur, région)
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
            if case.valeur is None:
                case.libres = set(range(1, len(case.région)))
                for v in case.voisins:
                    case.libres.discard(v.valeur)
                for m in case.région.cases:
                    if m is not case:
                        case.libres.discard(m.valeur)

    def __getitem__(self, position):
        h, l = position
        index = self.base.en_index(hauteur=h, largeur=l)
        return self.cases[index]

    def __setitem__(self, position, valeur):
        h, l = position
        index = self.base.en_index(hauteur=h, largeur=l)
        self.cases[index] = valeur

    def _ajouter_voisin(self, case, h, l):
        """Ajoute la case de coordonnées (h, l) aux voisins de la case
        si ces coordonnées sont valides
        """
        if (0 <= h < self.base.hauteur and 0 <= l < self.base.largeur):
            case.voisins.append(self[(h, l)])


class Traitement:
    def __init__(self):
        self.codec = Codec()
        self.lots = list()

    @staticmethod
    def charger():
        retour = Traitement()

        lecteurs = list()
        opts, args = getopt.getopt(sys.argv[1:], "f:")
        for opt, val in opts:
            if opt == "-f":
                lecteurs.append(Lecteur(val))
        codes = [int(c) for c in args]

        retour.lots = [codes, *lecteurs]

        return retour

    def effectuer(self):
        for lot in self.lots:
            for code in lot:
                self.gérer_grille(code)

    def gérer_grille(self, code):
        grille = self.codec.décoder(code)

        # D'abord, on supprime des valeurs
        n = grille.base.nb_cases()
        k = random.randint(n // 4, (3 * n) // 4)
        indices = random.sample(range(n), k)
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
                if t(grille):
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
        retour = False
        for r in grille.régions.values():
            if len(r.libres()) == 1:
                for c in r.cases:
                    if (c.libres is not None and len(c.libres) == 1):
                        retour = True
                        c.fixer()
                        logging.info(
                            f"Technique 1.1 : {c.position} = {c.valeur}")
        return retour


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    random.seed(1977)

    T = Traitement.charger()
    T.effectuer()
