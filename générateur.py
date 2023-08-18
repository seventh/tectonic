#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Générateur de grille complète
"""

import copy
import dataclasses
import getopt
import logging
import sys

import serial


@dataclasses.dataclass
class Configuration:

    hauteur: int = 5
    largeur: int = 4
    maximum: int = 5

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
        return retour


@dataclasses.dataclass
class Case:
    """Valeur associée à un identifiant de zone
    """

    zone: int = -1
    case: int = -1

    def est_valorisée(self):
        return self.case != -1


@dataclasses.dataclass
class Zone:
    """Ensemble de valeurs connexes et nombre de bords libres
    """

    valeurs: set = dataclasses.field(default_factory=set)
    bordure: int = 2

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

        self.cases = list()
        for h in range(conf.hauteur):
            for l in range(conf.largeur):
                self.cases.append(Case())

        self.zones = list()

    def __repr__(self):
        lignes = list()
        for id, zone in enumerate(self.zones):
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
                i = self.en_index(l, h)
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

    def en_index(self, largeur, hauteur):
        return self.conf.largeur * hauteur + largeur

    def prochains(self):
        retour = list()

        # Recherche de la première case affichable non valuée
        trouvé = False
        for h in range(self.conf.hauteur):
            for l in range(self.conf.largeur):
                i = self.en_index(l, h)
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

                        for z2 in zones:
                            grille.zones[z2].bordure -= 1

                        retour.append(grille)
                    déjà.append(z)

            # On tente de fusionner les deux zones
            if (False and len(zones) == 2 and zones[0] != zones[1]):
                if (len(self.zones[zones[0]].valeurs.intersection(
                        self.zones[zones[1]].valeurs)) == 0
                        and self.zones[zones[0]].bordure != 0
                        and self.zones[zones[1]].bordure != 0):
                    grille = copy.deepcopy(self)
                    z1 = grille.zones[zones[0]]
                    z2 = grille.zones[zones[1]]
                    z1.bordure += z2.bordure
                    z1.valeurs.update(z2.valeurs)
                    grille.zones[zones[1]] = z1
                    for case in grille.cases:
                        if case.zone == zones[1]:
                            case.zone = zones[0]
                    valeurs = grille._valeurs_possibles(l, h, zones[0])
                    for v in valeurs:
                        g2 = copy.deepcopy(grille)
                        g2.cases[i].case = v
                        g2.cases[i].zone = zones[0]
                        g2.zones[zones[0]].bordure -= 2
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
        i = self.en_index(l, h)
        if l > 0:
            j = i - 1
            retour.discard(self.cases[j].case)
        if h > 0:
            j = self.en_index(l, h - 1)
            retour.discard(self.cases[j].case)
        if l > 0 and h > 0:
            j = self.en_index(l - 1, h - 1)
            retour.discard(self.cases[j].case)
        if l < self.conf.largeur - 1 and h > 0:
            j = self.en_index(l + 1, h - 1)
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
            if zone.est_anormal():
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
                i = self.en_index(l, h)
                zone = self.cases[i].zone
                for delta_h, delta_l in [(-1, 1), (0, 1), (1, 1), (1, 0)]:
                    h2 = h + delta_h
                    l2 = l + delta_l
                    if (0 <= h2 < self.conf.hauteur
                            and 0 <= l2 < self.conf.largeur):
                        j = self.en_index(l2, h2)
                        zone2 = self.cases[j].zone
                        if zone != zone2:
                            voisinage.setdefault(zone, set()).add(zone2)
                            voisinage.setdefault(zone2, set()).add(zone)

        # Vérification basique
        for vs in voisinage.values():
            if len(vs) > 3:
                return False

        # Recherche d'un coloriage valide
        for k in sorted(voisinage):
            logging.debug(f"{k} → {sorted(voisinage[k])}")

        return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    CONF = Configuration.charger()
    print(CONF)
    GRILLES = [Grille(CONF)]
    while len(GRILLES) != 0:
        G = GRILLES.pop()
        if G.est_crédible():
            if G.est_complète():
                if False:
                    print(G.est_4_coloriable())
                print(G)
                if False:
                    print(f"{G!r}")
                print("")
                if False:
                    serial.décoder(serial.encoder(G))
            else:
                N = G.prochains()
                if False:
                    for M in N:
                        print(M)
                        print(f"{M!r}")
                        print("")

                GRILLES.extend(N)
                if False:
                    print(len(GRILLES))
