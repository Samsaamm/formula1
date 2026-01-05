import arcade
import numpy as np
import Main
from typing import List, Tuple, Callable, Optional, Union
from dataclasses import dataclass


# Configuration globale
@dataclass
class Config:
    """Configuration de la fenêtre"""
    WIDTH: int = 1280
    HEIGHT: int = 720
    SCROLL_FACTOR: float = 0.1
    ANCHORS: List[str] = None
    
    def __post_init__(self):
        if self.ANCHORS is None:
            self.ANCHORS = [
                'center', 'top_left', 'top_right', 'top_center',
                'bottom_left', 'bottom_right', 'bottom_center',
                'left_center', 'right_center'
            ]


config = Config()


class Object:
    """Objet de base avec gestion du redimensionnement et des ancres"""
    def __init__(
        self,
        x: float, y: float, width: float, height: float,
        color: Union[Tuple[int, int, int], Tuple[int, int, int, int]],
        visible: bool = True,
        rescale: bool = True,
        keep_proportion: bool = False,
        anchor: str = 'center'
    ):
        if anchor not in config.ANCHORS:
            raise ValueError(f"Anchor must be one of: {', '.join(config.ANCHORS)}")
        
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.visible = visible
        self.rescale = rescale
        self.keep_proportion = keep_proportion
        self.anchor = anchor

        self.zoom_scale_x = 1.0
        self.zoom_scale_y = 1.0
        
        # Dimensions originales pour le rescaling
        self._original_x = x
        self._original_y = y
        self._original_width = width
        self._original_height = height
        
        # Référence au parent (Container)
        self.parent: Optional['Container'] = None

    def get_anchor_point(self) -> Tuple[float, float]:
        """Retourne le point d'ancre actuel de l'objet"""
        anchor_map = {
            'center': (self.x + self.width / 2, self.y + self.height / 2),
            'top_left': (self.x, self.y + self.height),
            'top_right': (self.x + self.width, self.y + self.height),
            'top_center': (self.x + self.width / 2, self.y + self.height),
            'bottom_left': (self.x, self.y),
            'bottom_right': (self.x + self.width, self.y),
            'bottom_center': (self.x + self.width / 2, self.y),
            'left_center': (self.x, self.y + self.height / 2),
            'right_center': (self.x + self.width, self.y + self.height / 2)
        }
        return anchor_map[self.anchor]

    def compute_anchor(self, anchor: str, scale_x: float, scale_y: float) -> Tuple[float, float]:
        """Calcule la nouvelle position basée sur l'ancre et les échelles"""
        # Calcul des positions originales
        orig_center_x = self._original_x + self._original_width / 2
        orig_center_y = self._original_y + self._original_height / 2
        orig_right = self._original_x + self._original_width
        orig_top = self._original_y + self._original_height
        
        # Nouvelles positions scalées
        scaled_left = self._original_x * scale_x
        scaled_right = orig_right * scale_x
        scaled_bottom = self._original_y * scale_y
        scaled_top = orig_top * scale_y
        scaled_center_x = orig_center_x * scale_x
        scaled_center_y = orig_center_y * scale_y
        
        # Mapping des ancres vers les calculs
        anchor_map = {
            'center': (scaled_center_x - self.width / 2, scaled_center_y - self.height / 2),
            'top_left': (scaled_left, scaled_top - self.height),
            'top_right': (scaled_right - self.width, scaled_top - self.height),
            'top_center': (scaled_center_x - self.width / 2, scaled_top - self.height),
            'bottom_left': (scaled_left, scaled_bottom),
            'bottom_right': (scaled_right - self.width, scaled_bottom),
            'bottom_center': (scaled_center_x - self.width / 2, scaled_bottom),
            'left_center': (scaled_left, scaled_center_y - self.height / 2),
            'right_center': (scaled_right - self.width, scaled_center_y - self.height / 2)
        }
        
        return anchor_map[anchor]

    def rescale_object(self, scale_x: float, scale_y: float):
        """Redimensionne l'objet selon les échelles données (resize de fenêtre)"""
        if self.rescale:
            if self.keep_proportion:
                global_scale = min(scale_x, scale_y)
                self.width = self._original_width * global_scale * self.zoom_scale_x
                self.height = self._original_height * global_scale * self.zoom_scale_y
            else:
                self.width = self._original_width * scale_x * self.zoom_scale_x
                self.height = self._original_height * scale_y * self.zoom_scale_y
        
        self.x, self.y = self.compute_anchor(self.anchor, scale_x, scale_y)

    def apply_zoom(self, zoom_factor_x: float, zoom_factor_y: float):
        anchor_point = self.get_anchor_point()
        
        self.zoom_scale_x *= zoom_factor_x
        self.zoom_scale_y *= zoom_factor_y
        if self.rescale:
            if self.keep_proportion:
                global_zoom = min(zoom_factor_x, zoom_factor_y)
                self.width *= global_zoom
                self.height *= global_zoom
            else:
                self.width *= zoom_factor_x
                self.height *= zoom_factor_y

        new_anchor_point = self.get_anchor_point()
        self.x += (anchor_point[0] - new_anchor_point[0])
        self.y += (anchor_point[1] - new_anchor_point[1])



