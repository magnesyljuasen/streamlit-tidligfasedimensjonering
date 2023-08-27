import streamlit as st
import numpy as np
import altair as alt
import pandas as pd
from src.scripts.utils import render_svg, hour_to_month

class Environment:
    def __init__(self, option, co2_constant):
        self.co2_per_kwh = co2_constant 
        self.selected_option = option

    #i kilogram 
    def calculate_emissions(self, energy_arr, compressor_arr, peak_arr):
        el_co2_hourly = energy_arr * self.co2_per_kwh
        gshp_co2_hourly = (compressor_arr + peak_arr) * self.co2_per_kwh

        self.el_co2_monthly = np.array(hour_to_month(el_co2_hourly))
        self.gshp_co2_monthly = np.array(hour_to_month(gshp_co2_hourly))

        self.el_co2_sum = np.sum(self.el_co2_monthly) * 20
        self.gshp_co2_sum = np.sum(self.gshp_co2_monthly) * 20
        self.savings_co2_sum = (self.el_co2_sum - self.gshp_co2_sum)

        self.gshp = int(round(np.sum(compressor_arr), -1))
        self.el = int(round(np.sum(energy_arr) + np.sum(peak_arr), -1))
        self.savings_power = int(round(self.el - self.gshp, -1))
    
    def plot(self):
        gshp = self.gshp
        el = self.el
        savings = self.savings_power

        #--1
        source = pd.DataFrame({"label" : [f'Strøm: {gshp:,} kWh/år'.replace(","," "), f'Fra grunnen: {(el-gshp):,} kWh/år'.replace(","," ")], 
        "value": [gshp, savings]})
        c1 = alt.Chart(source).mark_arc(innerRadius=35).encode(
            theta=alt.Theta(field="value", type="quantitative"),
            color=alt.Color(field="label", type="nominal", scale=alt.Scale(range=['#48a23f', '#a23f47']), 
            legend=alt.Legend(orient='top', direction='vertical', title=f'Bergvarme'))).configure_view(strokeWidth=0)
            
        #--2
        source = pd.DataFrame({"label" : [f'Strøm: {el:,} kWh/år'.replace(","," ")], 
        "value": [el]})
        c2 = alt.Chart(source).mark_arc(innerRadius=35).encode(
            theta=alt.Theta(field="value", type="quantitative"),
            color=alt.Color(field="label", type="nominal", scale=alt.Scale(range=['#a23f47']), 
            legend=alt.Legend(orient='top', direction='vertical', title='Elektrisk oppvarming'))).configure_view(strokeWidth=0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.altair_chart(c1, use_container_width=True)
        with col2:
            st.altair_chart(c2, use_container_width=True) 
        
    def text_before(self):
        savings = round(self.savings_co2_sum/1000)
        flights = round(savings/(103/1000))

        st.write(f""" Vi har beregnet hvor mye strøm bergvarme vil spare i din bolig sammenlignet med å bruke elektrisk oppvarming.
        Figurene viser at du sparer {self.savings_power:,} kWh i året med bergvarme. 
        Hvis vi tar utgangspunkt i en {self.selected_option.lower()} strømmiks
        vil du i løpet av 20 år spare {savings} tonn CO\u2082. 
        Dette tilsvarer **{flights} flyreiser** mellom Oslo og Trondheim. """.replace(',', ' '))

    def text_after(self):
        savings_co2 = round(self.savings_co2_sum/1000)

        savings = round(self.savings_co2_sum/1000)
        flights = round(savings/(103/1000))

        c1, c2 = st.columns(2)
        with c1:
            svg = """ <svg width="13" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="614" y="84" width="13" height="26"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-614 -84)"><path d="M614.386 99.81 624.228 84.3312C624.464 83.9607 625.036 84.2358 624.89 84.6456L621.224 95.1164C621.14 95.3522 621.32 95.5992 621.572 95.5992L626.3 95.5992C626.603 95.5992 626.777 95.9417 626.597 96.1831L616.458 109.691C616.194 110.039 615.644 109.725 615.823 109.326L619.725 100.456C619.838 100.203 619.63 99.9223 619.355 99.9447L614.74 100.36C614.437 100.388 614.229 100.057 614.392 99.7987Z" stroke="#005173" stroke-width="0.308789" stroke-linecap="round" stroke-miterlimit="10" fill="#FFF"/></g></svg>"""
            render_svg(svg, "Strømbesparelse med bergvarme", f"{self.savings_power:,} kWh/år".replace(',', ' '))
            #st.metric(label="Strømbesparelse med bergvarme", value= f"{self.savings_power:,} kWh/år".replace(',', ' '))
        with c2:
            svg = """ <svg width="26" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="458" y="120" width="26" height="26"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-458 -120)"><path d="M480.21 137.875 480.21 135.438 472.356 129.885 472.356 124.604C472.356 123.548 471.814 122.167 471.001 122.167 470.216 122.167 469.647 123.548 469.647 124.604L469.647 129.885 461.793 135.438 461.793 137.875 469.647 133.948 469.647 139.852 466.939 142.208 466.939 143.833 471.001 142.208 475.064 143.833 475.064 142.208 472.356 139.852 472.356 133.948ZM472 140.261 474.522 142.455 474.522 143.033 471.203 141.706 471.001 141.624 470.8 141.706 467.481 143.033 467.481 142.455 470.003 140.261 470.189 140.099 470.189 133.072 469.403 133.463 462.335 136.999 462.335 135.718 469.96 130.328 470.189 130.166 470.189 124.604C470.189 123.645 470.703 122.708 471.001 122.708 471.341 122.708 471.814 123.664 471.814 124.604L471.814 130.166 472.043 130.328 479.668 135.718 479.668 136.999 472.598 133.463 471.814 133.072 471.814 140.099Z" stroke="#005173" stroke-width="0.270833"/></g></svg>"""
            render_svg(svg, "Utslippskutt med bergvarme etter 20 år", f"{flights:,} sparte flyreiser".replace(',', ' '))
            #st.metric(label="Utslippskutt med bergvarme etter 20 år", value= f"{flights:,} sparte flyreiser".replace(',', ' '))
