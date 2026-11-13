"""Scène 3D (Ursina) : sol, obstacles en cubes, cases explorées, trajet, robot, destination, caméra."""
from math import atan2, degrees, sin

from ursina import Entity, Vec3, camera, clamp, color, held_keys, mouse, time, window
from .config import C, HAUTEUR_OBSTACLE, TAILLE_BLOC
from .outils3d import (ajouter_boite, ajouter_plat, ajouter_ruban, maillage, rgb)


def hexcol(h):
    return color.hex(h)


class Scene3D:
    def __init__(self, lignes, colonnes):
        self.L, self.N = lignes, colonnes
        self.obstacles = set()
        self.par_bloc = {}        # (bi, bj) -> {cases}
        self.blocs = {}           # (bi, bj) -> Entity
        self.sales = set()
        self.position_cible = None
        self.cap_cible = 0.0
        self.vitesse = 60
        window.color = hexcol(C["fond"])

        self._construire_sol()
        self.explorees = Entity(model=None, double_sided=True)
        self.trajet = Entity(model=None, double_sided=True)
        self._construire_robot()
        self._construire_destination()
        self._construire_camera()

    # ---------- coordonnées ----------
    def monde(self, case, hauteur=0.0):
        l, c = case
        return Vec3(c + 0.5 - self.N / 2, hauteur, self.L / 2 - l - 0.5)

    def case_depuis_point(self, p):
        c = int(p.x + self.N / 2)
        l = int(self.L / 2 - p.z)
        if 0 <= l < self.L and 0 <= c < self.N:
            return l, c
        return None

    # ---------- construction ----------
    def _construire_sol(self):
        self.sol = Entity(model="cube", scale=(self.N, 0.4, self.L), position=(0, -0.2, 0),
                          color=hexcol(C["sol"]), collider="box")
        # socle visible autour de la grille
        Entity(model="cube", scale=(self.N + 3, 1.2, self.L + 3), position=(0, -1.0, 0),
               color=hexcol(C["panneau2"]))
        s, t, c = [], [], []
        base = rgb(C["grille"])
        for k in range(0, self.N + 1, 10):
            x = k - self.N / 2
            ajouter_plat(s, t, c, x - .06, -self.L / 2, x + .06, self.L / 2, 0.02, base)
        for k in range(0, self.L + 1, 10):
            z = k - self.L / 2
            ajouter_plat(s, t, c, -self.N / 2, z - .06, self.N / 2, z + .06, 0.02, base)
        Entity(model=maillage(s, t, c), double_sided=True)

    def _construire_robot(self):
        self.robot = Entity(position=(0, 0, 0))
        corps, tete, noir = rgb("#3b82f6"), rgb("#dbe8ff"), rgb("#0c1528")
        s, t, c = [], [], []
        ajouter_boite(s, t, c, -1.3, 0.0, -1.3, 1.3, 1.3, 1.3, corps)
        ajouter_boite(s, t, c, -1.5, 0.0, -1.5, -1.0, 0.6, 1.5, rgb("#1e3a8a"))   # chenille gauche
        ajouter_boite(s, t, c, 1.0, 0.0, -1.5, 1.5, 0.6, 1.5, rgb("#1e3a8a"))     # chenille droite
        ajouter_boite(s, t, c, -0.9, 1.3, -0.9, 0.9, 2.2, 0.9, tete)
        ajouter_boite(s, t, c, -0.55, 1.6, 0.9, -0.2, 1.95, 0.95, noir)           # œil gauche (avant = +z)
        ajouter_boite(s, t, c, 0.2, 1.6, 0.9, 0.55, 1.95, 0.95, noir)             # œil droit
        ajouter_boite(s, t, c, -0.08, 2.2, -0.08, 0.08, 2.8, 0.08, tete)          # antenne
        ajouter_boite(s, t, c, -0.2, 2.8, -0.2, 0.2, 3.2, 0.2, rgb("#22c55e"))
        Entity(parent=self.robot, model=maillage(s, t, c), double_sided=True)

    def _construire_destination(self):
        self.dest = Entity(position=(0, 0, 0))
        s, t, c = [], [], []
        ajouter_boite(s, t, c, -1.4, 0.0, -1.4, 1.4, 0.3, 1.4, rgb("#14532d"))
        ajouter_boite(s, t, c, -0.8, 0.3, -0.8, 0.8, 0.6, 0.8, rgb("#22c55e"))
        ajouter_boite(s, t, c, -0.12, 0.6, -0.12, 0.12, 4.0, 0.12, rgb("#a7f3d0"))
        Entity(parent=self.dest, model=maillage(s, t, c), double_sided=True)
        self.balise = Entity(parent=self.dest, model="sphere", y=4.3, scale=0.9, color=hexcol("#4ade80"))

    def _construire_camera(self):
        self.pivot = Entity(position=(0, 0, 0), rotation=(58, 0, 0))
        camera.parent = self.pivot
        camera.position = (0, 0, -self.N * 2.1)
        camera.rotation = (0, 0, 0)
        camera.clip_plane_far = 5000
        camera.clip_plane_near = 0.5
        self.distance = self.N * 2.1

    def reinitialiser_camera(self):
        self.pivot.position = Vec3(0, 0, 0)
        self.pivot.rotation = Vec3(58, 0, 0)
        self.distance = self.N * 2.1

    # ---------- obstacles (regroupés en blocs de cases) ----------
    def _bloc(self, case):
        return case[0] // TAILLE_BLOC, case[1] // TAILLE_BLOC

    def _marquer(self, case):
        l, c = case
        for dl, dc in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            self.sales.add(self._bloc((l + dl, c + dc)))

    def poser_obstacle(self, case):
        if case in self.obstacles:
            return
        self.obstacles.add(case)
        self.par_bloc.setdefault(self._bloc(case), set()).add(case)
        self._marquer(case)

    def retirer_obstacle(self, case):
        if case not in self.obstacles:
            return
        self.obstacles.discard(case)
        self.par_bloc.get(self._bloc(case), set()).discard(case)
        self._marquer(case)

    def dessiner_obstacles(self, obstacles):
        self.obstacles = set(obstacles)
        self.par_bloc = {}
        for case in self.obstacles:
            self.par_bloc.setdefault(self._bloc(case), set()).add(case)
        self.sales |= set(self.par_bloc) | set(self.blocs)

    def _reconstruire(self):
        base = rgb(C["obstacle"])
        h = HAUTEUR_OBSTACLE
        for cle in self.sales:
            cases = self.par_bloc.get(cle)
            ancien = self.blocs.pop(cle, None)
            if ancien is not None:
                ancien.disable()
                ancien.model = None
            if not cases:
                continue
            s, t, c = [], [], []
            for l, col in cases:
                x0, z1 = col - self.N / 2, self.L / 2 - l
                z0, x1 = z1 - 1, x0 + 1
                faces = "h"
                if (l + 1, col) not in self.obstacles: faces += "s"   # voisin du bas (z plus petit)
                if (l - 1, col) not in self.obstacles: faces += "n"
                if (l, col + 1) not in self.obstacles: faces += "d"
                if (l, col - 1) not in self.obstacles: faces += "g"
                var = 0.95 + 0.05 * (((l * 7 + col * 13) % 5) / 4)
                ajouter_boite(s, t, c, x0, 0, z0, x1, h, z1, base, var, faces)
            self.blocs[cle] = Entity(model=maillage(s, t, c), double_sided=True)
        self.sales.clear()

    # ---------- cases explorées et trajet ----------
    def dessiner_explorees(self, cases):
        par_ligne = {}
        for l, c in cases:
            par_ligne.setdefault(l, []).append(c)
        s, t, col = [], [], []
        base = rgb(C["explore"])
        for l, cols in par_ligne.items():
            cols.sort()
            debut = prec = cols[0]
            for c in cols[1:] + [None]:
                if c is not None and c == prec + 1:
                    prec = c
                    continue
                x0, x1 = debut - self.N / 2, prec + 1 - self.N / 2
                z1 = self.L / 2 - l
                ajouter_plat(s, t, col, x0, z1 - 1, x1, z1, 0.05, base)
                debut = prec = c
        self.explorees.model = maillage(s, t, col) if t else None

    def dessiner_trajet(self, chemin, position, destination):
        if len(chemin) > 1:
            s, t, c = [], [], []
            pts = [(self.monde(case).x, self.monde(case).z) for case in chemin]
            ajouter_ruban(s, t, c, pts, 0.1, 0.8, rgb(C["chemin"]))
            self.trajet.model = maillage(s, t, c)
        else:
            self.trajet.model = None
        self.dest.position = self.monde(destination)
        nouveau = self.monde(position)
        if self.position_cible is None:
            self.robot.position = nouveau
        else:
            dx, dz = nouveau.x - self.position_cible.x, nouveau.z - self.position_cible.z
            if abs(dx) + abs(dz) > 0.01:
                self.cap_cible = degrees(atan2(dx, dz))
        self.position_cible = nouveau

    # ---------- caméra et animation ----------
    def mettre_a_jour(self):
        dt = time.dt
        if self.sales:
            self._reconstruire()
        # robot : déplacement fluide + orientation dans le sens de la marche
        if self.position_cible is not None:
            k = min(1.0, dt * (8 + self.vitesse * 0.35))
            self.robot.position += (self.position_cible - self.robot.position) * k
            ecart = (self.cap_cible - self.robot.rotation_y + 180) % 360 - 180
            self.robot.rotation_y += ecart * min(1.0, dt * 12)
        # balise de destination qui pulse
        self.balise.scale = 0.9 + 0.2 * sin(time.time() * 3)
        self._camera(dt)

    def _camera(self, dt):
        p = self.pivot
        v = mouse.velocity
        if held_keys["right mouse"]:
            p.rotation_y += v[0] * 220
            p.rotation_x = clamp(p.rotation_x - v[1] * 220, 8, 90)
        if held_keys["middle mouse"] or (held_keys["left shift"] and held_keys["left mouse"]):
            facteur = self.distance * 1.1
            p.position -= p.right * v[0] * facteur
            avant = Vec3(p.forward.x, 0, p.forward.z).normalized()
            p.position -= avant * v[1] * facteur * 1.4
        dx = held_keys["d"] + held_keys["right arrow"] - held_keys["a"] - held_keys["left arrow"]
        dz = held_keys["w"] + held_keys["up arrow"] - held_keys["s"] - held_keys["down arrow"]
        if dx or dz:
            avant = Vec3(p.forward.x, 0, p.forward.z).normalized()
            p.position += (p.right * dx + avant * dz) * dt * self.distance * 0.6
        camera.z = -self.distance

    def zoom(self, sens):
        self.distance = clamp(self.distance * (0.88 if sens > 0 else 1.14), 12, self.N * 4)