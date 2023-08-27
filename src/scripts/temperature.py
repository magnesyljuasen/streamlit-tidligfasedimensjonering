import numpy as np
import pandas as pd
import mpu 
import streamlit as st

class Temperature:
    def __init__(self):
        self.temperature_arr = np.zeros(8760)
        self.lat = float
        self.long = float
        self.id = str

    def from_file(self, id):
        temperature_array = 'src/data/temperature/_' + id + '_temperatur.csv'
        self.temperature_arr = pd.read_csv(temperature_array, sep=',', on_bad_lines='skip').to_numpy()

    def process(self, id):
        self.from_file(id)
        average = float("{:.2f}".format(np.average(self.temperature_arr)))
        text = ""
        if average < 3:
            text = """ Ettersom gjennomsnittstemperaturen er lav kan det være en 
            driftsstrategi å fryse grunnvannet i energibrønnen (merk at dette ikke 
            må gjøres hvis det er sensitive løsmasser / kvikkleire i området). """
        self.average_temperature = average
        self.average_temperature_text = text

    #@st.cache_data
    def import_csv (self):
        station_list = pd.read_csv('src/data/temperature/Stasjoner.csv', sep=',',on_bad_lines='skip')
        return station_list

    def closest_station (self, lat, long):
        distance_min = 1000000
        df = self.import_csv()
        for i in range (0, len (df)):
            distance = mpu.haversine_distance((df.iat [i,1], df.iat [i,2]), (lat, long))
            if distance != 0 and distance < distance_min:
                distance_min = distance
                self.id = df.iat [i,0]
                self.lat = df.iat [i,1]
                self.long = df.iat [i,2]
                self.distance_min = distance_min
