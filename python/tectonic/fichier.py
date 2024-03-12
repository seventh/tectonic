# -*- coding: utf-8 -*-

from .fichier_000 import Lecteur as Lecteur000
from .fichier_001 import Lecteur as Lecteur001
from .fichier_001 import Écrivain as Écrivain001


def lecteur(chemin):
    """Lecteur adapté au format du fichier
    """
    retour = None

    with open(chemin, "rb") as entrée:
        # Vérification du prélude
        prélude = entrée.read(8)
        if prélude == b"TECTONIC":
            # Version
            version = entrée.read(1)
            if version == b"\x00":
                retour = Lecteur000(chemin)
            elif version == b"\x01":
                retour = Lecteur001(chemin)

    return retour


def écrivain(chemin, base, *, reprise=False):
    return Écrivain001(chemin, base, 2**16, reprise=reprise)
