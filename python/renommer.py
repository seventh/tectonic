#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys


def renommer(répertoires):
    regex = re.compile("(?:p(\\d+))?h(\\d+)l(\\d+)m(\\d+)")

    for répertoire in répertoires:
        racine, _, fichiers = next(os.walk(répertoire))
        for nid in fichiers:
            c = regex.search(nid)
            if c:
                p, h, l, m = c.groups()
                radical = f"h{h:0>2}l{l:0>2}m{m:0>2}"
                if p is not None:
                    radical += f"-p{p:0>2}"
                but = nid[:c.start()] + radical + nid[c.end():]
                os.rename(os.path.join(racine, nid), os.path.join(racine, but))


if __name__ == "__main__":
    renommer(sys.argv[1:])
