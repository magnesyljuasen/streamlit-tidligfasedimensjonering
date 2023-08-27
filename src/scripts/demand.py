import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
from src.scripts.utils import hour_to_month

class Demand:
    def __init__(self):
        self.space_heating_arr = np.zeros(8760)
        self.dhw_arr = np.zeros(8760)
        self.energy_arr = np.zeros(8760)
        self.space_heating_sum = int
        self.dhw_sum = int
        self.energy_sum = int
    
    def update(self):
        self.space_heating_sum = int(np.sum(self.space_heating_arr))
        self.dhw_sum = int(np.sum(self.dhw_arr))
        self.energy_sum = int(np.sum(self.energy_arr))

    def from_file(self, area, weather_station_id):
        factor = 1
        dhw = 'src/data/database/' + 'SN180' + '_dhw.csv'
        space_heating = 'src/data/temperature/_' + weather_station_id + '_romoppvarming.csv'
        self.dhw_arr = (pd.read_csv(dhw, sep=',', on_bad_lines='skip').to_numpy() * area) * factor
        self.space_heating_arr = (pd.read_csv(space_heating, sep=',', on_bad_lines='skip').to_numpy() * area) * factor
        self.energy_arr = self.dhw_arr + self.space_heating_arr

    def plot(self):
        dhw_arr = hour_to_month (self.dhw_arr)
        romoppvarming_arr = hour_to_month (self.space_heating_arr)
        months = ['jan', 'feb', 'mar', 'apr', 'mai', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'des']
        data = pd.DataFrame({'Måneder' : months, 'Romoppvarmingsbehov' : romoppvarming_arr, 'Varmtvannsbehov' : dhw_arr, })
        c = alt.Chart(data).transform_fold(
            ['Romoppvarmingsbehov', 'Varmtvannsbehov'],
            as_=['Forklaring', 'Oppvarmingsbehov (kWh)']).mark_bar().encode(
            x=alt.X('Måneder:N', sort=months, title=None),
            y='Oppvarmingsbehov (kWh):Q',
            color=alt.Color('Forklaring:N', scale=alt.Scale(domain=['Romoppvarmingsbehov', 'Varmtvannsbehov'], 
            range=['#4a625c', '#8e9d99']), legend=alt.Legend(orient='top', direction='vertical', title=None)))
        st.altair_chart(c, use_container_width=True)

    def adjust(self):
        with st.form('1'):
            dhw_sum = self.dhw_sum
            dhw_sum_new = st.number_input('Varmtvann [kWh]', min_value = int(round(dhw_sum - dhw_sum/2, -1)), 
            max_value = int(round(dhw_sum + dhw_sum/2, -1)), value = round(dhw_sum, -1), step = int(500), help="""
            Erfaring viser at varmtvannsbehovet avhenger 
            av hvor mange som bor i en bolig, og bør justeres etter dette. 
            Bor dere mange i din bolig, bør du øke dette tallet. """)

            space_heating_sum = self.space_heating_sum
            space_heating_sum_new = st.number_input('Romoppvarming [kWh]', min_value = int(round(space_heating_sum - space_heating_sum/2, -1)), 
            max_value = int(round(space_heating_sum + space_heating_sum/2, -1)), value = round(space_heating_sum, -1), step = int(500), help= """
            Behovet for romoppvarming er beregnet ut fra oppgitt oppvarmet areal, 
            byggeår og temperaturdata fra nærmeste værstasjon for de 30 siste årene. """)
            dhew_percentage = dhw_sum_new / dhw_sum
            romoppvarming_prosent = space_heating_sum_new / space_heating_sum

            self.dhw_arr = (self.dhw_arr * dhew_percentage).flatten()
            self.space_heating_arr = (self.space_heating_arr * romoppvarming_prosent).flatten()
            self.energy_arr = (self.dhw_arr + self.space_heating_arr).flatten()
            submitted = st.form_submit_button("Oppdater")
    #---