import streamlit as st
from joblib import load
from decimal import Decimal
import numpy as np
import os
import requests

def generate_business_hour_feature(time_param):
    hour = time_param.hour

    if ((hour > 8) and (hour < 14)) or ((hour > 16) and (hour < 21)):
        hour = 2
        return hour
    elif (hour >=14) and (hour <= 16):
        hour = 1
        return hour
    else: 
        hour = 0
        return hour

def generate_weekend_feature(date_param):
    if date_param.weekday() == 6:
        weekend = 2
    elif date_param.weekday() == 5:
        weekend = 1
    else:
        weekend = 0
    
    return weekend

def generate_report(user_input, price):
    
    # Get the IP address from the environment variable
    IP_ADDRESS = os.environ.get('ENERGYFORECASTAPI_IP')

    # Endpoint URL
    url = f'http://{IP_ADDRESS}/predict-chat'

    # Request payload

    payload = {
        "gen_fossil_brown_coal": user_input[0][0],
        "gen_fossil_gas": user_input[0][1],
        "gen_fossil_hard_coal": user_input[0][2],
        "gen_fossil_oil": user_input[0][3],
        "gen_hydro": user_input[0][4],
        "gen_other_renewable": user_input[0][5],
        "gen_wind_onshore": user_input[0][6],
        "total_load_actual": user_input[0][7],
        "price": price,
        "max_seq_len": 0,
        "max_gen_len": 2048,
        "temperature": 0.2
    }

    # Header
    headers = {'Content-Type': 'application/json'}

    # Perform the request
    response = requests.post(url, json=payload, headers=headers)

    # Check the response
    if response.status_code == 200:
        print("Response:", response.json())
        json_data = response.json()
        report = json_data['results'][0][1]['content']
        return report
    else:
        st.header('Error', divider='rainbow')
        print("Error:", response.text)
        return response.text

def get_forecast_price(user_input):
    model = load('xgb_model.joblib')       
    price = np.float64(model.predict(user_input)[0])
    price = np.around(price, 2)
    return price

st.title("Predicting Energy Pricing")
st.write("This Intelligent App analyzes data on energy consumption and predicts the electricity price for the next hour. It then creates a report summarizing the electricity usage and price.")

with st.form("my_form"):
    generation_fossil_brown_coal_lignite = st.text_input('Generation of electicity from fossil brown coal/lignite (MW)', 582.0)
    generation_fossil_gas = st.text_input('Generation of electicity from fossil gas (MW)', 5537.0)
    generation_fossil_hard_coal = st.text_input('Generation of electicity from hard coal (MW)', 4039.0)
    generation_fossil_oil = st.text_input('Generation of electicity from oil (MW)', 331.0)
    generation_hydro_pumped_storage_consumption = st.text_input('Generation of electricity from hydroelectric power plants (MW)', 454.0)
    generation_other_renewable = st.text_input('Generation of electricity from renewable energy sources (MW)', 97.0)
    generation_wind_onshore = st.text_input('Generation of electricity from onshore wind turbine (MW)', 7556.0)
    total_load_actual = st.text_input('Total electricity demand or consumption', 31648.0)
    date_param = st.date_input("Date", value="today")
    time_param = st.time_input("Time", value="now")

    if date_param:
        weekday = date_param.weekday()
        weekend = generate_weekend_feature(date_param)
        month = date_param.month
    else:
        weekday = 0
        weekend = 0

    if time_param:
        hour = time_param.hour
        business_hour = generate_business_hour_feature(time_param)
    else:
        hour = 0
        business_hour = 0

    submitted = st.form_submit_button("Submit")
    if submitted:
       user_input = [[np.float64(generation_fossil_brown_coal_lignite), np.float64(generation_fossil_gas), 
                      np.float64(generation_fossil_hard_coal), np.float64(generation_fossil_oil),
                      np.float64(generation_hydro_pumped_storage_consumption), np.float64(generation_other_renewable),
                      np.float64(generation_wind_onshore), np.float64(total_load_actual), hour, weekday, month, business_hour,
                      weekend]]
       
       price = get_forecast_price(user_input)
       
       st.header('Forecast Price', divider='rainbow')
       st.write(f"{str(round(price, 2))} EUR/MW")
    
       report = generate_report(user_input, price)
       
       st.header('Analysis', divider='rainbow')
       st.write(report)