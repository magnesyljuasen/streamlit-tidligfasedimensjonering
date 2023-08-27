import streamlit as st
from st_keyup import st_keyup
import requests
import time 
import pandas as pd
import numpy as np

class Adjust:
    def __init__(self, elprice, elregion, spaceheating, dhw, depth_to_bedrock, groundwater_table, thermal_conductivity, dhw_arr, space_heating_arr, cop, energycoverage):
        self.dhw_arr = dhw_arr
        self.space_heating_arr = space_heating_arr
        self.demand_array = self.dhw_arr + self.space_heating_arr
        self.demand_old = int(np.sum(self.demand_array))
        self.elprice = elprice
        self.elregion = elregion
        self.space_heating_old = spaceheating
        self.dhw_old = dhw
        self.dhw_ratio_demand = self.dhw_old / self.demand_old
        self.energycoverage = energycoverage
        self.depth_to_bedrock = depth_to_bedrock
        self.groundwater_table = groundwater_table
        self.thermal_conductivity = thermal_conductivity
        self.cop = cop
        self.adjust_input()
        self.adjust()

    def adjust_input(self):
        with st.form('input'):
            with st.expander("Energi og effekt"):
                self._cop_exists()
                self.spaceheating_f()
                self.dhw_f()
                self.demand_f()
                #self.energycoverage_f()
                self.heatsystem_f()
            #with st.expander("Energibrønn og dimensjonering"):
            #    self.depth_to_bedrock_f()
            #    self.groundwater_table_f()
                #self.thermal_conductivity_f()
            #    st.markdown("---")
            with st.expander("Lønnsomhet og miljø"):    
                self.elprice_f()
                self.energymix_f()
                self.interest_f()
                st.markdown("---")
                st.write(f"*- Gjennomsnittlig spotpris: {round(float(np.mean(self.elprice)),2)} kr/kWh*")
                st.write(f"*- Utslippsfaktor: {(self.energymix)*1000} g CO₂e/kWh*")
                
            #self.payment_time_f()
            
            #self.borehole_resistance_f()              
            if st.form_submit_button('Oppdater'):
                self.start = True
            else:
                self.start = False
                
    def _cop_exists(self):
        self.COP_GULVVARME, self.COP_RADIATOR, self.COP_VARMTVANN = 0, 0, 0
        for index, value in enumerate(self.cop):
            if value == "Gulvvarme":
                self.COP_GULVVARME = 4
            elif value == "Radiator":
                self.COP_RADIATOR = 3.5
            elif value == "Varmtvann":
                self.COP_VARMTVANN = 2.5
    
    def heatsystem_f(self):
        VARMTVANN = self.COP_VARMTVANN * self.dhw_sum
        if self.COP_GULVVARME > 0 and self.COP_RADIATOR > 0:
            ROMOPPVARMING = ((self.COP_GULVVARME + self.COP_RADIATOR)/2) * self.space_heating_sum
        elif self.COP_GULVVARME > 0 and self.COP_RADIATOR == 0:
            ROMOPPVARMING = (self.COP_GULVVARME) * self.space_heating_sum
        elif self.COP_GULVVARME == 0 and self.COP_RADIATOR > 0:
            ROMOPPVARMING = (self.COP_RADIATOR) * self.space_heating_sum
        
        if self.COP_VARMTVANN == 0:                
            KOMBINERT_COP = (ROMOPPVARMING) / (self.space_heating_sum)
        elif self.COP_VARMTVANN > 0 and self.COP_GULVVARME == 0 and self.COP_RADIATOR == 0:
            KOMBINERT_COP = (VARMTVANN) / (self.dhw_sum)
        else:
            KOMBINERT_COP = (ROMOPPVARMING + VARMTVANN) / (self.space_heating_sum + self.dhw_sum)
            
        self.cop = float(st.slider("Årsvarmefaktor (SCOP)", value = float(KOMBINERT_COP), step = 0.1, min_value = 2.0, max_value= 5.0))

    def elprice_f(self):
        selected_el_option = st.selectbox("Strømpris", options=["Historisk strømpris: 2022", "Historisk strømpris: 2021", "Historisk strømpris: 2020", "Flat strømpris: 0.8 kr/kWh", "Flat strømpris: 1.5 kr/kWh", "Flat strømpris: 2.0 kr/kWh"], index = 1)
        selected_year = selected_el_option.split()[2]
        if float(selected_year) > 10:
            spotprice_arr = self._import_spotprice(selected_year)
            self.elprice = spotprice_arr
        else:
            self.elprice = float(selected_year)
    
    def _import_spotprice(self, selected_year):
        region_mapping = {
            'Sørøst-Norge (NO1)': 'NO1',
            'Sørvest-Norge (NO2)': 'NO2',
            'Midt-Norge (NO3)': 'NO3',
            'Nord-Norge (NO4)': 'NO4',
            'Vest-Norge (NO5)': 'NO5'
        }
        df = pd.read_excel("src/csv/spotpriser.xlsx", sheet_name=selected_year)
        spotprice_arr = df[region_mapping[self.elregion]].to_numpy()/1.25
        return spotprice_arr
            

    def energymix_f(self):
        option_list = ['Norsk', 'Norsk-europeisk', 'Europeisk']
        selected = st.selectbox('Strømmiks', options=option_list)
        x = {option_list[0] : 16.2/1000, option_list[1] : 116.9/1000, option_list[2] : 123/1000}
        self.energymix = x[selected]
        self.energyoption = selected

    def energycoverage_f(self):
        self.energycoverage = st.number_input('Energidekningsgrad [%]', min_value=80, value=self.energycoverage, max_value=100)
        
    def demand_f(self):
        self.demand_sum = st.number_input('Varmebehov [kWh/år]', min_value=0, value=(round(self.demand_old,-1)), max_value=100000, step=1000)
    
    def spaceheating_f(self):
        self.space_heating_sum = int(round(self.space_heating_old, 1))
        #self.space_heating_sum = st.number_input('Romoppvarmingsbehov [kWh/år]', min_value=0, value=(round(self.space_heating_old,-1)), max_value=100000, step=1000)

    def dhw_f(self):
        self.dhw_sum = int(round(self.dhw_old, 1))
        #self.dhw_sum = st.number_input('Varmtvannsbehov [kWh/år]', min_value=0, value=int(round(self.dhw_old,-1)), max_value=100000, step=1000)

    def depth_to_bedrock_f(self):
        self.depth_to_bedrock = st.number_input('Dybde til fjell [m]', min_value=0, value=self.depth_to_bedrock, max_value=100) 
        #help=''' Dybde til fjell påvirker kostnaden for å 
        #bore energibrønn, og kan variere mye fra sted til sted. 
        #Brønnborer bør sjekke dette opp mot NGU sine databaser for 
        #grunnvannsbrønner og grunnundersøkelser.''')

    def groundwater_table_f(self):
        self.groundwater_table = st.number_input('Dybde til grunnvannspeil [m]', min_value=0, value=self.groundwater_table, max_value=100)

    def thermal_conductivity_f(self):
        self.thermal_conductivity = st.number_input('Berggrunnens effektive varmeledningsevne [W/(m*K)]', min_value=2.0, value=self.thermal_conductivity, max_value=10.0, step=0.1)

    def investment_f(self):
        investment = self.investment
        self.investment = st.number_input("Juster investeringskostnad [kr]", 
        min_value = 10000, value = int(round(investment,-1)),max_value = 1000000, step = 5000)

    def payment_time_f(self):
        self.payment_time = st.number_input("Nedbetalingstid (lån) [år]", value = 20, min_value = 1, max_value = 20, step = 1)
        
    def interest_f(self):
        self.interest = st.number_input("Effektiv rente (lånefinansiert) [%]", value = 4.5, min_value = 0.0, max_value = 20.0, step = 0.1)

    def adjust(self):
        #dhw_sum = self.dhw_old
        #dhw_sum_new = self.dhw_sum

        #space_heating_sum = self.space_heating_old
        #space_heating_sum_new = self.space_heating_sum
        #dhw_percentage = dhw_sum_new / dhw_sum
        #space_heating_percentage = space_heating_sum_new / space_heating_sum

        #self.dhw_arr = (self.dhw_arr * dhw_percentage).flatten()
        #self.space_heating_arr = (self.space_heating_arr * space_heating_percentage).flatten()
        #self.energy_arr = (self.dhw_arr + self.space_heating_arr).flatten()
        
        demand_sum = self.demand_old
        demand_sum_new = self.demand_sum

        demand_percentage = demand_sum_new / demand_sum

        self.energy_arr = (self.demand_array * demand_percentage).flatten()
        self.dhw_arr = self.energy_arr * self.dhw_ratio_demand
        self.space_heating_arr = self.energy_arr-self.dhw_arr







    
