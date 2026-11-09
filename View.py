"""Vue RUBON (CustomTkinter) : affichage et saisie uniquement, aucune logique métier.
Installation : pip install customtkinter
La vue ne connaît pas le modèle : le contrôleur lui donne des données simples
et lui branche des fonctions via `lier(...)`.
"""
import tkinter as tk

import customtkinter as ctk

ctk.set_appearance_mode("dark")

C = dict(fond="#0a1222", entete="#0c1528", panneau="#0f1a30", panneau2="#142240", bordure="#1f2f4d",
         texte="#e8eefb", discret="#8d9bb8", bleu="#3b82f6", bleu_h="#2f6fd8", vert="#22c55e",
         vert_fond="#0f2d22", rouge="#f87171", rouge_fond="#35161a", obstacle="#6b7686",
         grille="#1a2a4a", zone="#0a1426", canvas="#0c1830", explore="#12264a", titre="#6ea0ff",
         selection="#16305f")
ALGOS = {"A* (recommandé)": "astar", "Dijkstra": "dijkstra", "BFS": "bfs"}
MODES = {"Obstacle": "obstacle", "Départ": "depart", "Destination": "destination"}
FAMILLE = "Segoe UI"


class Vue(ctk.CTk):
    def __init__(self, lignes=100, colonnes=100, taille_case=None):
        super().__init__()
        self.title("RUBON – Navigation du robot")
        self.configure(fg_color=C["fond"])
        self.resizable(False, False)
        self.lignes, self.colonnes = lignes, colonnes
        # taille d'une case adaptée à la hauteur de l'écran (4 à 7 pixels)
        self.s = taille_case or max(4, min(7, (self.winfo_screenheight() - 400) // lignes))
        self.commandes: dict = {}
        self._elements = []  # (widget, niveau minimal, options pack), dans l'ordre de création
        self._mode = "obstacle"

        self.var_algo = tk.StringVar(value="A* (recommandé)")
        self.var_optimal = tk.BooleanVar(value=True)
        self.var_aleatoire = tk.BooleanVar(value=False)
        self.var_vitesse = tk.DoubleVar(value=60)
        self.var_stats = {k: tk.StringVar(value="–") for k in ("longueur", "explorees", "temps", "replans")}
        self.f = lambda t=12, g=False: ctk.CTkFont(family=FAMILLE, size=t, weight="bold" if g else "normal")

        self._construire()
        self.afficher_niveau(3)

    # ---------- liaison avec le contrôleur ----------
    def lier(self, **commandes):
        self.commandes.update(commandes)

    def _appeler(self, nom, *args):
        fn = self.commandes.get(nom)
        return fn(*args) if fn else None

    def programmer(self, delai_ms, fonction):
        return self.after(delai_ms, fonction)

    def annuler(self, ident):
        self.after_cancel(ident)

    # ---------- lecture des contrôles ----------
    def mode(self): return self._mode
    def algorithme_choisi(self): return ALGOS[self.var_algo.get()]
    def mode_optimal(self): return self.var_optimal.get()
    def limite_texte(self): return self.ent_limite.get().strip()
    def obstacles_aleatoires(self): return self.var_aleatoire.get()
    def vitesse(self): return int(self.var_vitesse.get())

    # ---------- fabrique de widgets ----------
    def _ajouter(self, widget, niveau=1, **pack):
        self._elements.append((widget, niveau, pack))
        return widget

    def _bouton(self, parent, texte, nom, niveau=1, primaire=False, **pack):
        if primaire:
            kw = dict(fg_color=C["bleu"], hover_color=C["bleu_h"])
        else:
            kw = dict(fg_color=C["panneau2"], hover_color=C["bordure"], border_width=1, border_color=C["bordure"])
        b = ctk.CTkButton(parent, text=texte, command=lambda: self._appeler(nom), corner_radius=8, height=34,
                          text_color=C["texte"], font=self.f(12, primaire), **kw)
        return self._ajouter(b, niveau, **pack)

    def _carte(self, parent, titre, niveau=1):
        f = ctk.CTkFrame(parent, corner_radius=14, fg_color=C["panneau"], border_width=1, border_color=C["bordure"])
        ctk.CTkLabel(f, text=titre.upper(), text_color=C["titre"], font=self.f(10, True)).pack(
            anchor="w", padx=14, pady=(12, 6))
        return self._ajouter(f, niveau, fill="x", pady=(0, 10))

    @staticmethod
    def _fin(carte):
        ctk.CTkFrame(carte, height=6, fg_color="transparent").pack()

    @staticmethod
    def _arrondi(cv, x1, y1, x2, y2, r, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
               x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return cv.create_polygon(pts, smooth=True, **kw)

    def _logo(self, parent):
        cv = tk.Canvas(parent, width=40, height=40, bg=C["entete"], highlightthickness=0)
        self._arrondi(cv, 2, 2, 38, 38, 10, fill=C["bleu"])
        self._arrondi(cv, 10, 14, 30, 30, 5, fill="#dbe8ff")
        cv.create_oval(14, 19, 19, 24, fill=C["bleu"], outline="")
        cv.create_oval(21, 19, 26, 24, fill=C["bleu"], outline="")
        cv.create_line(20, 14, 20, 9, fill="#dbe8ff", width=2)
        cv.create_oval(18, 6, 22, 10, fill="#dbe8ff", outline="")
        return cv

    # ---------- construction ----------
    def _construire(self):
        # --- en-tête ---
        tete = ctk.CTkFrame(self, corner_radius=0, fg_color=C["entete"], height=64)
        tete.pack(fill="x")
        self._logo(tete).pack(side="left", padx=(22, 10), pady=12)
        bloc = ctk.CTkFrame(tete, fg_color="transparent")
        bloc.pack(side="left")
        ctk.CTkLabel(bloc, text="RUBON", font=self.f(14, True), text_color=C["texte"]).pack(anchor="w")
        ctk.CTkLabel(bloc, text="Robot for Urban Navigation and Barrier Obstacle Navigation", font=self.f(10),
                     text_color=C["discret"]).pack(anchor="w")
        ctk.CTkLabel(tete, text="  ●  Simulation active  ", fg_color=C["vert_fond"], text_color=C["vert"],
                     corner_radius=14, height=30, font=self.f(11)).pack(side="right", padx=22)

        # --- titre + niveaux ---
        haut = ctk.CTkFrame(self, fg_color="transparent")
        haut.pack(fill="x", padx=22, pady=(14, 8))
        gauche_t = ctk.CTkFrame(haut, fg_color="transparent")
        gauche_t.pack(side="left")
        ctk.CTkLabel(gauche_t, text="PROJET ALGORITHMIQUE", font=self.f(10, True), text_color=C["titre"]).pack(anchor="w")
        ctk.CTkLabel(gauche_t, text="Navigation du robot", font=self.f(26, True), text_color=C["texte"]).pack(anchor="w")
        ctk.CTkLabel(gauche_t, text="Explorez, testez et comparez les stratégies de recherche de chemin.",
                     font=self.f(12), text_color=C["discret"]).pack(anchor="w")
        self.seg_niveau = ctk.CTkSegmentedButton(
            haut, values=["Niveau 1", "Niveau 2", "Niveau 3"], command=lambda v: self.afficher_niveau(int(v[-1])),
            fg_color=C["panneau"], selected_color=C["panneau2"], selected_hover_color=C["panneau2"],
            unselected_color=C["panneau"], unselected_hover_color=C["panneau2"], text_color=C["texte"],
            font=self.f(12), height=38)
        self.seg_niveau.set("Niveau 3")
        self.seg_niveau.pack(side="right", anchor="s")

        corps = ctk.CTkFrame(self, fg_color="transparent")
        corps.pack(fill="both", expand=True, padx=22, pady=(0, 18))

        # --- carte de simulation ---
        sim = ctk.CTkFrame(corps, corner_radius=14, fg_color=C["panneau"], border_width=1, border_color=C["bordure"])
        sim.pack(side="left", anchor="n")
        entete = ctk.CTkFrame(sim, fg_color="transparent")
        entete.pack(fill="x", padx=16, pady=(12, 8))
        t = ctk.CTkFrame(entete, fg_color="transparent")
        t.pack(side="left")
        ctk.CTkLabel(t, text="Environnement de simulation", font=self.f(13, True), text_color=C["texte"]).pack(anchor="w")
        ctk.CTkLabel(t, text="Clic gauche : poser ou retirer un obstacle (glisser pour peindre)", font=self.f(10),
                     text_color=C["discret"]).pack(anchor="w")
        self.lbl_statut = ctk.CTkLabel(entete, text="  Prêt  ", fg_color=C["vert_fond"], text_color=C["vert"],
                                       corner_radius=8, height=28, font=self.f(11))
        self.lbl_statut.pack(side="right")

        zone = ctk.CTkFrame(sim, corner_radius=0, fg_color=C["zone"])
        zone.pack(fill="x")
        self.canvas = tk.Canvas(zone, width=self.colonnes * self.s, height=self.lignes * self.s, bg=C["canvas"],
                                highlightthickness=1, highlightbackground=C["bordure"], cursor="crosshair")
        self.canvas.pack(padx=12, pady=12)
        for k in range(0, self.colonnes + 1, 10):
            self.canvas.create_line(k * self.s, 0, k * self.s, self.lignes * self.s, fill=C["grille"], tags="grille")
        for k in range(0, self.lignes + 1, 10):
            self.canvas.create_line(0, k * self.s, self.colonnes * self.s, k * self.s, fill=C["grille"], tags="grille")
        self.canvas.bind("<Button-1>", lambda e: self._souris("clic", e))
        self.canvas.bind("<B1-Motion>", lambda e: self._souris("glisser", e))
        self.canvas.bind("<ButtonRelease-1>", lambda e: self._appeler("relache"))

        leg = ctk.CTkFrame(sim, fg_color="transparent")
        leg.pack(fill="x", padx=16, pady=(8, 2))
        for txt, col in (("●", C["bleu"]), ("●", C["vert"]), ("■", C["obstacle"]), ("■", C["explore"]),
                         ("┅", C["bleu"])):
            pass
        for sym, col, nom in (("●", C["bleu"], "Robot"), ("●", C["vert"], "Destination"),
                              ("■", C["obstacle"], "Obstacle"), ("■", "#1d3b78", "Explorées"),
                              ("┅", C["bleu"], "Chemin")):
            ctk.CTkLabel(leg, text=sym, text_color=col, font=self.f(11), width=12).pack(side="left")
            ctk.CTkLabel(leg, text=nom, text_color=C["discret"], font=self.f(10)).pack(side="left", padx=(2, 12))
        ctk.CTkLabel(leg, text=f"Grille {self.colonnes} × {self.lignes}", text_color=C["discret"],
                     font=self.f(10)).pack(side="right")

        barre = ctk.CTkFrame(sim, fg_color="transparent")
        barre.pack(fill="x", padx=16, pady=(6, 14))
        self._bouton(barre, "Calculer le chemin", "calculer", 1, True, side="left", padx=(0, 8))
        self._bouton(barre, "▶  Démarrer", "demarrer", 2, True, side="left", padx=(0, 8))
        self._bouton(barre, "⏸  Pause", "pause", 2, side="left", padx=(0, 8))
        self._bouton(barre, "⏭  Pas à pas", "pas", 2, side="left", padx=(0, 8))
        self._bouton(barre, "↺  Réinitialiser", "reinitialiser", 1, side="left")
        vit = ctk.CTkFrame(barre, fg_color="transparent")
        ctk.CTkLabel(vit, text="Vitesse", font=self.f(11), text_color=C["discret"]).pack(side="left", padx=(0, 8))
        ctk.CTkSlider(vit, from_=1, to=100, variable=self.var_vitesse, width=110, progress_color=C["bleu"],
                      button_color=C["bleu"], button_hover_color=C["bleu_h"], fg_color=C["panneau2"]).pack(side="left")
        self._ajouter(vit, 2, side="right")

        # --- colonne de droite ---
        droite = ctk.CTkFrame(corps, fg_color="transparent", width=340)
        droite.pack(side="left", fill="y", padx=(16, 0), anchor="n")

        edition = self._carte(droite, "Édition de la grille", 1)
        seg = ctk.CTkSegmentedButton(
            edition, values=list(MODES), command=lambda v: setattr(self, "_mode", MODES[v]),
            fg_color=C["panneau2"], selected_color=C["selection"], selected_hover_color=C["selection"],
            unselected_color=C["panneau2"], unselected_hover_color=C["bordure"], text_color=C["texte"],
            font=self.f(12), height=34)
        seg.set("Obstacle")
        seg.pack(fill="x", padx=14, pady=(0, 8))
        outils = ctk.CTkFrame(edition, fg_color="transparent")
        outils.pack(fill="x", padx=14, pady=(0, 6))
        self._bouton(outils, "Effacer les obstacles", "effacer", 1, side="left", padx=(0, 8))
        self._bouton(outils, "Générer des obstacles", "generer", 3, side="left")
        self._fin(edition)

        algo = self._carte(droite, "Algorithme", 3)
        ctk.CTkOptionMenu(algo, values=list(ALGOS), variable=self.var_algo, height=34, anchor="w",
                          command=lambda _v: self._appeler("options"), fg_color=C["panneau2"],
                          button_color=C["bordure"], button_hover_color=C["bleu"], dropdown_fg_color=C["panneau2"],
                          dropdown_hover_color=C["bordure"], text_color=C["texte"], dropdown_text_color=C["texte"],
                          font=self.f(12), dropdown_font=self.f(12)).pack(fill="x", padx=14, pady=(0, 8))
        ctk.CTkCheckBox(algo, text="Mode optimal", variable=self.var_optimal, command=lambda: self._appeler("options"),
                        fg_color=C["bleu"], hover_color=C["bleu_h"], border_color=C["bordure"],
                        text_color=C["texte"], font=self.f(12), checkbox_width=18, checkbox_height=18).pack(
            anchor="w", padx=14, pady=(0, 8))
        ligne = ctk.CTkFrame(algo, fg_color="transparent")
        ligne.pack(fill="x", padx=14, pady=(0, 6))
        ctk.CTkLabel(ligne, text="Limite de temps (ms)", font=self.f(12), text_color=C["discret"]).pack(side="left")
        self.ent_limite = ctk.CTkEntry(ligne, width=90, height=30, placeholder_text="aucune", fg_color=C["panneau2"],
                                       border_color=C["bordure"], text_color=C["texte"], font=self.f(12))
        self.ent_limite.pack(side="right")
        self.ent_limite.bind("<FocusOut>", lambda _e: self._appeler("options"))
        self.ent_limite.bind("<Return>", lambda _e: self._appeler("options"))
        self._fin(algo)

        dyn = self._carte(droite, "Niveaux 2 & 3 · Obstacles dynamiques", 2)
        ctk.CTkSwitch(dyn, text="Obstacles aléatoires pendant le trajet", variable=self.var_aleatoire,
                      progress_color=C["bleu"], text_color=C["texte"], font=self.f(12)).pack(
            anchor="w", padx=14, pady=(0, 6))
        ctk.CTkLabel(dyn, text="Probabilité 0,3 avant chaque pas, replanification automatique.", font=self.f(10),
                     text_color=C["discret"], wraplength=290, justify="left").pack(anchor="w", padx=14)
        self._fin(dyn)

        stats = self._carte(droite, "Performances (dernier résultat)", 3)
        grille = ctk.CTkFrame(stats, fg_color="transparent")
        grille.pack(fill="x", padx=11)
        grille.columnconfigure((0, 1), weight=1)
        for i, (cle, lib) in enumerate((("longueur", "Longueur du chemin"), ("explorees", "Cases explorées"),
                                        ("temps", "Temps de calcul (ms)"), ("replans", "Replanifications"))):
            tuile = ctk.CTkFrame(grille, corner_radius=10, fg_color=C["panneau2"])
            tuile.grid(row=i // 2, column=i % 2, sticky="ew", padx=3, pady=3)
            ctk.CTkLabel(tuile, text=lib, font=self.f(10), text_color=C["discret"]).pack(anchor="w", padx=10, pady=(8, 0))
            ctk.CTkLabel(tuile, textvariable=self.var_stats[cle], font=self.f(20, True),
                         text_color=C["texte"]).pack(anchor="w", padx=10, pady=(0, 8))
        self._fin(stats)

        comp = self._carte(droite, "Comparaison", 3)
        self._bouton(comp, "Comparer les algorithmes", "comparer", 3, fill="x", padx=14, pady=(0, 8))
        tab = ctk.CTkFrame(comp, corner_radius=10, fg_color=C["panneau2"])
        self._ajouter(tab, 3, fill="x", padx=14, pady=(0, 6))
        tab.columnconfigure((0, 1, 2, 3), weight=1)
        self.cellules = []
        for i, ligne_txt in enumerate((("Algo", "Long.", "Explorées", "ms"),) + (("–",) * 4,) * 3):
            rang = []
            for j, txt in enumerate(ligne_txt):
                lb = ctk.CTkLabel(tab, text=txt, font=self.f(11, i == 0),
                                  text_color=C["discret"] if i == 0 else C["texte"])
                lb.grid(row=i, column=j, pady=3, sticky="ew")
                rang.append(lb)
            self.cellules.append(rang)
        self._fin(comp)

    def _souris(self, nom, evt):
        l = min(max(evt.y // self.s, 0), self.lignes - 1)
        c = min(max(evt.x // self.s, 0), self.colonnes - 1)
        self._appeler(nom, l, c)

    # ---------- affichage ----------
    def afficher_niveau(self, n):
        self.seg_niveau.set(f"Niveau {n}")
        for w, _, _ in self._elements:
            w.pack_forget()
        for w, niveau, pack in self._elements:  # on réempile dans l'ordre de création
            if niveau <= n:
                w.pack(**pack)

    def afficher_statut(self, texte, ok=True):
        self.lbl_statut.configure(text=f"  {texte}  ", text_color=C["vert"] if ok else C["rouge"],
                                  fg_color=C["vert_fond"] if ok else C["rouge_fond"])

    def afficher_stats(self, longueur, explorees, temps_ms, replanifications):
        fmt = lambda v, f="{}": "–" if v is None else f.format(v)
        self.var_stats["longueur"].set(fmt(longueur))
        self.var_stats["explorees"].set(fmt(explorees))
        self.var_stats["temps"].set(fmt(temps_ms, "{:.2f}"))
        self.var_stats["replans"].set(str(replanifications))

    def afficher_comparaison(self, lignes):
        for i in range(3):
            valeurs = lignes[i] if i < len(lignes) else ("–",) * 4
            for j, v in enumerate(valeurs):
                self.cellules[i + 1][j].configure(text=str(v))

    def _rect(self, case):
        l, c = case
        s = self.s
        return c * s + 1, l * s + 1, (c + 1) * s, (l + 1) * s

    def poser_obstacle(self, case):
        self.canvas.create_rectangle(*self._rect(case), fill=C["obstacle"], outline="",
                                     tags=("obstacle", f"o{case[0]}_{case[1]}"))
        self.canvas.tag_raise("dyn")

    def retirer_obstacle(self, case):
        self.canvas.delete(f"o{case[0]}_{case[1]}")

    def dessiner_obstacles(self, obstacles):
        self.canvas.delete("obstacle")
        for case in obstacles:
            self.poser_obstacle(case)

    def dessiner_explorees(self, cases):
        """Cases explorées par l'algorithme, regroupées par séquences horizontales (peu d'éléments)."""
        cv, s = self.canvas, self.s
        cv.delete("explore")
        par_ligne = {}
        for l, c in cases:
            par_ligne.setdefault(l, []).append(c)
        for l, cols in par_ligne.items():
            cols.sort()
            debut = prec = cols[0]
            for c in cols[1:] + [None]:
                if c is not None and c == prec + 1:
                    prec = c
                    continue
                cv.create_rectangle(debut * s, l * s, (prec + 1) * s, (l + 1) * s, fill=C["explore"],
                                    outline="", tags="explore")
                debut = prec = c
        cv.tag_lower("explore", "grille")

    def dessiner_trajet(self, chemin, position, destination):
        cv, s = self.canvas, self.s
        cv.delete("dyn")
        if len(chemin) > 1:
            pts = [v for l, c in chemin for v in ((c + .5) * s, (l + .5) * s)]
            cv.create_line(*pts, fill=C["bleu"], width=2, dash=(2, 4), tags="dyn")
        l, c = destination
        cv.create_oval((c - 1.2) * s, (l - 1.2) * s, (c + 2.2) * s, (l + 2.2) * s, fill="#14532d",
                       outline="", tags="dyn")
        cv.create_oval((c - .5) * s, (l - .5) * s, (c + 1.5) * s, (l + 1.5) * s, fill=C["vert"],
                       outline="#a7f3d0", tags="dyn")
        l, c = position
        cv.create_rectangle((c - 1) * s, (l - 1) * s, (c + 2) * s, (l + 2) * s, fill=C["bleu"],
                            outline="#bcd4ff", width=2, tags="dyn")
