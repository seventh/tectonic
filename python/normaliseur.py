#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vérifie si un code identifie une grille en forme normale
"""

import logging

from commun import Configuration
from tectonic.serial import Codec


class Traitement:

    def __init__(self, conf):
        self.lots = conf.lots
        self.saut_requis = False

    def afficher(self):
        for lot in self.lots:
            codec = Codec(lot.base)
            for code in lot:
                self.tester(code, codec)

    def tester(self, code, codec):
        grille = codec.décoder(code)
        grille.normaliser()
        nouveau = codec.encoder(grille)
        if nouveau != code:
            self.afficher_code(code)

    def afficher_code(self, code):
        if self.saut_requis:
            print("")
        print(code)
        self.saut_requis = True


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    CONF = Configuration.charger()
    T = Traitement(CONF)
    T.afficher()
