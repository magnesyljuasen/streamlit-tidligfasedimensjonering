import streamlit as st
import requests
import numpy as np
from streamlit_searchbox import st_searchbox
from streamlit_extras.no_default_selectbox import selectbox
from PIL import Image

class Input:
    def __init__(self):
        self.THERMAL_CONDUCTIVITY = 3.5
        self.GROUNDWATER_TABLE = 5
        self.COVERAGE = 90
        self.DEPTH_TO_BEDROCK = 10
        self.ELPRICE = 1.5
        

    def _address_search(self, searchterm: str):
        if not searchterm:
            return []
        antall = 5
        r = requests.get(f"https://ws.geonorge.no/adresser/v1/sok?sok={searchterm}&fuzzy=true&treffPerSide={antall}&sokemodus=OR", auth=('user', 'pass'))
        if r.status_code == 200 and len(r.json()["adresser"]) == antall:
            response = r.json()["adresser"]
        else:
            return []
        return [
            (
                f"{address['adressetekst']}, {address['poststed'].capitalize()}",
                [f"{address['adressetekst']}, {address['poststed']}",f"{address['representasjonspunkt']['lat']}", f"{address['representasjonspunkt']['lon']}", f"{address['postnummer']}"]
            )
            for address in response
        ]
    
    def address_input(self):
        selected_adr = st_searchbox(
            self._address_search,
            key="address_search",
            placeholder = "Adresse 🏠"
        )
        if selected_adr != None:
            self.adr = selected_adr[0]
            self.lat = float(selected_adr[1])
            self.long = float(selected_adr[2])
            self.postcode = selected_adr[3]
        else:
            #st_lottie("src/csv/house.json")
            #image = Image.open('src/data/figures/Ordinary day-amico.png')
            image = Image.open("src/data/figures/nylogo.png")
            st.image(image)
            st.stop()

    def area_input(self):
        c1, c2 = st.columns(2)
        with c1:
            area = st.slider('1. Velg oppvarmet boligareal [m²]', min_value=100, max_value=500)
            #area = st.text_input('1. Velg oppvarmet boligareal [m²]')
        with c2:
            st.info("Boligarealet som tilføres varme fra boligens varmesystem")
        minimum_area, maximum_area = 100, 500
        if area == 'None' or area == '':
            area = ''
        #elif area.isdecimal() and (float(area) >= minimum_area) and (float(area) <= maximum_area):
        #    area = float(area)
        #else:
        #    st.error(f'🚨 Oppvarmet boligareal må være mellom {minimum_area} og {maximum_area} m²')
        #    st.stop()
        self.area = area
    
    def heat_system_input(self):
        option_list = ['Gulvvarme', 'Radiator', 'Varmtvann']
        #st.write(f"Bergvarme krever at din bolig har et vannbårent varmesystem. Type varmesystem brukes til å estimere årsvarmefaktoren til varmepumpen.")
        c1, c2 = st.columns(2)
        with c1:
            selected = st.multiselect('1. Velg type varmesystem', options=option_list)
        with c2:
            st.info('Bergvarme krever at boligen har et vannbårent varmesystem')
            if len(selected) > 0:
                self.COP = selected
            else:
                st.stop()
            
        
    def demand_input(self, demand_array):
        demand_sum_old = int(round(np.sum(demand_array),-1))
        #st.write(f"Basert på geografi og boligareal estimerer vi at din bolig forbruker ca. **{demand_sum_old:,} kWh** til varme i året. Dette bør oppgis så nøyaktig som mulig, gjerne ut ifra målt varmeforbruk i din bolig. Varmeforbruket utgjør vanligvis ca. 50 - 60 % av det totale strømforbruket.".replace(',', ' '))
        c1, c2 = st.columns(2)
        with c1:
            demand_sum_new = st.number_input('1. Hva er boligens årlige varmebehov? [kWh/år]', value = demand_sum_old, step = 1000, min_value = 10000, max_value = 100000)
        with c2:
            st.info(f"Vi estimerer at din bolig har et årlig varmebehov på ca. {demand_sum_old:,} kWh".replace(",", " "))
        if demand_sum_new == 'None' or demand_sum_new == '':
            demand_sum_new = ''
            st.stop()
        #elif demand_sum_new.isdecimal() and int(demand_sum_new) and int(demand_sum_new):
        #    demand_sum_new = int(demand_sum_new)
        #else:
        #    st.error(f'🚨 Oppvarmet boligareal må være et tall')
        #    st.stop()
        #demand_sum_new = st.slider("Hva er boligens årlige varmebehov? [kWh/år]", min_value=0, value=demand_sum_old, max_value=50000, step=1000,  help="Her har vi har estimert varmebehov ut ifra størrelsen på ditt hus. Boligens varmebehov utgjør ca. 50-60% av det årlige strømforbruket.")
        demand_percentage = demand_sum_new / demand_sum_old
        self.demand_arr = (demand_array * demand_percentage).flatten()
