import streamlit as st
import numpy as np
import pandas as pd
import json
from shapely.geometry import Point, shape




class Electricity:
    def __init__(self):
        self.region = str
        self.elspot_arr = np.array(0)
        self.elspot_average = float
        self.year = str
    
    def update(self):
        self.elspot_average = np.average(self.elspot_arr) 

    def import_file(self):
        with open('src/csv/regioner.geojson') as f:
            js = json.load(f)
        f.close()
        return js

    def find_region(self, lat, long):
        punkt = Point(long, lat)
        js = self.import_file()
        region = 'NO 1'
        for feature in js['features']:
            polygon = shape(feature['geometry'])
            if polygon.contains(punkt):
                region = feature['properties']['ElSpotOmr']
        region_mapping = {
            'NO 1': 'Sørøst-Norge (NO1)',
            'NO 2': 'Sørvest-Norge (NO2)',
            'NO 3': 'Midt-Norge (NO3)',
            'NO 4': 'Nord-Norge (NO4)',
            'NO 5': 'Vest-Norge (NO5)'
        }
        self.region = region_mapping[region]

    def import_elspot_data(self):
        if self.year == '2018':
            return pd.read_csv('src/csv/el_spot_hourly_2018.csv', sep=';', on_bad_lines='skip')
        if self.year == '2019':
            return pd.read_csv('src/csv/el_spot_hourly_2019.csv', sep=';', on_bad_lines='skip')
        if self.year == '2020':
            return pd.read_csv('src/csv/el_spot_hourly_2020.csv', sep=';', on_bad_lines='skip')
        if self.year == '2021':
            return pd.read_csv('src/csv/el_spot_hourly_2021.csv', sep=';', on_bad_lines='skip')
        
    def elspot_price(self):
        elspot_df = self.import_elspot_data()
        i = 3
        if self.region == 'Sørøst-Norge (NO1)':
            i = 3
        if self.region == 'Sørvest-Norge (NO2)':
            i = 4
        if self.region == 'Midt-Norge (NO3)':
            i = 5
        if self.region == 'Nord-Norge (NO4)':
            i = 6
        if self.region == 'Vest-Norge (NO5)':
            i = 7
 
        elspot_adjusted = np.resize(elspot_df.iloc[:, i].to_numpy()/1000, 8760)
        self.elspot_hourly = elspot_adjusted
        self.elspot_average = np.nanmean(elspot_adjusted)

    def input(self):
        with st.form("3"):
            self.year = st.selectbox("Velg årlig fordeling av strømprisen (basert på historiske strømpriser)",
            ('2021', '2020', '2019', '2018'),
            help=""" Vi har hentet inn historiske strømpriser time for time for de siste 4 årene. 
            Du kan også skrive inn den strømprisen du selv ønsker å bruke i beregningen. """)
            if self.year == '2021':
                total_elprice = 1.37
            if self.year == '2020':
                total_elprice = 0.79
            if self.year == '2019':
                total_elprice = 1.15
            if self.year == '2018':
                total_elprice = 1.16
            self.elspot_price()
            self.elprice_average = st.number_input("Gjennomsnittlig strømpris (inkl. nettleie og avgifter) [NOK/kWh]", 
            value = total_elprice, min_value = float(self.elspot_average), step = 0.1)
            submitted = st.form_submit_button("Oppdater")
