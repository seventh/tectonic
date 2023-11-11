# -*- coding: utf-8 -*-
"""Éléments de base pour la manipulation de grilles de Tectonic
"""

import dataclasses


@dataclasses.dataclass
class Base:
    """Caractéristiques principales d'une Grille
    """

    largeur: int = 4
    hauteur: int = 5
    maximum: int = 5

    def en_index(self, *, hauteur, largeur):
        """(hauteur, largeur) → index
        """
        return hauteur * self.largeur + largeur

    def en_position(self, index):
        """index → (hauteur, largeur)
        """
        return divmod(index, self.largeur)

    def nb_cases(self):
        return self.hauteur * self.largeur

    def transposer(self):
        """Objet dual dont hauteur et largeur ont été inversées
        """
        self.hauteur, self.largeur = self.largeur, self.hauteur


@dataclasses.dataclass
class Case:

    valeur: int = -1
    région: int = -1


class Grille:

    def __init__(self, base):
        self.base = base

        taille = base.nb_cases()
        self.cases = [None] * taille
        for i in range(taille):
            self.cases[i] = Case()

    def __eq__(self, autre):
        return (self.base == autre.base and self.cases == autre.cases)

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        # On détermine la longueur des champs à afficher
        lgv = len(
            str(max([c.valeur for c in self.cases if c.valeur >= 1],
                    default=1)))
        lgr = len(
            str(max([c.région for c in self.cases if c.région >= 0],
                    default=1)))
        lgc = 3 + lgv + lgr

        # Constitution de la grille, ligne à ligne
        lignes = list()
        for h in range(self.base.hauteur):
            # Séparateur horizontal
            ligne = "+"
            for l in range(self.base.largeur):
                séparateur = " "
                if h == 0:
                    séparateur = "-"
                else:
                    r = self[(h, l)].région
                    if r >= 0 and self[(h - 1, l)].région != r:
                        séparateur = "-"
                ligne += séparateur * lgc + "+"
            lignes.append(ligne)

            # Cases
            ligne = str()
            for l in range(self.base.largeur):
                case = self[(h, l)]
                séparateur = " "
                if l == 0:
                    séparateur = "|"
                else:
                    r = case.région
                    if r >= 0 and self[(h, l - 1)].région != r:
                        séparateur = "|"
                ligne += séparateur
                if case.valeur >= 1:
                    v = f"{case.valeur:{lgv}}"
                else:
                    v = " " * lgv
                if case.région >= 0:
                    r = f"{case.région:{lgr}}"
                else:
                    r = " " * lgr
                ligne += f"({v},{r})"
            ligne += "|"
            lignes.append(ligne)

        # Dernier séparateur horizontal
        ligne = "+" + ("-" * lgc + "+") * self.base.largeur
        lignes.append(ligne)

        retour = "\n".join(lignes)
        return retour

    def __str__(self):
        # On détermine la longueur des champs à afficher
        lgv = len(
            str(max([c.valeur for c in self.cases if c.valeur >= 1],
                    default=1)))
        lgc = lgv

        # Constitution de la grille, ligne à ligne
        lignes = list()
        for h in range(self.base.hauteur):
            # Séparateur horizontal
            ligne = "+"
            for l in range(self.base.largeur):
                séparateur = " "
                if h == 0:
                    séparateur = "-"
                else:
                    r = self[(h, l)].région
                    if r >= 0 and self[(h - 1, l)].région != r:
                        séparateur = "-"
                ligne += séparateur * lgc + "+"
            lignes.append(ligne)

            # Cases
            ligne = str()
            for l in range(self.base.largeur):
                case = self[(h, l)]
                séparateur = " "
                if l == 0:
                    séparateur = "|"
                else:
                    r = case.région
                    if r >= 0 and self[(h, l - 1)].région != r:
                        séparateur = "|"
                ligne += séparateur
                if case.valeur >= 1:
                    v = f"{case.valeur:{lgv}}"
                else:
                    v = " " * lgv
                ligne += v
            ligne += "|"
            lignes.append(ligne)

        # Dernier séparateur horizontal
        ligne = "+" + ("-" * lgc + "+") * self.base.largeur
        lignes.append(ligne)

        retour = "\n".join(lignes)
        return retour

    def __getitem__(self, position):
        h, l = position
        index = self.base.en_index(hauteur=h, largeur=l)
        return self.cases[index]

    def __setitem__(self, position, valeur):
        h, l = position
        index = self.base.en_index(hauteur=h, largeur=l)
        self.cases[index] = valeur

    def nb_régions(self):
        """Nombre de régions différentes identifiées
        """
        régions = set([c.région for c in self.cases if c.région >= 0])
        return len(régions)

    def est_canonique(self):
        """Vrai ssi la grille est une forme canonique

        La forme canonique permet d'éliminer les symétries
        """
        # Premier filtre : les valeurs des cases
        for h in range(self.base.hauteur // 2):
            for l in range(self.base.largeur // 2):
                coords = [(h, l), (h, self.base.largeur - 1 - l),
                          (self.base.hauteur - 1 - h, l),
                          (self.base.hauteur - 1 - h,
                           self.base.largeur - 1 - l)]
                cases = [self[p].valeur for p in coords]
                valeurs = [v for v in cases[1:] if v >= 1]
                if len(valeurs) == 0:
                    if cases[0] >= 1:
                        return True
                else:
                    for v in valeurs:
                        if v < cases[0]:
                            return False  # cases[0] > min(valeurs)
                        elif v > cases[0]:
                            return True  # cases[0] < max(valeurs)

        # TODO Second filtre : la structure

        return True

    def est_normale(self):
        """Vrai ssi la grille respecte la forme normale
        """
        # Attribution de nouveaux numéros
        # anciens[r] est l'ancien numéro de la région désormais identifiée 'r'
        retour = True
        anciens = list()
        for case in self.cases:
            région = case.région
            if région >= 0:
                try:
                    nouvelle_région = anciens.index(région)
                except ValueError:
                    nouvelle_région = len(anciens)
                    anciens.append(région)
                if nouvelle_région != case.région:
                    retour = False
                    break
        return retour

    def normaliser(self):
        """Assure un ordre de numérotation entre Régions.

        La valeur de retour indique si une modification a été effectuée
        """
        # Attribution de nouveaux numéros
        # anciens[r] est l'ancien numéro de la région désormais identifiée 'r'
        utile = False
        anciens = list()
        for case in self.cases:
            région = case.région
            if région >= 0:
                try:
                    nouvelle_région = anciens.index(région)
                except ValueError:
                    nouvelle_région = len(anciens)
                    anciens.append(région)
                if nouvelle_région != case.région:
                    utile = True
                case.région = nouvelle_région
        return utile

    def est_complète(self):
        """Vrai ssi toutes les cases ont une valeur de fixée
        """
        for case in self.cases:
            if case.valeur < 1:
                return False
        return True

    def transposer(self):
        """Grille dont largeur et hauteur sont interverties
        """
        nouvelle_base = Base(largeur=self.base.hauteur,
                             hauteur=self.base.largeur,
                             maximum=self.base.maximum)
        cases = [None] * self.base.nb_cases()
        for i in range(len(cases)):
            h, l = nouvelle_base.en_position(i)
            j = self.base.en_index(hauteur=h, largeur=l)
            cases[i] = self.cases[j]

        self.base.transposer()
        self.cases[:] = cases
