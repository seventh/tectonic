# -*- coding: utf-8 -*-
"""Format de sérialisation d'une grille
"""

import générateur


def encoder(grille):
    pad_dimension = 256
    pad_valeur = grille.conf.maximum
    pad_frontière = 2

    assert grille.conf.hauteur < pad_dimension
    assert grille.conf.largeur < pad_dimension
    assert grille.conf.maximum < pad_dimension

    retour = 0

    # Encodage de la grille elle-même
    for h in range(grille.conf.hauteur):
        for l in range(grille.conf.largeur):
            # Encodage de la valeur en base-0
            retour *= pad_valeur
            c = grille.cases[grille.en_index(l, h)]
            retour += c.case - 1

            # Encodage de la frontière droite
            if l + 1 < grille.conf.largeur:
                retour *= pad_frontière
                c2 = grille.cases[grille.en_index(l + 1, h)]
                if c.zone != c2.zone:
                    retour += 1

            # Encodage de la frontière haute
            if h + 1 < grille.conf.hauteur:
                retour *= pad_frontière
                c3 = grille.cases[grille.en_index(l, h + 1)]
                if c.zone != c3.zone:
                    retour += 1

    # Encodage de ses dimensions
    retour *= pad_dimension
    retour += grille.conf.maximum
    retour *= pad_dimension
    retour += grille.conf.largeur
    retour *= pad_dimension
    retour += grille.conf.hauteur

    return retour


def décoder(code):
    pad_dimension = 256
    pad_frontière = 2

    # Décodage des dimensions
    code, hauteur = divmod(code, pad_dimension)
    code, largeur = divmod(code, pad_dimension)
    code, maximum = divmod(code, pad_dimension)
    pad_valeur = maximum

    conf = générateur.Configuration(hauteur, largeur, maximum)
    print(conf)

    # Décodage de la grille elle-même
    for h in reversed(range(conf.hauteur)):
        for l in reversed(range(conf.largeur)):
            # Décodage de la frontière haute
            if h + 1 < conf.hauteur:
                code, frontière = divmod(code, pad_frontière)
                print(frontière)

            # Décodage de la frontière droite
            if l + 1 < conf.largeur:
                code, frontière = divmod(code, pad_frontière)
                print(frontière)

            # Décodage de la valeur en base-0
            code, valeur = divmod(code, pad_valeur)
            valeur += 1
            print(valeur)
