import os
import fastf1
import fastf1.plotting
import numpy as np


def load_race(year, session_num):
    session = fastf1.get_session(year, session_num, 'Q')
    session.load()
    return session

if __name__ == "__main__":
    load_race()
