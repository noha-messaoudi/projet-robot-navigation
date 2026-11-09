"""Modèle : le robot."""
 
 
class Robot:
    def __init__(self, position):
        self.position = position
        self.chemin = []  # chemin restant à parcourir (sans la case actuelle)
 
    def definir_chemin(self, chemin):
        """chemin = liste de cases commençant par la position actuelle."""
        self.chemin = list(chemin[1:]) if chemin else []
 
    def a_fini(self):
        return not self.chemin
 
    def avancer(self):
        """Avance d'une case sur le chemin. Renvoie la nouvelle position."""
        if self.chemin:
            self.position = self.chemin.pop(0)
        return self.position
 