import arcade
import numpy as np
import Main
from typing import List, Tuple, Callable, Optional, Union, Literal
from dataclasses import dataclass
import os
import shutil
from fontTools.ttLib import TTFont


arcade.enable_timings()

@dataclass
class Config:
    """Configuration de la fenêtre"""
    WIDTH: int = 1280
    HEIGHT: int = 720
    SCROLL_FACTOR: float = 0.1
    ANCHORS: List[str] = None
    DIRECTORY: str = "Fonts"
    
    def __post_init__(self):
        if self.ANCHORS is None:
            self.ANCHORS = ['center', 'top_left', 'top_right', 'top_center', 'bottom_left', 'bottom_right', 'bottom_center', 'left_center', 'right_center']

config = Config()


if os.path.exists(config.DIRECTORY):
    shutil.rmtree(config.DIRECTORY)
os.mkdir(config.DIRECTORY)
print("Font directory created")

class FontManager:
    _fonts = {}
    _fonts_inv = {}

    @classmethod
    def load_font(cls, path, name: str):
        if name in cls._fonts:
            raise ValueError("This Font name already exist")
        
        if path in cls._fonts_inv:
            print(f"This path : {path} is already register under the name : {cls.get_name(path)}")
            arcade.load_font(f"{config.DIRECTORY}\{cls.get_name(path)}.ttf")
            return
        
        if not os.path.exists("Fonts"):
            raise ValueError("Directory error")
        
        font = TTFont(path)

        for record in font["name"].names:
            if record.nameID in (1, 2, 4, 6, 16, 17):
                record.string = name.encode(record.getEncoding())

        font.save(f"{config.DIRECTORY}\{name}.ttf")
        font.close()
        cls._fonts[name] = path
        cls._fonts_inv[path] = name
        arcade.load_font(f"{config.DIRECTORY}\{name}.ttf")

    @classmethod
    def get_name(cls, path):
        return cls._fonts_inv[path]
    
    @classmethod
    def get_path(cls, name):
        return cls._fonts[name]



