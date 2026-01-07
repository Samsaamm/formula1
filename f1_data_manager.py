import fastf1
import numpy as np
from typing import Union, Literal
from multiprocessing import cpu_count, Pool
from joblib import Parallel, delayed



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
        self._load_telemetry()

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
            lap = self.session.laps.pick_box_laps(which='in').iloc[0]
        else:
            raise ValueError("This lap_type doesn't exist")
        circuit_info = self.session.get_circuit_info()

        track = lap.get_pos_data().loc[:, ('X', 'Y')]
        track = track._append(track.iloc[:5], ignore_index=True)
        rotated_track = track
        rotated_track.columns = ["X", "Y"]
        return rotated_track
    
    def get_weather(self):
        return self.session.weather_data
    
    def get_max_lap(self):
        return self.session.total_laps
    
    def load_driver_telemetry(self, driver_code, laps_df):
        print(f"Getting telemetry from driver {driver_code}")
        x, y = [], []
        for i, lap in laps_df.iterrows():
            telemetry = lap.get_telemetry()
            if telemetry.empty:
                continue
            x.append(telemetry['X'].to_numpy())
            y.append(telemetry['Y'].to_numpy())
            return {'code': driver_code, 'data': {'x': x, 'y': y}, 'lap': i}
        

    def _load_telemetry(self):
        self.drivers_data = {}

        print(f"Getting data from {len(self.drivers)}...")

        driver_arg = [(code, self.session.laps.pick_drivers(driver)) for driver, code in self.drivers_codes.items()]
        self.results = Parallel(n_jobs=-1)(delayed(self.load_driver_telemetry)(code, laps) for code, laps in driver_arg)

if __name__ == "__main__":
    rdm = RaceDataManager(2021, 7, 'R')
    """ print(rdm.session)
    print(rdm.drivers_codes)
    print(rdm.get_weather()) """
    print(rdm.get_max_lap())
    