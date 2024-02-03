#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from commun import Configuration
from tectonic.serial import Codec


class Traitement:

    def __init__(self, conf):
        self.lots = conf.lots
        self.debug = conf.debug
        self.saut_requis = False

    def afficher(self):
        for lot in self.lots:
            codec = Codec(lot.base)
            for code in lot:
                grille = codec.décoder(code)
                self.afficher_grille(grille)

    def afficher_grille(self, grille):
        if self.saut_requis:
            print("")
        if self.debug:
            print(repr(grille))
        else:
            print(grille)
        self.saut_requis = True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    CONF = Configuration.charger()
    T = Traitement(CONF)
    T.afficher()