class Object:
    object_index = 0
    def __init__(self, parent: Union['Object', arcade.Window], x, y, width, height, color, visible = True, rescale = True, keep_proportion = False, anchor = 'center', name=None):
        if anchor not in config.ANCHORS:
            raise ValueError(f"Anchor must be one of: {', '.join(config.ANCHORS)}")
        self.parent = parent
        self.obj = Object.object_index
        Object.object_index += 1

        if isinstance(parent, Object):
            self.x, self.y = x + parent.x, y + parent.y
        else:
            self.x, self.y = x, y

        self.parent.add_listener('resize', self.rescale_object)
        self.parent.add_listener('draw', self.draw)
        self.parent.add_listener('zoom', self.notify_zoom)
        self.parent.add_listener('apply_zoom', self.apply_zoom)
        self.parent.add_listener('drag', self.notify_drag)
        self.parent.add_listener('apply_drag', self.apply_drag)
        self.width, self.height = width, height
        self.color = color
        self.visible = visible
        self.rescale = rescale
        self.keep_proportion = keep_proportion
        self.anchor = anchor
        self.name = name

        # Dimensions originales pour le rescaling
        self._original_x, self._original_y = x, y
        self._original_width, self._original_height = width, height

        # Zoom
        self.zoom_scale_x = 1
        self.zoom_scale_y = 1
        self.min_width = 50
        self.min_height = 50
        self.max_width = None
        self.max_height = None

        # Drag
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.max_offset_x = self.width - 50
        self.max_offset_y = self.height - 50

        # Listeners
        self.resize_listeners = []
        self.draw_listeners = []
        self.zoom_listeners = []
        self.apply_zoom_listeners = []
        self.drag_listeners = []
        self.apply_drag_listeners = []

        self.border = False

    def set_zoom_limit(self, width_min=50, height_min=50, width_max=None, height_max=None):
        self.min_width = width_min
        self.min_height = height_min
        self.max_width = width_max
        self.max_height = height_max

    def add_listener(self, type: str, fn):
        if type == 'resize':
            self.resize_listeners.append(fn)
        elif type == 'draw':
            self.draw_listeners.append(fn)
        elif type == 'zoom':
            self.zoom_listeners.append(fn)
        elif type == 'apply_zoom':
            self.apply_zoom_listeners.append(fn)
        elif type == 'drag':
            self.drag_listeners.append(fn)
        elif type == 'apply_drag':
            self.apply_drag_listeners.append(fn)
        else:
            raise ValueError("Arg 'type' invalid")
    
    def notify_resize(self, scale_x, scale_y):
        for fn in self.resize_listeners:
            fn(scale_x, scale_y)
    
    def notify_draw(self):
        for fn in self.draw_listeners:
            fn()

    def notify_zoom(self, x, y, scroll_x, scroll_y):
        take = False
        for fn in self.zoom_listeners:
            take = fn(x, y, scroll_x, scroll_y)

        if take:
            return True

        if x >= (self.x + self.drag_offset_x) and x <= (self.x + self.drag_offset_x + self.width) and y >= (self.y + self.drag_offset_y) and y <= (self.y + self.drag_offset_y + self.height):
            try:
                self.zoom(x, y, scroll_x, scroll_y)
                return True
            except ValueError:
                return False
            except AttributeError:
                return False
        else: return False
    
    def notify_apply_zoom(self, zoom_factor_x, zoom_factor_y):
        for fn in self.apply_zoom_listeners:
            fn(zoom_factor_x, zoom_factor_y)

    def notify_drag(self, x, y, dx, dy):
        take = False
        for fn in self.drag_listeners:
            take = fn(x, y, dx, dy)

        if take:
            return True
        
        if x >= (self.x + self.drag_offset_x) and x <= (self.x + self.drag_offset_x + self.width) and y >= (self.y + self.drag_offset_y) and y <= (self.y + self.drag_offset_y + self.height):
            try:
                self.drag(x, y, dx, dy)
                return True
            except ValueError:
                return False
            except AttributeError:
                return False
        else: return False

    def notify_apply_drag(self, x, y, dx, dy):
        for fn in self.apply_drag_listeners:
            fn(x, y, dx, dy)

    def get_anchor_point(self) -> Tuple[float, float]:
        """Return the anchor point of the object"""
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
    
    def compute_x_y(self, scale_x, scale_y):
        if isinstance(self.parent, Object) and not self.parent.rescale:
            scale_x = 1
            scale_y = 1

        orig_center_x = self._original_x + self._original_width / 2
        orig_center_y = self._original_y + self._original_height / 2
        orig_right = self._original_x + self._original_width
        orig_top = self._original_y + self._original_height

        scaled_left = self._original_x * scale_x
        scaled_right = orig_right * scale_x
        scaled_bottom = self._original_y * scale_y
        scaled_top = orig_top * scale_y
        scaled_center_x = orig_center_x * scale_x
        scaled_center_y = orig_center_y * scale_y

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

        if isinstance(self.parent, Object):
            self.x = self.parent.x + anchor_map[self.anchor][0]
            self.y = self.parent.y + anchor_map[self.anchor][1]
        else:
            self.x, self.y = anchor_map[self.anchor]
    
    def rescale_object(self, scale_x, scale_y):
        if self.rescale:
            if self.keep_proportion:
                global_scale = min(scale_x, scale_y)
                self.width = self._original_width * global_scale
                self.height = self._original_height * global_scale
            else:
                self.width = self._original_width * scale_x
                self.height = self._original_height * scale_y
        self.compute_x_y(scale_x, scale_y)
        self.notify_resize(scale_x, scale_y)

    def can_apply_zoom(self, zoom_factor_x, zoom_factor_y) -> bool:
        if self.keep_proportion:
            global_zoom = min(zoom_factor_x, zoom_factor_y)
            new_width = self.width * global_zoom
            new_height = self.height * global_zoom
        else:
            new_width = self.width * zoom_factor_x
            new_height = self.height * zoom_factor_y
    
        if new_width < self.min_width or new_height < self.min_height:
            return False
    
        if self.max_width is not None and new_width > self.max_width:
            return False
    
        if self.max_height is not None and new_height > self.max_height:
            return False
    
        return True
    
    def can_apply_zoom_recursive(self, zoom_factor_x, zoom_factor_y) -> bool:
        if not self.can_apply_zoom(zoom_factor_x, zoom_factor_y):
            return False

        for fn in self.apply_zoom_listeners:
            if hasattr(fn.__self__, "can_apply_zoom_recursive"):
                if not fn.__self__.can_apply_zoom_recursive(zoom_factor_x, zoom_factor_y):
                    return False

        return True

    def apply_zoom(self, zoom_factor_x, zoom_factor_y):
        anchor_point = self.get_anchor_point()

        self.zoom_scale_x *= zoom_factor_x
        self.zoom_scale_y *= zoom_factor_y
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
        self.notify_apply_zoom(zoom_factor_x, zoom_factor_y)

    def can_apply_drag(self, x, y, dx, dy):
        if self.drag_offset_x < -self.max_offset_x or self.drag_offset_x > self.max_offset_x or self.drag_offset_y < -self.max_offset_y or self.drag_offset_y > self.max_offset_y:
            return False
        
        return True

    def can_apply_drag_recursive(self, x, y, dx, dy):
        if not self.can_apply_drag(x, y, dx, dy):
            return False
        
        for fn in self.apply_drag_listeners:
            if hasattr(fn.__self__, "can_apply_drag_recursive"):
                if not fn.__self__.can_apply_drag_recursive(x, y, dx, dy):
                    return False
        
        return True

    def apply_drag(self, x, y, dx, dy):
        self.drag_offset_x += dx
        self.drag_offset_y += dy
        self.notify_apply_drag(x, y, dx, dy)

    def update_max_drag(self):
        pass

    def draw(self):
        if isinstance(self, Container) and not self.overflow:
            pass

        self.notify_draw()
        if self.border:
            arcade.draw_lbwh_rectangle_outline(self.x, self.y, self.width, self.height, self.border_color)

    def enable_border(self, color):
        """A fonction to display a border to help debuging"""
        self.border = True
        self.border_color = color
        pass
    
