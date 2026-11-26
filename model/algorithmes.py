"""Modèle : algorithmes de recherche de chemin (BFS, Dijkstra, A*, Hybride DP+Glouton)
et stratégie de sélection dynamique sous contrainte temporelle T(m).

Tous les algorithmes ont la signature :
    algo(grille, depart, arrivee, limite_temps=None) -> Resultat

limite_temps (en secondes) : si le calcul dépasse ce temps, on s'arrête et on
renvoie un chemin PARTIEL vers la case explorée la plus proche de la destination
(Resultat.complet = False).
"""
import heapq
import math
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


def limite_temps_prof_ms(m):
    """Contrainte temporelle T(m) = 60 + m * ln(m / 60) en ms (pour m >= 60)."""
    if m <= 60:
        return 60.0
    return 60.0 + m * math.log(m / 60.0)


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


# ----------------------------------------------------------------------
# Algorithme personnalisé : A* + Mémoïsation (1 structure) + Glouton pondéré
# ----------------------------------------------------------------------
class _MemoGloutonAStar:
    """Programmation dynamique légère (un seul dictionnaire memo_g sur les cases
    réellement traitées, invalidé automatiquement si la grille change de version)
    combinée à une pondération gloutonne adaptative f(n) = g(n) + w * h(n).
    """

    def __init__(self):
        self.memo_g = {}          # un seul tableau associatif : case -> meilleur coût g connu
        self._version = None
        self._arrivee = None

    def _preparer_memo(self, grille, arrivee):
        if self._version != grille.version or self._arrivee != arrivee:
            self.memo_g.clear()
            self._version = grille.version
            self._arrivee = arrivee

    def _poids_glouton(self, grille, depart, arrivee, limite_temps):
        """Calcule un poids w >= 1.0 :
        - w proche de 1.0 sur petite grille / faible densité (chemin court),
        - w plus élevé (> 1.0, comportement glouton) sur grande grille ou forte densité
          pour accélérer la recherche et respecter T(m).
        """
        nb_cases = max(1, grille.lignes * grille.colonnes)
        densite = len(grille.obstacles) / nb_cases
        m = max(grille.lignes, grille.colonnes)
        dist = manhattan(depart, arrivee)

        w = 1.0
        if m >= 150 or dist >= 120:
            w += 0.55
        elif m >= 90:
            w += 0.25

        if densite >= 0.25:
            w += 0.55
        elif densite >= 0.12:
            w += 0.25

        if limite_temps is not None and limite_temps < 0.05:
            w += 0.40

        return round(min(2.6, w), 2)

    def executer(self, grille, depart, arrivee, limite_temps=None):
        debut = time.perf_counter()
        w = self._poids_glouton(grille, depart, arrivee, limite_temps)
        nom = f"Hybride DP+Glouton (w={w})"

        if not grille.est_libre(depart) or not grille.est_libre(arrivee):
            return Resultat(None, 0, time.perf_counter() - debut, nom)

        self._preparer_memo(grille, arrivee)

        # Réutilisation ciblée si 'depart' possède déjà un coût g valide dans memo_g
        g = {}
        parent = {depart: None}
        if depart in self.memo_g:
            g[depart] = self.memo_g[depart]
        else:
            g[depart] = 0
            self.memo_g[depart] = 0

        fermes = set()
        explorees = 0
        visitees = []
        compteur = 0
        h0 = manhattan(depart, arrivee)
        tas = [(g[depart] + w * h0, h0, compteur, depart)]

        while tas:
            # Si on approche de 80% de la limite, on pousse encore un peu le côté glouton
            w_courant = w
            if limite_temps is not None:
                ecoule = time.perf_counter() - debut
                if ecoule > limite_temps:
                    return _resultat_partiel(parent, depart, arrivee, explorees, debut, nom, visitees)
                if ecoule > 0.8 * limite_temps:
                    w_courant = max(w_courant, 2.5)

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
                nouveau_g = g[courante] + 1
                memo_v = self.memo_g.get(v)
                if memo_v is not None and memo_v < nouveau_g:
                    nouveau_g = memo_v

                if v not in g or nouveau_g < g[v]:
                    g[v] = nouveau_g
                    self.memo_g[v] = nouveau_g
                    parent[v] = courante
                    h = manhattan(v, arrivee)
                    compteur += 1
                    heapq.heappush(tas, (nouveau_g + w_courant * h, h, compteur, v))

        return Resultat(None, explorees, time.perf_counter() - debut, nom, visitees=visitees)


