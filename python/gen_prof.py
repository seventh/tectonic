#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Générateur de grille complète

À la différence du générateur original, celui-ci adopte une approche en
profondeur d'abord.
"""

import dataclasses
import getopt
import itertools
import logging
import os.path
import sys

from tectonic import Base
from tectonic import Case
from tectonic import Grille
from tectonic import Progrès
from tectonic.fichier import lecteur as get_lecteur
from tectonic.fichier import écrivain as get_écrivain
from tectonic.serial import Codec


@dataclasses.dataclass
class Configuration:

    hauteur: int = 5
    largeur: int = 4
    maximum: int = 5
    chemin: str = "../data"

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


def charger_avancement(conf):
    """Met en place un contexte propre pour reprendre la génération
    """
    # A priori, c'est simple : pour générer une grille (H, L, M), on
    # a besoin de tous les paliers intermédiaires, jusqu'à rencontrer
    # le palier le plus grand dont le fichier est complet. Le plus petit
    # palier à considérer est celui fourni par 'identifier_meilleur_départ'

    # Cela pose la question des paliers complets ou non. Un fichier sans
    # marqueur de fin est par construction incomplet, c'est le sens même du
    # marqueur
    pass


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


@dataclasses.dataclass
class Région:
    """Ensemble de valeurs connexes et nombre de bords libres
    """

    # Valeurs des cases de la région
    valeurs: set = dataclasses.field(default_factory=set)
    # Identifiants des régions voisines
    voisins: set = dataclasses.field(default_factory=set)
    # Nombre de cases limitrophes libres
    bordure: int = 0

    def __eq__(self, autre):
        return (self.valeurs == autre.valeurs and self.voisins == autre.voisins
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
        débutant à 1. Toutes les valeurs autorisées n'ont pas à être
        représentées (dans une grille autorisant le 5, une région avec les
        quatre valeurs 1, 2, 3, 4 sera considérée complète)
        """
        n = len(self.valeurs)
        if n == 0:
            return True

        minimum = min(self.valeurs)
        if minimum != 1:
            return True

        maximum = max(self.valeurs)
        if n != maximum - minimum + 1:
            return True

        return False


class Analyseur:
    """Analyse d'une grille

    Cette analyse consiste à identifier, région par région, les valeurs dont
    elles sont constituées, ainsi que les identifiants des régions connexes,
    et le nombre de cases limitrophes libres.
    """

    def __init__(self, grille):
        self.g = grille
        self.régions = dict()

        self._calculer()

    def _calculer(self):
        bords = dict()

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
                        r2 = self.g.cases[j].région
                        if r2 < 0:
                            bords.setdefault(r1, set()).add(j)
                        elif r2 != r1:
                            self.régions.setdefault(r1,
                                                    Région()).voisins.add(r2)
                            self.régions.setdefault(r2,
                                                    Région()).voisins.add(r1)

        for r, cases in bords.items():
            self.régions[r].bordure = len(cases)

    def région_max(self):
        return max(self.régions, default=-1)


class GénérateurPremierPalier:

    def __init__(self, base):
        grille = Grille(base)
        self.code = Codec(base).encoder(grille)

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


