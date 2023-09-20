# -*- coding: utf-8 -*-
"""Format de sérialisation d'une grille

Chaque case est encodée comme un couple (valeur, zone), ce qui fonctionne
particulièrement bien avec des grilles partiellement renseignées et ne
nécessite pas d'avoir conscience des zones elles-mêmes.
"""

import logging

import générateur


def encoder(grille):
    pad_dimension = 256
    # La valeur «0» sera utilisée pour les cases non définies
    pad_valeur = grille.conf.maximum + 1
    # Une valeur est réservée pour les cases dont la zone n'est pas encore
    # définie
    pad_zone = len(grille.zones) + 1

    assert grille.conf.hauteur < pad_dimension
    assert grille.conf.largeur < pad_dimension
    assert grille.conf.maximum < pad_dimension
    assert len(grille.zones) < pad_dimension

    if False:
        logging.debug(f"Encodage\n{grille}\n{grille.zones}")

    retour = 0

    # Encodage de la grille elle-même
    for h in reversed(range(grille.conf.hauteur)):
        for l in reversed(range(grille.conf.largeur)):
            c = grille.cases[grille.en_index(l, h)]

            # Encodage de la zone
            retour *= pad_zone
            if c.zone >= 0:
                retour += c.zone + 1

            # Encodage de la valeur
            retour *= pad_valeur
            if c.case >= 1:
                retour += c.case

    # Encodage de ses dimensions
    retour *= pad_dimension
    retour += len(grille.zones)
    retour *= pad_dimension
    retour += grille.conf.maximum
    retour *= pad_dimension
    retour += grille.conf.largeur
    retour *= pad_dimension
    retour += grille.conf.hauteur

    if False:
        recons = décoder(retour)
        print(grille)
        print(grille.zones)
        print(recons)
        print(recons.zones)
        assert décoder(retour) == grille

    return retour


def décoder(code):
    pad_dimension = 256

    # Décodage des dimensions
    code, hauteur = divmod(code, pad_dimension)
    code, largeur = divmod(code, pad_dimension)
    code, maximum = divmod(code, pad_dimension)
    code, nb_zones = divmod(code, pad_dimension)

    pad_valeur = maximum + 1
    pad_zone = nb_zones + 1

    conf = générateur.Dimension(hauteur, largeur, maximum)
    retour = générateur.Grille(conf)
    retour.zones = [None] * nb_zones

    # Décodage de la grille elle-même
    for h in range(conf.hauteur):
        for l in range(conf.largeur):
            i = retour.en_index(l, h)

            # Décodage de la valeur
            code, valeur = divmod(code, pad_valeur)
            if valeur > 0:
                retour.cases[i].case = valeur

            # Décodage de la zone
            code, zone = divmod(code, pad_zone)
            zone -= 1
            if zone >= 0:
                retour.cases[i].zone = zone

                if retour.zones[zone] is None:
                    retour.zones[zone] = générateur.Zone()
                retour.zones[zone].valeurs.add(valeur)

    # Informations de bordure
    # Le code est robuste au fait que celles-ci ne soient plus encodées

    # RAPPEL : «bordures» est le nombre de bords libres de la zone
    bordures = [0] * nb_zones
    for h in range(conf.hauteur):
        for l in range(conf.largeur):
            i = retour.en_index(l, h)
            z = retour.cases[i].zone
            if z != -1:
                for l2, h2 in [(l, h + 1), (l + 1, h)]:
                    if (0 <= h2 < conf.hauteur and 0 <= l2 < conf.largeur):
                        j = retour.en_index(l2, h2)
                        if retour.cases[j].zone == -1:
                            bordures[z] += 1
    for i, z in enumerate(retour.zones):
        z.bordure = bordures[i]

    if False:
        logging.debug(f"Décodage\n{retour}\n{retour.zones}")

    return retour
