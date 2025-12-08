import arcade
import numpy as np

WIDTH = 1280
HEIGHT = 720

ANCHORS = ['center', 'top_left', 'top_right', 'top_center', 'bottom_left', 'bottom_right', 'bottom_center', 'left_center', 'right_center']
SCROLL_FACTOR = 1        


class Container:
    def __init__(self, x, y, width, height, color, rescale=True, keep_proportion=False, anchor='center', scrollable_x=False, scrollable_y=False, zoomable=False):
        if anchor not in ANCHORS:
            raise ValueError("Anchors must be one oh these values :" \
            "'center', 'top_left', 'top_right', 'top_center', 'bottom_left', 'bottom_right', 'bottom_center', 'left_center', 'right_center'")
        
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color # bg color
        self.rescale = rescale
        self.keep_proportion = keep_proportion
        self.anchor = anchor
        self.scrollable_x = scrollable_x
        self.scrollable_y = scrollable_y
        self.zoomable = zoomable

        # Original dim
        self.original_width = width
        self.original_height = height
        self.original_x = x
        self.original_y = y
    
    def draw(self):
        arcade.draw_lbwh_rectangle_filled(self.x, self.y, self.width, self.height, self.color)

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

    def rescale_container(self, x_scale, y_scale):
        global_scale = None
        if self.keep_proportion:
            global_scale = min(x_scale, y_scale)

        if self.rescale:
            self.width = self.original_width * (global_scale if global_scale != None else x_scale)
            self.height = self.original_height * (global_scale if global_scale != None else y_scale)

        new_x, new_y = self.compute_anchor(self.anchor, x_scale, y_scale)
        self.x = new_x
        self.y = new_y

    def to_screen(self, x_local, y_local):
        x_screen = self.x + (x_local / self.original_width) * self.width
        y_screen = self.y + (y_local / self.original_height) * self.height
        return x_screen, y_screen
    
    def to_local(self, x_screen, y_screen):
        x_local = ((x_screen - self.x) / self.width) * self.original_width
        y_local = ((y_screen - self.y) / self.height) * self.original_height
        return x_local, y_local
    
    def to_screen_array(self, x_array: np.ndarray, y_array: np.ndarray):
        x_screen = self.x + (x_array / self.original_width) * self.width
        y_screen = self.y + (y_array / self.original_height) * self.height
        return x_screen, y_screen
    
    def to_local_array(self, x_array: np.ndarray, y_array: np.ndarray):
        x_local = ((x_array - self.x) / self.width) * self.original_width
        y_local = ((y_array - self.y) / self.height) * self.original_height
        return x_local, y_local
    
    def zoom(self, x, y, scroll_x, scroll_y):
        print(f"Scroll détecté : scroll_x={scroll_x}, scroll_y={scroll_y}")
        
    







class RaceWindow(arcade.Window):
    def __init__(self, title, track, circuit_info):
        super().__init__(WIDTH, HEIGHT, title, resizable=True)
        arcade.set_background_color(arcade.color.BLACK)

        # Track container
        self.tc_margin = [0.05, 0.15, 0.05, 0.05, '%'] # Top, Bottom, Left, Right, '%' or 'px'
        if self.tc_margin[4] == '%':
            self.tc_input = [
                self.tc_margin[2]*WIDTH,
                self.tc_margin[1]*HEIGHT,
                WIDTH - (self.tc_margin[2]*WIDTH + self.tc_margin[3]*WIDTH),
                HEIGHT - (self.tc_margin[0]*HEIGHT + self.tc_margin[1]*HEIGHT)
            ]
        elif self.tc_margin[4] == 'px':
            self.tc_input = [
                self.tc_margin[2],
                self.tc_margin[1],
                WIDTH - (self.tc_margin[2] + self.tc_margin[3]),
                HEIGHT - (self.tc_margin[0] + self.tc_margin[1])
            ]
        else:
            raise ValueError("self.tc_margin[4] must be '%' or 'px'")

        self.containers = [
            Container(self.tc_input[0], self.tc_input[1], self.tc_input[2], self.tc_input[3], arcade.color.YELLOW, keep_proportion=False, anchor='bottom_center', zoomable=True)
        ]

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        for c in self.containers:
            if c.zoomable and x >= c.x and x <= (c.x + c.width) and y >= c.y and y <= (c.y + c.height):
                c.zoom(x, y, scroll_x, scroll_y)


    def in_container(self, container_index, func, *args, **kwargs):
        cont = self.containers[container_index]
        if len(args[0]) >= 1:
            points_arr = np.array(args[0])
            xs = points_arr[:, 0]
            ys = points_arr[:, 1]

            xs, ys = cont.to_screen_array(xs, ys)

            points = np.column_stack((xs, ys)).tolist()

        return func(points, *args[1:])

    def on_draw(self):
        self.clear()

        for c in self.containers:
            c.draw()

        test_point = [(100, 100), (1000, 100), (1000, 200), (100, 200), (100, 100)]
        self.in_container(0, arcade.draw_line_strip, test_point, arcade.color.GRAY, 4)

    def on_resize(self, width, height):
        super().on_resize(width, height)

        x_scale = width / WIDTH
        y_scale = height / HEIGHT

        for c in self.containers:
            c.rescale_container(x_scale, y_scale)

    def run(self):
        """Lance la boucle principale."""
        arcade.run()


if __name__ == "__main__":
    win = RaceWindow('Race', 1, 1)
    win.run()