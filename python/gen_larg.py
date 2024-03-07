#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Générateur de grille complète
"""

import dataclasses
import getopt
import logging
import os.path
import sys

from tectonic import Base
from tectonic import Case
from tectonic import Progrès
from tectonic.fichier import lecteur as get_lecteur
from tectonic.fichier import écrivain as get_écrivain
from tectonic.serial import Codec
from générateur import Analyseur
from générateur import ProducteurProgrès
from générateur import GénérateurGrilleVide


@dataclasses.dataclass
class Configuration:

    hauteur: int = 5
    largeur: int = 4
    maximum: int = 5
    chemin: str = "../data"
    mono_palier: bool = False
    palier_max: int = None
    strict: bool = False

    @staticmethod
    def charger():
        retour = Configuration()
        opts, args = getopt.getopt(sys.argv[1:], "h:l:m:qs:", ["strict"])
        for opt, val in opts:
            if opt == "--strict":
                retour.strict = True
            elif opt == "-q":
                retour.mono_palier = True
            elif not val.isdecimal():
                logging.warning(f"Option «{opt} {val}» ignorée")
                continue
            else:
                val = int(val)
                if opt == "-h" and val > 0:
                    retour.hauteur = val
                elif opt == "-l" and val > 0:
                    retour.largeur = val
                elif opt == "-m" and val > 2:
                    retour.maximum = val
                elif opt == "-s" and val > 0:
                    retour.palier_max = val
        if len(args) != 0:
            retour.chemin = args[0]

        if (retour.palier_max is None
                or retour.palier_max > retour.hauteur * retour.largeur):
            retour.palier_max = retour.hauteur * retour.largeur

        return retour

    def base(self):
        return Base(hauteur=self.hauteur,
                    largeur=self.largeur,
                    maximum=self.maximum)


def identifier_meilleur_départ(conf):
    """Renvoie une paire (Progrès, str)

    Si str est différent de None, c'est un chemin d'accès à un fichier en
    lecture
    """
    meilleur_fichier = None
    meilleur_progrès = None
    extension_min = None

    if not os.path.isdir(conf.chemin):
        os.makedirs(conf.chemin, mode=0o755)
    else:
        _, _, fichiers = next(os.walk(conf.chemin))
        for f in fichiers:
            p = Progrès.depuis_chaîne(f)
            if p is not None:
                éligible = False
                if conf.strict:
                    éligible = (p.largeur == conf.largeur
                                and p.hauteur == conf.hauteur
                                and p.maximum == conf.maximum)
                elif p.maximum >= conf.maximum:
                    if p.largeur == conf.largeur:
                        if p.hauteur == conf.hauteur:
                            éligible = True
                        elif p.palier <= (min(p.hauteur, conf.hauteur) -
                                          1) * p.largeur + 1:
                            éligible = True
                    elif p.palier < min(p.largeur, conf.largeur):
                        éligible = True
                if éligible:
                    # À choisir, on ne veut pas à avoir à modifier le nombre de
                    # cases. Si ce n'est pas possible, on veut optimiser les
                    # temps de chargement, ce qui signifie :
                    # - s'il faut rajouter des cases, en ajouter le plus
                    # possible ;
                    # - s'il faut en retirer, en retirer le moins possible.
                    extension = conf.base().nb_cases() - p.base().nb_cases()
                    if (meilleur_fichier is None
                            or p.palier > meilleur_progrès.palier
                            or (p.palier == meilleur_progrès.palier and
                                (p.maximum < meilleur_progrès.maximum or
                                 (p.maximum == meilleur_progrès.maximum and
                                  (extension == 0 or
                                   (extension_min != 0
                                    and extension > extension_min)))))):
                        meilleur_progrès = p
                        meilleur_fichier = f
                        extension_min = extension

    if meilleur_fichier is None:
        return (Progrès(hauteur=conf.hauteur,
                        largeur=conf.largeur,
                        maximum=conf.maximum,
                        palier=0), None)
    else:
        return (meilleur_progrès, meilleur_fichier)


def convertir(conf, progrès, nom_fichier):
    logging.info(f"Conversion depuis «{nom_fichier}»")

    # Configuration de la lecture
    lecteur = get_lecteur(os.path.join(conf.chemin, nom_fichier))
    décodeur = Codec(progrès.base())

    filtrage_case_par_case = (progrès.maximum != conf.maximum)
    extension = conf.base().nb_cases() - progrès.base().nb_cases()
    if extension <= 0:
        cases_ext = None
    else:
        cases_ext = [None] * extension
        for i in range(extension):
            cases_ext[i] = Case()

    # Configuration de l'écriture
    progrès = Progrès(hauteur=conf.hauteur,
                      largeur=conf.largeur,
                      maximum=conf.maximum,
                      palier=progrès.palier)
    encodeur = Codec(progrès.base())
    nom_fichier = str(progrès) + ".log"
    écrivain = get_écrivain(os.path.join(conf.chemin, nom_fichier),
                            progrès.base())

    # Conversion à la volée des codes
    for code in lecteur:
        grille = décodeur.décoder(code)

        retenu = True
        if filtrage_case_par_case:
            for case in grille.cases[:progrès.palier]:
                if case.valeur > conf.maximum:
                    retenu = False
                    break
            else:
                grille.base.maximum = conf.maximum

        if retenu:
            grille.base.hauteur = conf.hauteur
            grille.base.largeur = conf.largeur
            if extension > 0:
                grille.cases.extend(cases_ext)
            elif extension < 0:
                del grille.cases[extension:]

            code = encodeur.encoder(grille)
            écrivain.ajouter(code)
    écrivain.clore()

    return progrès, nom_fichier


class Chercheur:

    def __init__(self, conf, progrès, nom_fichier):
        self.conf = conf
        self.progrès = progrès
        self.nom_fichier = nom_fichier
        self.codec = Codec(progrès.base())

        self.nuls = 0
        self.consommés = 0
        self.produits = 0

    def trouver(self):
        base = self.conf.base()
        trace = False
        while self.progrès.palier < self.conf.palier_max:
            # Lecteur
            if self.nom_fichier is None:
                if not trace:
                    logging.info("Initialisation du contexte")
                    trace = True
                lecteur = GénérateurGrilleVide(base)
            else:
                lecteur = get_lecteur(
                    os.path.join(self.conf.chemin, self.nom_fichier))
                if not trace:
                    logging.info(f"Reprise depuis «{self.nom_fichier}» : "
                                 f"{lecteur.nb_codes} grilles")
                    trace = True

            # Écrivain
            self.progrès.palier += 1
            self.nom_fichier = str(self.progrès) + ".log"
            self.progrès.palier -= 1
            écrivain = get_écrivain(
                os.path.join(self.conf.chemin, self.nom_fichier),
                self.progrès.base())

            # Statistiques
            self.consommés = 0
            self.nuls = 0

            # Génération
            pp = ProducteurProgrès(self.progrès)
            for code in lecteur:
                self.consommés += 1
                nouveaux = list(pp.itérer(code))

                if len(nouveaux) == 0:
                    # logging.warning(f"Le code {code} est nullipare")
                    self.nuls += 1
                for neuf in nouveaux:
                    if (self.progrès.palier != base.nb_cases() - 1
                            or self.valider(neuf)):
                        écrivain.ajouter(neuf)

            # Itération
            self.progrès.palier += 1
            logging.info(
                f"Palier n°{self.progrès.palier} atteint : "
                f"{écrivain.nb_codes} grilles "
                f"(×{écrivain.nb_codes/self.consommés:.2f}) "
                f"et {self.nuls/self.consommés:.2%} nuls "
                f"→ ×{écrivain.nb_codes/(self.consommés-self.nuls):.2f}")
            écrivain.clore()

            # Génération d'un seul palier demandée
            if self.conf.mono_palier:
                break

    def valider(self, code):
        retour = True
        grille = self.codec.décoder(code)
        analyseur = Analyseur(grille)
        for r in analyseur.régions.values():
            if r.est_anormal():
                retour = False
        return retour


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    CONF = Configuration.charger()
    logging.info(CONF)

    # Chargement du meilleur contexte
    PROGRÈS, NOM_FICHIER = identifier_meilleur_départ(CONF)

    # Conversion si nécessaire
    if PROGRÈS.base() != CONF.base():
        PROGRÈS, NOM_FICHIER = convertir(CONF, PROGRÈS, NOM_FICHIER)
        assert PROGRÈS.base() == CONF.base()

    # Itérations
    CHERCHEUR = Chercheur(CONF, PROGRÈS, NOM_FICHIER)
    CHERCHEUR.trouver()
