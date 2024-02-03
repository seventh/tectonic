#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyse la longueur de tous les codes fournis.

Vu que chaque code est de taille variable, la question du meilleur encodage
d'une séquence se pose.

Plusieurs idées sont évaluées :

* Alterner lexème de taille sur 8 bits et lexème de code.

* Utiliser un bit pour déterminer si les 7 bits qui suivent nécessitent
encore d'être étendus par l'octet qui suit (~varint).

* Utiliser un bit pour déterminer si le lexème suivant est une taille ou un
code. S'il est à 1, c'est une taille sur 7 bits, sinon, c'est un code. Ce
qui signifie que, pour une taille de N octets, il n'y a en réalité que
(8N - 1) bits utilisables.

* Trier les codes au préalable pour éviter limiter le nombre de lexèmes de
taille
"""
import logging

from commun import Configuration


def nb_bits(valeur):
    """Nombre de bits nécessaires pour représenter une valeur positive
    """
    return max(1, valeur.bit_length())


def nb_octets(valeur):
    """Nombre d'octets nécessaires pour représenter une valeur positive
    """
    return (nb_bits(valeur) + 7) // 8


class Encodeur:

    def __init__(self, nom):
        self.nom = nom
        self._nb_octets = 0

    def ajouter(self, code):
        raise NotImplementedError

    def nb_octets(self):
        return self._nb_octets


class EncodeurA(Encodeur):
    """Chaque code est préfixé par un entier de 8 bits pour sa taille.

    0 → [1, 0] → 2 octets
    1 → [1, 1] → 2 octets
    …
    255 → [1, 255] → 2 octets
    256 → [2, 1, 0] → 3 octets
    """

    def __init__(self):
        super().__init__("A")

    def ajouter(self, code):
        self._nb_octets += 1

        lg = nb_octets(code)
        self._nb_octets += lg


class EncodeurB(Encodeur):
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
        super().__init__("B")

    def ajouter(self, code):
        lg = (nb_bits(code) + 6) // 7
        self._nb_octets += lg


class EncodeurC(Encodeur):
    """Mélange des deux

    Le premier bit du lexème détermine si c'est une taille ou un code.
    """

    def __init__(self):
        super().__init__("C")
        self._taille_précédente = 1

    def ajouter(self, code):
        nbits = nb_bits(code)
        lg = 1 + nbits // 8
        if self._taille_précédente != lg:
            self._nb_octets += 1
            self._taille_précédente = lg
        self._nb_octets += self._taille_précédente


class EncodeurD(Encodeur):
    """La taille ne peut qu'augmenter

    Le premier bit du lexème détermine si c'est une taille ou un code.
    """

    def __init__(self):
        super().__init__("D")
        self._taille_précédente = 1

    def ajouter(self, code):
        nbits = nb_bits(code)
        lg = 1 + nbits // 8
        if self._taille_précédente < lg:
            self._nb_octets += 1
            self._taille_précédente = lg
        self._nb_octets += self._taille_précédente


class EncodeurE(Encodeur):
    """Mode flux regroupé par tailles

    Un en-tête annonce la structure du contenu :
    - nombre de tailles différentes (1 octet, 7 bits utiles)
    - pour chaque taille : 1 octet de taille (8 bits utiles), 4 octets de
    nombres de lexèmes

    En fin de fichier, 1 octet pour terminer le flux
    """

    def __init__(self):
        super().__init__("E")
        self.tailles = dict()

    def ajouter(self, code):
        lg = nb_octets(code)
        self.tailles[lg] = self.tailles.get(lg, 0) + 1
        self._nb_octets += lg

    def nb_octets(self):
        # En-tête
        retour = 1 + 5 * len(self.tailles)

        # Corps
        retour += self._nb_octets

        # Fin
        retour += 1

        return retour


class EncodeurF(Encodeur):
    """Format C sur flux regroupé par tailles
    """

    def __init__(self):
        super().__init__("F")
        self.tailles = dict()

    def ajouter(self, code):
        nbbits = nb_bits(code)
        self.tailles[nbbits] = self.tailles.get(nbbits, 0) + 1

    def nb_octets(self):
        # On trie les tailles par ordre croissants
        tailles = sorted(self.tailles)

        # 1 à 7 bits → 1 octet
        # 8 à 15 bits → 2 octets
        # 16 à 23 bits → 3 octets
        # …
        nb_octets = [(1 + nbbits // 8) for nbbits in tailles]

        taille_précédente = 1
        for i, t in enumerate(tailles):
            if nb_octets[i] != taille_précédente:
                self._nb_octets += 1
                taille_précédente = nb_octets[i]
            self._nb_octets += taille_précédente * self.tailles[t]
        return self._nb_octets


class EncodeurG(Encodeur):
    """Compactage de chaque symbole sur 4 bits

    On a besoin de 12 symboles:
    - les chiffres de 0 à 9
    - un séparateur (saut de ligne)
    - un marqueur de fin de fichier
    """

    def __init__(self):
        super().__init__("G")
        self._nb_mots = 0

    def ajouter(self, code):
        nb_mots = len(str(code))
        if self._nb_mots != 0:
            nb_mots += 1
        self._nb_mots += nb_mots

    def nb_octets(self):
        # On compte également le marqueur de fin de fichier
        return 1 + self._nb_mots // 2


def format_françois(nombre):
    chaîne = str(nombre)
    lg = len(chaîne)
    nb_groupes = (lg + 2) // 3
    groupes = list()
    i = 0
    j = lg - 3 * (nb_groupes - 1)
    while i != lg:
        groupes.append(chaîne[i:j])
        i = j
        j += 3
    retour = ".".join(groupes)
    # return chaîne
    return retour


def déterminer_longueur_code(conf):
    estimateurs = [
        EncodeurA(),
        EncodeurB(),
        EncodeurC(),
        EncodeurD(),
        EncodeurE(),
        EncodeurF(),
        EncodeurG(),
    ]

    for lot in conf.lots:
        for code in lot:
            for e in estimateurs:
                e.ajouter(code)

    résultats = dict([(e.nom, e.nb_octets()) for e in estimateurs])
    for nom in sorted(résultats, key=lambda r: résultats[r]):
        print(f"{nom} : {format_françois(résultats[nom])} octets")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    CONF = Configuration.charger()
    déterminer_longueur_code(CONF)
