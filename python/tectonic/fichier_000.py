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

Définition du marqueur de fin (1 octet):

  +---+---------------------------------------+
  | B | marqueur de fin : '\b10000000'        |
  +---+---------------------------------------+
"""

import logging
import os
import os.path

from . import Progrès


class Écrivain:

    def __init__(self, chemin, base):
        self.sortie = open(chemin, "wt")
        self._nb_codes = 0

    @property
    def nb_codes(self):
        """Nombre total d'enregistrements disponibles
        """
        return self._nb_codes

    def configurer(self, base):
        # Rien à faire. Présent simplement pour assurer la compatibilité avec
        # d'autres formats
        pass

    def ajouter(self, valeur):
        self.sortie.write(str(valeur) + "\n")
        self._nb_codes += 1

    def clore(self):
        self.sortie.write("-1\n")
        self.sortie.close()
        self.sortie = None


class Lecteur:

    def __init__(self, chemin):
        self.chemin = chemin
        self.entrée = open(chemin, "rt")

        progrès = Progrès.depuis_chaîne(os.path.basename(chemin))
        self._base = progrès.base()

        # Détermination du nombre total d'enregistrements disponibles
        self._nb_codes = 0
        ligne = None
        for ligne in self.entrée:
            self._nb_codes += 1
        if ligne != "-1\n":
            logging.warning(
                f"Le fichier «{os.path.basename(chemin)}» peut être incomplet."
            )
        else:
            self._nb_codes -= 1

        # Numéro de la prochaine ligne à lire
        self.id_ligne = 0

    @property
    def base(self):
        """Base commune à tous les codes
        """
        return self._base

    def __iter__(self):
        self.entrée.seek(0, 0)
        self.id_ligne = 0
        return self

    def __next__(self):
        if self.id_ligne == self._nb_codes:
            raise StopIteration
        else:
            retour = int(self.entrée.readline())
            self.id_ligne += 1
            return retour

    @property
    def nb_codes(self):
        """Nombre total d'enregistrements disponibles
        """
        return self._nb_codes
