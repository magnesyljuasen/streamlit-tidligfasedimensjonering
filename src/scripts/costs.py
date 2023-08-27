import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import datetime

from src.scripts.utils import render_svg, hour_to_month, month_to_hour


class Costs:
    def __init__(self, payment_time, interest):
        self.payment_time = payment_time
        self.interest = interest

    def calculate_investment (self, heat_pump_size, meter, depth_to_bedrock):
        #heat_pump_price = 141000
        if heat_pump_size > 12:
            heat_pump_price = int(heat_pump_price + (heat_pump_size - 12) * 12000)
        heat_pump_price = 12000 * heat_pump_size
        
        #graving_pris = 30000
        #rigg_pris = 15000
        #etablering_pris = 3500
        #odex_sko_pris = 575
        #bunnlodd_pris = 1000
        #lokk_pris = 700
        #odex_i_losmasser_pris = 700  # per meter
        #fjellboring_pris = 170  # per meter
        #kollektor_pris = 90  # per meter

        #kollektor = (meter - 1) * kollektor_pris
        #boring = ((meter - depth_to_bedrock) * fjellboring_pris) + (depth_to_bedrock * odex_i_losmasser_pris)
        #boring_faste_kostnader = etablering_pris + odex_sko_pris + bunnlodd_pris + lokk_pris + rigg_pris + graving_pris

        #energibronn_pris = int(kollektor) + int(boring) + int(boring_faste_kostnader)
        energibronn_pris = meter * 600
        komplett_pris = energibronn_pris + heat_pump_price
        self.investment = int(komplett_pris)

    def adjust(self):
        with st.form("5"):
            investment = self.investment
            self.investment = st.number_input("Juster investeringskostnad [kr]", 
            min_value = 10000, value = int(round(investment,-1)), 
            max_value = 1000000, step = 5000)
            self.interest = st.number_input("Juster effektiv rente [%]", value = 1.0, min_value = 0.0, max_value = 20.0, step = 0.1)
            submitted = st.form_submit_button("Oppdater")

    def _is_weekend_or_holiday(self, day_number):
        # Convert day number to a date object
        year = datetime.datetime.now().year  # Get the current year
        date = datetime.datetime(year, 1, 1) + datetime.timedelta(day_number - 1)

        # Check if the date is a weekend (Saturday or Sunday)
        if date.weekday() >= 5:
            return "helg"

        # Check if the date is a holiday in the Norwegian calendar
        norwegian_holidays = [
            (1, 1),   # New Year's Day
            (5, 1),   # Labor Day
            (5, 17),  # Constitution Day
            (12, 25), # Christmas Day
            (12, 26)  # Boxing Day
        ]
        
        if (date.month, date.day) in norwegian_holidays:
            return "helg"

        # If neither weekend nor holiday, consider it a regular weekday
        return "ukedag"

    def _elcost(self, energy_arr, elprice_arr):
        elprice = elprice_arr
        #-- detaljert på strømpris
        if type(elprice) != float:
            fast_gebyr_arr = np.full(8760, 49/8760) # kr
            spotpris_arr = energy_arr * elprice # kr
            pslag_arr = energy_arr * (1/100) # kr
            forbruksavgift_arr = energy_arr * (15.41/100) # kr
            enova_avgift_arr = energy_arr * (1/100) # kr
            kapasitetsledd, energiledd_arr = self._nettleie(energy_arr) # kr
            kapasitetsledd_arr = month_to_hour(kapasitetsledd) # kr
            
            #self.elprice_df = pd.DataFrame({
            #    'Gebyr spotpris': fast_gebyr_arr,
            #    'Spotpris': spotpris_arr,
            #    'Påslag': pslag_arr,
            #    'Forbruksavgift': forbruksavgift_arr,
            #    'Enova': enova_avgift_arr,
            #    'Kapasitetsledd': kapasitetsledd_arr,
            #    'Energiledd': energiledd_arr
            #})
            el_cost = (fast_gebyr_arr + spotpris_arr + pslag_arr + forbruksavgift_arr + enova_avgift_arr + kapasitetsledd_arr + energiledd_arr)
            self.elprice_arr = el_cost/energy_arr
            return el_cost
        else:
            #self.elprice_df = pd.DataFrame({"Stømpris" : np.full(8760,self.elprice_arr).flatten()})
            el_cost = elprice * energy_arr
            self.elprice_arr = np.full(8760,elprice)
            return el_cost
           
    def _nettleie(self, energy_arr):
        max_value = 0
        max_value_list = []
        day = 0
        kapasitetsledd_mapping = {
            1 : 130,
            2 : 190,
            3 : 280,
            4 : 375,
            5 : 470,
            6 : 565,
            7 : 1250,
            8 : 1720,
            9 : 2190,
            10 : 4180
        }
        energiledd_day = 35.20/100 #kr/kWh
        energliedd_night = 28.95/100 #kr/kWh
        state = "night"
        energiledd_arr = []
        for i, new_max_value in enumerate(energy_arr):
            # finne state
            if (i % 6) == 0:
                state = "day"
            if (i % 22) == 0:
                state = "night"
            # energiledd
            if state == "night":
                energiledd_arr.append(new_max_value * energliedd_night)
            elif state == "helg":
                energiledd_arr.append(new_max_value * energliedd_night)
            elif state == "day":
                energiledd_arr.append(new_max_value * energiledd_day)
            # kapasitetsledd
            if new_max_value > max_value:
                max_value = new_max_value
            if i % 24 == 0:
                # energliedd
                day_type = self._is_weekend_or_holiday(day)
                if day_type == "helg":
                    state = "night"
                if day_type == "ukedag":
                    state = "day"
                # kapasitetsledd
                max_value_list.append(max_value)
                max_value = 0
                day = day + 1
                if day == 31:
                    max_jan = float(round(np.mean(np.sort(max_value_list)[::-1][:3]),2))
                    max_value_list = []
                if day == 31 + 28:
                    max_feb = float(round(np.mean(np.sort(max_value_list)[::-1][:3]),2))
                    max_value_list = []
                if day == 31 + 28 + 31:
                    max_mar = float(round(np.mean(np.sort(max_value_list)[::-1][:3]),2))
                    max_value_list = []
                if day == 31 + 28 + 31 + 30:
                    max_apr = float(round(np.mean(np.sort(max_value_list)[::-1][:3]),2))
                    max_value_list = []
                if day == 31 + 28 + 31 + 30 + 31:
                    max_may = float(round(np.mean(np.sort(max_value_list)[::-1][:3]),2))
                    max_value_list = []
                if day == 31 + 28 + 31 + 30 + 31 + 30:
                    max_jun = float(round(np.mean(np.sort(max_value_list)[::-1][:3]),2))
                    max_value_list = []
                if day == 31 + 28 + 31 + 30 + 31 + 30 + 31:
                    max_jul = float(round(np.mean(np.sort(max_value_list)[::-1][:3]),2))
                    max_value_list = []
                if day == 31 + 28 + 31 + 30 + 31 + 30 + 31 + 31:
                    max_aug = float(round(np.mean(np.sort(max_value_list)[::-1][:3]),2))
                    max_value_list = []
                if day == 31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30:
                    max_sep = float(round(np.mean(np.sort(max_value_list)[::-1][:3]),2))
                    max_value_list = []
                if day == 31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31:
                    max_oct = float(round(np.mean(np.sort(max_value_list)[::-1][:3]),2))
                    max_value_list = []
                if day == 31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30:
                    max_nov = float(round(np.mean(np.sort(max_value_list)[::-1][:3]),2))
                    max_value_list = []
                if day == 31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30 + 31:
                    max_dec = float(round(np.mean(np.sort(max_value_list)[::-1][:3]),2))
                    max_value_list = []
        max_array = [max_jan, max_feb, max_mar, max_apr, max_may, max_jun, max_jul, max_aug, max_sep, max_oct, max_nov, max_dec]
        kapasitestledd_arr = []
        for i, mnd_max in enumerate(max_array):
            if mnd_max < 2:
                kapasitestledd_arr.append(kapasitetsledd_mapping[1])
            if mnd_max > 2 and mnd_max < 5:
                kapasitestledd_arr.append(kapasitetsledd_mapping[2])
            if mnd_max > 5 and mnd_max < 10:
                kapasitestledd_arr.append(kapasitetsledd_mapping[3])
            if mnd_max > 10 and mnd_max < 15:
                kapasitestledd_arr.append(kapasitetsledd_mapping[4])
            if mnd_max > 15 and mnd_max < 20:
                kapasitestledd_arr.append(kapasitetsledd_mapping[5])
            if mnd_max > 20 and mnd_max < 25:
                kapasitestledd_arr.append(kapasitetsledd_mapping[6])
            if mnd_max > 25 and mnd_max < 50:
                kapasitestledd_arr.append(kapasitetsledd_mapping[7])
            if mnd_max > 50 and mnd_max < 75:
                kapasitestledd_arr.append(kapasitetsledd_mapping[8])
            if mnd_max > 75 and mnd_max < 100:
                kapasitestledd_arr.append(kapasitetsledd_mapping[9])
            if mnd_max > 100:
                kapasitestledd_arr.append(kapasitetsledd_mapping[10])
        return kapasitestledd_arr, energiledd_arr

    def calculate_monthly_costs(self, energy_arr, compressor_arr, peak_arr, elprice_arr, investment):
        self.elprice_arr = elprice_arr
        instalment = 0
        if investment != 0:
            if self.interest < 0.50000000000000000:
                monthly_antall = self.payment_time * 12
                monthly_rente = 0
            else:
                monthly_antall = self.payment_time * 12
                monthly_rente = (self.interest/100) / 12
            if monthly_rente > 0:
                instalment = investment / ((1 - (1 / (1 + monthly_rente) ** monthly_antall)) / monthly_rente)
            else:
                instalment = investment / monthly_antall

        el_cost_hourly = self._elcost(energy_arr, elprice_arr)
        gshp_cost_hourly = self._elcost(compressor_arr + peak_arr, elprice_arr)

        self.el_cost_monthly = np.array(hour_to_month(el_cost_hourly.flatten()))
        self.gshp_cost_monthly = np.array(hour_to_month(gshp_cost_hourly)) + instalment

        self.el_cost_sum = np.sum(self.el_cost_monthly)
        self.gshp_cost_sum = np.sum(self.gshp_cost_monthly)
        self.savings_sum = self.el_cost_sum - self.gshp_cost_sum

    def plot(self, kostnad):
        st.write("**Sammenligning**")
        gshp_text_1 = "Bergvarme"        
        gshp_text_2 = f"{kostnad}: " + str(int(round(self.gshp_cost_sum, -1))) + " kr/år"
        el_text_1 = "Elektrisk oppvarming"
        el_text_2 = f"{kostnad}: " + str(int(round(self.el_cost_sum, -1))) + " kr/år"
        
        months = ['jan', 'feb', 'mar', 'apr', 'mai', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'des']
        wide_form = pd.DataFrame({
            'Måneder' : months,
            gshp_text_1 : self.gshp_cost_monthly, 
            el_text_1 : self.el_cost_monthly})

        c1 = alt.Chart(wide_form).transform_fold(
            [gshp_text_1, el_text_1],
            as_=['key', 'Kostnader (kr)']).mark_bar(opacity=1).encode(
                x=alt.X('Måneder:N', sort=months, title=None),
                y=alt.Y('Kostnader (kr):Q',stack=None),
                color=alt.Color('key:N', scale=alt.Scale(domain=[gshp_text_1], 
                range=['#48a23f']), legend=alt.Legend(orient='top', 
                direction='vertical', title=gshp_text_2))).configure_view(strokeWidth=0)

        c2 = alt.Chart(wide_form).transform_fold(
            [gshp_text_1, el_text_1],
            as_=['key', 'Kostnader (kr)']).mark_bar(opacity=1).encode(
                x=alt.X('Måneder:N', sort=months, title=None),
                y=alt.Y('Kostnader (kr):Q',stack=None, title=None),
                color=alt.Color('key:N', scale=alt.Scale(domain=[el_text_1], 
                range=['#880808']), legend=alt.Legend(orient='top', 
                direction='vertical', title=el_text_2))).configure_view(strokeWidth=0)

        col1, col2 = st.columns(2)
        with col1:
            st.altair_chart(c1, use_container_width=True)  
        with col2:
            st.altair_chart(c2, use_container_width=True) 
    
    def plot_elprice(self):
        st.write("**Forutsatt strømpris**")
        st.write(f"Gjennomsnittlig strømpris inkl. nettleie samt skatter og avgifter (uten strømstøtte): {round(float(np.mean(self.elprice_arr)),2)} kr/kWh") 
        df = pd.DataFrame({
            'Timer i ett år' : np.array(range(0, len(self.elprice_arr))),
            'Strømpris (kr/kWh)' : self.elprice_arr})
        c = alt.Chart(df).mark_area().encode(
                x=alt.X('Timer i ett år', scale=alt.Scale(domain=[0,8760])),
                y=alt.Y('Strømpris (kr/kWh)'),
                color=alt.value('#005173')).configure_view(strokeWidth=0)
                #legend = alt.Legend(title='Strømpris (kr/kWh)', orient='top', values=[3.22]))
        st.altair_chart(c, use_container_width=True)

    def operation_show(self):
        st.write(""" Investeringskostnaden omfatter en komplett installasjon av et 
        bergvarmeanlegg, inkludert energibrønn, varmepumpe og installasjon. 
        Merk at dette er et estimat. Endelig pris fastsettes av leverandøren. """)

        st.write(""" Investeringskostnaden dekker ikke installasjon av vannbåren varme i boligen. 
        Søylediagrammene viser årlige driftskostnader med bergvarme 
        sammenlignet med elektrisk oppvarming. """)
        
    def operation_show_after(self):
        investment = int(round(self.investment, -1))
        operation_saving = int(round(self.savings_sum, -1))
        total_saving = int(round(self.savings_sum*20 - self.investment,-1))
        self.total_saving = total_saving
        c1, c2, c3 = st.columns(3)
        with c1:
            svg = """ <svg width="26" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="369" y="79" width="26" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-369 -79)"><path d="M25.4011 12.9974C25.4011 19.8478 19.8478 25.4011 12.9974 25.4011 6.14699 25.4011 0.593654 19.8478 0.593654 12.9974 0.593654 6.14699 6.14699 0.593654 12.9974 0.593654 19.8478 0.593654 25.4011 6.14699 25.4011 12.9974Z" stroke="#005173" stroke-width="0.757136" stroke-miterlimit="10" fill="#fff" transform="matrix(1 0 0 1.03846 369 79)"/><path d="M16.7905 6.98727 11.8101 19.0075 11.6997 19.0075 9.20954 12.9974" stroke="#005173" stroke-width="0.757136" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.03846 369 79)"/></g></svg>"""
            render_svg(svg, "Estimert investeringskostnad", f"{investment:,} kr".replace(',', ' '))
            #st.metric(label="Estimert investeringskostnad", value= f"{investment:,} kr".replace(',', ' '))
        with c2:
            svg = """ <svg width="29" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="323" y="79" width="29" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-323 -79)"><path d="M102.292 91.6051C102.292 91.6051 102.831 89.8359 111.221 89.8359 120.549 89.8359 120.01 91.6051 120.01 91.6051L120.01 107.574C120.01 107.574 120.523 109.349 111.221 109.349 102.831 109.349 102.292 107.574 102.292 107.574Z" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 94.7128C102.292 94.7128 102.831 96.4872 111.221 96.4872 120.549 96.4872 120.01 94.7128 120.01 94.7128" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 97.9487C102.292 97.9487 102.831 99.718 111.221 99.718 120.549 99.718 120 97.9487 120 97.9487" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 101.19C102.292 101.19 102.831 102.964 111.221 102.964 120.549 102.964 120.01 101.19 120.01 101.19" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 104.385C102.292 104.385 102.831 106.154 111.221 106.154 120.549 106.154 120.01 104.385 120.01 104.385" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M120 91.6051C120 91.6051 120.513 93.3795 111.21 93.3795 102.821 93.3795 102.282 91.6051 102.282 91.6051" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M19.0769 16.7436C19.0769 21.9407 14.8638 26.1538 9.66667 26.1538 4.46953 26.1538 0.25641 21.9407 0.25641 16.7436 0.25641 11.5465 4.46953 7.33333 9.66667 7.33333 14.8638 7.33333 19.0769 11.5464 19.0769 16.7436Z" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M9.66667 11.6 11.4564 15.9231 15.1487 14.5744 14.4513 19.3231 4.88205 19.3231 4.18462 14.5744 7.87692 15.9231 9.66667 11.6Z" stroke="#005173" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M4.86667 20.3846 14.5231 20.3846" stroke="#005173" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.02056 323 79.0234)"/></g></svg>"""
            render_svg(svg, "Reduserte utgifter til oppvarming", f"{operation_saving:,} kr/år".replace(',', ' '))
            #st.metric(label="Reduserte utgifter til oppvarming", value= f"{operation_saving:,} kr/år".replace(',', ' '))
        with c3:
            svg = """ <svg width="29" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="323" y="79" width="29" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-323 -79)"><path d="M102.292 91.6051C102.292 91.6051 102.831 89.8359 111.221 89.8359 120.549 89.8359 120.01 91.6051 120.01 91.6051L120.01 107.574C120.01 107.574 120.523 109.349 111.221 109.349 102.831 109.349 102.292 107.574 102.292 107.574Z" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 94.7128C102.292 94.7128 102.831 96.4872 111.221 96.4872 120.549 96.4872 120.01 94.7128 120.01 94.7128" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 97.9487C102.292 97.9487 102.831 99.718 111.221 99.718 120.549 99.718 120 97.9487 120 97.9487" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 101.19C102.292 101.19 102.831 102.964 111.221 102.964 120.549 102.964 120.01 101.19 120.01 101.19" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 104.385C102.292 104.385 102.831 106.154 111.221 106.154 120.549 106.154 120.01 104.385 120.01 104.385" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M120 91.6051C120 91.6051 120.513 93.3795 111.21 93.3795 102.821 93.3795 102.282 91.6051 102.282 91.6051" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M19.0769 16.7436C19.0769 21.9407 14.8638 26.1538 9.66667 26.1538 4.46953 26.1538 0.25641 21.9407 0.25641 16.7436 0.25641 11.5465 4.46953 7.33333 9.66667 7.33333 14.8638 7.33333 19.0769 11.5464 19.0769 16.7436Z" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M9.66667 11.6 11.4564 15.9231 15.1487 14.5744 14.4513 19.3231 4.88205 19.3231 4.18462 14.5744 7.87692 15.9231 9.66667 11.6Z" stroke="#005173" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M4.86667 20.3846 14.5231 20.3846" stroke="#005173" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.02056 323 79.0234)"/></g></svg>"""
            render_svg(svg, "Samlet besparelse etter 20 år", f"{total_saving:,} kr".replace(',', ' '))
            #st.metric(label="Samlet besparelse etter 20 år", value = f"{total_saving:,} kr".replace(',', ' '))
             
    def operation_and_investment_show(self):
        investment = int(round(self.investment, -1))
        savings1 = int(round(self.savings_sum, -1))
        savings2 = int(round(self.savings_sum*20, -1))
        c1, c2, c3 = st.columns(3)
        with c1:
            svg = """ <svg width="26" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="369" y="79" width="26" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-369 -79)"><path d="M25.4011 12.9974C25.4011 19.8478 19.8478 25.4011 12.9974 25.4011 6.14699 25.4011 0.593654 19.8478 0.593654 12.9974 0.593654 6.14699 6.14699 0.593654 12.9974 0.593654 19.8478 0.593654 25.4011 6.14699 25.4011 12.9974Z" stroke="#005173" stroke-width="0.757136" stroke-miterlimit="10" fill="#fff" transform="matrix(1 0 0 1.03846 369 79)"/><path d="M16.7905 6.98727 11.8101 19.0075 11.6997 19.0075 9.20954 12.9974" stroke="#005173" stroke-width="0.757136" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.03846 369 79)"/></g></svg>"""
            render_svg(svg, "Investeringskostnad (lånefinansiert)", f"{0:,} kr".replace(',', ' '))
            #st.metric(label="Investeringskostnad", value= f"{0:,} kr".replace(',', ' '))
        with c2:
            svg = """ <svg width="29" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="323" y="79" width="29" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-323 -79)"><path d="M102.292 91.6051C102.292 91.6051 102.831 89.8359 111.221 89.8359 120.549 89.8359 120.01 91.6051 120.01 91.6051L120.01 107.574C120.01 107.574 120.523 109.349 111.221 109.349 102.831 109.349 102.292 107.574 102.292 107.574Z" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 94.7128C102.292 94.7128 102.831 96.4872 111.221 96.4872 120.549 96.4872 120.01 94.7128 120.01 94.7128" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 97.9487C102.292 97.9487 102.831 99.718 111.221 99.718 120.549 99.718 120 97.9487 120 97.9487" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 101.19C102.292 101.19 102.831 102.964 111.221 102.964 120.549 102.964 120.01 101.19 120.01 101.19" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 104.385C102.292 104.385 102.831 106.154 111.221 106.154 120.549 106.154 120.01 104.385 120.01 104.385" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M120 91.6051C120 91.6051 120.513 93.3795 111.21 93.3795 102.821 93.3795 102.282 91.6051 102.282 91.6051" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M19.0769 16.7436C19.0769 21.9407 14.8638 26.1538 9.66667 26.1538 4.46953 26.1538 0.25641 21.9407 0.25641 16.7436 0.25641 11.5465 4.46953 7.33333 9.66667 7.33333 14.8638 7.33333 19.0769 11.5464 19.0769 16.7436Z" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M9.66667 11.6 11.4564 15.9231 15.1487 14.5744 14.4513 19.3231 4.88205 19.3231 4.18462 14.5744 7.87692 15.9231 9.66667 11.6Z" stroke="#005173" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M4.86667 20.3846 14.5231 20.3846" stroke="#005173" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.02056 323 79.0234)"/></g></svg>"""
            render_svg(svg, "Reduserte utgifter til oppvarming", f"{savings1:,} kr/år".replace(',', ' '))
            #st.metric(label="Reduserte utgifter til oppvarming", value= f"{savings1:,} kr/år".replace(',', ' '))
        with c3:
            svg = """ <svg width="29" height="35" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden"><defs><clipPath id="clip0"><rect x="323" y="79" width="29" height="27"/></clipPath></defs><g clip-path="url(#clip0)" transform="translate(-323 -79)"><path d="M102.292 91.6051C102.292 91.6051 102.831 89.8359 111.221 89.8359 120.549 89.8359 120.01 91.6051 120.01 91.6051L120.01 107.574C120.01 107.574 120.523 109.349 111.221 109.349 102.831 109.349 102.292 107.574 102.292 107.574Z" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 94.7128C102.292 94.7128 102.831 96.4872 111.221 96.4872 120.549 96.4872 120.01 94.7128 120.01 94.7128" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 97.9487C102.292 97.9487 102.831 99.718 111.221 99.718 120.549 99.718 120 97.9487 120 97.9487" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 101.19C102.292 101.19 102.831 102.964 111.221 102.964 120.549 102.964 120.01 101.19 120.01 101.19" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M102.292 104.385C102.292 104.385 102.831 106.154 111.221 106.154 120.549 106.154 120.01 104.385 120.01 104.385" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M120 91.6051C120 91.6051 120.513 93.3795 111.21 93.3795 102.821 93.3795 102.282 91.6051 102.282 91.6051" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 231.728 -12.3976)"/><path d="M19.0769 16.7436C19.0769 21.9407 14.8638 26.1538 9.66667 26.1538 4.46953 26.1538 0.25641 21.9407 0.25641 16.7436 0.25641 11.5465 4.46953 7.33333 9.66667 7.33333 14.8638 7.33333 19.0769 11.5464 19.0769 16.7436Z" stroke="#005173" stroke-width="0.512821" stroke-miterlimit="10" fill="#FFF" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M9.66667 11.6 11.4564 15.9231 15.1487 14.5744 14.4513 19.3231 4.88205 19.3231 4.18462 14.5744 7.87692 15.9231 9.66667 11.6Z" stroke="#005173" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="#FFF" transform="matrix(1 0 0 1.02056 323 79.0234)"/><path d="M4.86667 20.3846 14.5231 20.3846" stroke="#005173" stroke-width="0.512821" stroke-linecap="round" stroke-linejoin="round" fill="none" transform="matrix(1 0 0 1.02056 323 79.0234)"/></g></svg>"""
            render_svg(svg, "Samlet besparelse etter 20 år", f"{savings2:,} kr".replace(',', ' '))
            #st.metric(label="Samlet besparelse etter 20 år", value = f"{savings2:,} kr".replace(',', ' '))

    def operation_and_investment_after(self):

        st.write(f""" Mange banker har begynt å tilby billigere boliglån hvis boligen regnes som miljøvennlig; et såkalt grønt boliglån. 
        En oppgradering til bergvarme kan kvalifisere boligen din til et slikt lån. """)

        st.write(f""" Søylediagrammene viser årlige kostnader til oppvarming hvis investeringen finansieres 
        av et grønt lån. Her har vi forutsatt at investeringen nedbetales i 
        løpet av 20 år med effektiv rente på {round(self.interest,2)} %. Du kan endre betingelsene for lånet 
        i menyen til venstre.""")

    def investment_show(self):
        st.subheader("Investeringskostnad") 
        st.write(""" Investeringskostnaden omfatter en komplett installsjon av 
        bergvarme inkl. varmepumpe, montering og energibrønn. 
        Merk at dette er et estimat, og endelig pris må fastsettes av forhandler. """)
        st.metric(label="Investeringskostnad", value=(str(int(round(self.investment, -1))) + " kr"))

    def profitibality_operation_and_investment(self):
        if self.savings_sum < 0:
            st.warning("Bergvarme er ikke lønnsomt etter 20 år med valgte betingelser for lånefinansiering.", icon="⚠️")
            #st.stop()

    def profitibality_operation(self):
        if self.total_saving < 0:
            st.warning("Bergvarme er ikke lønnsomt etter 20 år med valgte forutsetninger for direkte kjøp.", icon="⚠️")
            st.stop()