"""Modèle : façade unique utilisée par le contrôleur / la vue (niveaux 1, 2 et 3)."""
import random

from .grille import Grille
from .robot import Robot
from .algorithmes import ALGORITHMES, comparer_algorithmes, limite_temps_prof_ms

# Statuts renvoyés par etape()
ARRIVE = "arrive"
AVANCE = "avance"
REPLANIFIE = "replanifie"
BLOQUE = "bloque"


class ModeleNavigation:
    def __init__(self, lignes=15, colonnes=15, depart=(0, 0), destination=None,
                 algorithme="astar", limite_temps=None, mode_optimal=False):
        self.grille = Grille(lignes, colonnes)
        self.destination = destination or (lignes - 1, colonnes - 1)
        self.robot = Robot(depart)
        self.chemin = None
        self.dernier_resultat = None
        self.nb_replanifications = 0

        # --- Niveau 3 ---
        self.algorithme = algorithme      # "bfs", "dijkstra", "astar", "hybride" ou "auto"
        self.limite_temps = limite_temps  # secondes (None = pas de limite)
        self.mode_optimal = mode_optimal  # True : recalcul à chaque changement d'obstacle
        self._version_calcul = self.grille.version

        # --- Contrainte temporelle T(m) et suivi des performances ---
        m = max(lignes, colonnes)
        self.limite_tm_ms = limite_temps_prof_ms(m)
        self.limite_manuelle_ms = limite_temps * 1000.0 if limite_temps is not None else None
        self.historique_temps_ms = []
        self._appliquer_limite_effective()

    # ------------------------------------------------------------------
    # Contrainte temporelle T(m) et suivi du temps moyen
    # ------------------------------------------------------------------
    def _appliquer_limite_effective(self):
        """Utilise la limite manuelle si définie, sinon applique automatiquement T(m)."""
        limite_ms = (
            self.limite_manuelle_ms
            if self.limite_manuelle_ms is not None
            else self.limite_tm_ms
        )
        self.limite_temps = limite_ms / 1000.0

    def definir_limite_manuelle_ms(self, limite_ms):
        """Définit une limite manuelle en ms, ou None pour repasser sur T(m) automatique."""
        self.limite_manuelle_ms = limite_ms
        self._appliquer_limite_effective()

    def temps_moyen_ms(self):
        """Temps moyen de calcul (en ms) sur les calculs effectués."""
        if not self.historique_temps_ms:
            return None
        return sum(self.historique_temps_ms) / len(self.historique_temps_ms)

    def respecte_limite_moyenne(self):
        """Vérifie si le temps moyen respecte la limite active (en ms)."""
        moy = self.temps_moyen_ms()
        if moy is None:
            return None
        limite_active_ms = (
            self.limite_temps * 1000.0
            if self.limite_temps is not None
            else self.limite_tm_ms
        )
        return moy <= limite_active_ms

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    def basculer_obstacle(self, case):
        if case in (self.robot.position, self.destination):
            return
        self.grille.basculer_obstacle(case)

    def definir_destination(self, case):
        if self.grille.est_libre(case):
            self.destination = case

    def definir_depart(self, case):
        if self.grille.est_libre(case):
            self.robot = Robot(case)
            self.chemin = None

    def choisir_algorithme(self, nom):
        if nom not in ALGORITHMES:
            raise ValueError(f"Algorithme inconnu : {nom}")
        self.algorithme = nom

    def generer_obstacles_aleatoires(self, densite=0.2):
        self.grille.generer_obstacles_aleatoires(
            densite, exclus={self.robot.position, self.destination})

    # ------------------------------------------------------------------
    # Calcul du chemin
    # ------------------------------------------------------------------
    def calculer_chemin(self):
        self._appliquer_limite_effective()
        fonction = ALGORITHMES[self.algorithme]
        if self.algorithme == "auto":
            res = fonction(
                self.grille,
                self.robot.position,
                self.destination,
                self.limite_temps,
                nb_replanifications=self.nb_replanifications,
                temps_moyen_ms=self.temps_moyen_ms(),
            )
        else:
            res = fonction(self.grille, self.robot.position, self.destination, self.limite_temps)
        self.dernier_resultat = res
        self.historique_temps_ms.append(res.temps * 1000.0)
        self._version_calcul = self.grille.version
        self.chemin = res.chemin
        self.robot.definir_chemin(res.chemin)
        return self.chemin  # None si aucun chemin

    def comparer(self, repetitions=5):
        """Compare les algorithmes depuis la position actuelle du robot."""
        return comparer_algorithmes(self.grille, self.robot.position, self.destination,
                                    self.limite_temps, repetitions)

    def a_atteint_destination(self):
        return self.robot.position == self.destination

    # ------------------------------------------------------------------
    # Simulation (niveaux 2 et 3)
    # ------------------------------------------------------------------
    def chemin_est_valide(self):
        return all(self.grille.est_libre(case) for case in self.robot.chemin)

    def _mettre_a_jour_chemin_affiche(self):
        if self.robot.chemin:
            self.chemin = [self.robot.position] + self.robot.chemin
        else:
            self.chemin = None if not self.a_atteint_destination() else [self.robot.position]

    def etape(self):
        """Un pas de simulation, à appeler à chaque tick du timer.

        On recalcule le chemin si :
          - le robot n'en a plus (début, ou chemin partiel terminé) ;
          - le chemin restant est bloqué par un obstacle (niveau 2) ;
          - mode_optimal : la grille a changé depuis le dernier calcul (niveau 3),
            pour profiter d'un raccourci qui vient de s'ouvrir.
        """
        if self.a_atteint_destination():
            return ARRIVE

        grille_changee = self.grille.version != self._version_calcul
        doit_recalculer = (not self.robot.chemin
                           or not self.chemin_est_valide()
                           or (self.mode_optimal and grille_changee))

        replanifie = False
        if doit_recalculer:
            replanifie = True
            self.nb_replanifications += 1
            self.calculer_chemin()
            if self.chemin is None:
                return BLOQUE

        self.robot.avancer()
        self._mettre_a_jour_chemin_affiche()

        if self.a_atteint_destination():
            return ARRIVE
        return REPLANIFIE if replanifie else AVANCE

    def evenement_aleatoire(self, probabilite=0.3, nb_obstacles=1, cibler_chemin=False):
        """Fait apparaître ou disparaître `nb_obstacles` au hasard avec la probabilité `probabilite`.
        Renvoie la liste des cases modifiées.
        """
        if probabilite <= 0 or random.random() > probabilite:
            return []

        modifiees = []
        interdits = {self.robot.position, self.destination}

        for _ in range(max(1, int(nb_obstacles))):
            if cibler_chemin and self.robot.chemin and random.random() < 0.4:
                case = random.choice(self.robot.chemin)
            else:
                case = (
                    random.randrange(self.grille.lignes),
                    random.randrange(self.grille.colonnes),
                )
            if case in interdits:
                continue
            self.grille.basculer_obstacle(case)
            modifiees.append(case)

        return modifiees