class FunctionObject(Object):
    """Objet qui dessine via une fonction personnalisée"""
    
    def __init__(
        self,
        function: Callable,
        *args,
        color: Union[Tuple[int, int, int], Tuple[int, int, int, int]],
        visible: bool = True,
        rescale: bool = True,
        keep_proportion: bool = False,
        anchor: str = 'center'
    ):
        
        # Calcul des dimensions à partir des points
        xs = [p[0] for p in args[0]]
        ys = [p[1] for p in args[0]]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        super().__init__(
            min_x, min_y, max_x - min_x, max_y - min_y,
            color, visible, rescale, keep_proportion, anchor
        )
        
        self.function = function
        self.points = args[0]
        self.args = args

    def remap_points(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Remappe les points dans l'espace de l'objet redimensionné"""
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        
        x_min, y_min = min(xs), min(ys)
        x_max, y_max = max(xs), max(ys)
        
        # Éviter division par zéro
        x_range = x_max - x_min if x_max != x_min else 1
        y_range = y_max - y_min if y_max != y_min else 1
        
        scale_x = self.width / x_range
        scale_y = self.height / y_range
        
        return [((x - x_min) * scale_x + self.x, (y - y_min) * scale_y + self.y) for x, y in points]
    
    def _interpolate(self, points, nb_points=2000):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        t_old = np.linspace(0, 1, len(xs))
        t_new = np.linspace(0, 1, nb_points)
        xs_i = np.interp(t_new, t_old, xs)
        ys_i = np.interp(t_new, t_old, ys)
        return [(float(x), float(y)) for x, y in zip(xs_i, ys_i)] 

    def draw(self):
        """Dessine l'objet via la fonction personnalisée"""
        if not self.visible:
            return
        
        remapped_points = self.remap_points(self.points)
        
        # Si l'objet a un parent Container, convertir en coordonnées écran
        if isinstance(self.parent, Container):
            remapped_points = self.parent.to_screen_coordinates(remapped_points)
            remapped_points = self._interpolate(remapped_points)
            remapped_points = self.parent.overflow_controller(remapped_points)
        
        for j in range(len(remapped_points)):
            self.function(remapped_points[j], *self.args[1:])


class Container(Object):
    """Conteneur pouvant contenir d'autres objets"""
    
    def __init__(
        self,
        x: float, y: float, width: float, height: float,
        color: Union[Tuple[int, int, int], Tuple[int, int, int, int]],
        visible: bool = True,
        rescale: bool = True,
        keep_proportion: bool = False,
        anchor: str = 'center',
        scrollable_x: bool = False,
        scrollable_y: bool = False,
        zoomable: bool = False,
        overflow: bool = False
    ):
        super().__init__(x, y, width, height, color, visible, rescale, keep_proportion, anchor)
        
        self.scrollable_x = scrollable_x
        self.scrollable_y = scrollable_y
        self.zoomable = zoomable
        self.overflow = overflow
        
        self._objects: List[Object] = []
        
        # Pour le scrolling et zoom
        self.offset_x = 0.0
        self.offset_y = 0.0

    @property
    def objects(self) -> List[Object]:
        """Retourne la liste des objets"""
        return self._objects

    def add(self, obj: Object):
        """Ajoute un objet au conteneur"""
        self._objects.append(obj)
        obj.parent = self

    def remove(self, obj: Object):
        """Retire un objet du conteneur"""
        if obj in self._objects:
            self._objects.remove(obj)
            obj.parent = None

    def to_screen_coordinates(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Convertit les points relatifs en coordonnées écran"""
        return [
            (self.x + x + self.offset_x, self.y + y + self.offset_y)
            for x, y in points
        ]

    def rescale_object(self, scale_x: float, scale_y: float):
        """Redimensionne le conteneur et ses enfants"""
        super().rescale_object(scale_x, scale_y)

        for obj in self._objects:
            obj.rescale_object(scale_x, scale_y)

    def overflow_controller(self, points):
        points = np.array(points)
        if self.overflow == False:
            mask = (points[:, 0] >= self.x) & (points[:, 0] <= (self.x + self.width)) & \
                   (points[:, 1] >= self.y) & (points[:, 1] <= (self.y + self.height))

            out, seg = [], []
            for i in range(len(mask)):
                if mask[i]:
                    seg.append(points[i])
                else:
                    if seg:
                        out.append(seg)
                        seg = []
            if seg:
                out.append(seg)
            return out
        else:
            return points
        
    def zoom(self, x, y, scroll_x, scroll_y):
        max_scroll = scroll_x if abs(scroll_x) > abs(scroll_y) else scroll_y
        zoom_delta = 1.0 + (max_scroll * config.SCROLL_FACTOR)

        zoom_delta = max(0.5, min(zoom_delta, 1.5))
        
        for obj in self._objects:
            obj.apply_zoom(zoom_delta, zoom_delta)
            

    def draw(self):
        """Dessine le conteneur et ses objets"""
        if not self.visible:
            return
        
        # Dessine le fond
        arcade.draw_lbwh_rectangle_filled(self.x, self.y, self.width, self.height, self.color)
        
        # Dessine les objets enfants
        for obj in self._objects:
            obj.draw()


class RaceWindow(arcade.Window):
    """Fenêtre principale avec gestion des conteneurs"""
    
    def __init__(
        self,
        title: str = "Race Window",
        track: Optional[any] = None,
        circuit_info: Optional[any] = None,
        width: int = None,
        height: int = None
    ):
        width = width or config.WIDTH
        height = height or config.HEIGHT
        
        super().__init__(width, height, title, resizable=True)
        arcade.set_background_color(arcade.color.BLACK)
        
        self.track = track
        self.circuit_info = circuit_info
        self.circuit_rotation = self.circuit_info.rotation
        """ self.world_inner_points = []
        self.world_outer_points = []
        self.screen_inner_points = []
        self.screen_outer_points = []
        self.world_bounds = None
        self.calculate_track_geometry()
        self.update_screen_coordinates() """
        
        # Margin: [top, bottom, left, right, unit]
        
        self.containers: List[Container] = []

    def _margin_to_dimensions(self, margin: List) -> Tuple[float, float, float, float]:
        """Convertit les marges en dimensions (x, y, width, height)"""
        unit = margin[4]
        top, bottom, left, right = margin[:4]
        
        if unit == '%':
            x = left * config.WIDTH
            y = bottom * config.HEIGHT
            width = config.WIDTH - (left + right) * config.WIDTH
            height = config.HEIGHT - (top + bottom) * config.HEIGHT
        elif unit == 'px':
            x = left
            y = bottom
            width = config.WIDTH - (left + right)
            height = config.HEIGHT - (top + bottom)
        else:
            raise ValueError("Margin unit must be '%' or 'px'")
        
        return x, y, width, height

    def add_container(self, margin: List, color, **kwargs):
        """Ajoute un conteneur à la fenêtre"""
        cont = Container(
            *self._margin_to_dimensions(margin),
            color,
            **kwargs
        )
        self.containers.append(cont)

    def on_draw(self):
        """Dessine tous les conteneurs"""
        self.clear()
        
        for container in self.containers:
            container.draw()

    def on_resize(self, width: int, height: int):
        """Gère le redimensionnement de la fenêtre"""
        super().on_resize(width, height)
        
        scale_x = width / config.WIDTH
        scale_y = height / config.HEIGHT
        
        for container in self.containers:
            container.rescale_object(scale_x, scale_y)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        for c in self.containers:
            if c.zoomable and x >= c.x and x <= (c.x + c.width) and y >= c.y and y <= (c.y + c.height):
                c.zoom(x, y, scroll_x, scroll_y)

    def run(self):
        """Lance la boucle principale"""
        arcade.run()

""" 

    def calculate_track_geometry(self, track_width = 200):
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

 """


# Exemple d'utilisation
if __name__ == "__main__":
    ret = Main.main(2021, 7)
    track, circuit_info = ret[0], ret[1]

    window = RaceWindow('Race Visualization', track=track, circuit_info=circuit_info)

    window.add_container([0.1, 0.1, 0.05, 0.05, '%'], arcade.color.YELLOW, keep_proportion=False, anchor='top_left', zoomable=True)
    window.add_container([20, 150, 0, 1100, 'px'], arcade.color.RED, keep_proportion=True, anchor='top_left')

    test_points = [(100, 100), (1000, 100), (1000, 200), (100, 200), (100, 100)]
    test_obj = FunctionObject(
        arcade.draw_line_strip,
        test_points,
        arcade.color.GRAY,
        4,
        color=arcade.color.WHITE,
        keep_proportion=True,
        anchor='center'
    )
    window.containers[0].add(test_obj)

    
    window.run()