# -*- coding: utf-8 -*-

import getopt
import logging
import sys

from tectonic import Base
from tectonic import Lecteur
from tectonic.fichier_001 import Lecteur as LecteurBinaire


class Configuration:

    def __init__(self):
        self.lots = list()
        self.debug = False

    @staticmethod
    def charger():
        retour = Configuration()

        base = None
        hauteur = None
        largeur = None
        maximum = None
        opts, args = getopt.getopt(sys.argv[1:], "f:gh:l:m:")
        for opt, val in opts:
            if opt == "-f":
                retour.lots.append(LecteurBinaire(val))
            elif opt == "-g":
                retour.debug = True
            elif not val.isdecimal():
                logging.warning(f"Option {opt}{val} incorrecte")
            else:
                val = int(val)
                if opt == "-h":
                    hauteur = val
                elif opt == "-l":
                    largeur = val
                elif opt == "-m":
                    maximum = val
        codes = [int(c) for c in args]
        if not (hauteur is None and largeur is None and maximum is None):
            if not (hauteur is None or largeur is None or maximum is None):
                base = Base(hauteur=hauteur, largeur=largeur, maximum=maximum)
            else:
                if hauteur is not None:
                    logging.warning(
                        f"Option -h{hauteur} ignorée : base incomplète")
                if largeur is not None:
                    logging.warning(
                        f"Option -l{largeur} ignorée : base incomplète")
                if maximum is not None:
                    logging.warning(
                        f"Option -m{maximum} ignorée : base incomplète")
        if len(codes) > 0:
            if base is None:
                logging.warning("Arguments ignorés : base incomplète")
            else:
                retour.lots.append(Lecteur(base, codes))

        return retour
