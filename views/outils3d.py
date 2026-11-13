"""Petits outils pour fabriquer des maillages 3D (boîtes ombrées, bandes, rubans)."""
from math import hypot

from ursina import Mesh, Vec3, Vec4

# luminosité de chaque face (éclairage "peint" dans les couleurs des sommets)
HAUT, AVANT, ARRIERE, DROITE, GAUCHE = 1.0, 0.80, 0.58, 0.70, 0.50


def rgb(hexa):
    h = hexa.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def teinte(base, facteur):
    return Vec4(min(base[0] * facteur, 1), min(base[1] * facteur, 1), min(base[2] * facteur, 1), 1)


def _quad(sommets, coul, p0, p1, p2, p3, c):
    i = len(sommets)
    sommets.extend((p0, p1, p2, p3))
    coul.extend((c, c, c, c))
    return (i, i + 1, i + 2, i + 3)


def ajouter_boite(sommets, tris, coul, x0, y0, z0, x1, y1, z1, base, facteur=1.0, faces="hsndg"):
    """Ajoute une boîte. faces : h=haut, s=avant (-z), n=arrière (+z), d=droite (+x), g=gauche (-x)."""
    if "h" in faces:
        tris.append(_quad(sommets, coul, (x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0),
                          teinte(base, HAUT * facteur)))
    if "s" in faces:
        tris.append(_quad(sommets, coul, (x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0),
                          teinte(base, AVANT * facteur)))
    if "n" in faces:
        tris.append(_quad(sommets, coul, (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
                          teinte(base, ARRIERE * facteur)))
    if "d" in faces:
        tris.append(_quad(sommets, coul, (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1),
                          teinte(base, DROITE * facteur)))
    if "g" in faces:
        tris.append(_quad(sommets, coul, (x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0),
                          teinte(base, GAUCHE * facteur)))


def ajouter_plat(sommets, tris, coul, x0, z0, x1, z1, y, base):
    """Rectangle horizontal à la hauteur y."""
    tris.append(_quad(sommets, coul, (x0, y, z0), (x0, y, z1), (x1, y, z1), (x1, y, z0), teinte(base, 1.0)))


def ajouter_ruban(sommets, tris, coul, points, y, largeur, base):
    """Ruban plat suivant une ligne brisée [(x, z), ...]."""
    demi = largeur / 2
    c = teinte(base, 1.0)
    for (xa, za), (xb, zb) in zip(points, points[1:]):
        dx, dz = xb - xa, zb - za
        n = hypot(dx, dz) or 1
        dx, dz = dx / n, dz / n
        px, pz = -dz * demi, dx * demi
        xa, za, xb, zb = xa - dx * demi, za - dz * demi, xb + dx * demi, zb + dz * demi
        tris.append(_quad(sommets, coul, (xa + px, y, za + pz), (xb + px, y, zb + pz),
                          (xb - px, y, zb - pz), (xa - px, y, za - pz), c))


def maillage(sommets, tris, coul):
    return Mesh(vertices=[Vec3(*s) for s in sommets], triangles=tris, colors=coul, mode="triangle")