class Container(Object):
    container_index = 0
    def __init__(self, parent: Union['Object', arcade.Window], x, y, width, height, color, visible = True, rescale = True, keep_proportion = False, anchor = 'center', scrollable_x = False, scrollable_y = False, zoomable = False, overflow = False, name=None):
        super().__init__(parent, x, y, width, height, color, visible, rescale, keep_proportion, anchor, name)
        self.cont = Container.container_index
        Container.container_index += 1

        self.scrollable_x = scrollable_x
        self.scrollable_y = scrollable_y
        self.zoomable = zoomable
        self.overflow = overflow

        self.zoom_x = 1
        self.zoom_y = 1

    def zoom(self, x, y, scroll_x, scroll_y):
        if not self.zoomable:
            raise ValueError('Not zoomable')
        
        max_scroll = scroll_x if abs(scroll_x) > abs(scroll_y) else scroll_y
        zoom_delta = 1.0 + (max_scroll * config.SCROLL_FACTOR)

        if not self.can_apply_zoom_recursive(zoom_delta, zoom_delta):
            return

        self.notify_apply_zoom(zoom_delta, zoom_delta)

    def drag(self, x, y, dx, dy):
        if not self.scrollable_x and not self.scrollable_y:
            raise ValueError('Not scrollable')
        
        if not self.scrollable_y:
            dy = 0

        if not self.scrollable_x:
            dx = 0

        #if not self.can_apply_drag_recursive(x, y, dx, dy):
        #    return

        #print(f"Dragging: dx={dx}, dy={dy}")
        self.notify_apply_drag(x, y, dx, dy)
        pass

    def draw(self):
        if self.visible:
            arcade.draw_lbwh_rectangle_filled(self.x + self.drag_offset_x, self.y + self.drag_offset_y, self.width, self.height, self.color)
        super().draw()

