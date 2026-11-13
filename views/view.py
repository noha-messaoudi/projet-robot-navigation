"""Vue RUBON en 3D (Ursina) : affichage et saisie uniquement, aucune logique métier.
Installation : pip install ursina
La vue ne connaît pas le modèle : le contrôleur lui donne des données simples
et lui branche des fonctions via `lier(...)`. L'interface publique est la même que l'ancienne vue 2D.

Fichiers :
    config.py       taille de la grille (200 x 200), couleurs, algorithmes
    outils3d.py     fabrication des maillages (cubes ombrés, rubans)
    scene3d.py      scène 3D : sol, obstacles, robot, destination, caméra
    interface3d.py  panneau de commandes par-dessus la scène
    View.py         classe Vue (assemblage + interface pour le contrôleur)
"""
from time import monotonic
from panda3d.core import loadPrcFileData
loadPrcFileData("", "audio-library-name null")
from ursina import Entity, Ursina, held_keys, mouse
from .config import ALGOS, COLONNES, LIGNES
from .interface3d import Interface
from .scene3d import Scene3D

class _Moteur(Entity):
    """Reçoit update() et input() d'Ursina et les transmet à la vue."""

    def __init__(self, vue):
        super().__init__()
        self.vue = vue

    def update(self):
        self.vue._image()

    def input(self, key):
        self.vue._touche(key)


class Vue:
    def __init__(self, lignes=LIGNES, colonnes=COLONNES, taille_case=None):
        self.lignes, self.colonnes = lignes, colonnes
        self.app = Ursina(title="RUBON – Navigation du robot (3D)", borderless=False, development_mode=False)
        self.commandes: dict = {}
        self._taches: dict = {}
        self._compteur = 0
        self._derniere_case = None
        self._peint = False
        self.scene = Scene3D(lignes, colonnes)
        self.ui = Interface(self)
        self.ui.lbl_grille.text = f"Grille {colonnes} × {lignes}"
        self._moteur = _Moteur(self)

    # ---------- liaison avec le contrôleur ----------
    def lier(self, **commandes):
        self.commandes.update(commandes)

    def _appeler(self, nom, *args):
        fn = self.commandes.get(nom)
        return fn(*args) if fn else None

    def programmer(self, delai_ms, fonction):
        self._compteur += 1
        self._taches[self._compteur] = (monotonic() + delai_ms / 1000, fonction)
        return self._compteur

    def annuler(self, ident):
        self._taches.pop(ident, None)

    def mainloop(self):
        self.app.run()

    run = mainloop

    # ---------- lecture des contrôles ----------
    def mode(self): return self.ui.mode
    def algorithme_choisi(self): return ALGOS[self.ui.algo]
    def mode_optimal(self): return self.ui.optimal
    def limite_texte(self): return self.ui.ent_limite.text.strip()
    def obstacles_aleatoires(self): return self.ui.aleatoire
    def vitesse(self): return self.ui.vitesse

    # ---------- boucle d'animation et saisie ----------
    def _image(self):
        maintenant = monotonic()
        for ident, (heure, fn) in list(self._taches.items()):
            if heure <= maintenant:
                self._taches.pop(ident, None)
                fn()
        self.scene.mettre_a_jour()
        self.ui.mettre_a_jour()
        if self._peint and held_keys["left mouse"] and mouse.hovered_entity is self.scene.sol and mouse.world_point:
            case = self.scene.case_depuis_point(mouse.world_point)
            if case and case != self._derniere_case:
                self._derniere_case = case
                self._appeler("glisser", *case)

    def _touche(self, key):
        if key == "left mouse down" and mouse.hovered_entity is self.scene.sol and mouse.world_point \
                and not held_keys["left shift"]:
            case = self.scene.case_depuis_point(mouse.world_point)
            if case:
                self._peint, self._derniere_case = True, case
                self._appeler("clic", *case)
        elif key == "left mouse up":
            if self._peint:
                self._appeler("relache")
            self._peint = False
        elif key == "scroll up":
            if not (mouse.hovered_entity and mouse.hovered_entity.has_ancestor(self.ui.racine)):
                self.scene.zoom(1)
        elif key == "scroll down":
            if not (mouse.hovered_entity and mouse.hovered_entity.has_ancestor(self.ui.racine)):
                self.scene.zoom(-1)
        elif key == "r":
            self.scene.reinitialiser_camera()

    # ---------- affichage (appelé par le contrôleur) ----------
    def afficher_niveau(self, n): self.ui.afficher_niveau(n)
    def afficher_statut(self, texte, ok=True): self.ui.afficher_statut(texte, ok)

    def afficher_stats(self, longueur, explorees, temps_ms, replanifications):
        self.ui.afficher_stats(longueur, explorees, temps_ms, replanifications)

    def afficher_comparaison(self, lignes): self.ui.afficher_comparaison(lignes)
    def poser_obstacle(self, case): self.scene.poser_obstacle(case)
    def retirer_obstacle(self, case): self.scene.retirer_obstacle(case)
    def dessiner_obstacles(self, obstacles): self.scene.dessiner_obstacles(obstacles)
    def dessiner_explorees(self, cases): self.scene.dessiner_explorees(cases)

    def dessiner_trajet(self, chemin, position, destination):
        self.scene.dessiner_trajet(chemin, position, destination)