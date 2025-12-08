import importlib
import Import
importlib.reload(Import)
from Import import load_race
import numpy as np
import matplotlib.pyplot as plt

def main(year, session_num):
    session = load_race(year=year, session_num=session_num)

    # Example lap
    lap = session.laps.pick_fastest()
    circuit_info = session.get_circuit_info()
    track = DrawTrack(lap, circuit_info)
    return [track, circuit_info]

def DrawTrack(lap, circuit_info):
    pos = lap.get_pos_data()
    track = pos.loc[:, ('X', 'Y')]
    track = track._append(track.iloc[0], ignore_index=True)
    track.columns = track.columns.get_level_values(-1)
    track_angle = circuit_info.rotation / 180 * np.pi
    rotated_track = rotate(track, angle=track_angle)
    rotated_track.columns = ["X", "Y"]
    return rotated_track
    

def rotate(xy, *, angle):
    rot_mat = np.array([[np.cos(angle), np.sin(angle)],
                        [-np.sin(angle), np.cos(angle)]])
    return np.matmul(xy, rot_mat)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Session selection")
    parser.add_argument('--year', type=int, default=2021, help='Session year')
    parser.add_argument('--session', type=int, default=7, help='Session number')

    args = parser.parse_args()
    main(args.year, args.session)