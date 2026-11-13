from views.view import Vue
from views.config import LIGNES, COLONNES
from controllers.controleur import Controleur

vue = Vue(LIGNES, COLONNES)
Controleur(vue, LIGNES, COLONNES)
vue.mainloop()