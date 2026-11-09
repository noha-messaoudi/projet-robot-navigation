"""Contrôleur : relie la vue (CustomTkinter) au modèle.

La vue ne connaît pas le modèle, le modèle ne connaît pas la vue :
tout passe par ce fichier.
"""
from model.modele import ModeleNavigation, ARRIVE, BLOQUE, REPLANIFIE


class Controleur:
    PROBA_OBSTACLE = 0.3   # probabilité d'un événement aléatoire avant chaque pas

    def __init__(self, vue, lignes=100, colonnes=100):
        self.vue = vue
        self.lignes, self.colonnes = lignes, colonnes
        self.timer = None            # identifiant du timer de la vue
        self.peinture = None         # True = on pose des obstacles en glissant, False = on les retire
        self._dernier_dessine = None # dernier Resultat dont les cases explorées sont affichées
        self._nouveau_modele()

        vue.lier(clic=self.clic, glisser=self.glisser, relache=self.relache,
                 calculer=self.calculer, demarrer=self.demarrer, pause=self.pause,
                 pas=self.pas, reinitialiser=self.reinitialiser, effacer=self.effacer,
                 generer=self.generer, comparer=self.comparer, options=self.appliquer_options)
        self.appliquer_options()
        self._rafraichir_trajet()

    # ------------------------------------------------------------------
    # Modèle et options
    # ------------------------------------------------------------------
    def _nouveau_modele(self):
        # le robot et la destination sont dessinés en 3x3 cases : on les éloigne des bords
        self.modele = ModeleNavigation(self.lignes, self.colonnes, depart=(2, 2),
                                       destination=(self.lignes - 3, self.colonnes - 3))

    def appliquer_options(self):
        """Lit les réglages de la vue et les donne au modèle."""
        self.modele.choisir_algorithme(self.vue.algorithme_choisi())
        self.modele.mode_optimal = self.vue.mode_optimal()
        texte = self.vue.limite_texte().replace(",", ".")
        try:
            ms = float(texte)
            self.modele.limite_temps = ms / 1000 if ms > 0 else None
        except ValueError:
            self.modele.limite_temps = None   # champ vide ou invalide : pas de limite

    def _delai(self):
        """Vitesse du curseur (1 à 100) -> délai entre deux pas en millisecondes."""
        return max(10, 1000 // max(1, self.vue.vitesse()))

    # ------------------------------------------------------------------
    # Souris
    # ------------------------------------------------------------------
    def clic(self, l, c):
        case = (l, c)
        mode = self.vue.mode()
        if mode == "obstacle":
            self.peinture = case not in self.modele.grille.obstacles
            self._peindre(case)
        elif mode == "depart":
            self.modele.definir_depart(case)
            self._apres_deplacement_point()
        elif mode == "destination":
            self.modele.definir_destination(case)
            self._apres_deplacement_point()

    def glisser(self, l, c):
        if self.vue.mode() == "obstacle" and self.peinture is not None:
            self._peindre((l, c))

    def relache(self):
        self.peinture = None

    def _peindre(self, case):
        """Pose (ou retire) un obstacle selon le geste commencé au clic."""
        m = self.modele
        if case in (m.robot.position, m.destination):
            return
        existe = case in m.grille.obstacles
        if self.peinture and not existe:
            m.basculer_obstacle(case)
            self.vue.poser_obstacle(case)
        elif not self.peinture and existe:
            m.basculer_obstacle(case)
            self.vue.retirer_obstacle(case)

    def _apres_deplacement_point(self):
        """Départ ou destination déplacé : on recalcule si un chemin était affiché."""
        if self.modele.chemin:
            self._calculer()
        else:
            self._rafraichir_trajet()

    # ------------------------------------------------------------------
    # Boutons
    # ------------------------------------------------------------------
    def calculer(self):
        self.appliquer_options()
        self._calculer()

    def _calculer(self):
        chemin = self.modele.calculer_chemin()
        res = self.modele.dernier_resultat
        if chemin is None:
            self.vue.afficher_statut("Aucun chemin", ok=False)
        elif not res.complet:
            self.vue.afficher_statut("Chemin partiel (limite de temps)")
        else:
            self.vue.afficher_statut("Chemin trouvé")
        self._rafraichir_tout()

    def demarrer(self):
        if self.timer is not None or self.modele.a_atteint_destination():
            return
        self.appliquer_options()
        self._tick()

    def pause(self):
        if self.timer is not None:
            self.vue.annuler(self.timer)
            self.timer = None
            self.vue.afficher_statut("En pause")

    def pas(self):
        self.pause()
        self.appliquer_options()
        self._faire_etape()

    def reinitialiser(self):
        self._arreter_timer()
        self._nouveau_modele()
        self.appliquer_options()
        self._dernier_dessine = None
        self.vue.dessiner_obstacles(set())
        self.vue.dessiner_explorees([])
        self.vue.afficher_stats(None, None, None, 0)
        self.vue.afficher_statut("Prêt")
        self._rafraichir_trajet()

    def effacer(self):
        self.modele.grille.vider()
        self.vue.dessiner_obstacles(set())

    def generer(self):
        self.modele.generer_obstacles_aleatoires(0.2)
        self.vue.dessiner_obstacles(self.modele.grille.obstacles)

    def comparer(self):
        self.appliquer_options()
        lignes = []
        for r in self.modele.comparer(repetitions=3):
            long = "–" if r.longueur is None else r.longueur
            lignes.append((r.nom, long, r.cases_explorees, f"{r.temps * 1000:.2f}"))
        self.vue.afficher_comparaison(lignes)

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------
    def _tick(self):
        """Un pas d'animation, puis programmation du suivant."""
        self.timer = None
        if self.vue.obstacles_aleatoires():
            case = self.modele.evenement_aleatoire(self.PROBA_OBSTACLE)
            if case is not None:
                if case in self.modele.grille.obstacles:
                    self.vue.poser_obstacle(case)
                else:
                    self.vue.retirer_obstacle(case)
        statut = self._faire_etape()
        if statut != ARRIVE:
            self.timer = self.vue.programmer(self._delai(), self._tick)

    def _faire_etape(self):
        statut = self.modele.etape()
        if statut == ARRIVE:
            self.vue.afficher_statut("Destination atteinte !")
        elif statut == BLOQUE:
            self.vue.afficher_statut("Aucun chemin pour l'instant…", ok=False)
        elif statut == REPLANIFIE:
            self.vue.afficher_statut("Replanification")
        else:
            self.vue.afficher_statut("En route")
        self._rafraichir_tout()
        return statut

    def _arreter_timer(self):
        if self.timer is not None:
            self.vue.annuler(self.timer)
            self.timer = None

    # ------------------------------------------------------------------
    # Affichage
    # ------------------------------------------------------------------
    def _rafraichir_trajet(self):
        m = self.modele
        self.vue.dessiner_trajet(m.chemin or [], m.robot.position, m.destination)

    def _rafraichir_tout(self):
        m = self.modele
        res = m.dernier_resultat
        if res is not None:
            if res is not self._dernier_dessine:   # nouveau calcul : on redessine les explorées
                self.vue.dessiner_explorees(res.cases_visitees)
                self._dernier_dessine = res
            self.vue.afficher_stats(res.longueur, res.cases_explorees,
                                    res.temps * 1000, m.nb_replanifications)
        self._rafraichir_trajet()