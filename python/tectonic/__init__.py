# -*- coding: utf-8 -*-
"""Éléments de base pour la manipulation de grilles de Tectonic
"""

import dataclasses


@dataclasses.dataclass
class Base:
    """Caractéristiques principales d'une Grille
    """

    largeur: int = 4
    hauteur: int = 5
    maximum: int = 5

    def en_index(self, largeur, hauteur):
        return hauteur * self.largeur + largeur

    def nb_cases(self):
        return self.hauteur * self.largeur

    def transposée(self):
        """Objet dual dont hauteur et largeur ont été inversées
        """
        return Base(largeur=self.hauteur,
                    hauteur=self.largeur,
                    maximum=self.maximum)


@dataclasses.dataclass
class Case:

    valeur: int = -1
    région: int = -1


class Grille:

    def __init__(self, base):
        self.base = base

        taille = base.nb_cases()
        self.cases = [None] * taille
        for i in range(taille):
            self.cases[i] = Case()

    def __eq__(self, autre):
        return (self.base == autre.base and self.cases == autre.cases)

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        # On détermine la longueur des champs à afficher
        lgv = len(str(max([c.valeur for c in self.cases if c.valeur >= 1])))
        lgr = len(str(max([c.région for c in self.cases if c.région >= 0])))
        lgc = 3 + lgv + lgr

        # Constitution de la grille, ligne à ligne
        lignes = list()
        for h in range(self.base.hauteur):
            # Séparateur horizontal
            ligne = "+"
            for l in range(self.base.largeur):
                séparateur = "-"
                if h > 0 and self[(l, h - 1)].région == self[(l, h)].région:
                    séparateur = " "
                ligne += séparateur * lgc + "+"
            lignes.append(ligne)

            # Cases
            ligne = str()
            for l in range(self.base.largeur):
                case = self[(l, h)]
                séparateur = "|"
                if l > 0 and self[(l - 1, h)].région == case.région:
                    séparateur = " "
                ligne += séparateur
                if case.valeur >= 1:
                    v = f"{case.valeur:{lgv}}"
                else:
                    v = " " * lgv
                if case.région >= 0:
                    r = f"{case.région:{lgr}}"
                else:
                    r = " " * lgr
                ligne += f"({v},{r})"
            ligne += "|"
            lignes.append(ligne)

        # Dernier séparateur horizontal
        ligne = "+" + ("-" * lgc + "+") * self.base.largeur
        lignes.append(ligne)

        retour = "\n".join(lignes)
        return retour

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
        # return self.conf.en_index(largeur, hauteur)
        return self.conf.largeur * hauteur + largeur

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
                i = self.en_index(l, h)
                j = retour.en_index(h, l)
                retour.cases[j] = copy.deepcopy(self.cases[i])
        return retour
