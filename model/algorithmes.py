"""Modèle : algorithmes de recherche de chemin (BFS, Dijkstra, A*).

Tous ont la même signature : algo(grille, depart, arrivee, limite_temps=None)
et renvoient un objet Resultat.

limite_temps (en secondes) : si le calcul dépasse ce temps, on s'arrête et on
renvoie un chemin PARTIEL vers la case explorée la plus proche de la destination
(Resultat.complet = False).
"""
import heapq
import time
from collections import deque


class Resultat:
    def __init__(self, chemin, cases_explorees, temps, nom, complet=True, visitees=None):
        self.chemin = chemin                    # liste de cases, ou None
        self.cases_explorees = cases_explorees  # nombre de cases développées
        self.temps = temps                      # secondes
        self.nom = nom
        self.complet = complet                  # False si arrêt par limite de temps
        self.cases_visitees = visitees or []    # cases explorées (pour l'affichage)

    @property
    def longueur(self):
        return len(self.chemin) - 1 if self.chemin else None

    def __repr__(self):
        partiel = "" if self.complet else " [PARTIEL]"
        return (f"{self.nom}: longueur={self.longueur}, "
                f"explorées={self.cases_explorees}, "
                f"temps={self.temps * 1000:.3f} ms{partiel}")


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _zero(a, b):
    return 0


def _reconstruire(parent, arrivee):
    chemin = []
    case = arrivee
    while case is not None:
        chemin.append(case)
        case = parent[case]
    chemin.reverse()
    return chemin


def _resultat_partiel(parent, depart, arrivee, explorees, debut, nom, visitees):
    """Chemin vers la case découverte la plus proche de l'arrivée."""
    meilleure = min(parent, key=lambda c: manhattan(c, arrivee))
    if meilleure == depart:
        chemin = None  # aucun progrès possible
    else:
        chemin = _reconstruire(parent, meilleure)
    return Resultat(chemin, explorees, time.perf_counter() - debut, nom, complet=False,
                    visitees=visitees)


def _depassee(debut, limite_temps):
    return limite_temps is not None and time.perf_counter() - debut > limite_temps


# ----------------------------------------------------------------------
# BFS (niveau 1)
# ----------------------------------------------------------------------
def bfs(grille, depart, arrivee, limite_temps=None):
    nom = "BFS"
    debut = time.perf_counter()
    if not grille.est_libre(depart) or not grille.est_libre(arrivee):
        return Resultat(None, 0, time.perf_counter() - debut, nom)

    parent = {depart: None}
    file = deque([depart])
    explorees = 0
    visitees = []

    while file:
        if _depassee(debut, limite_temps):
            return _resultat_partiel(parent, depart, arrivee, explorees, debut, nom, visitees)
        courante = file.popleft()
        explorees += 1
        visitees.append(courante)
        if courante == arrivee:
            return Resultat(_reconstruire(parent, arrivee), explorees,
                            time.perf_counter() - debut, nom, visitees=visitees)
        for v in grille.voisins(courante):
            if v not in parent:
                parent[v] = courante
                file.append(v)

    return Resultat(None, explorees, time.perf_counter() - debut, nom, visitees=visitees)


# ----------------------------------------------------------------------
# Recherche avec file de priorité : Dijkstra (h = 0) et A* (h = Manhattan)
# ----------------------------------------------------------------------
def _meilleur_d_abord(grille, depart, arrivee, nom, heuristique, limite_temps):
    debut = time.perf_counter()
    if not grille.est_libre(depart) or not grille.est_libre(arrivee):
        return Resultat(None, 0, time.perf_counter() - debut, nom)

    g = {depart: 0}           # coût du meilleur chemin connu jusqu'à chaque case
    parent = {depart: None}
    fermes = set()
    explorees = 0
    visitees = []
    compteur = 0              # départage les égalités dans le tas
    h0 = heuristique(depart, arrivee)
    tas = [(h0, h0, compteur, depart)]  # (f, h, ordre, case)

    while tas:
        if _depassee(debut, limite_temps):
            return _resultat_partiel(parent, depart, arrivee, explorees, debut, nom, visitees)
        _, _, _, courante = heapq.heappop(tas)
        if courante in fermes:
            continue
        fermes.add(courante)
        explorees += 1
        visitees.append(courante)

        if courante == arrivee:
            return Resultat(_reconstruire(parent, arrivee), explorees,
                            time.perf_counter() - debut, nom, visitees=visitees)

        for v in grille.voisins(courante):
            nouveau_g = g[courante] + 1   # chaque déplacement coûte 1
            if v not in g or nouveau_g < g[v]:
                g[v] = nouveau_g
                parent[v] = courante
                h = heuristique(v, arrivee)
                compteur += 1
                heapq.heappush(tas, (nouveau_g + h, h, compteur, v))

    return Resultat(None, explorees, time.perf_counter() - debut, nom, visitees=visitees)


def dijkstra(grille, depart, arrivee, limite_temps=None):
    return _meilleur_d_abord(grille, depart, arrivee, "Dijkstra", _zero, limite_temps)


def a_star(grille, depart, arrivee, limite_temps=None):
    return _meilleur_d_abord(grille, depart, arrivee, "A*", manhattan, limite_temps)


ALGORITHMES = {"bfs": bfs, "dijkstra": dijkstra, "astar": a_star}


# ----------------------------------------------------------------------
# Comparaison (pour le rapport)
# ----------------------------------------------------------------------
def comparer_algorithmes(grille, depart, arrivee, limite_temps=None, repetitions=1):
    """Lance chaque algorithme sur la même grille. Renvoie la liste des Resultat.
    Le temps affiché est la moyenne sur `repetitions` exécutions."""
    resultats = []
    for fonction in ALGORITHMES.values():
        total = 0.0
        res = None
        for _ in range(repetitions):
            res = fonction(grille, depart, arrivee, limite_temps)
            total += res.temps
        res.temps = total / repetitions
        resultats.append(res)
    return resultats