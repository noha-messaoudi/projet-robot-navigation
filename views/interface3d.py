"""Interface 2D superposée à la scène 3D : panneau de droite (boutons, algorithmes, statistiques...)."""
from ursina import Button, Entity, InputField, Text, camera, color, mouse, window
from .config import ALGOS, C, MODES


def hexcol(h):
    return color.hex(h)


class Bloc(Entity):
    """Carte du panneau : position locale (0,0) = coin haut-gauche, y négatif vers le bas."""

    def __init__(self, parent, largeur, hauteur, niveau, titre=None, fond=True):
        super().__init__(parent=parent)
        self.largeur, self.hauteur, self.niveau = largeur, hauteur, niveau
        if fond:
            Entity(parent=self, model="quad", scale=(largeur, hauteur), position=(largeur / 2, -hauteur / 2, 0.5),
                   color=hexcol(C["panneau"]), collider="box")
        if titre:
            Text(parent=self, text=titre.upper(), x=0.012, y=-0.008, scale=0.62, color=hexcol(C["titre"]))


class Interface:
    LARGEUR = 0.36

    def __init__(self, vue):
        self.vue = vue
        self.niveau = 3
        self.blocs = []
        self.mode = "obstacle"
        self.algo = "A* (recommandé)"
        self.optimal = True
        self.aleatoire = False
        self.vitesse = 60
        self.aspect = None
        self.racine = Entity(parent=camera.ui)
        self.gauche = Entity(parent=camera.ui)
        self.fond = Entity(parent=self.racine, model="quad", color=hexcol(C["entete"]), z=1, collider="box")
        self._construire()
        self.afficher_niveau(3)

    # ---------- fabrique ----------
    def _bouton(self, parent, texte, x, y, w, h, action, primaire=False):
        b = Button(parent=parent, text=texte, scale=(w, h), position=(x + w / 2, y - h / 2, -0.1),
                   color=hexcol(C["bleu"] if primaire else C["panneau2"]), on_click=action, text_size=0.62)
        return b

    def _texte(self, parent, texte, x, y, taille=0.7, coul="texte"):
        return Text(parent=parent, text=texte, x=x, y=y, scale=taille, color=hexcol(C[coul]))

    def _bloc(self, h, niveau, titre=None, fond=True):
        b = Bloc(self.racine, self.LARGEUR, h, niveau, titre, fond)
        self.blocs.append(b)
        return b

    def _appeler(self, nom):
        return lambda: self.vue._appeler(nom)

    # ---------- construction ----------
    def _construire(self):
        L = self.LARGEUR
        # --- titre en haut à gauche ---
        self._texte(self.gauche, "RUBON", 0, 0, 1.4, "texte")
        self._texte(self.gauche, "Navigation du robot · vue 3D", 0, -0.034, 0.7, "discret")
        self._texte(self.gauche, "Clic gauche : obstacle/départ/destination   ·   Clic droit : tourner   ·   "
                    "Molette : zoom   ·   Clic milieu ou flèches : déplacer   ·   R : vue d'origine",
                    0, -0.07, 0.55, "discret")
        self.lbl_statut = Text(parent=camera.ui, text="Prêt", origin=(-0.5, -0.5), scale=0.9, color=hexcol(C["vert"]))
        self.lbl_grille = self._texte(self.gauche, "", 0, -0.095, 0.6, "discret")

        # --- niveaux ---
        b = self._bloc(0.05, 1, fond=False)
        self.btn_niveau = {}
        for i in (1, 2, 3):
            self.btn_niveau[i] = self._bouton(b, f"Niveau {i}", i * 0 + (i - 1) * (L / 3), 0, L / 3 - 0.006, 0.044,
                                              lambda n=i: self.afficher_niveau(n))

        # --- simulation ---
        b = self._bloc(0.05, 1, fond=False)
        self._bouton(b, "Calculer le chemin", 0, 0, L / 2 - 0.006, 0.044, self._appeler("calculer"), True)
        self._bouton(b, "Réinitialiser", L / 2, 0, L / 2, 0.044, self._appeler("reinitialiser"))
        b = self._bloc(0.05, 2, fond=False)
        w = (L - 0.012) / 3
        self._bouton(b, "Démarrer", 0, 0, w, 0.044, self._appeler("demarrer"), True)
        self._bouton(b, "Pause", w + 0.006, 0, w, 0.044, self._appeler("pause"))
        self._bouton(b, "Pas à pas", 2 * (w + 0.006), 0, w, 0.044, self._appeler("pas"))
        self._construire_vitesse()

        # --- édition ---
        b = self._bloc(0.135, 1, "Édition de la grille")
        self.btn_mode = {}
        w = (L - 0.03 - 0.012) / 3
        for i, nom in enumerate(MODES):
            self.btn_mode[nom] = self._bouton(b, nom, 0.015 + i * (w + 0.006), -0.034, w, 0.04,
                                              lambda n=nom: self._choisir_mode(n))
        self._bouton(b, "Effacer les obstacles", 0.015, -0.082, (L - 0.036) / 2, 0.04, self._appeler("effacer"))
        self.btn_generer = self._bouton(b, "Générer des obstacles", 0.015 + (L - 0.036) / 2 + 0.006, -0.082,
                                        (L - 0.036) / 2, 0.04, self._appeler("generer"))
        self.edition = b
        self._choisir_mode("Obstacle")

        # --- algorithme (niveau 3) ---
        b = self._bloc(0.135, 3, "Algorithme")
        self.btn_algo = {}
        w = (L - 0.03 - 0.012) / 3
        for i, nom in enumerate(ALGOS):
            court = nom.replace(" (recommandé)", "")
            self.btn_algo[nom] = self._bouton(b, court, 0.015 + i * (w + 0.006), -0.034, w, 0.04,
                                              lambda n=nom: self._choisir_algo(n))
        self.btn_optimal = self._bouton(b, "Mode optimal", 0.015, -0.082, 0.165, 0.04, self._basculer_optimal)
        self._texte(b, "Limite (ms)", 0.195, -0.093, 0.6, "discret")
        self.ent_limite = InputField(parent=b, scale=(0.075, 0.04), position=(L - 0.015 - 0.0375, -0.082 - 0.02),
                                     default_value="", character_limit=7, limit_content_to="0123456789")
        self.ent_limite.z = -0.1
        self.ent_limite.color = hexcol(C["panneau2"])
        self._choisir_algo("A* (recommandé)")
        self._maj_optimal()

        # --- obstacles dynamiques (niveau 2) ---
        b = self._bloc(0.085, 2, "Niveaux 2 & 3 · Obstacles dynamiques")
        self.btn_alea = self._bouton(b, "Obstacles aléatoires", 0.015, -0.034, L - 0.03, 0.04, self._basculer_alea)
        self._maj_alea()

        # --- statistiques (niveau 3) ---
        b = self._bloc(0.15, 3, "Performances (dernier résultat)")
        self.txt_stats = {}
        w = (L - 0.03 - 0.008) / 2
        for i, (cle, lib) in enumerate((("longueur", "Longueur du chemin"), ("explorees", "Cases explorées"),
                                        ("temps", "Temps de calcul (ms)"), ("replans", "Replanifications"))):
            x = 0.015 + (i % 2) * (w + 0.008)
            y = -0.034 - (i // 2) * 0.057
            Entity(parent=b, model="quad", scale=(w, 0.052), position=(x + w / 2, y - 0.026, 0.2),
                   color=hexcol(C["panneau2"]))
            self._texte(b, lib, x + 0.008, y - 0.006, 0.55, "discret")
            self.txt_stats[cle] = self._texte(b, "–", x + 0.008, y - 0.022, 1.0, "texte")

        # --- comparaison (niveau 3) ---
        b = self._bloc(0.175, 3, "Comparaison")
        self._bouton(b, "Comparer les algorithmes", 0.015, -0.034, L - 0.03, 0.04, self._appeler("comparer"))
        self.cellules = []
        xs = (0.02, 0.15, 0.22, 0.31)
        for i in range(4):
            rang = []
            for j in range(4):
                t = self._texte(b, ("Algo", "Long.", "Explorées", "ms")[j] if i == 0 else "–", xs[j] - 0.005 * (j > 0),
                                -0.086 - i * 0.021, 0.62, "discret" if i == 0 else "texte")
                rang.append(t)
            self.cellules.append(rang)

    def _construire_vitesse(self):
        L = self.LARGEUR
        b = self._bloc(0.04, 2, fond=False)
        self._texte(b, "Vitesse", 0.004, -0.012, 0.65, "discret")
        self.piste = Button(parent=b, scale=(0.18, 0.014), position=(0.19, -0.02, -0.1),
                            color=hexcol(C["panneau2"]), highlight_color=hexcol(C["bordure"]),
                            pressed_color=hexcol(C["bordure"]))
        self.poignee = Entity(parent=b, model="quad", scale=(0.014, 0.03), z=-0.2, color=hexcol(C["bleu"]),
                              y=-0.02)
        self.txt_vitesse = self._texte(b, "60", L - 0.06, -0.012, 0.65, "texte")
        self._maj_vitesse(60)

    # ---------- état des boutons ----------
    def _colorer(self, bouton, actif):
        bouton.color = hexcol(C["selection"] if actif else C["panneau2"])

    def _choisir_mode(self, nom):
        self.mode = MODES[nom]
        for n, b in self.btn_mode.items():
            self._colorer(b, n == nom)

    def _choisir_algo(self, nom):
        self.algo = nom
        for n, b in self.btn_algo.items():
            self._colorer(b, n == nom)
        self.vue._appeler("options")

    def _basculer_optimal(self):
        self.optimal = not self.optimal
        self._maj_optimal()
        self.vue._appeler("options")

    def _maj_optimal(self):
        self.btn_optimal.text = "Mode optimal : " + ("oui" if self.optimal else "non")
        self._colorer(self.btn_optimal, self.optimal)

    def _basculer_alea(self):
        self.aleatoire = not self.aleatoire
        self._maj_alea()

    def _maj_alea(self):
        self.btn_alea.text = "Obstacles aléatoires : " + ("activés" if self.aleatoire else "désactivés") + " (p = 0,3)"
        self._colorer(self.btn_alea, self.aleatoire)

    def _maj_vitesse(self, v):
        self.vitesse = int(max(1, min(100, v)))
        self.poignee.x = self.piste.x - 0.09 + (self.vitesse - 1) / 99 * 0.18
        self.txt_vitesse.text = str(self.vitesse)
        if hasattr(self.vue, "scene"):
            self.vue.scene.vitesse = self.vitesse

    # ---------- niveaux et disposition ----------
    def afficher_niveau(self, n):
        self.niveau = n
        for i, b in self.btn_niveau.items():
            self._colorer(b, i == n)
        self.btn_generer.enabled = n >= 3
        self._disposer()

    def _disposer(self):
        self.aspect = window.aspect_ratio
        x = self.aspect / 2 - self.LARGEUR - 0.015
        self.racine.position = (0, 0)
        self.fond.scale = (self.LARGEUR + 0.03, 1.2)
        self.fond.position = (x + self.LARGEUR / 2, 0, 1)
        y = 0.48
        for b in self.blocs:
            b.enabled = b.niveau <= self.niveau
            if b.enabled:
                b.position = (x, y)
                y -= b.hauteur + 0.007
        self.gauche.position = (-self.aspect / 2 + 0.02, 0.48)
        self.lbl_statut.position = (-self.aspect / 2 + 0.02, -0.48)

    # ---------- mise à jour à chaque image ----------
    def mettre_a_jour(self):
        if window.aspect_ratio != self.aspect:
            self._disposer()
        if mouse.left and mouse.hovered_entity is self.piste:
            self._maj_vitesse(1 + (mouse.point[0] + 0.5) * 99)

    # ---------- affichage ----------
    def afficher_statut(self, texte, ok=True):
        self.lbl_statut.text = texte
        self.lbl_statut.color = hexcol(C["vert"] if ok else C["rouge"])

    def afficher_stats(self, longueur, explorees, temps_ms, replanifications):
        fmt = lambda v, f="{}": "–" if v is None else f.format(v)
        self.txt_stats["longueur"].text = fmt(longueur)
        self.txt_stats["explorees"].text = fmt(explorees)
        self.txt_stats["temps"].text = fmt(temps_ms, "{:.2f}")
        self.txt_stats["replans"].text = str(replanifications)

    def afficher_comparaison(self, lignes):
        for i in range(3):
            valeurs = lignes[i] if i < len(lignes) else ("–",) * 4
            for j, v in enumerate(valeurs):
                self.cellules[i + 1][j].text = str(v)