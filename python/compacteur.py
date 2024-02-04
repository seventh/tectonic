#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compacteur de fichiers au format TECTONIC1

Limite à 1 unique bloc de description
"""

from collections import namedtuple
import logging
import os

from commun import Configuration

Segment = namedtuple("Segment", "taille nombre")


class Bloc:

    def __init__(self, entrée):
        self.décalage = entrée.tell()
        self.segments = list()
        n = int.from_bytes(entrée.read(1), byteorder="big", signed=True)
        while n > 0:
            taille = int.from_bytes(entrée.read(1),
                                    byteorder="big",
                                    signed=False)
            nombre = int.from_bytes(entrée.read(4),
                                    byteorder="big",
                                    signed=False)
            self.segments.append(Segment(taille, nombre))
            n -= 1
        self.contenu = entrée.tell()

    def __str__(self):
        lignes = list()
        lignes.append("Bloc")
        lignes.append(
            "  - en-tête : [0x{self.décalage:08x} 0x{self.contenu:08x}]")
        début = self.contenu
        for i, s in enumerate(self.segments):
            fin = début + s.nombre * s.taille
            lignes.append(
                f"  - bloc {i} : {s.nombre:8d} codes × {s.taille} octets : [0x{début:08x} 0x{fin:08x}]"
            )
            début = fin
        return "\n".join(lignes)

    def fin(self):
        retour = self.contenu
        for s in self.segments:
            retour += s.nombre * s.taille
        return retour

    def tailles(self):
        retour = sorted(set([s.taille for s in self.segments]))
        return retour

    def sélection(self, taille):
        """Itérateur des segments de la taille demandée

        Chaque réponse est de la forme (décalage, nombre)
        """
        décalage = self.contenu
        for s in self.segments:
            if s.taille == taille:
                yield (décalage, s.nombre)
            décalage += s.nombre * s.taille


def compacter(lecteur, suffixe):
    chemin = lecteur.chemin

    # Cartographie
    blocs = list()
    with open(chemin, "rb") as entrée:
        entrée.seek(16, os.SEEK_SET)
        while True:
            b = Bloc(entrée)
            if len(b.segments) == 0:
                break
            blocs.append(b)
            entrée.seek(b.fin(), os.SEEK_SET)

    # Caractéristiques du bloc compact
    segments = dict()
    for b in blocs:
        for s in b.segments:
            segments[s.taille] = segments.get(s.taille, 0) + s.nombre

    # Compactage
    with (open(chemin, "rb") as entrée, open(chemin + suffixe, "wb") as
          sortie):
        # En-tête
        sortie.write(entrée.read(16))
        sortie.write(
            len(segments).to_bytes(length=1, byteorder="big", signed=False))
        for taille in sorted(segments):
            sortie.write(
                taille.to_bytes(length=1, byteorder="big", signed=False))
            sortie.write(segments[taille].to_bytes(length=4,
                                                   byteorder="big",
                                                   signed=False))
        # Bloc
        for taille in sorted(segments):
            for b in blocs:
                for décalage, nombre in b.sélection(taille):
                    entrée.seek(décalage, os.SEEK_SET)
                    sortie.write(entrée.read(taille * nombre))
        # Marque finale
        sortie.write((-128).to_bytes(length=1, byteorder="big", signed=True))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    CONF = Configuration.charger()
    for lot in CONF.lots:
        compacter(lot, CONF.suffixe)
