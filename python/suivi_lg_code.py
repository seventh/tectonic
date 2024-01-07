#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyse la longueur de tous les codes fournis.

Vu que chaque code est de taille variable, la question du meilleur
encodage d'une séquence se pose.
"""
import getopt
import math
import sys

from tectonic.fichier1 import Lecteur


class Configuration:

    def __init__(self):
        self.codes = list()
        self.lots = list()

    @staticmethod
    def charger():
        retour = Configuration()
        opts, args = getopt.getopt(sys.argv[1:], "f:")
        for opt, val in opts:
            if opt == "-f":
                retour.lots.append(val)
        retour.codes[:] = [int(x) for x in args]

        return retour


class EncodeurA:
    """Chaque code est préfixé par un entier de 8 bits pour sa taille.

    0 → [0] → 1 octet
    1 → [1, 1] → 2 octets
    …
    255 → [1, 255] → 2 octets
    256 → [2, 1, 0] → 3 octets
    """

    def __init__(self):
        self.nom = "A"
        self._nb_octets = 0

    def ajouter(self, code):
        self._nb_octets += 1

        lg = math.ceil(math.log2(code + 1) / 8)
        self._nb_octets += lg

    def nb_octets(self):
        return self._nb_octets


class EncodeurB:
    """Chaque code est encodé comme un varint non signé.

    0 → [0] → 1 octet
    1 → [1] → 1 octet
    …
    127 → [127] → 1 octet
    128 → [192, 0] → 2 octets
    …
    16383 → [255, 127] → 2 octets
    16384 → [127, 0, 0] → 3 octets
    """

    def __init__(self):
        self.nom = "B"
        self._nb_octets = 0

    def ajouter(self, code):
        if code == 0:
            lg = 1
        else:
            lg = math.ceil(math.log2(code + 1) / 7)
        self._nb_octets += lg

    def nb_octets(self):
        return self._nb_octets


class EncodeurC:
    """Mélange des deux

    Si la taille ne change pas par rapport au précédent, le premier bit est
    à 0.
    Sinon, il est à 1 et les 7 suivants sont la taille.

    Donc, par rapport à un encodage binaire simple :
    - le nouveau code prend un bit de plus si la taille ne change pas
    - le nouveau code prend un octet de plus si la taille change
    """

    def __init__(self):
        self.nom = "C"
        self._nb_octets = 0
        self._taille_précédente = 0

    def ajouter(self, code):
        lg = math.ceil(math.log2(code + 1) / 8)
        if self._taille_précédente != lg:
            self._nb_octets += 1 + lg
            self._taille_précédente = lg
        else:
            lg = math.ceil((1 + math.log2(code + 1)) / 8)
            self._nb_octets += lg

    def nb_octets(self):
        return self._nb_octets


def déterminer_longueur_code(conf):
    estimateurs = [
        EncodeurA(),
        EncodeurB(),
        EncodeurC(),
    ]

    for code in conf.codes:
        for e in estimateurs:
            e.ajouter(code)
    for lot in conf.lots:
        lecteur = Lecteur(lot)
        for code in lecteur:
            for e in estimateurs:
                e.ajouter(code)

    for e in estimateurs:
        print(f"{e.nom} : {e.nb_octets()} octets")


if __name__ == "__main__":
    CONF = Configuration.charger()
    déterminer_longueur_code(CONF)
