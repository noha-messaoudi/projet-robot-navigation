"""Modèle : la grille et ses obstacles."""
import random


class Grille:
    def __init__(self, lignes, colonnes):
        self.lignes = lignes
        self.colonnes = colonnes
        self.obstacles = set()  # ensemble de (ligne, colonne)
        self.version = 0        # +1 à chaque modification (sert à détecter un changement)

    def est_dans_grille(self, case):
        l, c = case
        return 0 <= l < self.lignes and 0 <= c < self.colonnes

    def est_libre(self, case):
        return self.est_dans_grille(case) and case not in self.obstacles

    def ajouter_obstacle(self, case):
        if self.est_dans_grille(case) and case not in self.obstacles:
            self.obstacles.add(case)
            self.version += 1

    def retirer_obstacle(self, case):
        if case in self.obstacles:
            self.obstacles.discard(case)
            self.version += 1

    def basculer_obstacle(self, case):
        """Ajoute l'obstacle s'il n'existe pas, le retire sinon (utile pour un clic)."""
        if case in self.obstacles:
            self.retirer_obstacle(case)
        else:
            self.ajouter_obstacle(case)

    def generer_obstacles_aleatoires(self, densite, exclus=()):
        """Remplit la grille d'obstacles (densite entre 0 et 1), sauf sur les cases exclues."""
        for l in range(self.lignes):
            for c in range(self.colonnes):
                if (l, c) not in exclus and random.random() < densite:
                    self.ajouter_obstacle((l, c))

    def vider(self):
        if self.obstacles:
            self.obstacles.clear()
            self.version += 1

    def voisins(self, case):
        """Cases libres accessibles en 1 déplacement (haut, bas, gauche, droite)."""
        l, c = case
        for dl, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            v = (l + dl, c + dc)
            if self.est_libre(v):
                yield v
 