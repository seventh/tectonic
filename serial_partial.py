# -*- coding: utf-8 -*-
"""Format de sérialisation d'une grille

Chaque case est encodée comme un couple (valeur, zone), ce qui fonctionne
particulièrement bien avec des grilles partiellement renseignées et ne
nécessite pas d'avoir conscience des zones elles-mêmes.
"""

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

    conf = générateur.Configuration(hauteur, largeur, maximum)
    retour = générateur.Grille(conf)

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

                while len(retour.zones) <= zone:
                    retour.zones.append(générateur.Zone())
                if valeur > 0:
                    retour.zones[zone].valeurs.add(valeur)

    return retour
