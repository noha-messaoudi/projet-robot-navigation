"""Constantes partagées : taille de la grille, couleurs, algorithmes, modes."""
LIGNES = 200
COLONNES = 200

C = dict(fond="#0a1222", entete="#0c1528", panneau="#0f1a30", panneau2="#142240", bordure="#1f2f4d",
         texte="#e8eefb", discret="#8d9bb8", bleu="#3b82f6", bleu_h="#2f6fd8", vert="#22c55e",
         vert_fond="#0f2d22", rouge="#f87171", rouge_fond="#35161a", obstacle="#6b7686",
         grille="#1f3358", sol="#0e1c38", explore="#173a78", titre="#6ea0ff", selection="#2b57a8",
         chemin="#8ec1ff")

ALGOS = {"A* (recommandé)": "astar", "Dijkstra": "dijkstra", "BFS": "bfs"}
MODES = {"Obstacle": "obstacle", "Départ": "depart", "Destination": "destination"}

HAUTEUR_OBSTACLE = 1.8   # hauteur des cubes d'obstacle (1 case = 1 unité)
TAILLE_BLOC = 25         # les obstacles sont regroupés en blocs de 25 x 25 cases (mise à jour rapide)