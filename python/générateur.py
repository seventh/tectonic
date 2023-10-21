#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Générateur de grille complète
"""

import copy
import dataclasses
import getopt
import itertools
import logging
import os.path
import re
import sys

from tectonic import Base
from tectonic import Case
from tectonic import Grille
from tectonic.fichier1 import Lecteur
from tectonic.fichier1 import Écrivain
from tectonic.serial2 import Codec


@dataclasses.dataclass
class Configuration:

    hauteur: int = 5
    largeur: int = 4
    maximum: int = 5
    chemin: str = "../data"

    def __eq__(self, autre):
        return (self.hauteur == autre.hauteur and self.largeur == autre.largeur
                and self.maximum == autre.maximum
                and self.chemin == autre.chemin)

    @staticmethod
    def charger():
        retour = Configuration()
        opts, args = getopt.getopt(sys.argv[1:], "h:l:m:")
        for opt, val in opts:
            if not val.isdecimal():
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
        if len(args) != 0:
            retour.chemin = args[0]

        return retour

    def base(self):
        return Base(hauteur=self.hauteur,
                    largeur=self.largeur,
                    maximum=self.maximum)


class Progression:
    """Progrès de recherche : base & palier atteints
    """

    def __init__(self, palier, hauteur, largeur, maximum):
        self.palier = palier
        self.hauteur = hauteur
        self.largeur = largeur
        self.maximum = maximum

    def __str__(self):
        return (f"p{self.palier}"
                f"h{self.hauteur}"
                f"l{self.largeur}"
                f"m{self.maximum}")

    def __repr__(self):
        return (f"{self.__class__.__name__}[0x{id(self):x}]"
                f"(palier={self.palier},"
                f"hauteur={self.hauteur},"
                f"largeur={self.largeur},"
                f"maximum={self.maximum})")

    _REGEX = re.compile("p(\\d+)h(\\d+)l(\\d+)m(\\d+)")

    @staticmethod
    def depuis_chaîne(chaîne):
        retour = None
        m = Progression._REGEX.search(chaîne)
        if m:
            retour = Progression(*(int(x) for x in m.groups()))
        return retour

    def base(self):
        return Base(hauteur=self.hauteur,
                    largeur=self.largeur,
                    maximum=self.maximum)


def identifier_meilleur_départ(conf):
    """Renvoie une paire (Progression, str)

    Si str est différent de None, c'est un chemin d'accès à un fichier en
    lecture
    """
    meilleur_fichier = None
    meilleur_progrès = None
    extension_min = None

    _, _, fichiers = next(os.walk(conf.chemin))
    for f in fichiers:
        p = Progression.depuis_chaîne(f)
        if p is not None:
            éligible = False
            if p.maximum >= conf.maximum:
                if p.largeur == conf.largeur:
                    if p.hauteur == conf.hauteur:
                        éligible = True
                    elif p.palier <= (min(p.hauteur, conf.hauteur) -
                                      1) * p.largeur:
                        éligible = True
                elif p.palier < p.largeur < conf.largeur:
                    éligible = True
            if éligible:
                # À choisir, on ne veut pas à avoir à modifier le nombre de
                # cases. Si ce n'est pas possible, on veut optimiser les temps
                # de chargement, ce qui signifie :
                # - s'il faut rajouter des cases, en ajouter le plus possible ;
                # - s'il faut en retirer, en retirer le moins possible.
                extension = conf.hauteur * conf.largeur - p.hauteur * p.largeur
                if (meilleur_fichier is None
                        or p.palier > meilleur_progrès.palier or
                    (p.palier == meilleur_progrès.palier and
                     (p.maximum < meilleur_progrès.maximum or
                      (p.maximum == meilleur_progrès.maximum and
                       (extension == 0 or extension > extension_min))))):
                    meilleur_progrès = p
                    meilleur_fichier = f
                    extension_min = extension

    if meilleur_fichier is None:
        return (Progression(0, conf.hauteur, conf.largeur, conf.maximum), None)
    else:
        return (meilleur_progrès, meilleur_fichier)


def convertir(conf, progrès, nom_fichier):
    logging.info(f"Conversion depuis «{nom_fichier}»")

    # Chargement de tous les codes, et conversion à la volée
    lecteur = Lecteur(os.path.join(conf.chemin, nom_fichier))
    codec = Codec()
    codes = [None] * lecteur.nb_codes
    nb_codes = 0

    filtrage_case_par_case = (progrès.maximum != conf.maximum)
    extension = conf.base().nb_cases() - progrès.base().nb_cases()

    if extension <= 0:
        cases_ext = None
    else:
        cases_ext = [None] * extension
        for i in range(extension):
            cases_ext[i] = Case()

    for code in lecteur:
        grille = codec.décoder(code)

        retenu = True
        if filtrage_case_par_case:
            for case in grille.cases[:progrès.palier]:
                if case.valeur > conf.maximum:
                    retenu = False
                    break
            else:
                grille.base.maximum = conf.maximum

        if retenu:
            if extension != 0:
                grille.base.hauteur = conf.hauteur
                grille.base.largeur = conf.largeur
                if extension > 0:
                    grille.cases.extend(cases_ext)
                elif extension < 0:
                    del grille.cases[extension:]

            code = codec.encoder(grille)
            codes[nb_codes] = code
            nb_codes += 1

    del codes[nb_codes:]
    codes.sort()

    # Écriture pour capitaliser sur ces résultats
    progrès = Progression(progrès.palier, conf.hauteur, conf.largeur,
                          conf.maximum)
    nom_fichier = str(progrès) + ".log"

    écrivain = Écrivain(os.path.join(conf.chemin, nom_fichier))
    for code in codes:
        écrivain.ajouter(code)
    del écrivain

    return progrès, nom_fichier


@dataclasses.dataclass
class Région:
    """Ensemble de valeurs connexes et nombre de bords libres
    """

    valeurs: set = dataclasses.field(default_factory=set)
    bordure: int = 0

    def __eq__(self, autre):
        return (self.valeurs == autre.valeurs
                and self.bordure == autre.bordure)

    def est_anormal(self):
        """Une Zone est anormale si elle est fermée et ne contient pas toutes
        les valeurs prévues
        """
        retour = False
        if self.bordure == 0 and self.est_incomplète():
            retour = True
        return retour

    def est_incomplète(self):
        """Vrai ssi les valeurs ne forment pas un intervalle continu
        débutant à 1
        """
        retour = False
        n = 0
        minimum = None
        maximum = None
        for v in self.valeurs:
            n += 1
            if n == 1:
                minimum = v
                maximum = v
            elif v < minimum:
                minimum = v
            elif v > maximum:
                maximum = v
        if minimum != 1 or n != maximum - minimum + 1:
            retour = True
        return retour


class Scholdu:

    def __init__(self, grille):
        self.g = grille
        self.régions = dict()

        self._calculer()

    def _calculer(self):
        for i, case in enumerate(self.g.cases):
            r1 = case.région
            if r1 >= 0:
                if case.valeur > 0:
                    self.régions.setdefault(r1,
                                            Région()).valeurs.add(case.valeur)

                h1, l1 = self.g.base.en_position(i)
                for h2, l2 in [(h1, l1 + 1), (h1 + 1, l1)]:
                    if (h2 < self.g.base.hauteur and l2 < self.g.base.largeur):
                        j = self.g.base.en_index(hauteur=h2, largeur=l2)
                        if self.g.cases[j].région < 0:
                            self.régions.setdefault(r1, Région()).bordure += 1

    def région_max(self):
        return max(self.régions, default=-1)


class GénérateurPremierPalier:

    def __init__(self, base):
        grille = Grille(base)
        self.code = Codec().encoder(grille)

        self.a_produit = True

    def __iter__(self):
        self.a_produit = False
        return self

    def __next__(self):
        if self.a_produit:
            raise StopIteration
        else:
            self.a_produit = True
            return self.code


def valider(grille):
    retour = True
    scholdu = Scholdu(grille)
    for r in scholdu.régions.values():
        if r.est_anormal():
            retour = False
    return retour


class Chercheur:

    def __init__(self, conf, progrès, nom_fichier):
        self.conf = conf
        self.progrès = progrès
        self.nom_fichier = nom_fichier

    def trouver(self):
        codec = Codec()
        palier_max = self.conf.base().nb_cases()
        trace = False
        while self.progrès.palier < palier_max:
            if self.nom_fichier is None:
                if not trace:
                    logging.info("Initialisation du contexte")
                    trace = True
                lecteur = GénérateurPremierPalier(self.conf.base())
            else:
                lecteur = Lecteur(
                    os.path.join(self.conf.chemin, self.nom_fichier))
                if not trace:
                    logging.info(f"Reprise depuis «{self.nom_fichier}» : "
                                 f"{lecteur.nb_codes} grilles")
                    trace = True

            étage = set()
            for code in lecteur:
                grille = codec.décoder(code)
                nouvelles = self.prochaines(grille)
                for nouvelle in nouvelles:
                    if (self.progrès.palier != palier_max - 1
                            or self.valider(nouvelle)):
                        nouveau_code = codec.encoder(nouvelle)
                        étage.add(nouveau_code)

            étage = sorted(étage)

            self.progrès.palier += 1
            self.nom_fichier = str(self.progrès) + ".log"

            logging.info(f"Palier n°{self.progrès.palier} atteint : "
                         f"{len(étage)} grilles")

            écrivain = Écrivain(
                os.path.join(self.conf.chemin, self.nom_fichier))
            for code in étage:
                écrivain.ajouter(code)
            del écrivain

        # Écriture finale
        lecteur = Lecteur(os.path.join(self.conf.chemin, self.nom_fichier))
        écrivain = Écrivain(
            os.path.join(self.conf.chemin, (f"h{self.conf.hauteur}"
                                            f"l{self.conf.largeur}"
                                            f"m{self.conf.maximum}"
                                            ".log")))
        for code in lecteur:
            écrivain.ajouter(code)

    def prochaines(self, grille_initiale):
        """Remplissage de la prochaine case
        """
        retour = list()

        i = self.progrès.palier
        h, l = grille_initiale.base.en_position(self.progrès.palier)
        scholdu = Scholdu(grille_initiale)

        # Régions à compléter
        nb_régions = 0
        régions = set()
        # → case du dessus
        if h > 0:
            nb_régions += 1
            régions.add(grille_initiale[(h - 1, l)].région)
        # → case de gauche
        if l > 0:
            nb_régions += 1
            régions.add(grille_initiale[(h, l - 1)].région)
        régions = sorted(régions)

        # Calcul des valeurs possibles au minimum, selon la règle du voisinage
        valeurs_possibles = set(range(1, grille_initiale.base.maximum + 1))
        if l > 0:
            valeurs_possibles.discard(grille_initiale[(h, l - 1)].valeur)
        if h > 0:
            valeurs_possibles.discard(grille_initiale[(h - 1, l)].valeur)
            if l > 0:
                valeurs_possibles.discard(grille_initiale[(h - 1,
                                                           l - 1)].valeur)
            if l + 1 < grille_initiale.base.largeur:
                valeurs_possibles.discard(grille_initiale[(h - 1,
                                                           l + 1)].valeur)

        # 1) On étend chacune des régions de toutes les façons possibles
        if len(régions) == 1:
            r = régions[0]
            valeurs = valeurs_possibles.difference(scholdu.régions[r].valeurs)
            for v in valeurs:
                grille = copy.deepcopy(grille_initiale)
                grille.cases[i].région = r
                grille.cases[i].valeur = v
                retour.append(grille)
        else:
            for r1, r2 in itertools.permutations(régions, 2):
                # On vérifie qu'on ne rendrait pas «r2» anormale de toute pièce
                if not (scholdu.régions[r2].bordure == 1
                        and scholdu.régions[r2].est_incomplète()):
                    valeurs = valeurs_possibles.difference(
                        scholdu.régions[r1].valeurs)
                    for v in valeurs:
                        grille = copy.deepcopy(grille_initiale)
                        grille.cases[i].région = r1
                        grille.cases[i].valeur = v
                        retour.append(grille)

        # 2) On fusionne les régions voisines
        for r1, r2 in itertools.combinations(régions, 2):
            if scholdu.régions[r1].valeurs.isdisjoint(
                    scholdu.régions[r2].valeurs):
                valeurs = valeurs_possibles.difference(
                    scholdu.régions[r1].valeurs)
                valeurs.difference_update(scholdu.régions[r2].valeurs)
                if len(valeurs) > 0:
                    grille_modèle = copy.deepcopy(grille_initiale)
                    for case in grille_modèle.cases:
                        if case.région == r2:
                            case.région = r1
                    for v in valeurs:
                        grille = copy.deepcopy(grille_modèle)
                        grille.cases[i].région = r1
                        grille.cases[i].valeur = v
                        grille.normaliser()
                        retour.append(grille)

        # 3) On crée une toute nouvelle région, en veillant à ce qu'elle ne
        # puisse pas être incomplète
        génération_autorisée = True
        if len(régions) == 1:
            r = régions[0]
            if (scholdu.régions[r].bordure == nb_régions
                    and scholdu.régions[r].est_incomplète()):
                génération_autorisée = False
        elif len(régions) == 2:
            for r in régions:
                if (scholdu.régions[r].bordure == 1
                        and scholdu.régions[r].est_incomplète()):
                    génération_autorisée = False

        if génération_autorisée:
            for v in valeurs_possibles:
                if True or v <= grille_initiale.base.nb_cases() - i:
                    grille = copy.deepcopy(grille_initiale)
                    grille.cases[i].région = scholdu.région_max() + 1
                    grille.cases[i].valeur = v
                    retour.append(grille)

        # Production des nouveaux états
        return retour

    def valider(self, grille):
        retour = True
        scholdu = Scholdu(grille)
        for r in scholdu.régions.values():
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
