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
    pad_bordure = 2 * (grille.conf.maximum + 1) + 1

    assert grille.conf.hauteur < pad_dimension
    assert grille.conf.largeur < pad_dimension
    assert grille.conf.maximum < pad_dimension
    assert len(grille.zones) < pad_dimension

    logging.debug(f"Encodage\n{grille}\n{grille.zones}")

    retour = 0

    # Encodage des informations de zones
    for z in reversed(range(len(grille.zones))):
        zone = grille.zones[z]
        retour *= pad_bordure
        if zone is None:
            retour += (pad_bordure - 1)
        else:
            retour += zone.bordure

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
    pad_bordure = 2 * (maximum + 1) + 1

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

    # Décodage des informations par Zone
    for z in range(nb_zones):
        # Nombre de bordures pour la zone n°z
        code, bordure = divmod(code, pad_bordure)
        if bordure < pad_bordure - 1:
            if retour.zones[z] is not None:
                retour.zones[z].bordure = bordure

    assert code == 0

    # Ici, on peut tenter de reconstituer les informations de bordure
    # uniquement à partir des informations de case, pour les supprimer
    # du Code

    logging.debug(f"Décodage\n{retour}\n{retour.zones}")

    return retour
