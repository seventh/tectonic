#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from commun import Configuration
from tectonic.serial import Codec


def déterminer_nb_régions(conf):
    nb_régions = dict()

    for lot in conf.lots:
        codec = Codec(lot.base)
        for code in lot:
            grille = codec.décoder(code)
            n = grille.nb_régions()
            nb_régions[n] = nb_régions.get(n, 0) + 1

    for n in sorted(nb_régions):
        print(f"{n} régions : {nb_régions[n]}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    CONF = Configuration.charger()
    déterminer_nb_régions(CONF)
