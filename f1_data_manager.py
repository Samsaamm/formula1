import fastf1
import numpy as np
from typing import Union, Literal
from multiprocessing import Pool, cpu_count

def rotate(xy, *, angle):
    rot_mat = np.array([[np.cos(angle), np.sin(angle)],
                        [-np.sin(angle), np.cos(angle)]])
    return np.matmul(xy, rot_mat)


class ScheduleDataManager:
    def __init__(self):
        pass



class RaceDataManager:
    def __init__(self, year, session_number, session_type: Union[Literal['R'], Literal['S'], Literal['Q']] = 'R'):
        self.year = year
        self.session_number = session_number
        self.session_type = session_type
        self.load_session()
        self.load_circuit_rotation()
        self.load_drivers()
        self._load_telemetry

    def load_session(self):
        self.session = fastf1.get_session(self.year, self.session_number, self.session_type)
        self.session.load(telemetry=True, weather=True)
        self.event_name = self.session.event['EventName']
        self.date = self.session.date

    def load_circuit_rotation(self):
        self.circuit = self.session.get_circuit_info()
        self.rotation = self.circuit.rotation

    def load_drivers(self):
        self.drivers = self.session.drivers
        self.drivers_codes = {num: self.session.get_driver(num)['Abbreviation'] for num in self.drivers}

    def get_track_layout(self, lap_type='fast'):
        if lap_type == 'fast':
            lap = self.session.laps.pick_fastest()
        elif lap_type == 'box':
            lap = self.session.laps.pick_box_laps(which='both').iloc[0]
        else:
            raise ValueError("This lap_type doesn't exist")
        circuit_info = self.session.get_circuit_info()

        track = lap.get_pos_data().loc[:, ('X', 'Y')]
        track = track._append(track.iloc[:5], ignore_index=True)
        rotated_track = track
        #rotated_track = rotate(track, angle=circuit_info.rotation / 180 * np.pi)
        rotated_track.columns = ["X", "Y"]
        return rotated_track
    
    def get_weather(self):
        return self.session.weather_data
    
    def _load_driver_telemetry(self, args):
        driver, driver_code = args
        print(f"Getting telemetry from driver {driver_code}")

        laps = self.session.laps.pick_drivers(driver)
        if laps.empty:
            return
        
        x, y = [], []
        telemetry = {
            'code': driver_code,
            'data': {
                'x': x,
                'y': y,
            }
        }

        for _, lap in laps.iterlaps():
            lap_telemetry = lap.get_telemetry()
            lap_number = lap.LapNumber
            if lap_telemetry.empty:
                continue

            telemetry['data']['x'].append(lap_telemetry["X"].to_numpy())
            telemetry['data']['y'].append(lap_telemetry["Y"].to_numpy())

        return telemetry
        

    def _load_telemetry(self):
        self.drivers_data = {}

        print(f"Getting data from {len(self.drivers)}...")
        driver_arg = [(d, self.drivers_codes[d]) for d in self.drivers]
        num_process = min(cpu_count(), len(self.drivers))
        with Pool(processes=num_process) as pool:
            self.results = pool.map(self._load_driver_telemetry, driver_arg)

        print(len(self.results[0]['data']['x']))


if __name__ == "__main__":
    rdm = RaceDataManager(2021, 7, 'Q')
    """ print(rdm.session)
    print(rdm.drivers_codes)
    print(rdm.get_weather()) """
    