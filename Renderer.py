import arcade 
import numpy as np

WIDTH = 1280
HEIGHT = 720


class F1ReplayWindow(arcade.Window):
    def __init__(self, title, track, circuit_info):
        super().__init__(WIDTH, HEIGHT, title, resizable=True)
        arcade.set_background_color(arcade.color.BLACK)

        self.track = track
        self.circuit_info = circuit_info
        self.circuit_rotation = self.circuit_info.rotation

        # Stocker les points monde (non transformés)
        self.world_inner_points = []
        self.world_outer_points = []
        
        # Points écran (transformés)
        self.screen_inner_points = []
        self.screen_outer_points = []
        
        # Bounds du monde
        self.world_bounds = None
        
        self.calculate_track_geometry()
        self.update_screen_coordinates()

    def calculate_track_geometry(self, track_width=200):
        """Calcule la géométrie de la piste dans les coordonnées monde."""
        plot_x = self.track["X"].to_numpy()
        plot_y = self.track["Y"].to_numpy()

        # Calculer les gradients
        dx = np.gradient(plot_x)
        dy = np.gradient(plot_y)

        # Normaliser
        norm = np.hypot(dx, dy)
        norm[norm == 0] = 1.0
        dx /= norm
        dy /= norm

        # Calculer les normales perpendiculaires
        nx = -dy
        ny = dx

        # Calculer les bords de la piste
        half_width = track_width / 2
        x_inner = plot_x + nx * half_width
        x_outer = plot_x - nx * half_width
        y_inner = plot_y + ny * half_width
        y_outer = plot_y - ny * half_width

        # Stocker les points monde
        self.world_inner_points = list(zip(x_inner, y_inner))
        self.world_outer_points = list(zip(x_outer, y_outer))

        # Appliquer la rotation aux points monde si nécessaire
        if self.circuit_rotation != 0:
            self.world_inner_points = self._rotate_points(self.world_inner_points, plot_x, plot_y)
            self.world_outer_points = self._rotate_points(self.world_outer_points, plot_x, plot_y)

        # Calculer les bounds
        all_x = list(x_inner) + list(x_outer)
        all_y = list(y_inner) + list(y_outer)
        
        if self.circuit_rotation != 0:
            all_x = [p[0] for p in self.world_inner_points + self.world_outer_points]
            all_y = [p[1] for p in self.world_inner_points + self.world_outer_points]
        
        self.world_bounds = {
            'x_min': np.min(all_x),
            'x_max': np.max(all_x),
            'y_min': np.min(all_y),
            'y_max': np.max(all_y),
            'center_x': (np.min(all_x) + np.max(all_x)) / 2,
            'center_y': (np.min(all_y) + np.max(all_y)) / 2
        }

    def _rotate_points(self, points, plot_x, plot_y):
        """Applique la rotation aux points autour du centre."""
        center_x = np.mean(plot_x)
        center_y = np.mean(plot_y)
        
        cos_r = np.cos(self.circuit_rotation)
        sin_r = np.sin(self.circuit_rotation)
        
        rotated = []
        for x, y in points:
            tx = x - center_x
            ty = y - center_y
            rx = tx * cos_r - ty * sin_r
            ry = tx * sin_r + ty * cos_r
            rotated.append((rx + center_x, ry + center_y))
        
        return rotated

    def update_screen_coordinates(self):
        """Met à jour les coordonnées écran en fonction de la taille de la fenêtre."""
        if not self.world_bounds:
            return

        width = self.width
        height = self.height
        margin = 0.05  # 5% de marge

        # Dimensions du monde
        world_w = self.world_bounds['x_max'] - self.world_bounds['x_min']
        world_h = self.world_bounds['y_max'] - self.world_bounds['y_min']
        
        # Éviter division par zéro
        world_w = max(world_w, 1.0)
        world_h = max(world_h, 1.0)

        # Espace utilisable
        usable_w = width * (1 - 2 * margin)
        usable_h = height * (1 - 2 * margin)

        # Calculer l'échelle (maintenir le ratio)
        scale_x = usable_w / world_w
        scale_y = usable_h / world_h
        scale = min(scale_x, scale_y)

        # Calculer les offsets pour centrer
        offset_x = (width - world_w * scale) / 2 - self.world_bounds['x_min'] * scale
        offset_y = (height - world_h * scale) / 2 - self.world_bounds['y_min'] * scale

        # Transformer tous les points
        self.screen_inner_points = [
            (x * scale + offset_x, y * scale + offset_y) 
            for x, y in self.world_inner_points
        ]
        self.screen_outer_points = [
            (x * scale + offset_x, y * scale + offset_y) 
            for x, y in self.world_outer_points
        ]

        # Stocker pour usage ultérieur
        self.track_scale = scale
        self.offset_x = offset_x
        self.offset_y = offset_y

    def world_to_screen(self, x, y):
        """Convertit des coordonnées monde en coordonnées écran."""
        return (x * self.track_scale + self.offset_x, 
                y * self.track_scale + self.offset_y)

    def screen_to_world(self, sx, sy):
        """Convertit des coordonnées écran en coordonnées monde."""
        return ((sx - self.offset_x) / self.track_scale,
                (sy - self.offset_y) / self.track_scale)

    def on_resize(self, width, height):
        """Appelé automatiquement par Arcade lors du redimensionnement."""
        super().on_resize(width, height)
        self.update_screen_coordinates()

    def on_draw(self):
        """Dessine la piste."""
        self.clear()

        # Dessiner les bords de la piste
        if len(self.screen_inner_points) > 1:
            arcade.draw_line_strip(
                self.screen_inner_points, 
                arcade.color.GRAY, 
                4
            )
        
        if len(self.screen_outer_points) > 1:
            arcade.draw_line_strip(
                self.screen_outer_points, 
                arcade.color.GRAY, 
                4
            )

    def run(self):
        """Lance la boucle principale."""
        arcade.run()