class FunctionObject(Object):
    def __init__(self, parent: Union['Object', arcade.Window], width=None, height=None, color=None, visible=True, rescale=True, keep_proportion=True, anchor='center'):
        x, y = 0, 0
        super().__init__(parent, x, y, parent.width, parent.height, color, visible, rescale, keep_proportion, anchor)
        self.function = None
        self.initial_width = parent.width
        self.initial_height = parent.height

    def remap_point_on_zoom(self, scale_x, scale_y):
        return [(x * scale_x, y * scale_y) for x, y in self.base_point]

    def apply_zoom(self, zoom_factor_x, zoom_factor_y):
        super().apply_zoom(zoom_factor_x, zoom_factor_y)
        scale_x = self.width / self.initial_width
        scale_y = self.height / self.initial_height

        self.radius = self.base_radius * min(scale_x, scale_y)
        self.radius = max(1, self.radius)

        self.point = self.remap_point_on_zoom(scale_x, scale_y)
        num = 0
        if self.function in (arcade.draw_circle_filled, arcade.draw_circle_outline):
            num = 3

    def set_function(self, function, *args, **kwargs):
        self.function = function
        if self.function in (arcade.draw_circle_filled, arcade.draw_circle_outline):
            self.point = [(args[0], args[1])]
            self.base_point = np.array(self.point, dtype=float)
            self.radius = args[2]
            self.base_radius = self.radius
            self.color = args[3]
        self.args = args
        self.kwargs = kwargs

    def draw(self):
        if not self.visible:
            return
        
        if self.function == None:
            raise ValueError("Plaese use set_function")
        
        if self.function in (arcade.draw_circle_filled, arcade.draw_circle_outline):
            self.function(self.point[0][0] + self.x + self.drag_offset_x, self.point[0][1] + self.y + self.drag_offset_y, self.radius, self.color,*self.args[4:], **self.kwargs)
        super().draw()

class LineObject(Object):
    def __init__(self, parent: Union['Object', arcade.Window], function, *args, width=None, height=None, color=None, visible=True, rescale=True, keep_proportion=True, anchor='center'):
        x, y = 0, 0
        super().__init__(parent, x, y, parent.width, parent.height, color, visible, rescale, keep_proportion, anchor)
        
        self.function = function
        self.points = self._interpolate(args[0])
        self.args = args
        self.color = args[1]
        self.thickness = args[2]

        self.base_points = np.array(self.points, dtype=float)
        self.base_thickness = self.thickness

        self.initial_width = parent.width
        self.initial_height = parent.height
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        x_max, y_max = max(xs), max(ys)
        self.initial_max_x  = x_max
        self.initial_max_y = y_max

    def _interpolate(self, points, nb_points = 2000):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        t_old = np.linspace(0, 1, len(xs))
        t_new = np.linspace(0, 1, nb_points)
        xs_i = np.interp(t_new, t_old, xs)
        ys_i = np.interp(t_new, t_old, ys)
        return [(float(x), float(y)) for x, y in zip(xs_i, ys_i)]

    def remap_point_on_zoom(self, scale_x, scale_y):
        return [(x * scale_x, y * scale_y) for x, y in self.base_points]

    def apply_zoom(self, scroll_x, scroll_y):
        super().apply_zoom(scroll_x, scroll_y)

        scale_x = self.width / self.initial_width
        scale_y = self.height / self.initial_height

        self.thickness = self.base_thickness * min(scale_x, scale_y)
        self.thickness = max(1, self.thickness)

        self.points = self.remap_point_on_zoom(scale_x, scale_y)

    def draw(self):
        if not self.visible:
            return
        
        if isinstance(self.parent, Container) and not self.parent.overflow:
            arcade.get_window().ctx.scissor = (int(self.parent.x), int(self.parent.y), int(self.parent.width), int(self.parent.height))
        
        n_points = [(x + self.x + self.drag_offset_x, y + self.y + self.drag_offset_y) for (x, y) in self.points]
        self.function(n_points, self.color, self.thickness, *self.args[3:])
        arcade.get_window().ctx.scissor = None
        super().draw()

