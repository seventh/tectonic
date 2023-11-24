# -*- coding: utf-8 -*-
"""Encodage complet (grille + base)
"""

from . import Base, Grille


class Codec:
    """Transformation entre code binaire et Grille

    Que ce soit pour la valeur d'une case ou sa région d'appartenance, la
    valeur «0» représente une caractéristique indéfinie. Ce choix n'a pas
    d'incidence sur l'encodage des valeurs, par contre, tous les
    identifiants de région sont décalés d'une unité.
    """

    FORMAT = 2

    def __init__(self, base=None):
        # L'argument 'base' est proposé par compatibilité
        self.pad_dimension = 256

    def décoder(self, code):
        """Grille de code correspondant
        """
        # - Décodage des caractéristiques du format
        code, hauteur = divmod(code, self.pad_dimension)
        code, largeur = divmod(code, self.pad_dimension)
        code, maximum = divmod(code, self.pad_dimension)
        code, nb_régions = divmod(code, self.pad_dimension)

        pad_valeur = maximum + 1
        pad_région = nb_régions + 1

        base = Base(largeur, hauteur, maximum)
        retour = Grille(base)

        # - Décodage de la grille elle-même
        for case in retour.cases:
            # -- Décodage de la valeur
            code, valeur = divmod(code, pad_valeur)
            if valeur > 0:
                case.valeur = valeur

            # -- Décodage de la région
            code, région = divmod(code, pad_région)
            if région > 0:
                case.région = région - 1

            # -- Optimisation : interruption prématurée
            if code == 0:
                break

        return retour

    def encoder(self, grille):
        """Code associé à la Grille fournie
        """
        pad_valeur = 1 + grille.base.maximum
        pad_région = 1 + grille.nb_régions()

        # - Encodage de la grille elle-même
        retour = 0
        for c in reversed(grille.cases):
            # -- Encodage de la région
            retour *= pad_région
            if c.région >= 0:
                retour += c.région + 1

            # -- Encodage de la valeur
            retour *= pad_valeur
            if c.valeur >= 1:
                retour += c.valeur

        # - Encodage de caractéristiques du format
        retour *= self.pad_dimension
        retour += grille.nb_régions()
        retour *= self.pad_dimension
        retour += grille.base.maximum
        retour *= self.pad_dimension
        retour += grille.base.largeur
        retour *= self.pad_dimension
        retour += grille.base.hauteur

        return retour
