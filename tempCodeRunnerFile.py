"""
import random
from model.modele import ModeleNavigation, ARRIVE
from model.algorithmes import comparer_algorithmes, bfs, a_star
from model.grille import Grille


def afficher(m):
    for l in range(m.grille.lignes):
        ligne = ""
        for c in range(m.grille.colonnes):
            if (l, c) == m.robot.position: ligne += "R "
            elif (l, c) == m.destination: ligne += "D "
            elif (l, c) in m.grille.obstacles: ligne += "# "
            elif m.chemin and (l, c) in m.chemin: ligne += "* "
            else: ligne += ". "
        print(ligne)
    print()


def tableau(resultats):
    print(f"{'Algorithme':<10} {'Longueur':>9} {'Explorées':>10} {'Temps (ms)':>11}  Complet")
    for r in resultats:
        print(f"{r.nom:<10} {str(r.longueur):>9} {r.cases_explorees:>10} "
              f"{r.temps * 1000:>11.3f}  {r.complet}")
    print()


# ---- Test 1 : comparaison des 3 algorithmes sur une même grille ----
print("=== Test 1 : comparaison BFS / Dijkstra / A* (grille 40x40, 25% d'obstacles) ===")
random.seed(3)
while True:  # on régénère la grille tant qu'elle n'a pas de solution
    m = ModeleNavigation(40, 40, depart=(0, 0), destination=(39, 39))
    m.generer_obstacles_aleatoires(0.25)
    if bfs(m.grille, (0, 0), (39, 39)).chemin:
        break
tableau(m.comparer(repetitions=5))

# ---- Test 2 : moyenne sur 30 grilles aléatoires ----
print("=== Test 2 : moyenne sur 30 grilles aléatoires ===")
random.seed(7)
cumul = {}
nb = 0
while nb < 30:
    g = Grille(40, 40)
    g.generer_obstacles_aleatoires(0.25, exclus={(0, 0), (39, 39)})
    res = comparer_algorithmes(g, (0, 0), (39, 39))
    if res[0].chemin is None:
        continue  # grille sans solution : on l'ignore
    nb += 1
    for r in res:
        c = cumul.setdefault(r.nom, [0, 0, 0.0])
        c[0] += r.longueur; c[1] += r.cases_explorees; c[2] += r.temps
print(f"{'Algorithme':<10} {'Long. moy.':>10} {'Expl. moy.':>11} {'Temps moy. (ms)':>16}")
for nom, (lg, ex, t) in cumul.items():
    print(f"{nom:<10} {lg / nb:>10.1f} {ex / nb:>11.1f} {t / nb * 1000:>16.3f}")
print()

# ---- Test 3 : limite de temps ----
print("=== Test 3 : limite de temps sur une grande grille (300x300) ===")
random.seed(5)
g = Grille(300, 300)
g.generer_obstacles_aleatoires(0.2, exclus={(0, 0), (299, 299)})
print("Sans limite  :", bfs(g, (0, 0), (299, 299)))
r = bfs(g, (0, 0), (299, 299), limite_temps=0.01)
print("Limite 10 ms :", r)
print("  -> chemin partiel jusqu'à", r.chemin[-1] if r.chemin else None)
print()

# ---- Test 4 : un obstacle disparaît -> raccourci (niveau 3) ----
print("=== Test 4 : raccourci quand un obstacle disparaît ===")
for mode in (False, True):
    m = ModeleNavigation(7, 7, depart=(0, 0), destination=(0, 6), mode_optimal=mode)
    for l in range(6):
        m.grille.ajouter_obstacle((l, 3))     # mur avec une ouverture en bas
    m.calculer_chemin()
    m.etape()
    m.basculer_obstacle((0, 3))               # le mur s'ouvre en haut
    m.etape()
    print(f"mode_optimal={mode} -> cases restantes pour arriver : {len(m.robot.chemin)}")
print()

# ---- Test 5 : simulation dynamique complète avec A* et limite de temps ----
print("=== Test 5 : simulation dynamique (A*, mode optimal, limite 5 ms) ===")
random.seed(11)
m = ModeleNavigation(15, 15, depart=(0, 0), destination=(14, 14),
                     algorithme="astar", limite_temps=0.005, mode_optimal=True)
m.generer_obstacles_aleatoires(0.2)
m.calculer_chemin()
for tick in range(300):
    m.evenement_aleatoire(0.3)
    if m.etape() == ARRIVE:
        print(f"Arrivé en {tick + 1} ticks, {m.nb_replanifications} recalcul(s)")
        break
else:
    print("Pas arrivé")
afficher(m)
"""