class TextObject(Object):
    def __init__(self, parent: Union['Object', arcade.Window], width=None, height=None, color=None, visible=True, rescale=True, keep_proportion=True, anchor='center'):
        x, y = 0, 0
        super().__init__(parent, x, y, 0, 0, color, visible, rescale, keep_proportion, anchor)
        self.function = None
        self.text = None

    def update_dim(self):
        if self.text == None:
            raise ValueError("Text doesn't exist. Please use set_function before update_text")
        self.width = self.text.content_width + self.text.x
        self.height = self.text.content_height + self.text.y

    def update_pos(self):
        if self.text == None:
            raise ValueError("Text doesn't exist. Please use set_function before update_text")
        self.text.x = self.text.x + self.x
        self.text.y = self.text.y + self.y
        
    def update_text(self, new_text):
        if self.text == None:
            raise ValueError("Text doesn't exist. Please use set_function before update_text")
        self.text.text = new_text
        self.update_dim()

    def set_function(self, function, *args, **kwargs):
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.text = self.function(*self.args, **self.kwargs)
        self.update_dim()

    def draw(self):
        if not self.visible:
            return

        if self.function == None:
            raise ValueError("Plaese use set_function")
        self.text = self.function(*self.args, **self.kwargs)
        self.update_pos()
        self.text.draw()
        super().draw()

class OptimalTextObject(Object):
    def __init__(self, parent: Union['Object', arcade.Window], x=0, y=0, width=None, height=None, color=None, visible=True, rescale=True, keep_proportion=True, anchor='center'):
        super().__init__(parent, x, y, 0, 0, color, visible, rescale, keep_proportion, anchor)
        self.text_object: arcade.Text = arcade.Text("", x, y, color=color, anchor_x=anchor)
        self.dirty = True

    def update_text(self, new_text: str):
        if self.text_object.text != new_text:
            self.text_object.text = new_text
            self.dirty = True

    def update_font(self, font_name=None, font_size=None):
        if font_name is not None:
            self.text_object.font_name = font_name
        if font_size is not None:
            self.text_object.font_size = font_size
        self.dirty = True

    def draw(self):
        if not self.visible:
            return
        if self.dirty:
            self.width = self.text_object.content_width
            self.height = self.text_object.content_height
            self.dirty = False
        self.text_object.x = self.x
        self.text_object.y = self.y
        self.text_object.draw()
        super().draw()

class TextureObject(Object):
    def __init__(self, parent: Union['Object', arcade.Window], path, x, y, width: Union[int, Literal["auto"]] = None, height: Union[int, Literal["auto"]] = None, **kwargs):
        self.texture = arcade.load_texture(path)
        w = parent.width if width == "auto" else (width or self.texture.width)
        h = parent.height if height == "auto" else (height or self.texture.height)
        if width == 'auto' and height == "auto":
            m = min(parent.width, parent.height)
            w = m
            h = m
        super().__init__(parent, x, y, w, h, None, **kwargs)

        self.angle = 0

    def update_angle(self, angle):
        self.angle = angle

    def draw(self):
        if not self.visible:
            return

        arcade.draw_texture_rect(self.texture, arcade.LBWH(self.x, self.y, self.width, self.height), angle=0)
        super().draw()


class SpriteObject(Object):
    def __init__(self):
        pass


