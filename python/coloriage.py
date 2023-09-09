#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pour vérifier la compatibilité d'une grille avec Tiwanaku :

- 5 valeurs au maximum
- Dimensions 5×5 ou 5×9
- Coloriable avec 4 couleurs
"""

import logging
import sys

import serial


def statuer(code):
    grille = serial.décoder(code)
    print(grille.est_4_coloriable())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for code in sys.argv[1:]:
        statuer(int(code))
