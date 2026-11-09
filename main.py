from views.vue import Vue                      # <- adaptez au nom du fichier de la vue
from controllers.controleur import Controleur

LIGNES, COLONNES = 100, 100

vue = Vue(LIGNES, COLONNES)
Controleur(vue, LIGNES, COLONNES)
vue.mainloop()