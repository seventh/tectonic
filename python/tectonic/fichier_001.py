# -*- coding:utf-8 -*-
"""Format de fichier binaire

Définition de l'en-tête (16 octets):

  +---+---------------------------------------+
  | s | "TECTONIC"                            |
  | B | numéro de version : '\x01'            |
  | B | Base.hauteur                          |
  | B | Base.largeur                          |
  | B | Base.maximum                          |
  | L | nombre total de codes                 |
  +---+---------------------------------------+

Définition d'un bloc:

  +---+---------------------------------------+
  | B | nombre de paires taille×nombre (<128) |
  | B | taille 'k'                            |
  | L | nombre de code pour la taille 'k'     |
  +---+---------------------------------------+

  puis:

   nombre[0] codes de longueur taille[0]
   nombre[1] codes de longueur taille[1]
   …

Définition du marqueur de fin (1 octet):

  +---+---------------------------------------+
  | B | marqueur de fin : '\b10000000'        |
  +---+---------------------------------------+
"""

import os
import struct

from . import Base


class Écrivain:
    """Format ressemblant à un flux
    """

    FORMAT = 1

    def __init__(self, chemin, base, bloc=0):
        """Prépare une nouvelle sortie

        'bloc' détermine le nombre de codes par bloc. Si < 1, on cherchera
        à minimiser le nombre de blocs.
        """
        assert bloc >= 0, "Valeur positive ou nulle"
        self.bloc = bloc

        self.sortie = open(chemin, "wb")

        # Écriture de l'en-tête
        self.sortie.write(b"TECTONIC\x01")
        self.sortie.write(
            struct.pack(">BBB", base.hauteur, base.largeur, base.maximum))

        # Réservation de 4 octets pour la taille
        self.sortie.write(b"\x00" * 4)

        self._nb_codes = 0

        # Le cache est par taille de code (en octets)
        self._nb_codes_en_attente = 0
        self.cache = dict()

    @property
    def nb_codes(self):
        """Nombre total d'enregistrements disponibles
        """
        return self._nb_codes + self._nb_codes_en_attente

    def purger(self):
        """Transfère les codes en cache dans le fichier
        """
        tailles = sorted(self.cache)

        while len(tailles) > 0:
            # Marqueur de structure
            nb_tailles = min(127, len(tailles))
            self.sortie.write(struct.pack(">B", nb_tailles))

            # Structure
            for taille in tailles[:nb_tailles]:
                self.sortie.write(
                    struct.pack(">BL", taille, len(self.cache[taille])))

            # Contenu
            for taille in tailles[:nb_tailles]:
                for code in self.cache[taille]:
                    self.sortie.write(
                        code.to_bytes(length=taille,
                                      byteorder="big",
                                      signed=False))
                self._nb_codes += len(self.cache[taille])

            # Itération
            del tailles[:nb_tailles]

        # Suppression du cache
        self._nb_codes_en_attente = 0
        self.cache.clear()

    def ajouter(self, code):
        nb_bits = max(1, code.bit_length())
        nb_octets = (nb_bits + 7) // 8
        self.cache.setdefault(nb_octets, list()).append(code)
        self._nb_codes_en_attente += 1

        if self._nb_codes_en_attente == self.bloc:
            self.purger()

    def clore(self):
        if self._nb_codes_en_attente != 0:
            self.purger()

        # Écriture du marqueur de fin de flux
        self.sortie.write(struct.pack(">B", 128))

        # Écriture de la taille
        self.sortie.seek(12, os.SEEK_SET)
        self.sortie.write(struct.pack(">L", self._nb_codes))

        # Fermeture
        self.sortie.close()
        self.sortie = None


class Lecteur:

    FORMAT = 1

    def __init__(self, chemin):
        self.chemin = chemin
        self.entrée = open(chemin, "rb")

        # Vérification du prélude
        prélude = self.entrée.read(9)
        assert prélude == b"TECTONIC\x01"

        # Dimensions
        tampon = self.entrée.read(3)
        hauteur, largeur, maximum = struct.unpack(">3B", tampon)
        self._base = Base(largeur=largeur, hauteur=hauteur, maximum=maximum)

        # Nombre de codes
        tampon = self.entrée.read(4)
        self.nb_codes = struct.unpack(">L", tampon)[0]

        # Préparation de l'itération
        self.fin_rencontrée = False
        self.id_code = 0
        self.cache = list()

    @property
    def base(self):
        """Base commune à tous les codes
        """
        return self._base

    def __iter__(self):
        self.entrée.seek(16, os.SEEK_SET)
        self.fin_rencontrée = False
        self.id_code = 0
        self.cache.clear()
        return self

    def __next__(self):
        if len(self.cache) == 0:
            self._charger()
        if self.fin_rencontrée:
            raise StopIteration
        else:
            taille, nombre = self.cache[0]
            retour = int.from_bytes(self.entrée.read(taille),
                                    byteorder="big",
                                    signed=False)
            self.id_code += 1
            nombre -= 1
            if nombre == 0:
                del self.cache[0]
            else:
                self.cache[0] = (taille, nombre)
            return retour

    def _charger(self):
        marqueur = struct.unpack(">B", self.entrée.read(1))[0]
        if marqueur > 127:
            self.fin_rencontrée = True
        else:
            for k in range(marqueur):
                paire = struct.unpack(">BL", self.entrée.read(5))
                self.cache.append(paire)