class RaceWindow(arcade.Window):
    def __init__(self, title, width, height):
        width = width or config.WIDTH
        height = height or config.HEIGHT
        self.title = title
        super().__init__(width, height, title, resizable=True)
        arcade.set_background_color(arcade.color.BLACK)

        self.set_minimum_size(100, 100)

        self.resize_listeners = []
        self.draw_listeners = []
        self.zoom_listeners = []
        self.drag_listeners = []

        self.dragging = False

    def add_listener(self, type: str, fn):
        if type == 'resize':
            self.resize_listeners.append(fn)
        elif type == 'draw':
            self.draw_listeners.append(fn)
        elif type == 'zoom':
            self.zoom_listeners.append(fn)
        elif type == 'apply_zoom':
            pass
        elif type == 'drag':
            self.drag_listeners.append(fn)
        elif type == 'apply_drag':
            pass
        else:
            raise ValueError("Arg 'type' invalid")
    
    def notify_resize(self, scale_x, scale_y):
        for fn in self.resize_listeners:
            fn(scale_x, scale_y)
    
    def notify_draw(self):
        for fn in self.draw_listeners:
            fn()

    def notify_zoom(self, x, y, scroll_x, scroll_y):
        for fn in self.zoom_listeners:
            fn(x, y, scroll_x, scroll_y)

    def notify_drag(self,x, y, dx, dy):
        for fn in self.drag_listeners:
            fn(x, y, dx, dy)

    def on_draw(self):
        self.clear()
        self.notify_draw()

    def on_resize(self, width: int, height: int):
        """Gère le redimensionnement de la fenêtre"""
        super().on_resize(width, height)
        scale_x = width / config.WIDTH
        scale_y = height / config.HEIGHT

        self.notify_resize(scale_x, scale_y)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.notify_zoom(x, y, scroll_x, scroll_y)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.dragging = True

    def on_mouse_motion(self, x, y, dx, dy):
        if self.dragging:
            self.notify_drag(x, y, dx, dy)

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.dragging = False

    def on_update(self, delta_time):
        fps = arcade.get_fps()
        self.set_caption(self.title + f" | {fps: .2f}")

    def clear_all(self):
        pass

    def run(self):
        """Lance la boucle principale"""
        arcade.run()


if __name__ == "__main__":
    """ arcade.load_font("F1-Font-Family/Formula1-Bold_web.ttf") """
    """ arcade.load_font("Formula1-Wide_web_0.ttf") """
    """ FontManager.load_font("Formula1-Wide_web_0.ttf", "Formula1Wide") """

    win = RaceWindow('Race', config.WIDTH, config.HEIGHT)
    obj = Container(win, 10, 10, 600, 600, arcade.color.YELLOW)
    obj.enable_border(arcade.color.GREEN)
    obj2 = Container(obj, 120, 120, 360, 360, arcade.color.RED, zoomable=True, scrollable_x=True)
    obj2.enable_border(arcade.color.GREEN)
    obj3 = Container(obj2, 60, 60, 240, 240, arcade.color.BLUE, rescale=True, zoomable=True, scrollable_x=True, scrollable_y=True)
    obj3.enable_border(arcade.color.GREEN)
    points = [(20, 20), (20, 220), (220, 220), (220, 20), (20, 20)]
    obj4 = LineObject(obj3, arcade.draw_line_strip, points, arcade.color.GRAY, 4, color=arcade.color.WHITE, rescale=False)
    obj4.enable_border(arcade.color.GREEN)
    obj5 = TextObject(obj, rescale=False, color=arcade.color.WHITE, anchor='bottom_left')
    obj5.set_function(arcade.Text, 'Test Text VER 123', 0, 0, arcade.color.BLACK, font_size = 18, font_name="Formula1Wide")
    obj5.enable_border(arcade.color.GREEN)
    obj6 = TextureObject(obj, "resources\F1Logo.png", 20, 100, 100, 100)
    obj6.enable_border(arcade.color.GREEN)
    print(obj.get_anchor_point())
    print(obj2.get_anchor_point())
    print(obj3.get_anchor_point())
    print(obj4.get_anchor_point())
    print(obj5.get_anchor_point())

    obj.rescale_object(2, 2)
    print(obj.width, obj.height, obj.x, obj.y)
    print(obj2.width, obj2.height, obj2.x, obj2.y)
    print(obj3.width, obj3.height, obj3.x, obj3.y)
    print(obj4.width, obj4.height, obj4.x, obj4.y)
    print(obj5.width, obj5.height, obj5.x, obj5.y)
    print(obj6.width, obj6.height, obj6.x, obj6.y)
    print(obj.get_anchor_point())
    print(obj2.get_anchor_point())
    print(obj3.get_anchor_point())
    print(obj4.get_anchor_point())
    print(obj5.get_anchor_point())
    win.run()