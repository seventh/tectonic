#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from tectonic.serial2 import Codec


def remonter(code):
    codec = Codec()

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
    remonter(int(sys.argv[1]))
