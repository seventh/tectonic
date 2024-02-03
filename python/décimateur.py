#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from commun import Configuration
from tectonic.fichier import Écrivain
from tectonic.serial import Codec


def identifier_sorties(nom):
    if nom is None:
        sortie_ok = "log.ok"
        sortie_ko = "log.ko"
    else:
        sortie_ok = nom + ".ok"
        sortie_ko = nom + ".ko"

    return (sortie_ok, sortie_ko)


def filtrer(lot):
    nom_ok, nom_ko = identifier_sorties(lot.chemin)
    sortie_ok = Écrivain(nom_ok, lot.base)
    sortie_ko = Écrivain(nom_ko, lot.base)

    codec = Codec(lot.base)
    for code in lot:
        grille = codec.décoder(code)
        if grille.est_canonique():
            sortie_ok.ajouter(code)
        else:
            sortie_ko.ajouter(code)

    sortie_ko.clore()
    sortie_ok.clore()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    CONF = Configuration.charger()

    for LOT in CONF.lots:
        filtrer(LOT)
