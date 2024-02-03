#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from commun import Configuration
from tectonic.serial import Codec


def remonter(codec, code):
    grille = codec.décoder(code)
    for i, case in enumerate(grille.cases):
        if case.valeur < 1:
            break
    i -= 1
    print(code)
    print(grille)
    print(repr(grille))
    while i >= 0:
        grille.cases[i].valeur = 0
        grille.cases[i].région = -1
        print(codec.encoder(grille))
        print(grille)
        i -= 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    CONF = Configuration.charger()
    for LOT in CONF.lots:
        CODEC = Codec(LOT.base)
        for CODE in LOT:
            remonter(CODEC, CODE)