class ProducteurProgrès:

    def __init__(self, progrès):
        self.palier = progrès.palier
        self.codec = Codec(progrès.base())

    def itérer(self, code):
        """Itérateur des grilles du palier suivant
        """
        grille = self.codec.décoder(code)
        analyseur = Analyseur(grille)

        i = self.palier
        h, l = grille.base.en_position(i)

        # Régions à compléter
        régions = set()
        # → case du dessus
        if h > 0:
            régions.add(grille[(h - 1, l)].région)
        # → case de gauche
        if l > 0:
            régions.add(grille[(h, l - 1)].région)
        régions = sorted(régions)

        # Calcul des valeurs possibles au maximum, selon la règle du voisinage
        valeurs_possibles = set(range(1, grille.base.maximum + 1))
        if l > 0:
            valeurs_possibles.discard(grille[(h, l - 1)].valeur)
        if h > 0:
            valeurs_possibles.discard(grille[(h - 1, l)].valeur)
            if l > 0:
                valeurs_possibles.discard(grille[(h - 1, l - 1)].valeur)
            if l + 1 < grille.base.largeur:
                valeurs_possibles.discard(grille[(h - 1, l + 1)].valeur)

        # 1) On étend chacune des régions de toutes les façons possibles
        if len(régions) == 1:
            r = régions[0]
            valeurs = valeurs_possibles.difference(
                analyseur.régions[r].valeurs)
            for v in valeurs:
                grille.cases[i].région = r
                grille.cases[i].valeur = v
                yield self.codec.encoder(grille)
        else:
            for r1, r2 in itertools.permutations(régions, 2):
                # On vérifie qu'on ne rendrait pas «r2» incomplète de toute
                # pièce
                if not (analyseur.régions[r2].bordure == 1
                        and analyseur.régions[r2].est_incomplète()):
                    valeurs = valeurs_possibles.difference(
                        analyseur.régions[r1].valeurs)
                    for v in valeurs:
                        grille.cases[i].région = r1
                        grille.cases[i].valeur = v
                        yield self.codec.encoder(grille)

        # 2) On crée une toute nouvelle région, en veillant à ce qu'elle ne
        # puisse pas être incomplète
        for r in régions:
            if (analyseur.régions[r].bordure == 1
                    and analyseur.régions[r].est_incomplète()):
                break
        else:
            for v in valeurs_possibles:
                grille.cases[i].région = analyseur.région_max() + 1
                grille.cases[i].valeur = v
                yield self.codec.encoder(grille)

        # 3) On fusionne les régions voisines
        for r1, r2 in itertools.combinations(régions, 2):
            if (r2 not in analyseur.régions[r1].voisins
                    and analyseur.régions[r1].valeurs.isdisjoint(
                        analyseur.régions[r2].valeurs)):
                valeurs = valeurs_possibles.difference(
                    analyseur.régions[r1].valeurs)
                valeurs.difference_update(analyseur.régions[r2].valeurs)
                if len(valeurs) > 0:
                    for case in grille.cases:
                        if case.région == r2:
                            case.région = r1
                    grille.cases[i].région = r1
                    grille.normaliser()
                    for v in valeurs:
                        grille.cases[i].valeur = v
                        yield self.codec.encoder(grille)


class Chercheur:

    def __init__(self, conf):
        self.conf = conf

    def trouver(self):
        base = self.conf.base()

        producteurs = list()
        enregistreurs = list()
        for palier in range(base.nb_cases() + 1):
            progrès = Progrès(base.hauteur, base.largeur, base.maximum, palier)

            if palier < base.nb_cases():
                producteurs.append(ProducteurProgrès(progrès))

            chemin = os.path.join(self.conf.chemin, str(progrès) + ".gle")
            enregistreurs.append(get_écrivain(chemin, base))

        itérateurs = [iter(GénérateurPremierPalier(base))]
        while len(itérateurs) != 0:
            k = len(itérateurs) - 1
            it = itérateurs[-1]
            try:
                # Code appartenent au palier 'k'
                code = next(it)
                if k < len(producteurs):
                    enregistreurs[k].ajouter(code)
                    itérateurs.append(producteurs[k].itérer(code))
                else:
                    grille = producteurs[-1].codec.décoder(code)
                    analyse = Analyseur(grille)
                    for r in analyse.régions.values():
                        if r.est_anormal():
                            break
                    else:
                        enregistreurs[-1].ajouter(code)
            except StopIteration:
                itérateurs.pop()

        for e in enregistreurs:
            e.clore()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    CONF = Configuration.charger()
    logging.info(CONF)

    CHERCHEUR = Chercheur(CONF)
    CHERCHEUR.trouver()
