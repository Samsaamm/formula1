import arcade
import numpy as np

WIDTH = 1280
HEIGHT = 720

ANCHORS = ['center', 'top_left', 'top_right', 'top_center', 'bottom_left', 'bottom_right', 'bottom_center', 'left_center', 'right_center']
SCROLL_FACTOR = 1  


class Object:
    def __init__(self, x, y, width, height, color, rescale=True, keep_proportion=False, anchor='center'):
        if anchor not in ANCHORS:
            raise ValueError("Anchors must be one oh these values :" \
            "'center', 'top_left', 'top_right', 'top_center', 'bottom_left', 'bottom_right', 'bottom_center', 'left_center', 'right_center'")
        
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.rescale = rescale
        self.keep_proportion = keep_proportion
        self.anchor = anchor

        # Original dim
        self.original_width = width
        self.original_height = height
        self.original_x = x
        self.original_y = y

    def compute_anchor(self, anchor, scale_x, scale_y):
        if anchor == 'center':
            center_x = (self.original_x + self.original_width / 2) * scale_x
            center_y = (self.original_y + self.original_height / 2) * scale_y
            new_x = center_x - self.width / 2
            new_y = center_y - self.height / 2
        elif anchor == 'top_left':
            new_x = self.original_x * scale_x
            new_y = (self.original_y + self.original_height) * scale_y - self.height
        elif anchor == 'top_right':
            new_x = (self.original_x + self.original_width) * scale_x - self.width
            new_y = (self.original_y + self.original_height) * scale_y - self.height
        elif anchor == 'top_center':
            center_x = (self.original_x + self.original_width / 2) * scale_x
            new_x = center_x - self.width / 2
            new_y = (self.original_y + self.original_height) * scale_y - self.height
        elif anchor == 'bottom_left':
            new_x = self.original_x * scale_x
            new_y = self.original_y * scale_y
        elif anchor == 'bottom_right':
            new_x = (self.original_x + self.original_width) * scale_x - self.width
            new_y = self.original_y * scale_y
        elif anchor == 'bottom_center':
            center_x = (self.original_x + self.original_width / 2) * scale_x
            new_x = center_x - self.width / 2
            new_y = self.original_y * scale_y
        elif anchor == 'left_center':
            center_y = (self.original_y + self.original_height / 2) * scale_y
            new_x = self.original_x * scale_x
            new_y = center_y - self.height / 2
        elif anchor == 'right_center':
            center_y = (self.original_y + self.original_height / 2) * scale_y
            new_x = (self.original_x + self.original_width) * scale_x - self.width
            new_y = center_y - self.height / 2

        return new_x, new_y

    def rescal_obj(self, x_scale, y_scale):
        global_scale = min(x_scale, y_scale)

        if self.rescale:
            self.width = self.original_width * (global_scale if self.keep_proportion else x_scale)
            self.height = self.original_height * (global_scale if self.keep_proportion else y_scale)

        new_x, new_y = self.compute_anchor(self.anchor, x_scale, y_scale)
        self.x = new_x
        self.y = new_y





class FunctionObject(Object):
    def __init__(self, function, *args, color, rescale=True, keep_proportion=False, anchor='center'):
        xs = [p[0] for p in args[0]]
        ys = [p[1] for p in args[0]]
        super().__init__(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys), color, rescale, keep_proportion, anchor)

        self.parent = None

        self.function = function
        self.args = args

    def draw(self):
        if isinstance(self.parent, Container):
            if len(self.args[0]) >= 1:
                points_arr = np.array(self.args[0])
                xs = points_arr[:, 0]
                ys = points_arr[:, 1]

                
                points = np.column_stack((xs, ys)).tolist()
                points = self.remap_point(points)
                points = self.parent.to_screen_array(points)
                self.function(points, *self.args[1:])

    def remap_point(self, points):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        x_min, y_min = min(xs), min(ys)
        x_max, y_max = max(xs), max(ys)

        scale_x = ((self.x + self.width) - self.x) / (x_max - x_min)
        scale_y = ((self.y + self.height) - self.y) / (y_max - y_min)

        new_points = [((x - x_min) * scale_x + self.x, (y - y_min) * scale_y + self.y) for x, y in points]
        return new_points







class Container(Object):
    def __init__(self, x, y, width, height, color, rescale=True, keep_proportion=False, anchor='center', scrollable_x=False, scrollable_y=False, zoomable=False, overflow=False):
        super().__init__(x, y, width, height, color, rescale, keep_proportion, anchor)

        self.scrollable_x = scrollable_x
        self.scrollable_y = scrollable_y
        self.zoomable = zoomable
        self.overflow = overflow

        # Objects
        self.objects = []

    def draw(self):
        arcade.draw_lbwh_rectangle_filled(self.x, self.y, self.width, self.height, self.color)
        for obj in self.objects:
            obj.draw()

    def rescal_obj(self, x_scale, y_scale):
        super().rescal_obj(x_scale, y_scale)

        for obj in self.objects:
            obj.rescal_obj(x_scale, y_scale)

    def add(self, obj):
        self.objects.append(obj)
        obj.parent = self

    def to_screen_array(self, points):
        new_points = []

        for x, y in points:
            x_screen = self.x + x
            y_screen = self.y + y
            new_points.append((x_screen, y_screen))

        return new_points






class RaceWindow(arcade.Window):
    def __init__(self, title, track, circuit_info):
        super().__init__(WIDTH, HEIGHT, title, resizable=True)
        arcade.set_background_color(arcade.color.BLACK)

        # Track container
        self.tc_margin = [0.05, 0.15, 0.05, 0.05, '%'] # Top, Bottom, Left, Right, '%' or 'px'

        self.containers = [
            Container(*self.margin_to_input(self.tc_margin), arcade.color.YELLOW, keep_proportion=False, anchor='top_left', zoomable=True)
        ]

        test_point = [(100, 100), (1000, 100), (1000, 200), (100, 200), (100, 100)]
        obj = FunctionObject(arcade.draw_line_strip, test_point, arcade.color.GRAY, 4, color=arcade.color.WHITE, keep_proportion=True)
        self.containers[0].add(obj)


    def margin_to_input(self, margin):
        if margin[4] == '%':
            input = [
                margin[2]*WIDTH,
                margin[1]*HEIGHT,
                WIDTH - (margin[2]*WIDTH + margin[3]*WIDTH),
                HEIGHT - (margin[0]*HEIGHT + margin[1]*HEIGHT)
            ]
        elif margin[4] == 'px':
            input = [
                margin[2],
                margin[1],
                WIDTH - (margin[2] + margin[3]),
                HEIGHT - (margin[0] + margin[1])
            ]
        else:
            raise ValueError("self.tc_margin[4] must be '%' or 'px'")
        return input
    
    def on_draw(self):
        self.clear()

        for c in self.containers:
            c.draw()

    def on_resize(self, width, height):
        super().on_resize(width, height)

        x_scale = width / WIDTH
        y_scale = height / HEIGHT

        for c in self.containers:
            c.rescal_obj(x_scale, y_scale)
    
    def run(self):
        """Launch the main loop"""
        arcade.run()
    









if __name__ == "__main__":
    win = RaceWindow('Race', 1, 1)
    win.run()