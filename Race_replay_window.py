import NewRenderer as rend
import arcade
import Main
import numpy as np
from UI_manager import DriverInfos, RaceInfos, StartingLight
from f1_data_manager import RaceDataManager, ScheduleDataManager
from typing import Union, Literal

import random

FPS = 60
DT = 1 / FPS

class RaceReplay(rend.RaceWindow):
    def __init__(self, year, session_number, session_type: Union[Literal['R'], Literal['S'], Literal['Q']] = 'R'):
        self.load_fonts()
        self.WIDTH = 1280
        self.HEIGHT = 720
        super().__init__("Race", self.WIDTH, self.HEIGHT)
        self.set_update_rate(DT)
        self.race_data = RaceDataManager(year, session_number, session_type)

        self.reset()
        self.main_draw()
        self.light = StartingLight(self)
        
        self.run()

    def reset(self):
        self.paused = True
        self.start_start_procedure = False
        self.global_time = 0.0
        self.race_time = 0.0
        self.play_speed = 1.0
        
        self.light_counter = 0
        self.random_time = random.uniform(1, 1.5)
        
    def load_fonts(self):
        rend.FontManager.load_font("Formula1-Bold_web_0.ttf", "Formula1Bold")

    def start_procedure(self):
        lights = self.light.lower_lights
        if self.global_time > self.light_counter and self.light_counter < 5:
            lights[self.light_counter].color = arcade.color.RED
            self.light_counter += 1

        if self.global_time > 4 + self.random_time:
            for l in lights:
                l.color = (50, 50, 50)
            self.paused = False



    def main_draw(self):
        track_container = rend.Container(self, 0, 0, 1280, 720, arcade.color.RED, anchor='bottom_center', keep_proportion=True, visible=False, scrollable_x=True, scrollable_y=True, zoomable=True)
        track_container.set_zoom_limit(200, 200)
        self.draw_track(track_container, 'fast')
        self.draw_track(track_container, 'box')
        position = rend.Container(self, 0, 100, 200, 600, arcade.color.YELLOW, rescale=False, anchor='top_left', keep_proportion=True)
        header = rend.Container(position, 0, 500, 200, 100, (42, 42, 42), rescale=False, keep_proportion=True, anchor="top_left", name="header")
        f1_logo_container = rend.Container(header, 25, 25, 150, 75, arcade.color.RED, rescale=False, keep_proportion=True, anchor="top_center", visible=False)
        f1_logo = rend.TextureObject(f1_logo_container, "resources\F1Logo.png", 0, -40, 150, 150, rescale=False)
        lap = rend.Container(header, 0, 0, 200, 25, arcade.color.BLUE, rescale=False, keep_proportion=True, anchor="bottom_left")
        classement = rend.Container(position, 0, 0, 200, 500, arcade.color.PINK, rescale=False, keep_proportion=True, anchor="bottom_center")
        #race_infos = RaceInfos(self)

        self.debug = rend.TextObject(self)
        self.debug.set_function(arcade.Text, f"{self.race_time}", 0, 0, arcade.color.WHITE)

        self.pilote = []
        for j in range(20):
            self.pilote.append(DriverInfos(classement))



    def world_to_screen(self, points):
        _cos_rot = np.cos(self.race_data.rotation)
        _sin_rot = np.sin(self.race_data.rotation)
        rot_mat = np.array([[ _cos_rot, -_sin_rot],
                            [ _sin_rot,  _cos_rot]])
        x_min, y_min = points.min(axis=0)
        x_max, y_max = points.max(axis=0)

        scale_x = self.WIDTH / (x_max - x_min)
        scale_y = self.HEIGHT / (y_max - y_min)
        scale = min(scale_x, scale_y)

        offset_x = (self.WIDTH - (x_max - x_min) * scale) / 2 - x_min * scale
        offset_y = (self.HEIGHT - (y_max - y_min) * scale) / 2 - y_min * scale
        offset = np.array([offset_x, offset_y])

        p = points
        if self.race_data.rotation != 0:
            p = p @ rot_mat.T
        return p * scale  + offset

    def draw_track(self, container, lap_type):
        points = self.race_data.get_track_layout(lap_type).to_numpy(dtype=float)

        points = self.world_to_screen(points)
        points = [tuple(p) for p in points]
        obj = rend.LineObject(container, arcade.draw_line_strip, points, arcade.color.GRAY, 4, color=arcade.color.WHITE, rescale=False, keep_proportion=True)
        obj.set_zoom_limit(200, 200)

        if lap_type == 'fast':
            self.track = obj
        elif lap_type == 'box':
            self.stand = obj



    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ENTER:
            self.global_time = 0.0
            self.start_start_procedure = True
        elif symbol == arcade.key.R:
            self.clear()
            self.reset()

    def on_update(self, delta_time):
        self.debug.set_function(arcade.Text, f"{self.race_time}", 0, 0, arcade.color.WHITE)
        if self.start_start_procedure:
            self.start_procedure()

        if self.paused:
            self.global_time += delta_time * self.play_speed
            return
        self.race_time += delta_time * self.play_speed
        
        

if __name__ == "__main__":
    race = RaceReplay(2021, 7, 'Q')