_hybride_instance = _MemoGloutonAStar()


def hybride_dp_glouton(grille, depart, arrivee, limite_temps=None):
    """Point d'entrée de l'algorithme personnalisé (A* + 1 table de mémoïsation + glouton)."""
    return _hybride_instance.executer(grille, depart, arrivee, limite_temps)


# ----------------------------------------------------------------------
# Stratégie de sélection dynamique
# ----------------------------------------------------------------------
def choisir_algorithme_dynamique(grille, depart, arrivee, limite_temps=None,
                                 nb_replanifications=0, temps_moyen_ms=None):
    """Choisit automatiquement l'algorithme le plus pertinent selon :
    - la taille de la grille (m) et le budget temps T(m),
    - la densité d'obstacles,
    - le dynamisme (nombre de replanifications),
    - l'historique du temps moyen par rapport à la limite.
    """
    nb_cases = max(1, grille.lignes * grille.colonnes)
    densite = len(grille.obstacles) / nb_cases
    m = max(grille.lignes, grille.colonnes)
    tm_ms = limite_temps_prof_ms(m)
    budget_ms = limite_temps * 1000.0 if limite_temps is not None else tm_ms

    # 1. Moyenne déjà proche ou supérieure au budget -> privilégier la rapidité gloutonne/hybride
    if temps_moyen_ms is not None and temps_moyen_ms > 0.85 * budget_ms:
        return hybride_dp_glouton

    # 2. Grille grande ou densité élevée ou budget serré -> algorithme hybride DP + glouton
    if m >= 120 or densite >= 0.20 or budget_ms <= 80.0:
        return hybride_dp_glouton

    # 3. Replanifications fréquentes sur grille moyenne -> algorithme hybride (mémoïsation)
    if nb_replanifications >= 2 and m >= 75:
        return hybride_dp_glouton

    # 4. Petite/moyenne grille peu dense avec budget confortable -> A* exact
    if densite < 0.15:
        return a_star

    # 5. Cas intermédiaire -> BFS
    return bfs


def selection_dynamique(grille, depart, arrivee, limite_temps=None,
                        nb_replanifications=0, temps_moyen_ms=None):
    """Exécute l'algorithme sélectionné dynamiquement et indique le choix dans le nom."""
    debut = time.perf_counter()
    algo_fn = choisir_algorithme_dynamique(
        grille, depart, arrivee,
        limite_temps=limite_temps,
        nb_replanifications=nb_replanifications,
        temps_moyen_ms=temps_moyen_ms,
    )
    res = algo_fn(grille, depart, arrivee, limite_temps)
    res.nom = f"Auto [{res.nom}]"
    if res.temps == 0.0:
        res.temps = time.perf_counter() - debut
    return res


ALGORITHMES = {
    "bfs": bfs,
    "dijkstra": dijkstra,
    "astar": a_star,
    "hybride": hybride_dp_glouton,
    "auto": selection_dynamique,
}


# ----------------------------------------------------------------------
# Comparaison (pour le rapport)
# ----------------------------------------------------------------------
def comparer_algorithmes(grille, depart, arrivee, limite_temps=None, repetitions=1):
    """Lance chaque algorithme sur la même grille. Renvoie la liste des Resultat.
    Le temps affiché est la moyenne sur `repetitions` exécutions."""
    resultats = []
    algos_a_comparer = {k: v for k, v in ALGORITHMES.items() if k != "auto"}
    for fonction in algos_a_comparer.values():
        total = 0.0
        res = None
        for _ in range(repetitions):
            res = fonction(grille, depart, arrivee, limite_temps)
            total += res.temps
        res.temps = total / repetitions
        resultats.append(res)
    return resultats