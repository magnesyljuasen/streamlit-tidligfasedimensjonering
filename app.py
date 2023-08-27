import streamlit as st
from src.scripts import input, adjust, temperature, demand, geology, geoenergy, environment, costs, electricity
from PIL import Image
import json
import base64
from src.scripts.utils import open_page
import numpy as np

st.set_page_config(
    page_title="Bergvarmekalkulatoren",
    page_icon="📟",
    layout="centered",
    initial_sidebar_state="expanded")

    
with open("src/styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
  
def on_click_function():
    st.session_state.is_expanded = False
    
# adresse og boligareal
if 'is_expanded' not in st.session_state:
    st.session_state.is_expanded = True
container = st.expander("Inndata", expanded=st.session_state.is_expanded)
with container:
    st.title("Bergvarmekalkulatoren")
    st.write(f"Med bergvarmekalkulatoren kan du raskt beregne potensialet for å hente energi fra bakken til din bolig! Start med å skrive inn adresse i søkefeltet under.")
    input_obj = input.Input()
    input_obj.address_input()
    input_obj.area_input()
    input_obj.heat_system_input()

    # hente inn temperatur
    temperature_obj = temperature.Temperature()
    temperature_obj.closest_station(input_obj.lat, input_obj.long)
    temperature_obj.process(temperature_obj.id)
    
    # strømpris
    electricity_obj = electricity.Electricity()
    electricity_obj.find_region(lat=input_obj.lat, long=input_obj.long)

    # beregne energibehov
    demand_obj = demand.Demand()
    demand_obj.from_file(input_obj.area, temperature_obj.id)
    demand_obj.update()
    
    # justere energibehov
    input_obj.demand_input((demand_obj.dhw_arr + demand_obj.space_heating_arr))
    start_calculation = st.button("Start kalkulator for min bolig", on_click=on_click_function)
    if "load_state" not in st.session_state:
        st.session_state.load_state = False

# resultater
my_bar = st.progress(0)
if start_calculation or st.session_state.load_state:
    st.session_state.load_state = True
    #placeholder_1.empty()
    with st.sidebar:
        ## justere forutsetninger
        image = Image.open("src/data/figures/bergvarmekalkulatoren_logo_blå.png")
        st.image(image)
        st.header("Forutsetninger")
        st.write("Her kan du justere forutsetningene som ligger til grunn for beregningene.")
        my_bar.progress(33)
        adjust_obj = adjust.Adjust(input_obj.ELPRICE, electricity_obj.region, demand_obj.space_heating_sum, demand_obj.dhw_sum, input_obj.GROUNDWATER_TABLE, input_obj.DEPTH_TO_BEDROCK, input_obj.THERMAL_CONDUCTIVITY, demand_obj.dhw_arr, demand_obj.space_heating_arr, input_obj.COP, input_obj.COVERAGE)
    # grunnvarmeberegning
    my_bar.progress(66)
    energy_arr = (adjust_obj.dhw_arr + adjust_obj.space_heating_arr)
    geoenergy_obj = geoenergy.Geoenergy(demand_arr=energy_arr, temperature=temperature_obj.average_temperature, cop=adjust_obj.cop, thermal_conductivity=adjust_obj.thermal_conductivity, groundwater_table=adjust_obj.groundwater_table, coverage=adjust_obj.energycoverage, temperature_array=temperature_obj.temperature_arr)
    environment = environment.Environment(option="Norsk-europeisk", co2_constant=adjust_obj.energymix)
    environment.calculate_emissions(energy_arr, 
    geoenergy_obj.energy_gshp_compressor_arr, geoenergy_obj.energy_gshp_peak_arr)
    my_bar.progress(100)
    st.header("Resultater for din bolig")
    with st.container():
        geoenergy_obj.show_results()
    st.write("")
    with st.container():
        st.write("**Strømsparing og utslippskutt med bergvarme**")
        environment.text_after()
        with st.expander("Mer om strømsparing og utslippskutt", expanded=False):
            environment.text_before()
            environment.plot()
    costs = costs.Costs(payment_time=20, interest=adjust_obj.interest)
    costs.calculate_investment(heat_pump_size=geoenergy_obj.heat_pump_size, meter = geoenergy_obj.meter, depth_to_bedrock = adjust_obj.depth_to_bedrock)
    st.write("")
    with st.container():
        st.write("**Lønnsomhet**")
        tab1, tab2 = st.tabs(["Direkte kjøp", "Lånefinansiert"])
        with tab1:
            costs.calculate_monthly_costs(energy_arr = energy_arr, compressor_arr = geoenergy_obj.energy_gshp_compressor_arr, peak_arr = geoenergy_obj.energy_gshp_peak_arr, elprice_arr = adjust_obj.elprice, investment = 0)
            costs.operation_show_after()
            with st.expander("Mer om lønnsomhet med bergvarme"):
                costs.operation_show()
                costs.plot("Driftskostnad")
                costs.plot_elprice()
            costs.profitibality_operation()

        with tab2:
            costs.calculate_monthly_costs(energy_arr = energy_arr, compressor_arr = geoenergy_obj.energy_gshp_compressor_arr, peak_arr = geoenergy_obj.energy_gshp_peak_arr, elprice_arr = adjust_obj.elprice, investment = costs.investment)
            costs.operation_and_investment_show()
            with st.expander("Mer om lønnsomhet med bergvarme"):
                costs.operation_and_investment_after()
                costs.plot("Totalkostnad")
                costs.plot_elprice()
            costs.profitibality_operation_and_investment()
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.write(""" Sjekk hvilke entreprenører som kan montere varmepumpe 
        og bore energibrønn hos deg - riktig og trygt! """)
        st.write(""" Bruk en entreprenør godkjent av Varmepumpeforeningen. """)

    # Standard Base64 Encoding
    data = {}
    data['bronndybde'] = geoenergy_obj.meter
    data['varmepumpe'] = geoenergy_obj.heat_pump_size
    data['oppvarmingsbehov'] = int(adjust_obj.space_heating_sum + adjust_obj.dhw_sum)
    data['boligareal'] = input_obj.area
    json_data = json.dumps(data)      
    encodedBytes = base64.b64encode(json_data.encode("utf-8"))
    encodedStr = str(encodedBytes, "utf-8")

    address_str = input_obj.adr.split(",")[0].split(" ")
    with c2:
        st.write("""Vi råder deg også til å: """)
        st.write("• Få entreprenør til å komme på befaring")
        st.write("• Vurdere både pris og kvalitet ")
        st.write("• Skrive kontrakt før arbeidet starter")
    st.text("")
    #st.button("Sjekk her hvem som kan installere bergvarme i din bolig", on_click=open_page, args=(f"https://www.varmepumpeinfo.no/forhandler?postnr={input_obj.postcode}&adresse={address_str[0]}+{address_str[1]}&type=bergvarme&meta={encodedStr}",))
    st.markdown(f'<a target="parent" style="background-color: #white;text-decoration: underline;color:black;font-size:2.0rem;border: solid 1px #e5e7eb; border-radius: 15px; text-align: center;padding: 16px 24px;min-height: 60px;display: inline-block;box-sizing: border-box;width: 100%;" href="https://www.varmepumpeinfo.no/forhandler?postnr={input_obj.postcode}&adresse={address_str[0]}+{address_str[1]}&type=bergvarme&meta={encodedStr}">Sett i gang - finn en seriøs entreprenør</a>', unsafe_allow_html=True)

