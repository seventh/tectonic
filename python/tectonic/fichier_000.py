# -*- coding: utf-8 -*-
"""Format de fichier en texte clair

Définition de l'en-tête (10 octets):

  +---+---------------------------------------+
  | s | "TECTONIC"                            |
  | B | numéro de version : '\x00'            |
  | B | saut de ligne                         |
  +---+---------------------------------------+

Puis, en clair :

  Base.hauteur
  Base.largeur
  Base.maximum
  nombre total de codes

Puis :

  1 entier par ligne (×nombre fois)

Définition du marqueur de fin (3 octets):

  +---+---------------------------------------+
  | s | "-1"                                  |
  | B | saut de ligne                         |
  +---+---------------------------------------+
"""

import os

from . import Base


class Écrivain:

    FORMAT = 0

    def __init__(self, chemin, base):
        self.sortie = open(chemin, "wt")

        # Écriture de l'en-tête
        self.sortie.write("TECTONIC\x00\n")
        self.sortie.write(str(base.hauteur) + "\n")
        self.sortie.write(str(base.largeur) + "\n")
        self.sortie.write(str(base.maximum) + "\n")

        # Réservation de 10 caractères pour la taille
        self._taille = self.sortie.tell()
        self.sortie.write("0         \n")

        self._nb_codes = 0

    @property
    def nb_codes(self):
        """Nombre total d'enregistrements disponibles
        """
        return self._nb_codes

    def purger(self):
        self.sortie.flush()

    def ajouter(self, valeur):
        self.sortie.write(str(valeur) + "\n")
        self._nb_codes += 1

    def clore(self):
        # Écriture du marqueur de fin de flux
        self.sortie.write("-1\n")

        # Écriture de la taille
        self.sortie.seek(self._taille, os.SEEK_SET)
        self.sortie.write(f"{self._nb_codes: <10d}\n")

        # Fermeture
        self.sortie.close()
        self.sortie = None


class Lecteur:

    FORMAT = 0

    def __init__(self, chemin):
        self.chemin = chemin
        self.entrée = open(chemin, "rt")

        # Vérification du prélude
        prélude = self.entrée.readline()
        assert prélude == "TECTONIC\x00\n"

        # Dimensions
        hauteur = int(self.entrée.readline())
        largeur = int(self.entrée.readline())
        maximum = int(self.entrée.readline())
        self._base = Base(largeur=largeur, hauteur=hauteur, maximum=maximum)

        # Nombre de codes
        self.nb_codes = int(self.entrée.readline())

        # Préparation de l'itération
        self.fin_rencontrée = False
        self.id_ligne = 0
        self._décalage = self.entrée.tell()

    @property
    def base(self):
        """Base commune à tous les codes
        """
        return self._base

    def __iter__(self):
        self.entrée.seek(self._décalage, os.SEEK_SET)
        self.id_ligne = 0
        return self

    def __next__(self):
        retour = int(self.entrée.readline())
        if retour == -1:
            raise StopIteration
        else:
            self.id_ligne += 1
            return retour
