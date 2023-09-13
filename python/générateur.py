#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Générateur de grille complète
"""

import copy
import dataclasses
import enum
import getopt
import logging
import os.path
import re
import sys

import serial


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

    def dimensions(self):
        return Dimension(hauteur=self.hauteur,
                         largeur=self.largeur,
                         maximum=self.maximum)


@dataclasses.dataclass
class Dimension:

    hauteur: int = 5
    largeur: int = 4
    maximum: int = 5

    def __eq__(self, autre):
        return (self.hauteur == autre.hauteur and self.largeur == autre.largeur
                and self.maximum == autre.maximum)

    def en_index(self, largeur, hauteur):
        # assert 0 <= largeur < self.largeur
        # assert 0 <= hauteur < self.hauteur

        return self.largeur * hauteur + largeur

    def transposition(self):
        """Intervertit hauteur et largeur
        """
        return Dimension(self.largeur, self.hauteur, self.maximum)


class Terrain(enum.IntEnum):
    """Différentes natures de terrain, fidèles au jeu «Tiwanaku»
    """

    herbe = enum.auto()
    roche = enum.auto()
    sable = enum.auto()
    terre = enum.auto()


@dataclasses.dataclass
class Case:
    """Valeur associée à un identifiant de zone
    """

    zone: int = -1
    case: int = -1

    def __eq__(self, autre):
        return (self.zone == autre.zone and self.case == autre.case)

    def est_valorisée(self):
        return self.case != -1


@dataclasses.dataclass
class Zone:
    """Ensemble de valeurs connexes et nombre de bords libres
    """

    valeurs: set = dataclasses.field(default_factory=set)
    bordure: int = 2

    def __eq__(self, autre):
        return (self.valeurs == autre.valeurs
                and self.bordure == autre.bordure)

    def est_anormal(self):
        """Une Zone est anormale si elle est fermée et ne contient pas toutes
        les valeurs prévues
        """
        retour = False
        if self.bordure == 0:
            minimum = None
            maximum = None
            n = 0
            for v in self.valeurs:
                n += 1
                if n == 1:
                    minimum = v
                    maximum = v
                else:
                    if v < minimum:
                        minimum = v
                    if v > maximum:
                        maximum = v
            if minimum != 1 or maximum != minimum + n - 1:
                retour = True
        return retour


class Grille:

    def __init__(self, conf):
        self.conf = conf

        self.cases = [None] * (conf.hauteur * conf.largeur)
        for i in range(len(self.cases)):
            self.cases[i] = Case()

        self.zones = list()

    def __eq__(self, autre):
        return (self.conf == autre.conf and self.cases == autre.cases
                and self.zones == autre.zones)

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        lignes = list()
        for id, zone in enumerate(self.zones):
            if zone is not None:
                lignes.append(f"{id} → {zone.bordure} bord(s) libres")
        return "\n".join(lignes)

    def __str__(self):
        lignes = list()
        sép_h = "+" + "-+" * self.conf.largeur

        for h in reversed(range(self.conf.hauteur)):
            # Séparateur horizontal
            if h == self.conf.hauteur - 1:
                ligne = sép_h
            else:
                ligne = str()

                for l in range(self.conf.largeur):
                    i = self.conf.largeur * h + l
                    j = i + self.conf.largeur

                    ligne += "+"

                    if (self.cases[i].zone != -1 and self.cases[j].zone != -1
                            and self.cases[i].zone != self.cases[j].zone):
                        ligne += "-"
                    else:
                        ligne += " "
                ligne += "+"
            lignes.append(ligne)

            # Valeurs des cases
            ligne = str()
            for l in range(self.conf.largeur):
                i = self.conf.en_index(l, h)
                j = i - 1
                if (l == 0 or
                    (self.cases[i].zone != -1 and self.cases[j].zone != -1
                     and self.cases[i].zone != self.cases[j].zone)):
                    ligne += "|"
                else:
                    ligne += " "

                if self.cases[i].est_valorisée():
                    ligne += str(self.cases[i].case)
                else:
                    ligne += "."
            ligne += "|"
            lignes.append(ligne)
        lignes.append(sép_h)

        retour = "\n".join(lignes)
        return retour

    def normaliser(self):
        """Assure un ordre de numérotation entre Zones
        """
        logging.debug("Normalisation !")
        logging.debug(self)
        logging.debug(self.zones)
        permutation = list()
        for i in range(self.conf.largeur * self.conf.hauteur):
            case = self.cases[i]
            zone = case.zone
            if zone != -1 and zone not in permutation:
                permutation.append(zone)

        utile = False
        if len(self.zones) != len(permutation):
            utile = True
        else:
            for après, avant in enumerate(permutation):
                if après != avant:
                    utile = True
                    logging.debug("Cas pas évident")
                    break

        if utile:
            for i in range(self.conf.largeur * self.conf.hauteur):
                case = self.cases[i]
                zone = case.zone
                if zone != -1:
                    case.zone = permutation.index(case.zone)
            self.zones[:] = [self.zones[p] for p in permutation]
        else:
            logging.debug("appel de merde")

        logging.debug("Fin de normalisation")
        logging.debug(utile)
        logging.debug(self)
        logging.debug(self.zones)
        logging.debug("===")

    def prochains(self):
        retour = list()

        # Recherche de la première case affichable non valuée
        trouvé = False
        for h in range(self.conf.hauteur):
            for l in range(self.conf.largeur):
                i = self.conf.en_index(l, h)
                if not self.cases[i].est_valorisée():
                    trouvé = True
                    break
            if trouvé:
                break

        # Prochains états
        if trouvé:
            # On identifie les zones à compléter
            zones = list()
            if l > 0:
                zones.append(self.cases[i - 1].zone)
            if h > 0:
                zones.append(self.cases[i - self.conf.largeur].zone)
            zones.sort()

            # On ajoute toutes les cases possibles pour chaque zone
            # identifiée
            déjà = list()
            for z in zones:
                if z not in déjà:
                    valeurs = self._valeurs_possibles(l, h, z)
                    for v in valeurs:
                        grille = copy.deepcopy(self)
                        grille.cases[i].zone = z
                        grille.cases[i].case = v
                        grille.zones[z].valeurs.add(v)

                        zone = grille.zones[z]
                        if l < self.conf.largeur - 1:
                            zone.bordure += 1
                        if h < self.conf.hauteur - 1:
                            zone.bordure += 1
                        if l > 0 and h > 0 and len(zones) == 1:
                            zone.bordure -= 1

                        for z1 in zones:
                            grille.zones[z1].bordure -= 1

                        retour.append(grille)
                    déjà.append(z)

            # On tente de fusionner les deux zones
            if (True and len(zones) == 2 and zones[0] != zones[1]):
                if (len(self.zones[zones[0]].valeurs.intersection(
                        self.zones[zones[1]].valeurs)) == 0
                        and self.zones[zones[0]].bordure != 0
                        and self.zones[zones[1]].bordure != 0):
                    grille = copy.deepcopy(self)
                    z0 = grille.zones[zones[0]]
                    z1 = grille.zones[zones[1]]
                    # On fusionne les périmètres, on consomme 2 bords, on en
                    # offre 2 (en général)
                    z0.bordure += z1.bordure
                    if l == self.conf.largeur - 1:
                        grille.zones[zones[0]].bordure -= 1
                    if h == self.conf.hauteur - 1:
                        grille.zones[zones[0]].bordure -= 1
                    z0.valeurs.update(z1.valeurs)
                    for case in grille.cases:
                        if case.zone == zones[1]:
                            case.zone = zones[0]
                    if zones[1] == len(grille.zones) - 1:
                        del grille.zones[zones[1]]
                    else:
                        grille.zones[zones[1]] = None
                        logging.debug(grille)
                        logging.debug(f"aaa {grille.zones}")
                        grille.normaliser()
                        logging.debug(f"bbb {grille.zones}")
                        logging.debug(grille)
                    valeurs = grille._valeurs_possibles(l, h, zones[0])
                    for v in valeurs:
                        g2 = copy.deepcopy(grille)
                        g2.cases[i].case = v
                        g2.cases[i].zone = zones[0]
                        g2.zones[zones[0]].valeurs.add(v)
                        retour.append(g2)

            # On crée une nouvelle zone
            valeurs = self._valeurs_possibles(l, h, -1)
            for v in valeurs:
                zone = Zone()
                if l == self.conf.largeur - 1:
                    zone.bordure -= 1
                if h == self.conf.hauteur - 1:
                    zone.bordure -= 1
                zone.valeurs.add(v)
                grille = copy.deepcopy(self)
                grille.cases[i].case = v
                grille.cases[i].zone = len(grille.zones)
                grille.zones.append(zone)

                for z in zones:
                    grille.zones[z].bordure -= 1

                retour.append(grille)

        # Production des nouveaux états
        return retour

    def _valeurs_possibles(self, l, h, id_zone):
        retour = set(range(1, self.conf.maximum + 1))

        # On supprime toutes les valeurs déjà présentes dans la zone
        if id_zone != -1:
            retour.difference_update(self.zones[id_zone].valeurs)

        # On supprime toutes les valeurs à proximité
        i = self.conf.en_index(l, h)
        if l > 0:
            j = i - 1
            retour.discard(self.cases[j].case)
        if h > 0:
            j = self.conf.en_index(l, h - 1)
            retour.discard(self.cases[j].case)
        if l > 0 and h > 0:
            j = self.conf.en_index(l - 1, h - 1)
            retour.discard(self.cases[j].case)
        if l < self.conf.largeur - 1 and h > 0:
            j = self.conf.en_index(l + 1, h - 1)
            retour.discard(self.cases[j].case)

        return retour

    def est_complète(self):
        retour = True
        for i in range(len(self.cases)):
            if not self.cases[i].est_valorisée():
                retour = False
                break

        return retour

    def est_crédible(self):
        retour = True
        for zone in self.zones:
            if zone is not None and zone.est_anormal():
                retour = False
                break
        return retour

    def est_4_coloriable(self):
        """Vrai ssi la Grille est coloriable avec 4 couleurs.

        Une case peut partager la couleur d'une de ses 8 voisines ssi elles
        sont dans la même zone
        """
        # https://fr.wikipedia.org/wiki/Th%C3%A9or%C3%A8me_des_quatre_couleurs
        # Attention, le théorême ne vaut que pour le partage de frontière. Ce
        # qui n'est pas la définition retenue dans Tiwanaku.

        # On établit le graphe des voisinages de Zones
        voisinage = dict()
        for h in range(self.conf.hauteur):
            for l in range(self.conf.largeur):
                i = self.conf.en_index(l, h)
                zone = self.cases[i].zone
                for delta_h, delta_l in [(-1, 1), (0, 1), (1, 1), (1, 0)]:
                    h2 = h + delta_h
                    l2 = l + delta_l
                    if (0 <= h2 < self.conf.hauteur
                            and 0 <= l2 < self.conf.largeur):
                        j = self.conf.en_index(l2, h2)
                        zone2 = self.cases[j].zone
                        if zone != zone2:
                            voisinage.setdefault(zone, set()).add(zone2)
                            voisinage.setdefault(zone2, set()).add(zone)

        # Recherche d'un coloriage valide
        for k in sorted(voisinage):
            logging.debug(f"{k} → {sorted(voisinage[k])}")

        # Coloriage par force brute
        couleurs = [None] * len(self.zones)
        couleurs[0] = Terrain.herbe
        i = 1
        while 0 < i < len(self.zones):
            possibles = set(Terrain)
            for voisin in voisinage[i]:
                if voisin < i:
                    possibles.discard(couleurs[voisin])
            possibles = sorted(possibles)
            if len(possibles) == 0:
                couleurs[i] = None
                i -= 1
            elif couleurs[i] is None:
                couleurs[i] = possibles[0]
                i += 1
            else:
                j = possibles.index(couleurs[i])
                if j + 1 < len(possibles):
                    couleurs[i] = possibles[j + 1]
                    i += 1
                else:
                    couleurs[i] = None
                    i -= 1

        if False and i == len(self.zones):
            print(couleurs)

        return i == len(self.zones)

    def transposition(self):
        """Grille dont largeur et hauteur sont interverties
        """
        retour = Grille(self.conf.transposition())
        retour.zones = copy.deepcopy(self.zones)
        for h in range(self.conf.hauteur):
            for l in range(self.conf.largeur):
                i = self.conf.en_index(l, h)
                j = retour.conf.en_index(h, l)
                retour.cases[j] = copy.deepcopy(self.cases[i])
        return retour


def charger_enregistrement(conf):
    """Récupère l'état le plus avancé des calculs

    On cherche le plus haut palier atteint parmis tous les enregistrements :
    1) de même maximum, voire plus
    2a) de même largeur, mais de palier <= hauteur×(L-1)
    2b) de largeur différente, mais de palier < largeur
    """
    regex = re.compile("p(\\d+)h(\\d+)l(\\d+)m(\\d+).log\\Z")

    _, _, fichiers = next(os.walk(conf.chemin))
    meilleur = None
    palier_max = None
    maximum_min = None
    extension_min = None
    for f in fichiers:
        m = regex.match(f)
        if m:
            groupe = tuple(int(x) for x in m.groups())
            palier, hauteur, largeur, maximum = groupe
            éligible = False
            if maximum >= conf.maximum:
                if largeur == conf.largeur:
                    if hauteur == conf.hauteur:
                        éligible = True
                    elif palier <= (min(hauteur, conf.hauteur) - 1) * largeur:
                        éligible = True
                elif palier < largeur < conf.largeur:
                    éligible = True
            if éligible:
                # Lequel nous intéresse le plus ? Celui qui demande le moins
                # de reprise. Alors, quels sont les différents types de
                # reprises ?
                # Prélude obligatoire : décoder
                # 1) Si le maximum est supérieur à celui de la conf, il faut
                #    filtrer les grilles qui emploient des valeurs non
                #    désirées, c'est-à-dire inspecter toutes les cases de
                #    toutes les grilles
                # 2) Si les dimensions ne sont pas les bonnes, il faut
                #    redimensionner la grille (extension bourrine)
                # Fin obligatoire : changer la conf et encoder
                extension = conf.hauteur * conf.largeur - hauteur * largeur
                if meilleur is None:
                    palier_max = palier
                    maximum_min = maximum
                    extension_min = extension
                    meilleur = f
                elif palier > palier_max:
                    palier_max = palier
                    maximum_min = maximum
                    extension_min = extension
                    meilleur = f
                elif palier == palier_max and maximum < maximum_min:
                    maximum_min = maximum
                    extension_min = extension
                    meilleur = f
                elif palier == palier_max and maximum == maximum_min and 0 <= extension < extension_min:
                    extension_min = extension
                    meilleur = f

    # Et maintenant, on charge
    if meilleur is None:
        logging.info("Initialisation du contexte")
        palier_max = 0
        codes = [serial.encoder(Grille(conf.dimensions()))]
    else:
        logging.info(f"Reprise depuis «{meilleur}»")
        codes = list()

        filtrage_case_par_case = (maximum_min != conf.maximum)
        redimensionnement = (extension_min != 0)
        reprise = (filtrage_case_par_case or redimensionnement)

        with open(os.path.join(conf.chemin, meilleur), "rt") as entrée:
            if not reprise:
                for ligne in entrée:
                    code = int(ligne.strip())
                    codes.append(code)
            else:
                for ligne in entrée:
                    code = int(ligne.strip())

                    grille = serial.décoder(code)

                    retenu = True
                    if filtrage_case_par_case:
                        for case in grille.cases:
                            if case.valeur > conf.maximum:
                                retenu = False
                                break
                        else:
                            grille.conf.maximum = conf.maximum

                    if retenu and redimensionnement:
                        extension = [None] * extension_min
                        for i in range(len(extension)):
                            extension[i] = Case()
                        grille.cases.extend(extension)
                        grille.conf.hauteur = conf.hauteur
                        grille.conf.largeur = conf.largeur
                    if retenu:
                        code = serial.encoder(grille)
                    codes.append(code)
                codes.sort()

        if reprise:
            with open(
                    os.path.join(
                        conf.chemin,
                        f"p{palier_max}h{conf.hauteur}l{conf.largeur}m{conf.maximum}.log"
                    ), "wt") as sortie:
                for code in codes:
                    sortie.write(str(code) + "\n")

    return palier_max, codes


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    CONF = Configuration.charger()
    logging.info(CONF)

    # Chargement du meilleur contexte
    ID_PALIER, PALIER = charger_enregistrement(CONF)
    ÉTAGE = set()

    # Fixation d'une case à la fois
    PALIER_MAX = CONF.largeur * CONF.hauteur
    while ID_PALIER < PALIER_MAX:
        logging.info(f"Palier n°{ID_PALIER} atteint : {len(PALIER)} grilles")
        while len(PALIER) != 0:
            CODE = PALIER.pop()
            G = serial.décoder(CODE)
            N = G.prochains()
            for G in N:
                if G.est_crédible():
                    CODE = serial.encoder(G)
                    ÉTAGE.add(CODE)

        PALIER = sorted(ÉTAGE)
        ÉTAGE.clear()
        ID_PALIER += 1

        # Enregistrement des calculs intermédiaires
        CHEMIN = os.path.join(
            CONF.chemin,
            f"p{ID_PALIER}h{CONF.hauteur}l{CONF.largeur}m{CONF.maximum}.log")
        with open(CHEMIN, "wt") as sortie:
            for CODE in PALIER:
                sortie.write(str(CODE) + "\n")

    # Affichage final
    logging.info(f"Palier n°{PALIER_MAX} atteint : {len(PALIER)} grilles")
    with open(
            os.path.join(CONF.chemin,
                         f"h{CONF.hauteur}l{CONF.largeur}m{CONF.maximum}.log"),
            "wt") as SORTIE:
        for CODE in PALIER:
            SORTIE.write(f"{CODE}\n")
