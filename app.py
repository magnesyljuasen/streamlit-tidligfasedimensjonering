import streamlit as st
from PIL import Image
import json
import base64
import numpy as np
import requests
from streamlit_searchbox import st_searchbox
from streamlit_extras.no_default_selectbox import selectbox
from PIL import Image
import mpu
import pandas as pd
from shapely.geometry import Point, shape
from st_keyup import st_keyup
import time
import numpy as np
from scipy.constants import pi
import pygfunction as gt
import altair as alt
import math
from GHEtool import Borefield, FluidData, GroundData, PipeData 
from plotly import graph_objects as go
import plotly.express as px
import datetime
from streamlit_extras.chart_container import chart_container

class Calculator:
    def __init__(self):
        self.THERMAL_CONDUCTIVITY = 3.5
        self.GROUNDWATER_TABLE = 5
        self.DEPTH_TO_BEDROCK = 10
        self.BUILDING_TYPE = "A"
        self.BUILDING_STANDARD = "X"
        
        self.MINIMUM_TEMPERATURE = 0
        self.BOREHOLE_BURIED_DEPTH = 10
        self.BOREHOLE_RADIUS = (115/1000)/2
        self.BOREHOLE_DEPTH = 300
        self.BOREHOLE_DISTANCE = 15
        self.BOREHOLE_SIMULATION_YEARS = 30
        self.EFFECT_COVERAGE = 50

        self.MAXIMUM_DEPTH = 300
        self.COST_PER_METER = 400
        self.COST_HEAT_PUMP_PER_KW = 12000
        self.PAYMENT_TIME = 30
        self.INTEREST = 3.0
        self.WATERBORNE_HEAT_CONSTANT = 1300
        self.waterborne_heat_cost = 0
        
        self.ELPRICE_REGIONS = {
        'NO 1': 'Sørøst-Norge (NO1)',
        'NO 2': 'Sørvest-Norge (NO2)',
        'NO 3': 'Midt-Norge (NO3)',
        'NO 4': 'Nord-Norge (NO4)',
        'NO 5': 'Vest-Norge (NO5)'
        }
        
        self.ELPRICE_REGIONS_BACK = {
        'Sørøst-Norge (NO1)': 'NO1',
        'Sørvest-Norge (NO2)': 'NO2',
        'Midt-Norge (NO3)': 'NO3',
        'Nord-Norge (NO4)': 'NO4',
        'Vest-Norge (NO5)': 'NO5'
        }
    
    def set_streamlit_settings(self):
        st.set_page_config(
        page_title="Tidligfasedimensjonering",
        page_icon="♨️",
        layout="centered",
        initial_sidebar_state="expanded")
        
        with open("src/styles/main.css") as f:
            st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

        st.markdown(
            """
            <style>
            [data-testid="collapsedControl"] svg {
                height: 3rem;
                width: 3rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
       
    def streamlit_input_container(self):
        def __streamlit_onclick_function():
            st.session_state.is_expanded = False  
        if 'is_expanded' not in st.session_state:
            st.session_state.is_expanded = True
        container = st.expander("Inndata", expanded = st.session_state.is_expanded)
        with container:
            # -- Input content
            self.__streamlit_calculator_input()
            # -- Input content
            start_calculation = st.button("Start kalkulator for bygget", on_click=__streamlit_onclick_function)
            if 'load_state' not in st.session_state:
                st.session_state.load_state = False
        if start_calculation or st.session_state.load_state:
            self.progress_bar = st.progress(0)
            st.toast("Beregner ...", icon = "💻")
            st.session_state.load_state = True
        else:
            st.stop()
            
    def __streamlit_calculator_input(self):
        st.header("Tidligfasedimensjonering")
        st.write(f"Beregn potensialet for å hente energi fra bakken til ditt bygg! Start med å skrive inn adresse i søkefeltet under.")
        self.__streamlit_address_input()
        self.__streamlit_profet_or_not_input()
        if self.CUSTOM_INPUT == False:
            c1, c2 = st.columns(2)
            with c1:
                self.__streamlit_area_input()
            with c2:
                self.__streamlit_age_input()
            #c1, c2 = st.columns(2)
            #with c1:
            #    state = self.__streamlit_waterborne_heat_input()
            #with c2:
            self.__streamlit_heat_system_input()
            #if state == False:
            #    st.stop()
            # temperaturdata
            self.__get_temperature_data()
            # strømpriser
            self.__find_elprice_region()
            # energibehov
            self.__profet_calculation()
        else:
            self.__get_temperature_data()
            self.__find_elprice_region()
            self.__streamlit_heat_system_input()
        self.__streamlit_demand_input()


    def __streamlit_profet_or_not_input(self):
        selected_option = selectbox("Hvordan vil du laste opp energibehov?", options = ["PROFet", "Last opp timeserie [kW]"], no_selection_label = "")
        if selected_option == None:
            st.stop()
        elif selected_option == "Last opp timeserie [kW]":
            self.CUSTOM_INPUT = True
            uploaded_file = st.file_uploader("Last opp varmebehov (excel) [kW]")
            if uploaded_file:
                df = pd.read_excel(uploaded_file, header = None)
                df[0]=df[0].replace(',','.',regex=True).astype(float)
                demand_array = df.iloc[:,0].to_numpy()
                self.dhw_demand = demand_array * 0.1
                self.space_heating_demand = demand_array * 0.9
            else:
                st.stop()
        elif selected_option == "PROFet":
            self.CUSTOM_INPUT = False
         
    
    def __streamlit_address_input(self):
        def __address_search(searchterm: str):
            if not searchterm:
                return []
            number_of_addresses = 5
            r = requests.get(f"https://ws.geonorge.no/adresser/v1/sok?sok={searchterm}&fuzzy=true&treffPerSide={number_of_addresses}&sokemodus=OR", auth=('user', 'pass'))
            if r.status_code == 200 and len(r.json()["adresser"]) == number_of_addresses:
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
        selected_adr = st_searchbox(
            __address_search,
            key="address_search",
            placeholder = "Adresse 🏠"
        )
        if selected_adr != None:
            try:
                self.address_name = selected_adr[0]
            except Exception:
                st.warning("Fyll inn adresse på nytt", icon="⚠️")
                st.stop()
            self.address_lat = float(selected_adr[1])
            self.address_long = float(selected_adr[2])
            self.address_postcode = selected_adr[3]
        else:
            #st_lottie("src/csv/house.json")
            image = Image.open('src/data/figures/Ordinary day-amico.png')
            #image = Image.open("src/data/figures/nylogo.png")
            st.image(image)
            st.stop()
            
    def __area_input(self):
        number = st.text_input('Oppvarmet bygningsareal [m²]', help = "bygningsarealet som tilføres varme fra byggens varmesystem")
        if number.isdigit():
            number = float(number)
        elif number == 'None' or number == '':
            number = 0
        else:
            st.error('Input må være et tall')
            number = 0
        return number
    
    def __streamlit_age_input(self):
        #c1, c2 = st.columns(2)
        #with c2:
        #    st.info("Bygningsstandard brukes til å anslå oppvarmingsbehovet for ditt bygg")
        #with c1:
        selected_option = selectbox("Velg bygningsstandard", options = ["Eldre", "TEK10/TEK17", "Passivhus"], no_selection_label = "", help = "Bygningsstandard brukes til å anslå oppvarmingsbehovet for ditt bygg")
        if selected_option == None:
            st.stop()
        elif selected_option == "Eldre":
            self.BUILDING_STANDARD = "X"
        elif selected_option == "TEK10/TEK17":
            self.BUILDING_STANDARD = "Y"
        elif selected_option == "Passivhus":
            self.BUILDING_STANDARD = "Z"
                
    def __streamlit_area_input(self):
        #c1, c2 = st.columns(2)
        #with c2:
        #st.info("bygningsarealet som tilføres varme fra byggens varmesystem")
        #with c1:
        self.building_area = self.__area_input()

        
    def __streamlit_heat_system_input(self):
        option_list = ['Gulvvarme', 'Radiator', 'Varmtvann']
        #c1, c2 = st.columns(2)
        #with c1:
        #if self.waterborne_heat_cost == 0:
        #    text = "type"
        #else:
        #    text = "ønsket"
        selected = st.multiselect(f'Type vannbårent varmesystem (COP)', options=option_list, help = "Type varmegiver bestemmer energieffektiviteten til systemet")
        #with c2:
        #st.info('Type varmegiver bestemmer energieffektiviteten til systemet')
        if len(selected) > 0:
            self.selected_cop_option = selected
        else:
            st.stop()
                
    def __streamlit_waterborne_heat_input(self):
        #c1, c2 = st.columns(2)
        #with c2:
        #st.info("Bergvarme krever at byggen har et vannbårent varmesystem")
        #with c1:
        selected_option = selectbox("Har byggen vannbåren varme?", options = ["Ja", "Nei"], no_selection_label = "", help = "Bergvarme krever at byggen har et vannbårent varmesystem")
        if selected_option == None:
            self.waterborne_heat_cost = 0
            state = False
        elif selected_option == "Nei":
            self.waterborne_heat_cost = self.__rounding_to_int(self.WATERBORNE_HEAT_CONSTANT * self.building_area)
            state = True
        elif selected_option == "Ja":
            self.waterborne_heat_cost = 0
            state = True
        return state
            
    def __streamlit_demand_input(self):
        demand_sum_old = self.__rounding_to_int(np.sum(self.dhw_demand + self.space_heating_demand))
        #c1, c2 = st.columns(2)
        #with c1:
        demand_sum_new = st.number_input('Hva er byggets årlige varmebehov? [kWh/år]', value = demand_sum_old, step = 1000)
        #with c2:
        if demand_sum_new == 'None' or demand_sum_new == '':
            demand_sum_new = ''
            st.stop()
        demand_percentage = demand_sum_new / demand_sum_old
        self.dhw_demand = (self.dhw_demand * demand_percentage).flatten()
        self.space_heating_demand = (self.space_heating_demand * demand_percentage).flatten()
        
    def __get_temperature_data(self):
        # find closest weather station
        distance_min = 1000000
        df = pd.read_csv('src/data/temperature/Stasjoner.csv', sep=',',on_bad_lines='skip')
        for i in range (0, len (df)):
            distance = mpu.haversine_distance((df.iat [i,1], df.iat [i,2]), (self.address_lat, self.address_long))
            if distance != 0 and distance < distance_min:
                distance_min = distance
                self.weatherstation_id = df.iat[i,0]
                self.weatherstation_lat = df.iat[i,1]
                self.weatherstation_long = df.iat[i,2]
                self.weatherstation_distance = distance_min
        # get temperature array
        temperature_array = 'src/data/temperature/_' + self.weatherstation_id + '_temperatur.csv'
        self.temperature_arr = pd.read_csv(temperature_array, sep=',', on_bad_lines='skip').to_numpy()
        self.average_temperature = float("{:.2f}".format(np.average(self.temperature_arr)))
        
    def __find_elprice_region(self):
        # import json function
        def __import_json():
            with open('src/csv/regioner.geojson') as f:
                js = json.load(f)
            f.close()
            return js
        json_file = __import_json()
        # find region
        region = 'NO 1'
        for feature in json_file['features']:
            polygon = shape(feature['geometry'])
            if polygon.contains(Point(self.address_long, self.address_lat)):
                region = feature['properties']['ElSpotOmr']
        self.elprice_region = self.ELPRICE_REGIONS[region]
        
    def __profet_calculation(self):
        profet_data_df = pd.read_csv('src/data/demand/profet_data.csv', sep = ";")
        space_heating_series = profet_data_df[f"{self.BUILDING_TYPE}_{self.BUILDING_STANDARD}_SPACEHEATING"]
        self.space_heating_demand = self.building_area * np.array(space_heating_series)
        dhw_heating_series = profet_data_df[f"{self.BUILDING_TYPE}_{self.BUILDING_STANDARD}_DHW"]
        self.dhw_demand = self.building_area * np.array(dhw_heating_series)
        electric_demand_series = profet_data_df[f"{self.BUILDING_TYPE}_{self.BUILDING_STANDARD}_ELECTRIC"]
        self.electric_demand = self.building_area * np.array(electric_demand_series)
    
    def __streamlit_sidebar_settings(self):
        #image = Image.open("src/data/figures/bergvarmekalkulatoren_logo_blå.png")
        #st.image(image)
        st.header("Forutsetninger")
        #st.write("Her kan du justere forutsetningene som ligger til grunn for beregningene.")

    def environmental_calculation(self):
        self.geoenergy_emission_series = (self.compressor_series + self.peak_series) * self.emission_constant_electricity
        self.direct_el_emission_series = (self.dhw_demand + self.space_heating_demand) * self.emission_constant_electricity
        self.emission_savings = self.__rounding_to_int((np.sum(self.direct_el_emission_series - self.geoenergy_emission_series) * self.BOREHOLE_SIMULATION_YEARS) / 1000)
        self.emission_savings_flights = self.__rounding_to_int(self.emission_savings/(103/1000))

    
    def cost_calculation(self):
        # -- investeringskostnader 
        self.geoenergy_investment_cost = self.__rounding_to_int((self.BOREHOLE_DEPTH * self.number_of_boreholes) * self.COST_PER_METER) # brønn + graving
        self.heatpump_cost = self.__rounding_to_int((self.heat_pump_size) * self.COST_HEAT_PUMP_PER_KW) # varmepumpe
        self.investment_cost = self.geoenergy_investment_cost + self.heatpump_cost + self.waterborne_heat_cost

        # -- driftskostnader
        self.direct_el_operation_cost = (self.dhw_demand + self.space_heating_demand) * self.elprice # kostnad direkte elektrisk
        self.geoenergy_operation_cost = (self.compressor_series + self.peak_series) * self.elprice # kostnad grunnvarme 
        self.savings_operation_cost = self.__rounding_to_int(np.sum(self.direct_el_operation_cost - self.geoenergy_operation_cost)) # besparelse
        self.savings_operation_cost_lifetime = self.savings_operation_cost * self.BOREHOLE_SIMULATION_YEARS
        
        # -- lån
        total_number_of_months = self.PAYMENT_TIME * 12
        amortisering = self.investment_cost / total_number_of_months
        prosentandel_renter = self.investment_cost * (self.INTEREST/100) / 12
        self.loan_cost_monthly = amortisering + prosentandel_renter
        self.loan_cost_yearly = self.loan_cost_monthly * 12

        # -- visningsvariabler
        self.short_term_investment = self.__rounding_to_int(self.savings_operation_cost)
        self.long_term_investment = self.__rounding_to_int(self.savings_operation_cost_lifetime - self.investment_cost)

        self.short_term_loan = self.__rounding_to_int(self.savings_operation_cost - self.loan_cost_yearly)
        self.long_term_loan = self.__rounding_to_int((self.savings_operation_cost - self.loan_cost_yearly) * self.BOREHOLE_SIMULATION_YEARS)
        
        
    def __plot_costs(self):
        x = [i for i in range(1, self.BOREHOLE_SIMULATION_YEARS)]
        y_1 = np.sum(self.geoenergy_operation_cost) * np.array(x) + self.investment_cost
        y_2 = (np.sum(self.geoenergy_operation_cost) + (self.loan_cost_monthly * 12)) * np.array(x)
        y_3 = np.sum(self.direct_el_operation_cost) * np.array(x)
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y_1,
                hoverinfo='skip',
                mode='lines',
                line=dict(width=1, color="#48a23f"),
                name=f"Bergvarme (direktekjøp): \n {self.__rounding_cost_plot_to_int(np.max(y_1)):,} kr".replace(",", " "),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y_2,
                hoverinfo='skip',
                mode='lines',
                line=dict(width=1, color="#1d3c34"),
                name=f"Bergvarme <br> (lånefinansiert): {self.__rounding_cost_plot_to_int(np.max(y_2)):,} kr".replace(",", " "),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y_3,
                hoverinfo='skip',
                mode='lines',
                line=dict(width=1, color="#880808"),
                name=f"Direkte <br> elektrisk: {self.__rounding_cost_plot_to_int(np.max(y_3)):,} kr".replace(",", " "),
            )
        )
        fig["data"][0]["showlegend"] = True
        fig.update_layout(legend=dict(itemsizing='constant'))
        fig.update_layout(
            margin=dict(l=50,r=50,b=10,t=10,pad=0),
            yaxis_title="Oppvarmingskostnader [kr]",
            plot_bgcolor="white",
            legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)"),
            barmode="stack",
            xaxis = dict(
                tickmode = 'array',
                tickvals = [i for i in range(1, self.BOREHOLE_SIMULATION_YEARS, 2)],
                ticktext = [f"År {i}" for i in range(1, self.BOREHOLE_SIMULATION_YEARS, 2)]
                ))
        
        fig.update_xaxes(
            range=[0, 31],
            ticks="outside",
            linecolor="black",
            gridcolor="lightgrey",
        )
        fig.update_yaxes(
            tickformat=",",
            ticks="outside",
            linecolor="black",
            gridcolor="lightgrey",
        )
        fig.update_layout(separators="* .*")
        return fig
    
    def __plot_costs_loan(self):
        x = [i for i in range(0, self.BOREHOLE_SIMULATION_YEARS + 1)]
        y_1 = (np.sum(self.geoenergy_operation_cost) + (self.loan_cost_monthly * 12)) * np.array(x)
        y_2 = np.sum(self.direct_el_operation_cost) * np.array(x)
        fig = go.Figure(data = [
            go.Bar(
                x=x,
                y=y_1,
                hoverinfo='skip',
                marker_color = "#48a23f",
                name=f"Bergvarme (lån):<br>{self.__rounding_cost_plot_to_int(np.max(y_1)):,} kr".replace(",", " "),
            )
            , 
            go.Bar(
                x=x,
                y=y_2,
                hoverinfo='skip',
                marker_color = "#880808",
                name=f"Direkte elektrisk:<br>{self.__rounding_cost_plot_to_int(np.max(y_2)):,} kr".replace(",", " "),
            )])

        tickspacing = 3
        fig["data"][0]["showlegend"] = True
        fig.update_layout(legend=dict(itemsizing='constant'))
        fig.update_layout(
            autosize=True,
            margin=dict(l=0,r=0,b=10,t=10,pad=0),
            yaxis_title="Oppvarmingskostnader [kr]",
            plot_bgcolor="white",
            legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)"),
            xaxis = dict(
                tickmode = 'array',
                tickvals = [i for i in range(1, self.BOREHOLE_SIMULATION_YEARS + 1, tickspacing)],
                ticktext = [f"År {i}" for i in range(1, self.BOREHOLE_SIMULATION_YEARS + 1, tickspacing)]
                ))
        
        fig.update_xaxes(
            range=[0, self.BOREHOLE_SIMULATION_YEARS],
            ticks="outside",
            linecolor="black",
            gridcolor="lightgrey",
        )
        fig.update_yaxes(
            tickformat=",",
            ticks="outside",
            linecolor="black",
            gridcolor="lightgrey",
        )
        fig.update_layout(separators="* .*")
        return fig
    
    def __plot_costs_investment(self):
        x = [i for i in range(0, self.BOREHOLE_SIMULATION_YEARS + 1)]
        y_1 = np.sum(self.geoenergy_operation_cost) * np.array(x) + self.investment_cost
        y_2 = np.sum(self.direct_el_operation_cost) * np.array(x)
        fig = go.Figure(data = [
            go.Bar(
                x=x,
                y=y_1,
                hoverinfo='skip',
                marker_color = "#48a23f",
                name=f"Bergvarme:<br>{self.__rounding_cost_plot_to_int(np.max(y_1)):,} kr".replace(",", " "),
            )
            , 
            go.Bar(
                x=x,
                y=y_2,
                hoverinfo='skip',
                marker_color = "#880808",
                name=f"Direkte elektrisk:<br>{self.__rounding_cost_plot_to_int(np.max(y_2)):,} kr".replace(",", " "),
            )])
    
        tickspacing = 3
        fig["data"][0]["showlegend"] = True
        fig.update_layout(legend=dict(itemsizing='constant'))
        fig.update_layout(
            autosize=True,
            margin=dict(l=0,r=0,b=10,t=10,pad=0),
            yaxis_title="Oppvarmingskostnader [kr]",
            plot_bgcolor="white",
            legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)"),
            xaxis = dict(
                tickmode = 'array',
                tickvals = [i for i in range(1, self.BOREHOLE_SIMULATION_YEARS + 1, tickspacing)],
                ticktext = [f"År {i}" for i in range(1, self.BOREHOLE_SIMULATION_YEARS + 1, tickspacing)]
                ))
        
        fig.update_xaxes(
            range=[0, self.BOREHOLE_SIMULATION_YEARS],
            ticks="outside",
            linecolor="black",
            gridcolor="lightgrey",
        )
        fig.update_yaxes(
            tickformat=",",
            ticks="outside",
            linecolor="black",
            gridcolor="lightgrey",
        )
        fig.update_layout(separators="* .*")
        return fig
        
    def __plot_environmental(self):
        geoenergy_emission = self.__rounding_to_int(np.sum(self.compressor_series + self.peak_series))
        direct_el_emmision = self.__rounding_to_int(np.sum(self.dhw_demand + self.space_heating_demand))
        emission_savings = self.__rounding_to_int(np.sum(self.delivered_from_wells_series))  
        col1, col2 = st.columns(2)
        with col1:
            source = pd.DataFrame({"label" : [f'Strøm: {geoenergy_emission:,} kWh/år'.replace(","," "), f'Fra grunnen: {(direct_el_emmision-geoenergy_emission):,} kWh/år'.replace(","," ")], "value": [geoenergy_emission, emission_savings]})
            fig = px.pie(source, names='label', values='value', color_discrete_sequence = ['#48a23f', '#a23f47'], hole = 0.4)
            fig.update_layout(
            margin=dict(l=0,r=0,b=0,t=0,pad=0),
            plot_bgcolor="white",
            legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)"),
            legend_title_text = "Bergvarme"
            )

            st.plotly_chart(figure_or_data = fig, use_container_width=True, )
        with col2:
            source = pd.DataFrame({"label" : [f'Strøm: {direct_el_emmision:,} kWh/år'.replace(","," ")], "value": [direct_el_emmision]})
            fig = px.pie(source, names='label', values='value', color_discrete_sequence = ['#a23f47'], hole = 0.4)
            fig.update_layout(
            margin=dict(l=0,r=0,b=0,t=0,pad=0),
            plot_bgcolor="white",
            legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)"),
            legend_title_text = "Direkte elektrisk oppvarming"
            )
            fig.update_traces(textinfo='none')
            fig.update_layout(
                autosize=True,
            )
            st.plotly_chart(figure_or_data = fig, use_container_width=True, )

    def streamlit_calculations(self):
        with st.sidebar:
            self.__streamlit_sidebar_settings()
            self.__streamlit_adjust_input()
        self.progress_bar.progress(33)
        # grunnvarmeberegning
        self.borehole_calculation()
        # stømsparingsberegning
        self.environmental_calculation()
        # kostnadsberegning
        self.cost_calculation() 

    def __streamlit_adjust_input(self):
        self.progress_bar.progress(33)
        with st.form('input'):
            st.write("**Energi- og effekt**")
            self.__adjust_heat_pump_size_energy()
            self.__adjust_cop()
            st.markdown("---")
            st.write("**Brønn**")
            self.__adjust_well_parameters()
            st.markdown("---")
            st.write("**Geologi**")
            self.__adjust_geology_parameters()
            self.__adjust_parameters()
            st.markdown("---")
            st.write("**Simulering**")
            self.__adjust_simulation_parameters()
            st.markdown("---")
            st.write("**Andre**")
            self.__adjust_elprice()  
            self.__adjust_energymix()
            self.__adjust_interest()
            
            #    st.markdown("---")
            #    st.write(f"*- Gjennomsnittlig spotpris: {round(float(np.mean(self.elprice)),2)} kr/kWh*")
            #    st.write(f"*- Utslippsfaktor: {(self.energymix)*1000} g CO₂e/kWh*")
                               
            st.form_submit_button('Oppdater')

    def __adjust_well_parameters(self):
        self.BOREHOLE_DEPTH = st.number_input("Dybde [m]", value = 300, step = 50)
        self.GROUNDWATER_TABLE = st.number_input("Grunnvannstand [m]", value = 5, step = 1)
        self.SIMULATION_BOREHOLE_DEPTH = self.BOREHOLE_DEPTH - self.GROUNDWATER_TABLE
        self.BOREHOLE_DISTANCE = st.number_input("Avstand mellom brønner [m]", value = 15, step = 1)
        self.BOREHOLE_FIELD = self.__select_borehole_field()
        
    def __adjust_simulation_parameters(self):
        self.SIMULATION_MODE = st.selectbox("Alternativer", options = ["Lås brønndybde", "Lås minimumstemperatur"])
        if self.SIMULATION_MODE == "Lås minimumstemperatur":
            self.MINIMUM_TEMPERATURE = st.number_input("Minimumstemperatur [°C]", value = 0, step = 1)
        self.BOREHOLE_SIMULATION_YEARS = st.number_input("Simuleringsperiode [år]", value = 25, step = 5)

    def __adjust_geology_parameters(self):
        self.THERMAL_CONDUCTIVITY = st.number_input("Effektiv varmeledningsevne [W/(m∙K)]", value = 3.5, step = 0.1)
        self.BOREHOLE_RESISTANCE = st.number_input("Borehullsmotstand [(m∙K)/W]", value = 0.10)
        self.GROUND_TEMPERATURE = st.number_input("Uforstyrret temperatur (terrengnivå) [°C]", value = self.average_temperature)
        
        
        #self.DEPTH_TO_BEDROCK = st.number_input("Dybde til fjell [m]", value = 10, step = 1)

    def __adjust_parameters(self):
        self.MAXIMUM_DEPTH = 300
        self.COST_PER_METER = 400
        self.COST_HEAT_PUMP_PER_KW = 12000
        self.PAYMENT_TIME = 30
        self.INTEREST = 3.0

                
    def __adjust_cop(self):
        space_heating_sum = np.sum(self.space_heating_demand)
        dhw_sum = np.sum(self.dhw_demand)
        cop_gulvvarme, cop_radiator, cop_varmtvann = 0, 0, 0
        for index, value in enumerate(self.selected_cop_option):
            if value == "Gulvvarme":
                cop_gulvvarme = 4.0
            elif value == "Radiator":
                cop_radiator = 3.5
            elif value == "Varmtvann":
                cop_varmtvann = 2.5
        dhw = cop_varmtvann * dhw_sum
        if cop_gulvvarme > 0 and cop_radiator > 0:
            space_heating = ((cop_gulvvarme + cop_radiator)/2) * space_heating_sum
        elif cop_gulvvarme > 0 and cop_radiator == 0:
            space_heating = cop_gulvvarme * space_heating_sum
        elif cop_gulvvarme == 0 and cop_radiator > 0:
            space_heating = cop_radiator * space_heating_sum
        
        if cop_varmtvann == 0:                
            combined_cop = space_heating / (space_heating_sum)
        elif cop_varmtvann > 0 and cop_gulvvarme == 0 and cop_radiator == 0:
            combined_cop = dhw / (dhw_sum)
        else:
            combined_cop = (space_heating + dhw) / (space_heating_sum + dhw_sum)
            
        self.COMBINED_COP = float(st.number_input("Årsvarmefaktor (SCOP)", value = float(combined_cop), step = 0.1, min_value = 2.0, max_value= 5.0))

    def __adjust_elprice(self):
        self.elprice = st.number_input("Velg strømpris [kr/kWh]", min_value = 1.0, value = 2.0, max_value = 5.0, step = 0.1)
        #selected_el_option = st.selectbox("Strømpris", options=["Historisk strømpris: 2022", "Historisk strømpris: 2021", "Historisk strømpris: 2020", "Flat strømpris: 0.8 kr/kWh", "Flat strømpris: 1.5 kr/kWh", "Flat strømpris: 2.0 kr/kWh"], index = 1)
        #selected_year = selected_el_option.split()[2]
        #if float(selected_year) > 10:
        #    df = pd.read_excel("src/csv/spotpriser.xlsx", sheet_name=selected_year)
        #    spotprice_arr = df[self.ELPRICE_REGIONS_BACK[self.elprice_region]].to_numpy()/1.25
        #    self.elprice = spotprice_arr
        #else:
        #    self.elprice = float(selected_year)
             
    def __adjust_energymix(self):
        option_list = ['Norsk', 'Norsk-europeisk', 'Europeisk']
        selected = st.selectbox('Strømmiks', options=option_list, index = 1)
        x = {option_list[0] : 19/1000, option_list[1] : 116.9/1000, option_list[2] : 123/1000}
        self.emission_constant_electricity = x[selected]
        self.selected_emission_constant = selected
        
    def __adjust_interest(self):
        self.INTEREST = st.number_input("Lånerente [%]", min_value = 0.0, value = self.INTEREST, max_value = 10.0, step = 0.1)
        
    def __adjust_heat_pump_size_energy(self):
        thermal_demand = self.space_heating_demand + self.dhw_demand
        energidekningsgrad = st.number_input("Energidekningsgrad [%]", value = 90, min_value = 0, max_value = 100, step = 5)
        heat_pump_array = self.__energidekningsgrad_calculation(dekningsgrad = energidekningsgrad, timeserie = thermal_demand)
        self.heat_pump_size = self.__rounding_to_int(np.max(heat_pump_array))

    def __energidekningsgrad_calculation(self, dekningsgrad, timeserie):
        if dekningsgrad == 100:
            return timeserie
        timeserie_sortert = np.sort(timeserie)
        timeserie_sum = np.sum(timeserie)
        timeserie_N = len(timeserie)
        startpunkt = timeserie_N // 2
        i = 0
        avvik = 0.0001
        pm = 2 + avvik
        while abs(pm - 1) > avvik:
            cutoff = timeserie_sortert[startpunkt]
            timeserie_tmp = np.where(timeserie > cutoff, cutoff, timeserie)
            beregnet_dekningsgrad = (np.sum(timeserie_tmp) / timeserie_sum) * 100
            pm = beregnet_dekningsgrad / dekningsgrad
            gammelt_startpunkt = startpunkt
            if pm < 1:
                startpunkt = startpunkt + timeserie_N // 2 ** (i + 2) - 1
            else:
                startpunkt = startpunkt - timeserie_N // 2 ** (i + 2) - 1
            if startpunkt == gammelt_startpunkt:
                break
            i += 1
            if i > 13:
                break
        return timeserie_tmp
    
    def __borehole_field_shape(self):
        N_1 = st.number_input("Antall brønner (X)", value = 5, step = 1)
        N_2 = st.number_input("Antall brønner (Y)", value = 1, step = 1)
        N_b = N_1 * N_2
        return N_1, N_2, N_b
    
    def __select_borehole_field(self):
        B, H, D, R = self.BOREHOLE_DISTANCE, self.SIMULATION_BOREHOLE_DEPTH, self.BOREHOLE_BURIED_DEPTH, self.BOREHOLE_RADIUS
        selected_field = st.selectbox("Konfigurasjon", options = ["Rektangulær", "Boks", "U", "L", "Sirkulær", "Fra fil"])
        if selected_field == "Rektangulær":
            N_1, N_2, N_B = self.__borehole_field_shape() 
            FIELD = gt.boreholes.rectangle_field(N_1, N_2, B, B, H, D, R)
        if selected_field == "Boks": 
            N_1, N_2, N_B = self.__borehole_field_shape() 
            FIELD = gt.boreholes.box_shaped_field(N_1, N_2, B, B, H, D, R)
        if selected_field == "U":
            N_1, N_2, N_B = self.__borehole_field_shape() 
            FIELD = gt.boreholes.U_shaped_field(N_1, N_2, B, B, H, D, R)
        if selected_field == "L":
            N_1, N_2, N_B = self.__borehole_field_shape() 
            FIELD = gt.boreholes.L_shaped_field(N_1, N_2, B, B, H, D, R)
        if selected_field == "Sirkulær":
            N_B = st.number_input("Antall borehull", value = 5, step = 1)
            FIELD = gt.boreholes.circle_field(N_B, B, H, D, R)
        if selected_field == "Fra fil":
            file = st.file_uploader("Last opp koordinater i CSV")
            df = pd.read_excel(file)
            pos = []
            for i in range(0, len(df)):
                x = df['x'][i]
                y = df['y'][i]
                pos.append((x,y))
            FIELD = [gt.boreholes.Borehole(H, D, self.R_B, x, y, 0, 0) for (x, y) in pos]
            FIELD = gt.boreholes.remove_duplicates(FIELD, disp=True)
        #st.pyplot(gt.boreholes.visualize_field(FIELD))
        return FIELD
        
    def borehole_calculation(self):
        # energy
        thermal_demand = self.dhw_demand + self.space_heating_demand
        self.heat_pump_series = np.where(thermal_demand > self.heat_pump_size, self.heat_pump_size, thermal_demand)
        self.delivered_from_wells_series = self.heat_pump_series - self.heat_pump_series / self.COMBINED_COP
        self.compressor_series = self.heat_pump_series - self.delivered_from_wells_series
        self.peak_series = thermal_demand - self.heat_pump_series

        data = GroundData(k_s = self.THERMAL_CONDUCTIVITY, T_g = self.GROUND_TEMPERATURE, R_b = self.BOREHOLE_RESISTANCE, flux = 0.04)
        borefield = Borefield(simulation_period = self.BOREHOLE_SIMULATION_YEARS)
        borefield.set_ground_parameters(data) 
        borefield.set_hourly_heating_load(heating_load = self.delivered_from_wells_series)
        borefield.set_hourly_cooling_load(np.zeros(8760))        
        borefield.set_max_ground_temperature(16)
        borefield.set_min_ground_temperature(self.MINIMUM_TEMPERATURE)
        #i = self.__rounding_to_int(np.sum(self.delivered_from_wells_series)/80/300)
        #self.borehole_depth = self.MAXIMUM_DEPTH + 1
        #while self.borehole_depth >= self.MAXIMUM_DEPTH:
        borefield.set_borefield(self.BOREHOLE_FIELD)
        if self.SIMULATION_MODE == "Lås brønndybde":
            borefield.calculate_temperatures(hourly = True)
        elif self.SIMULATION_MODE == "Lås minimumstemperatur":
            self.SIMULATION_BOREHOLE_DEPTH = borefield.size(L4_sizing=True, use_constant_Tg = False) + self.GROUNDWATER_TABLE
        self.progress_bar.progress(66)
        self.borehole_temperature_arr = borefield.results_peak_heating
        self.number_of_boreholes = borefield.number_of_boreholes
        self.kWh_per_meter = np.sum((self.delivered_from_wells_series)/(self.SIMULATION_BOREHOLE_DEPTH * self.number_of_boreholes))
        self.W_per_meter = np.max((self.delivered_from_wells_series))/(self.SIMULATION_BOREHOLE_DEPTH* self.number_of_boreholes) * 1000
        #st.caption(f"Tester {i} brønner")
        #i = i + 1
        #if i == 50:
        #    st.error("Beregning feilet, prøv en annen varmepumpestørrelse")
        #    break
            
    def __render_svg_metric(self, svg, text, result):
        """Renders the given svg string."""
        b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
        html = f'<medium> {text} </medium> <br> <img src="data:image/svg+xml;base64,%s"/> <font size="+5">  {result} </font>' % b64
        st.write(html, unsafe_allow_html=True)
                
    def __plot_gshp_delivered(self):
        y_arr_1 = self.compressor_series
        y_arr_2 = self.delivered_from_wells_series
        y_arr_3 = self.peak_series
        x_arr = np.array(range(0, len(self.delivered_from_wells_series)))
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=x_arr,
                y=y_arr_1,
                hoverinfo='skip',
                stackgroup="one",
                fill="tonexty",
                line=dict(width=0, color="#1d3c34"),
                name=f"Strøm til varmepumpe:<br>{self.__rounding_to_int(np.sum(y_arr_1)):,} kWh/år | {self.__rounding_to_int(np.max(y_arr_1)):,} kW".replace(
                    ",", " "
                ))
        )
        fig.add_trace(
            go.Scatter(
                x=x_arr,
                y=y_arr_2,
                hoverinfo='skip',
                stackgroup="one",
                fill="tonexty",
                line=dict(width=0, color="#48a23f"),
                name=f"Levert fra brønner:<br>{self.__rounding_to_int(np.sum(y_arr_2)):,} kWh/år | {self.__rounding_to_int(np.max(y_arr_2)):,} kW".replace(
                    ",", " "
                ))
        )
        fig.add_trace(
            go.Scatter(
                x=x_arr,
                y=y_arr_3,
                hoverinfo='skip',
                stackgroup="one",
                fill="tonexty",
                line=dict(width=0, color="#FFC358"),
                name=f"Spisslast:<br>{int(np.sum(y_arr_3)):,} kWh/år | {int(np.max(y_arr_3)):,} kW".replace(
                    ",", " "
                ))
        )

        fig["data"][0]["showlegend"] = True
        fig.update_layout(
        margin=dict(l=50,r=50,b=10,t=10,pad=0),
        yaxis_title="Effekt [kW]",
        plot_bgcolor="white",
        legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)"),
        barmode="stack",
        xaxis = dict(
                tickmode = 'array',
                tickvals = [0, 24 * (31), 24 * (31 + 28), 24 * (31 + 28 + 31), 24 * (31 + 28 + 31 + 30), 24 * (31 + 28 + 31 + 30 + 31), 24 * (31 + 28 + 31 + 30 + 31 + 30), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30 + 31)],
                ticktext = ["1.jan", "", "1.mar", "", "1.mai", "", "1.jul", "", "1.sep", "", "1.nov", "", "1.jan"]
                ))
        fig.update_xaxes(
            range=[0, 8760],
            ticks="outside",
            linecolor="black",
            gridcolor="lightgrey",
        )
        fig.update_yaxes(
            ticks="outside",
            linecolor="black",
            gridcolor="lightgrey",
        )
        return fig
    
    def __plot_gshp_delivered_varighetskurve(self):
        y_arr_1 = np.sort(self.compressor_series)[::-1]
        y_arr_2 = np.sort(self.delivered_from_wells_series)[::-1]
        y_arr_3 = np.sort(self.peak_series)[::-1]
        x_arr = np.array(range(0, len(self.delivered_from_wells_series)))
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=x_arr,
                y=y_arr_1,
                hoverinfo='skip',
                stackgroup="one",
                fill="tonexty",
                line=dict(width=0, color="#1d3c34"),
                name=f"Strøm til varmepumpe:<br>{self.__rounding_to_int(np.sum(y_arr_1)):,} kWh/år | {self.__rounding_to_int(np.max(y_arr_1)):,} kW".replace(
                    ",", " "
                ))
        )
        fig.add_trace(
            go.Scatter(
                x=x_arr,
                y=y_arr_2,
                hoverinfo='skip',
                stackgroup="one",
                fill="tonexty",
                line=dict(width=0, color="#48a23f"),
                name=f"Levert fra brønner:<br>{self.__rounding_to_int(np.sum(y_arr_2)):,} kWh/år | {self.__rounding_to_int(np.max(y_arr_2)):,} kW".replace(
                    ",", " "
                ))
        )
        fig.add_trace(
            go.Scatter(
                x=x_arr,
                y=y_arr_3,
                hoverinfo='skip',
                stackgroup="one",
                fill="tonexty",
                line=dict(width=0, color="#FFC358"),
                name=f"Spisslast:<br>{int(np.sum(y_arr_3)):,} kWh/år | {int(np.max(y_arr_3)):,} kW".replace(
                    ",", " "
                ))
        )

        fig["data"][0]["showlegend"] = True
        fig.update_layout(
        margin=dict(l=50,r=50,b=10,t=10,pad=0),
        yaxis_title="Effekt [kW]",
        xaxis_title="Varighet [timer]",
        plot_bgcolor="white",
        legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)"),
        barmode="stack",)

        fig.update_xaxes(
            range=[0, 8760],
            ticks="outside",
            linecolor="black",
            gridcolor="lightgrey",
        )
        fig.update_yaxes(
            ticks="outside",
            linecolor="black",
            gridcolor="lightgrey",
        )
        return fig
    
    def __plot_borehole_temperature(self):
        y_array = self.borehole_temperature_arr
        x_array = np.array(range(0, len(self.borehole_temperature_arr)))
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=x_array,
                y=y_array,
                hoverinfo='skip',
                mode='lines',
                line=dict(width=0.25, color="#1d3c34"),
            ))
           
        fig.update_layout(legend=dict(itemsizing='constant'))
        tickspacing = 5
        tickrange = self.__rounding_to_int(self.BOREHOLE_SIMULATION_YEARS/tickspacing)
        fig.update_layout(
            margin=dict(l=50,r=50,b=10,t=10,pad=10),
            yaxis_title="Gjennomsnittlig kollektorvæsketemperatur [°C]",
            plot_bgcolor="white",
            barmode="stack",
            xaxis = dict(
                tickmode = 'array',
                tickvals = [8760 * (i + 1) * tickspacing for i in range(tickrange)],
                ticktext = [f"År {(i + 1) * tickspacing}" for i in range(tickrange)]
                ))
        
        fig.update_xaxes(
            range=[0, 8760 * self.BOREHOLE_SIMULATION_YEARS],
            ticks="outside",
            linecolor="black",
            gridcolor="lightgrey",
        )
        fig.update_yaxes(
            ticks="outside",
            linecolor="black",
            gridcolor="lightgrey",
        )
        return fig
    
    def __rounding_to_int(self, number):
        return int(round(number, 0))
    
    def __rounding_costs_to_int(self, number):
        return int(round(number, -3))
    
    def __rounding_cost_plot_to_int(self, number):
        return int(round(number, -2))
    
    def sizing_results(self):
        with st.container():
            st.write("**Energibrønn og varmepumpe**")
            if self.number_of_boreholes == 1:
                well_description_text = "brønn"
            else:
                well_description_text = "brønner"
            #rounding = 25
            #meter_rounded = (self.borehole_depth // rounding) * rounding
            column_1, column_2 = st.columns(2)
            with column_1:
                svg = """<svg width="27" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="505" y="120" width="27" height="26"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-505 -120)"><path d="M18.6875 10.8333C20.9312 10.8333 22.75 12.6522 22.75 14.8958 22.75 17.1395 20.9312 18.9583 18.6875 18.9583L2.97917 18.9583C2.82959 18.9583 2.70833 19.0796 2.70833 19.2292 2.70833 19.3787 2.82959 19.5 2.97917 19.5L18.6875 19.5C21.2303 19.5 23.2917 17.4386 23.2917 14.8958 23.2917 12.353 21.2303 10.2917 18.6875 10.2917L3.63946 10.2917C3.63797 10.2916 3.63678 10.2904 3.63678 10.2889 3.6368 10.2882 3.63708 10.2875 3.63756 10.2871L7.23315 6.69148C7.33706 6.58388 7.33409 6.41244 7.22648 6.30852 7.12154 6.20715 6.95514 6.20715 6.85019 6.30852L2.78769 10.371C2.68196 10.4768 2.68196 10.6482 2.78769 10.754L6.85019 14.8165C6.95779 14.9204 7.12923 14.9174 7.23315 14.8098 7.33452 14.7049 7.33452 14.5385 7.23315 14.4335L3.63756 10.8379C3.63651 10.8369 3.63653 10.8351 3.63759 10.8341 3.6381 10.8336 3.63875 10.8333 3.63946 10.8333Z" stroke="#005173" stroke-width="0.270833" fill="#005173" transform="matrix(6.12323e-17 1 -1.03846 6.35874e-17 532 120)"/></g></svg>"""
                self.__render_svg_metric(svg, "Aktiv brønndybde", f"{self.number_of_boreholes} {well_description_text} á {self.__rounding_to_int(self.SIMULATION_BOREHOLE_DEPTH)} m")
            with column_2:
                svg = """<svg width="31" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="395" y="267" width="31" height="26"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-395 -267)"><path d="M24.3005 0.230906 28.8817 0.230906 28.8817 25.7691 24.3005 25.7691Z" stroke="#005173" stroke-width="0.461812" stroke-linecap="round" stroke-miterlimit="10" fill="#F0F3E3" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M1.40391 2.48455 1.40391 25.5936 6.41918 25.5936 6.41918 2.48455C4.70124 1.49627 3.02948 1.44085 1.40391 2.48455Z" stroke="#005173" stroke-width="0.461812" stroke-linecap="round" stroke-miterlimit="10" fill="#FFF" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M24.3005 25.7691 1.23766 25.7691" stroke="#1F3E36" stroke-width="0.461812" stroke-linecap="round" stroke-miterlimit="10" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M24.3005 0.230906 6.59467 0.230906 6.59467 25.7691" stroke="#1F3E36" stroke-width="0.461812" stroke-linecap="round" stroke-miterlimit="10" fill="#FFF" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M24.3005 17.6874 6.59467 17.6874" stroke="#1F3E36" stroke-width="0.461812" stroke-linecap="round" stroke-miterlimit="10" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M24.3005 8.33108 6.59467 8.33108" stroke="#1F3E36" stroke-width="0.461812" stroke-linecap="round" stroke-miterlimit="10" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M9.71652 12.4874 10.1691 12.4874 10.1691 14.0114 11.222 14.7133 11.222 16.108 10.2153 16.8007 9.71652 16.8007" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M9.72575 12.4874 9.26394 12.4874 9.26394 14.0114 8.22025 14.7133 8.22025 16.108 9.21776 16.8007 9.72575 16.8007" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M14.27 12.4874 14.7226 12.4874 14.7226 14.0114 15.7663 14.7133 15.7663 16.108 14.7687 16.8007 14.27 16.8007" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M14.27 12.4874 13.8174 12.4874 13.8174 14.0114 12.7645 14.7133 12.7645 16.108 13.7712 16.8007 14.27 16.8007" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M1.40391 5.90195 0.230906 5.90195 0.230906 10.9542 1.40391 10.9542" stroke="#005173" stroke-width="0.461812" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M1.40391 13.0046 0.230906 13.0046 0.230906 25.0025 1.40391 25.0025" stroke="#005173" stroke-width="0.461812" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M28.0412 4.58117 25.2611 4.58117 25.2611 2.73393 25.2611 2.10586 28.0412 2.10586 28.0412 4.58117Z" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M25.4366 2.73393 28.0412 2.73393" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M25.4366 3.34352 28.0412 3.34352" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M25.4366 3.95311 28.0412 3.95311" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M9.71652 20.6799 10.1691 20.6799 10.1691 22.2131 11.222 22.9059 11.222 24.3005 10.2153 25.0025 9.71652 25.0025" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M9.72575 20.6799 9.26394 20.6799 9.26394 22.2131 8.22025 22.9059 8.22025 24.3005 9.21776 25.0025 9.72575 25.0025" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M14.27 20.6799 14.7226 20.6799 14.7226 22.2131 15.7663 22.9059 15.7663 24.3005 14.7687 25.0025 14.27 25.0025" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M14.27 20.6799 13.8174 20.6799 13.8174 22.2131 12.7645 22.9059 12.7645 24.3005 13.7712 25.0025 14.27 25.0025" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M20.0149 1.05293 23.4139 1.05293 23.4139 7.56448 20.0149 7.56448Z" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M17.9552 13.0046 23.4046 13.0046 23.4046 15.5538 17.9552 15.5538Z" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M19.0913 11.6931C19.0913 11.9073 18.9176 12.081 18.7034 12.081 18.4891 12.081 18.3155 11.9073 18.3155 11.6931 18.3155 11.4788 18.4891 11.3052 18.7034 11.3052 18.9176 11.3052 19.0913 11.4788 19.0913 11.6931Z" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M18.7034 13.0046 18.7034 12.081" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M20.4028 11.6931C20.4028 11.9073 20.2292 12.081 20.0149 12.081 19.8007 12.081 19.627 11.9073 19.627 11.6931 19.627 11.4788 19.8007 11.3052 20.0149 11.3052 20.2292 11.3052 20.4028 11.4788 20.4028 11.6931Z" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M20.0149 13.0046 20.0149 12.081" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M21.7421 11.6931C21.7421 11.9073 21.5684 12.081 21.3542 12.081 21.1399 12.081 20.9663 11.9073 20.9663 11.6931 20.9663 11.4788 21.1399 11.3052 21.3542 11.3052 21.5684 11.3052 21.7421 11.4788 21.7421 11.6931Z" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M21.3542 13.0046 21.3542 12.081" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M23.0536 11.6931C23.0536 11.9073 22.88 12.081 22.6657 12.081 22.4515 12.081 22.2778 11.9073 22.2778 11.6931 22.2778 11.4788 22.4515 11.3052 22.6657 11.3052 22.88 11.3052 23.0536 11.4788 23.0536 11.6931Z" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1.04327 0 0 1 395.314 267)"/><path d="M22.6657 13.0046 22.6657 12.081" stroke="#005173" stroke-width="0.230906" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1.04327 0 0 1 395.314 267)"/></g></svg>"""
                self.__render_svg_metric(svg, "Varmepumpestørrelse", f"{self.heat_pump_size} kW")
            
            with st.expander("Mer om brønndybde og varmepumpestørrelse", expanded = True):
                st.pyplot(gt.boreholes.visualize_field(borefield = self.BOREHOLE_FIELD))
                
                chart_df = pd.DataFrame({
                    "Strøm til VP" : self.compressor_series,
                    "Levert fra brønner" : self.delivered_from_wells_series,
                    "Spisslast" : self.peak_series
                })
                with chart_container(chart_df):
                    st.plotly_chart(figure_or_data = self.__plot_gshp_delivered(), use_container_width=True)

                chart_df = pd.DataFrame({
                    "Strøm til VP" : np.sort(self.compressor_series)[::-1],
                    "Levert fra brønner" : np.sort(self.delivered_from_wells_series)[::-1],
                    "Spisslast" : np.sort(self.peak_series)[::-1]
                })
                with chart_container(chart_df):
                    st.plotly_chart(figure_or_data = self.__plot_gshp_delivered_varighetskurve(), use_container_width=True)
                
                
                chart_df = pd.DataFrame({
                    "Gjennomsnittlig kollektorvæsketemperatur" : self.borehole_temperature_arr,
                })
                with chart_container(chart_df):
                    st.plotly_chart(figure_or_data = self.__plot_borehole_temperature(), use_container_width=True)
                
                if self.number_of_boreholes > 1:
                    energy_well_text = "energibrønnene"
                else:
                    energy_well_text = "energibrønnen"
                st.write(f"""Den innledende beregningen viser at {energy_well_text} 
                         kan levere ca {self.__rounding_to_int(self.kWh_per_meter)} kWh/(m∙år) og 
                         {self.__rounding_to_int(self.W_per_meter)} W/m dersom minimumstemperaturen 
                         er {round(np.min(self.borehole_temperature_arr), 1)} °C.""")
                  
        
    def environmental_results(self):
        with st.container():
            st.write("**Strømsparing og utslippskutt**")
            c1, c2 = st.columns(2)
            with c1:
                svg = """ <svg width="13" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="614" y="84" width="13" height="26"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-614 -84)"><path d="M614.386 99.81 624.228 84.3312C624.464 83.9607 625.036 84.2358 624.89 84.6456L621.224 95.1164C621.14 95.3522 621.32 95.5992 621.572 95.5992L626.3 95.5992C626.603 95.5992 626.777 95.9417 626.597 96.1831L616.458 109.691C616.194 110.039 615.644 109.725 615.823 109.326L619.725 100.456C619.838 100.203 619.63 99.9223 619.355 99.9447L614.74 100.36C614.437 100.388 614.229 100.057 614.392 99.7987Z" stroke="#005173" stroke-width="0.308789" stroke-linecap="round" stroke-miterlimit="10" fill="#FFF"/></g></svg>"""
                self.__render_svg_metric(svg, "Strømbesparelse", f"{self.__rounding_to_int(np.sum(self.delivered_from_wells_series)):,} kWh/år".replace(',', ' '))
            with c2:
                svg = """ <svg width="26" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="458" y="120" width="26" height="26"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-458 -120)"><path d="M480.21 137.875 480.21 135.438 472.356 129.885 472.356 124.604C472.356 123.548 471.814 122.167 471.001 122.167 470.216 122.167 469.647 123.548 469.647 124.604L469.647 129.885 461.793 135.438 461.793 137.875 469.647 133.948 469.647 139.852 466.939 142.208 466.939 143.833 471.001 142.208 475.064 143.833 475.064 142.208 472.356 139.852 472.356 133.948ZM472 140.261 474.522 142.455 474.522 143.033 471.203 141.706 471.001 141.624 470.8 141.706 467.481 143.033 467.481 142.455 470.003 140.261 470.189 140.099 470.189 133.072 469.403 133.463 462.335 136.999 462.335 135.718 469.96 130.328 470.189 130.166 470.189 124.604C470.189 123.645 470.703 122.708 471.001 122.708 471.341 122.708 471.814 123.664 471.814 124.604L471.814 130.166 472.043 130.328 479.668 135.718 479.668 136.999 472.598 133.463 471.814 133.072 471.814 140.099Z" stroke="#005173" stroke-width="0.270833"/></g></svg>"""
                self.__render_svg_metric(svg, f"Utslippskutt etter {self.BOREHOLE_SIMULATION_YEARS} år", f"{self.emission_savings_flights:,} sparte flyreiser".replace(',', ' '))
            with st.expander("Mer om strømsparing og utslippskutt", expanded = True):
                st.write(f""" Vi har beregnet hvor mye strøm bergvarme vil spare i ditt bygg sammenlignet med å bruke elektrisk oppvarming.
                Figurene viser at du sparer {self.__rounding_to_int(np.sum(self.delivered_from_wells_series)):,} kWh i året med bergvarme. 
                Hvis vi tar utgangspunkt i en {self.selected_emission_constant.lower()} strømmiks
                vil du i løpet av {self.BOREHOLE_SIMULATION_YEARS} år spare {self.emission_savings} tonn CO\u2082. Dette tilsvarer **{self.emission_savings_flights} flyreiser** mellom Oslo og Trondheim. """.replace(',', ' '))

                self.__plot_environmental()

    def cost_results(self):
        def __show_metrics(investment, short_term_savings, long_term_savings, investment_unit = "kr", short_term_savings_unit = "kr/år", long_term_savings_unit = "kr", investment_text = "Estimert investeringskostnad"):
            column_1, column_2, column_3 = st.columns(3)
            with column_1:
                svg = """ <svg width="26" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="369" y="79" width="26" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-369 -79)"><path d="M25.4011 12.9974C25.4011 19.8478 19.8478 25.4011 12.9974 25.4011 6.14699 25.4011 0.593654 19.8478 0.593654 12.9974 0.593654 6.14699 6.14699 0.593654 12.9974 0.593654 19.8478 0.593654 25.4011 6.14699 25.4011 12.9974Z" stroke="#005173" stroke-width="0.757136" stroke-miterlimit="10" fill="#fff" transform="matrix(1 0 0 1.03846 369 79)"/><path d="M16.7905 6.98727 11.8101 19.0075 11.6997 19.0075 9.20954 12.9974" stroke="#005173" stroke-width="0.757136" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.03846 369 79)"/></g></svg>"""
                self.__render_svg_metric(svg, f"{investment_text}", f"{self.__rounding_costs_to_int(investment):,} {investment_unit}".replace(',', ' '))
            with column_2:
                svg = """ <svg width="29" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="323" y="79" width="29" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-323 -79)"><path d="M102.292 91.6051C102.292 91.6051 102.831 89.8359 111.221 89.8359 120.549 89.8359 120.01 91.6051 120.01 91.6051L120.01 107.574C120.01 107.574 120.523 109.349 111.221 109.349 102.831 109.349 102.292 107.574 102.292 107.574Z" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 94.7128C102.292 94.7128 102.831 96.4872 111.221 96.4872 120.549 96.4872 120.01 94.7128 120.01 94.7128" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 97.9487C102.292 97.9487 102.831 99.718 111.221 99.718 120.549 99.718 120 97.9487 120 97.9487" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 101.19C102.292 101.19 102.831 102.964 111.221 102.964 120.549 102.964 120.01 101.19 120.01 101.19" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 104.385C102.292 104.385 102.831 106.154 111.221 106.154 120.549 106.154 120.01 104.385 120.01 104.385" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M120 91.6051C120 91.6051 120.513 93.3795 111.21 93.3795 102.821 93.3795 102.282 91.6051 102.282 91.6051" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M19.0769 16.7436C19.0769 21.9407 14.8638 26.1538 9.66667 26.1538 4.46953 26.1538 0.25641 21.9407 0.25641 16.7436 0.25641 11.5465 4.46953 7.33333 9.66667 7.33333 14.8638 7.33333 19.0769 11.5464 19.0769 16.7436Z" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M9.66667 11.6 11.4564 15.9231 15.1487 14.5744 14.4513 19.3231 4.88205 19.3231 4.18462 14.5744 7.87692 15.9231 9.66667 11.6Z" stroke="#005173" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M4.86667 20.3846 14.5231 20.3846" stroke="#005173" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.02056 323 79.0234)"/></g></svg>"""
                self.__render_svg_metric(svg, f"Reduserte utgifter til oppvarming", f"{self.__rounding_costs_to_int(short_term_savings):,} {short_term_savings_unit}".replace(',', ' ')) 
            with column_3:
                svg = """ <svg width="29" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="323" y="79" width="29" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-323 -79)"><path d="M102.292 91.6051C102.292 91.6051 102.831 89.8359 111.221 89.8359 120.549 89.8359 120.01 91.6051 120.01 91.6051L120.01 107.574C120.01 107.574 120.523 109.349 111.221 109.349 102.831 109.349 102.292 107.574 102.292 107.574Z" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 94.7128C102.292 94.7128 102.831 96.4872 111.221 96.4872 120.549 96.4872 120.01 94.7128 120.01 94.7128" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 97.9487C102.292 97.9487 102.831 99.718 111.221 99.718 120.549 99.718 120 97.9487 120 97.9487" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 101.19C102.292 101.19 102.831 102.964 111.221 102.964 120.549 102.964 120.01 101.19 120.01 101.19" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 104.385C102.292 104.385 102.831 106.154 111.221 106.154 120.549 106.154 120.01 104.385 120.01 104.385" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M120 91.6051C120 91.6051 120.513 93.3795 111.21 93.3795 102.821 93.3795 102.282 91.6051 102.282 91.6051" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M19.0769 16.7436C19.0769 21.9407 14.8638 26.1538 9.66667 26.1538 4.46953 26.1538 0.25641 21.9407 0.25641 16.7436 0.25641 11.5465 4.46953 7.33333 9.66667 7.33333 14.8638 7.33333 19.0769 11.5464 19.0769 16.7436Z" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M9.66667 11.6 11.4564 15.9231 15.1487 14.5744 14.4513 19.3231 4.88205 19.3231 4.18462 14.5744 7.87692 15.9231 9.66667 11.6Z" stroke="#005173" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M4.86667 20.3846 14.5231 20.3846" stroke="#005173" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.02056 323 79.0234)"/></g></svg>"""
                self.__render_svg_metric(svg, f"Samlet besparelse etter {self.BOREHOLE_SIMULATION_YEARS} år", f"{self.__rounding_costs_to_int(long_term_savings):,} {long_term_savings_unit}".replace(',', ' ')) 
           
        with st.container():
            st.write("**Lønnsomhet**")
            tab1, tab2 = st.tabs(["Direktekjøp", "Lånefinansiert"])
            with tab1:
                # direktekjøp
                __show_metrics(investment = self.investment_cost, short_term_savings = self.short_term_investment, long_term_savings = self.long_term_investment)
                #st.success(f"Bergvarme sparer deg for  {self.savings_operation_cost_lifetime - self.investment_cost:,} kr etter 20 år! ".replace(",", " "), icon = "💰")
                with st.expander("Mer om lønnsomhet med bergvarme", expanded = True): 
                    st.write(""" Estimert investeringskostnad omfatter en komplett installasjon av et 
                    bergvarmeanlegg, inkludert energibrønn, varmepumpe og installasjon. Denne er antatt fordelt slik: """)
                    
                    if self.waterborne_heat_cost > 0:
                        st.write(f"- • Vannbåren varme: {self.__rounding_costs_to_int(self.waterborne_heat_cost):,} kr".replace(",", " "))
                    st.write(f"- • Energibrønn: {self.__rounding_costs_to_int(self.geoenergy_investment_cost):,} kr".replace(",", " "))
                    st.write(f"- • Væske-vann-varmepumpe: {self.__rounding_costs_to_int(self.heatpump_cost):,} kr".replace(",", " "))
                    st.write("")
                    st.write("""**Merk at dette er et estimat. Endelig pris fastsettes av leverandøren.**""")          
                          
                    st.plotly_chart(figure_or_data = self.__plot_costs_investment(), use_container_width=True, )

            with tab2:
                # lån
                if self.short_term_loan > 0:
                    __show_metrics(investment = 0, short_term_savings = self.short_term_loan, long_term_savings = self.long_term_loan, investment_text = "Investeringskostnad (lånefinasiert)")
                    #st.success(f"""Bergvarme sparer deg for {(self.loan_savings_monthly - self.loan_cost_monthly) * 12 * 20:,} kr etter 20 år! """.replace(",", " "), icon = "💰")
                    with st.expander("Mer om lønnsomhet med bergvarme"):                       
                        st.write(f""" Mange banker har begynt å tilby billigere bygglån hvis byggen regnes som miljøvennlig; et såkalt grønt bygglån. 
                        En oppgradering til bergvarme kan kvalifisere byggen din til et slikt lån. """)

                        st.write(f""" Søylediagrammene viser årlige kostnader til oppvarming hvis investeringen finansieres 
                        av et grønt lån. Her har vi forutsatt at investeringen nedbetales i 
                        løpet av {self.BOREHOLE_SIMULATION_YEARS} år med effektiv rente på {round(self.INTEREST,2)} % """)
                        st.plotly_chart(figure_or_data = self.__plot_costs_loan(), use_container_width=True, )
                else:
                    st.warning("Lånefinansiering er ikke lønnsomt med oppgitte forutsetninger. Endre forutsetningene for beregningene ved å trykke på knappen øverst i venstre hjørne.", icon="⚠️")
            
            
    def streamlit_results(self):
        st.header("Resultater for ditt bygg")
        self.sizing_results()
        self.environmental_results()
        self.cost_results()
        
    def streamlit_hide_fullscreen_view(self):
        hide_img_fs = '''
            <style>
            button[title="View fullscreen"]{
                visibility: hidden;}
            </style>
            '''
        st.markdown(hide_img_fs, unsafe_allow_html=True)
        
    def novap(self):
        st.header("Veien videre")
        st.write(""" Sjekk hvilke entreprenører som kan montere varmepumpe og bore energibrønn hos deg - riktig og trygt!
                 Bruk en entreprenør godkjent av Varmepumpeforeningen. """)
        
        st.write(""" Vi råder deg også til å:""")
        st.write("- • Få entreprenør til å komme på befaring")
        st.write("- • Vurdere både pris og kvalitet ")
        st.write("- • Skrive kontrakt før arbeidet starter")
        
        # Til NOVAP
        # Standard Base64 Encoding
        data = {}
        data['antall_borehull'] = self.number_of_boreholes
        data['bronndybde'] = self.SIMULATION_BOREHOLE_DEPTH
        data['varmepumpe'] = self.heat_pump_size
        data['oppvarmingsbehov'] = self.__rounding_to_int(np.sum(self.dhw_demand + self.space_heating_demand))
        data['varmtvannsbehov'] = self.__rounding_to_int(np.sum(self.dhw_demand))
        data['romoppvarmingsbehov'] = self.__rounding_to_int(np.sum(self.space_heating_demand))
        data['bygningsareal'] = self.building_area
        data['adresse'] = self.address_name
        data['investeringskostnad'] = self.investment_cost
        json_data = json.dumps(data)      
        encodedBytes = base64.b64encode(json_data.encode("utf-8"))
        encodedStr = str(encodedBytes, "utf-8")

        address_str = self.address_name.split(",")[0]
        address_str_first_char = address_str[0]
        if address_str_first_char.isdigit():
            # gnr/bnr
            address_str = address_str_first_char
        else:
            # vanlig
            address_str = address_str.replace(" ", "+")

        st.markdown(f'<a target="parent" style="background-color: #white;text-decoration: underline;color:black;font-size:2.0rem;border: solid 1px #e5e7eb; border-radius: 15px; text-align: center;padding: 16px 24px;min-height: 60px;display: inline-block;box-sizing: border-box;width: 100%;" href="https://www.varmepumpeinfo.no/forhandler?postnr={self.address_postcode}&adresse={address_str}&type=bergvarme&meta={encodedStr}">Sett i gang - finn en seriøs entreprenør</a>', unsafe_allow_html=True)       
 
    def main(self):
        self.set_streamlit_settings()
        #self.streamlit_hide_fullscreen_view()
        self.streamlit_input_container()
        self.streamlit_calculations()
        # ferdig
        self.progress_bar.progress(100)
        self.streamlit_results()
        #self.novap()
        
if __name__ == '__main__':
    calculator = Calculator()
    calculator.main()
