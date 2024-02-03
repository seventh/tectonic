#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pour vérifier la compatibilité d'une grille avec Tiwanaku :

- 5 valeurs au maximum (pas testé)
- Dimensions 5×5 ou 5×9 (pas testé)
- Coloriable avec 4 couleurs (testé !)
"""

import enum
import logging

from commun import Configuration
from tectonic.serial import Codec


class Terrain(enum.IntEnum):
    """Différentes natures de terrain, fidèles au jeu «Tiwanaku»
    """

    herbe = enum.auto()
    roche = enum.auto()
    sable = enum.auto()
    terre = enum.auto()


def est_4_coloriable(grille):
    """Vrai ssi la Grille est coloriable avec 4 couleurs.

    Une case peut partager la couleur d'une de ses 8 voisines ssi elles
    sont dans la même Région
    """
    # https://fr.wikipedia.org/wiki/Th%C3%A9or%C3%A8me_des_quatre_couleurs
    # Attention, le théorême ne vaut que pour le partage de frontière. Ce
    # qui n'est pas la définition retenue dans Tiwanaku.

    # On établit le graphe des voisinages de Régions
    voisinage = dict()
    for h1 in range(grille.base.hauteur):
        for l1 in range(grille.base.largeur):
            r1 = grille[(h1, l1)].région
            for delta_h, delta_l in [(-1, -1), (-1, 0), (-1, 1), (0, -1)]:
                h2 = h1 + delta_h
                l2 = l1 + delta_l
                if (0 <= h2 < grille.base.hauteur
                        and 0 <= l2 < grille.base.largeur):
                    r2 = grille[(h2, l2)].région
                    if r1 != r2:
                        voisinage.setdefault(r1, set()).add(r2)
                        voisinage.setdefault(r2, set()).add(r1)

    # Recherche d'un coloriage valide
    for k in sorted(voisinage):
        logging.debug(f"{k} → {sorted(voisinage[k])}")

    # Coloriage par force brute
    couleurs = [None] * len(voisinage)
    couleurs[0] = Terrain.herbe
    i = 1
    while 0 < i < len(voisinage):
        possibles = set(Terrain)
        for voisin in voisinage[i]:
            if voisin < i:
                possibles.discard(couleurs[voisin])
        possibles = sorted(possibles)
        if len(possibles) == 0:
            couleurs[i] = None
            i -= 1
        elif couleurs[i] is None:
            couleurs[i] = possibles[0]
            i += 1
        else:
            j = possibles.index(couleurs[i])
            if j + 1 < len(possibles):
                couleurs[i] = possibles[j + 1]
                i += 1
            else:
                couleurs[i] = None
                i -= 1

    if False and i == len(voisinage):
        print(couleurs)

    return i == len(voisinage)


def statuer(lots):
    affichage = False

    for lot in lots:
        codec = Codec(lot.base)
        for code in lot:
            grille = codec.décoder(code)
            if not est_4_coloriable(grille):
                logging.debug(grille)
                if affichage:
                    print("")
                print(code)
                affichage = True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    CONF = Configuration.charger()
    statuer(CONF.lots)
