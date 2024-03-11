# -*- coding: utf-8 -*-
"""Code commun à la génération de grilles pleines
"""

import dataclasses
import itertools

from tectonic import Grille
from tectonic.serial import Codec


@dataclasses.dataclass
class Région:
    """Ensemble de valeurs connexes et nombre de bords libres
    """

    # Valeurs des cases de la région
    valeurs: set = dataclasses.field(default_factory=set)
    # Identifiants des régions voisines
    voisins: set = dataclasses.field(default_factory=set)
    # Nombre de cases limitrophes libres
    bordure: int = 0

    def __eq__(self, autre):
        return (self.valeurs == autre.valeurs and self.voisins == autre.voisins
                and self.bordure == autre.bordure)

    def est_anormal(self):
        """Une Zone est anormale si elle est fermée et ne contient pas toutes
        les valeurs prévues
        """
        retour = False
        if self.bordure == 0 and self.est_incomplète():
            retour = True
        return retour

    def est_incomplète(self):
        """Vrai ssi les valeurs ne forment pas un intervalle continu
        débutant à 1. Toutes les valeurs autorisées n'ont pas à être
        représentées (dans une grille autorisant le 5, une région avec les
        quatre valeurs 1, 2, 3, 4 sera considérée complète)
        """
        n = len(self.valeurs)
        if n == 0:
            return True

        minimum = min(self.valeurs)
        if minimum != 1:
            return True

        maximum = max(self.valeurs)
        if n != maximum - minimum + 1:
            return True

        return False


class Analyseur:
    """Analyse d'une grille

    Cette analyse consiste à identifier, région par région, les valeurs dont
    elles sont constituées, ainsi que les identifiants des régions connexes,
    et le nombre de cases limitrophes libres.
    """

    def __init__(self, grille):
        self.g = grille
        self.régions = dict()

        self._calculer()

    def _calculer(self):
        bords = dict()

        for i, case in enumerate(self.g.cases):
            r1 = case.région
            if r1 >= 0:
                if case.valeur > 0:
                    self.régions.setdefault(r1,
                                            Région()).valeurs.add(case.valeur)

                h1, l1 = self.g.base.en_position(i)
                for h2, l2 in [(h1, l1 + 1), (h1 + 1, l1)]:
                    if (h2 < self.g.base.hauteur and l2 < self.g.base.largeur):
                        j = self.g.base.en_index(hauteur=h2, largeur=l2)
                        r2 = self.g.cases[j].région
                        if r2 < 0:
                            bords.setdefault(r1, set()).add(j)
                        elif r2 != r1:
                            self.régions.setdefault(r1,
                                                    Région()).voisins.add(r2)
                            self.régions.setdefault(r2,
                                                    Région()).voisins.add(r1)

        for r, cases in bords.items():
            self.régions[r].bordure = len(cases)

    def région_max(self):
        return max(self.régions, default=-1)


class GénérateurGrilleVide:

    def __init__(self, base):
        grille = Grille(base)
        self.code = Codec(base).encoder(grille)

        self.a_produit = True

    def __iter__(self):
        self.a_produit = False
        return self

    def __next__(self):
        if self.a_produit:
            raise StopIteration
        else:
            self.a_produit = True
            return self.code


class ProducteurProgrès:
    """Produit des grilles *pour* un certain palier, à partir d'un code issu
    du palier précédent
    """

    def __init__(self, progrès):
        self.palier = progrès.palier
        self.codec = Codec(progrès.base())

    def itérer(self, code):
        """Itérateur des grilles du palier suivant
        """
        grille = self.codec.décoder(code)
        analyseur = Analyseur(grille)

        i = self.palier - 1
        h, l = grille.base.en_position(i)

        # Régions à compléter
        régions = set()
        # → case du dessus
        if h > 0:
            régions.add(grille[(h - 1, l)].région)
        # → case de gauche
        if l > 0:
            régions.add(grille[(h, l - 1)].région)
        régions = sorted(régions)

        # Calcul des valeurs possibles au maximum, selon la règle du voisinage
        valeurs_possibles = set(range(1, grille.base.maximum + 1))
        if l > 0:
            valeurs_possibles.discard(grille[(h, l - 1)].valeur)
        if h > 0:
            valeurs_possibles.discard(grille[(h - 1, l)].valeur)
            if l > 0:
                valeurs_possibles.discard(grille[(h - 1, l - 1)].valeur)
            if l + 1 < grille.base.largeur:
                valeurs_possibles.discard(grille[(h - 1, l + 1)].valeur)

        # 1) On étend chacune des régions de toutes les façons possibles
        if len(régions) == 1:
            r = régions[0]
            valeurs = valeurs_possibles.difference(
                analyseur.régions[r].valeurs)
            for v in valeurs:
                grille.cases[i].région = r
                grille.cases[i].valeur = v
                yield self.codec.encoder(grille)
        else:
            for r1, r2 in itertools.permutations(régions, 2):
                # On vérifie qu'on ne rendrait pas «r2» incomplète de toute
                # pièce
                if not (analyseur.régions[r2].bordure == 1
                        and analyseur.régions[r2].est_incomplète()):
                    valeurs = valeurs_possibles.difference(
                        analyseur.régions[r1].valeurs)
                    for v in valeurs:
                        grille.cases[i].région = r1
                        grille.cases[i].valeur = v
                        yield self.codec.encoder(grille)

        # 2) On crée une toute nouvelle région, en veillant à ce qu'elle ne
        # puisse pas être incomplète
        for r in régions:
            if (analyseur.régions[r].bordure == 1
                    and analyseur.régions[r].est_incomplète()):
                break
        else:
            for v in valeurs_possibles:
                grille.cases[i].région = analyseur.région_max() + 1
                grille.cases[i].valeur = v
                yield self.codec.encoder(grille)

        # 3) On fusionne les régions voisines
        for r1, r2 in itertools.combinations(régions, 2):
            if (r2 not in analyseur.régions[r1].voisins
                    and analyseur.régions[r1].valeurs.isdisjoint(
                        analyseur.régions[r2].valeurs)):
                valeurs = valeurs_possibles.difference(
                    analyseur.régions[r1].valeurs)
                valeurs.difference_update(analyseur.régions[r2].valeurs)
                if len(valeurs) > 0:
                    for case in grille.cases:
                        if case.région == r2:
                            case.région = r1
                    grille.cases[i].région = r1
                    grille.normaliser()
                    for v in valeurs:
                        grille.cases[i].valeur = v
                        yield self.codec.encoder(grille)
