# -*- coding: utf-8 -*-
"""Encodage compact (sans base)
"""

import copy

from . import Grille


class Codec:
    """Transformation entre code binaire et Grille

    Que ce soit pour la valeur d'une case ou sa région d'appartenance, la
    valeur «0» représente une caractéristique indéfinie. Ce choix n'a pas
    d'incidence sur l'encodage des valeurs, par contre, tous les
    identifiants de région sont décalés d'une unité.
    """

    def __init__(self, base):
        """Les informations portées par la Base ne sont pas codées
        """
        self.base = base
        self.pad_dimension = 256
        self.pad_valeur = 1 + base.maximum

    def décoder(self, code):
        """Grille de code correspondant
        """
        # - Décodage des caractéristiques du format
        code, pad_région = divmod(code, self.pad_dimension)

        # - Décodage de la grille elle-même
        retour = Grille(copy.deepcopy(self.base))
        for case in retour.cases:
            # -- Décodage de la valeur
            code, valeur = divmod(code, self.pad_valeur)
            if valeur > 0:
                case.valeur = valeur

            # -- Décodage de la région
            code, région = divmod(code, pad_région)
            if région > 0:
                case.région = région - 1

        return retour

    def encoder(self, grille):
        """Code associé à la Grille fournie
        """
        pad_région = 1 + grille.nb_régions()

        # - Encodage de la grille elle-même
        retour = 0
        for c in reversed(grille.cases):
            # -- Encodage de la région
            retour *= pad_région
            if c.région >= 0:
                retour += 1 + c.région

            # -- Encodage de la valeur
            retour *= self.pad_valeur
            if c.valeur >= 1:
                retour += c.valeur

        # - Encodage des caractéristiques du format
        retour *= self.pad_dimension
        retour += pad_région

        return retour
