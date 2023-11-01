# -*- coding:utf-8 -*-
"""Format de fichier binaire

Ce format de fichier utilise le format de sérialisation `serial3`. Il
encode donc la Base à part.

Définition de l'entête :

+---+-------------------------------------+
| s | "TECTONIC"                          |
| B | numéro de version (ici, "2")        |
| B | Base.largeur                        |
| B | Base.hauteur                        |
| B | Base.maximum                        |
| B | nombre de mots de 4 octets par code |
| B | _réserve_                           |
| B | _réserve_                           |
| B | _réserve_                           |
| L | nombre de codes enregistrés         |
+---+-------------------------------------+
"""

import struct

from . import Base


class Écrivain:
    def __init__(self, chemin):
        self.nb_mots_par_code = 8

        self.nb_codes = 0
        self.sortie = open(chemin, "wb")
        self.sortie.write(b"TECTONIC\x02")

    def __del__(self):
        # Enregistrement du nombre de codes
        self.sortie.seek(16, 0)
        self.sortie.write(struct.pack(">L", self.nb_codes))
        self.sortie.close()
        self.sortie = None

    def configurer(self, base):
        self.sortie.write(
            struct.pack(">BBB", base.hauteur, base.largeur, base.maximum))

        self.sortie.write(struct.pack(">B", self.nb_mots_par_code))
        self.sortie.write(b"\x00\x00\x00")

        # Réservation du champ pour «nombre de codes enregistrés»
        self.sortie.write(struct.pack(">L", 0))

    def ajouter(self, valeur):
        # Découpage en mots de 4 octets
        mots = list()
        diviseur = 1 << (8 * 4)
        for i in range(self.nb_mots_par_code):
            valeur, mot = divmod(valeur, diviseur)
            mots.append(mot)
        mots.reverse()

        # Vérification de capacité. Si à l'issue de toutes ces divisions, il y
        # a encore un reste, c'est que la capacité n'est pas suffisante
        assert valeur == 0

        # Écriture GROS-BOUTISTE
        for mot in mots:
            self.sortie.write(struct.pack(">L", mot))
        self.sortie.flush()
        self.nb_codes += 1


class Lecteur:
    def __init__(self, chemin):
        self.nb_mots_par_code = 8

        self.entrée = open(chemin, "rb")
        prélude = self.entrée.read(9)
        assert prélude == b"TECTONIC\x02"

        tampon = self.entrée.read(4)
        hauteur, largeur, maximum, nb_mots_par_code = struct.unpack(
            ">4B", tampon)
        self.base = Base(largeur=largeur, hauteur=hauteur, maximum=maximum)
        self.nb_mots_par_code = nb_mots_par_code

        self.entrée.read(3)

        tampon = self.entrée.read(4)
        self.nb_codes = struct.unpack(">L", tampon)[0]
        self.id_code = 0

    def __iter__(self):
        self.entrée.seek(20, 0)
        self.id_code = 0
        return self

    def __next__(self):
        if self.id_code >= self.nb_codes:
            raise StopIteration
        else:
            retour = 0
            for i in range(self.nb_mots_par_code):
                retour *= 4
                retour += struct.unpack(">L", self.entrée.read(4))[0]
            self.id_code += 1
            return retour
