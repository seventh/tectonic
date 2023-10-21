# -*- coding: utf-8 -*-
"""Format de fichier en texte clair

1 entier par ligne, au format `serial2`.
Le fichier est éventuellement terminé par la valeur "-1"
"""

import logging
import os


class Écrivain:

    def __init__(self, chemin):
        self.sortie = open(chemin, "wt")

    def __del__(self):
        self.sortie.write("-1\n")
        self.sortie.close()
        self.sortie = None

    def ajouter(self, valeur):
        self.sortie.write(str(valeur) + "\n")


class Lecteur:

    def __init__(self, chemin):
        self.chemin = chemin
        self.entrée = open(chemin, "rt")

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
