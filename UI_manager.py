import NewRenderer as rend
import arcade
import Main
import numpy as np



class StartingLight:
    def __init__(self, parent):
        self.WIDTH = 300
        self.HEIGHT = 150
        self.container = rend.Container(parent, parent.width / 2 - self.WIDTH / 2, parent.height - self.HEIGHT, self.WIDTH, self.HEIGHT, arcade.color.RED, rescale=False, anchor="top_center", visible=False)
        self.high_part = rend.Container(self.container, 0, self.HEIGHT / 2, self.WIDTH, self.HEIGHT / 2, (15, 15, 15), rescale=False)

        red_light_width = 40
        offset = (270 - 5*red_light_width) / 6
        x = 15 + offset
        self.red_lights = []
        self.upper_lights = []
        self.lower_lights = []
        for i in range(5):
            block = rend.Container(self.container, x, 0, red_light_width, self.HEIGHT / 2, (15, 15, 15), rescale=False)
            self.red_lights.append(block)
            x += red_light_width + offset
            upper_light = rend.FunctionObject(block)
            upper_light.set_function(arcade.draw_circle_filled,red_light_width/2, 55, 15, (50, 50, 50))
            self.upper_lights.append(upper_light)

            lower_light = rend.FunctionObject(block)
            lower_light.set_function(arcade.draw_circle_filled,red_light_width/2, 20, 15, (50, 50, 50))
            self.lower_lights.append(lower_light)

    def toggle_visibility(self, state = True):
        self.high_part.visible = state
        for b in self.red_lights:
            b.visible = state
        for u in self.upper_lights:
            u.visible = state
        for l in self.lower_lights:
            l.visible = state

class LeaderBoard:
    def __init__(self, container, max_laps):
        self.leaderbord_container = rend.Container(container, 0, 100, 200, 600, arcade.color.YELLOW, rescale=False, anchor='top_left', keep_proportion=True)
        self.header = rend.Container(self.leaderbord_container, 0, 500, 200, 100, (15, 15, 15), rescale=False, keep_proportion=True, anchor="top_left", name="header")
        self.f1_logo_container = rend.Container(self.header, 25, 25, 150, 75, arcade.color.RED, rescale=False, keep_proportion=True, anchor="top_center", visible=False)
        self.f1_logo = rend.TextureObject(self.f1_logo_container, "resources\F1Logo.png", 0, -40, 150, 150, rescale=False)
        self.lap_container = rend.Container(self.header, 0, 0, 200, 25, arcade.color.BLUE, rescale=False, keep_proportion=True, anchor="bottom_left")
        self.lap_text = rend.OptimalTextObject(self.lap_container, x=100, y=5, color=arcade.color.WHITE, anchor='center')
        self.lap_text.update_text(f"1/{max_laps}")
        self.lap_text.update_font(font_name="Formula1Bold")
        self.ranking = rend.Container(self.leaderbord_container, 0, 0, 200, 500, arcade.color.PINK, rescale=False, keep_proportion=True, anchor="bottom_center")

        self.pilot_lines = []
        for j in range(20):
            self.pilot_lines.append(DriverInfos(self.ranking))

class RaceInfos:
    def __init__(self, parent):
        self.container = rend.Container(parent, parent.width / 2 - 100, parent.height - 100, 200, 100, arcade.color.RED)

class DriverInfos:
    i = 0
    def __init__(self, parent):
        self.container = rend.Container(parent, 0, DriverInfos.i*25, 200, 25, arcade.color.RED, rescale=False, keep_proportion=True, anchor="center")
        self.container.enable_border(arcade.color.BLACK)
        self.index_container = rend.Container(self.container, 0, 0, 25, 25, arcade.color.BLACK, rescale=False, keep_proportion=True, anchor="center")
        #self.index = rend.TextObject(self.index_container, rescale=False, keep_proportion=True, anchor="center")
        #self.index.set_function(arcade.Text, str(20 - DriverInfos.i), 25, 30, arcade.color.WHITE, font_name="Formula1Bold")
        self.index = rend.OptimalTextObject(self.index_container, x=12, y=6, color=arcade.color.WHITE, rescale=False, keep_proportion=True, anchor="center")
        self.index.update_text(str(20 - DriverInfos.i))
        self.index.update_font(font_name="Formula1Bold")

        DriverInfos.i += 1

    @classmethod
    def reset(cls):
        cls.i = 0

class DriverCard:
    def __init__(self):
        pass

class TimeLine:
    def __init__(self):
        pass