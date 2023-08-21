import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px

DATA_URL = "https://data.cityofnewyork.us/api/views/h9gi-nx95/rows.csv"

st.title("Motor Vehicle Collisions in New York City")
st.markdown("This application is a Streamlit dashboard that can be used to "
"analyze motor vehicle collisions in NYC")

@st.cache_data(persist=True)
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows, parse_dates=[['CRASH DATE', 'CRASH TIME']])
    print(data.columns)
    data.dropna(subset=['LATITUDE', 'LONGITUDE'], inplace=True)
    lowercase_underscore = lambda x: str(x).lower().replace(' ', '_')
    data.rename(lowercase_underscore, axis='columns', inplace=True)
    data.rename(columns={
        'crash_date_crash_time': 'date/time', 
        'number_of_persons_injured': 'injured_persons', 
        'number_of_pedestrians_injured': 'injured_pedestrians',
        'number_of_cyclist_injured': 'injured_cyclists',
        'number_of_motorist_injured': 'injured_motorists',
        }, 
    inplace=True)
    return data

data = load_data(100000)
print(data.columns)

st.header("Where are the most people injured in NYC?")
injured_people = st.slider("Number of persons injured in vehicle collisions", 0, 19)
st.map(data.query("injured_persons >= @injured_people")[["latitude", "longitude"]].dropna(how="any"))

st.header("How many collisions occur during a given time of day?")
hour = st.slider("Hour to look at", 0, 23)
original_data = data
data = data[data['date/time'].dt.hour == hour]

st.markdown("Vehicle collisions between %i:00 and %i:00" % (hour, (hour + 1) % 24))
midpoint = (np.average(data["latitude"]), np.average(data["longitude"]))

st.write(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state={
        "latitude": midpoint[0],
        "longitude": midpoint[1],
        "zoom": 11,
        "pitch": 50,
    },
    layers=[
        pdk.Layer(
        "HexagonLayer",
        data=data[['date/time', 'latitude', 'longitude']],
        get_position=["longitude", "latitude"],
        auto_highlight=True,
        radius=100,
        extruded=True,
        pickable=True,
        elevation_scale=4,
        elevation_range=[0, 1000],
        ),
    ],
))

st.subheader("Breakdown by minute between %i:00 and %i:00" % (hour, (hour + 1) % 24))
filtered = data[
    (data['date/time'].dt.hour >= hour) & (data['date/time'].dt.hour < (hour + 1))
]
hist = np.histogram(filtered['date/time'].dt.minute, bins=60, range=(0, 60))[0]
chart_data = pd.DataFrame({"minute": range(60), "crashes": hist})
fig = px.bar(chart_data, x='minute', y='crashes', hover_data=['minute', 'crashes'], height=400)
st.write(fig)

st.header("Top 5 dangerous streets by affected class")
select_class = st.selectbox('Affected class', ['Pedestrians', 'Cyclists', 'Motorists'])

## Improvement: this only takes into account non-fatal injuries. Could update to include all, or
## add ability to filter by injury type.
## Also, probably makes more sense to allow multiple classes at the same time.
if select_class == 'Pedestrians':
    st.write(original_data.query("injured_pedestrians >= 1")[["on_street_name", "injured_pedestrians"]].sort_values(by=['injured_pedestrians'], ascending=False).dropna(how="any")[:5])

elif select_class == 'Cyclists':
    st.write(original_data.query("injured_cyclists >= 1")[["on_street_name", "injured_cyclists"]].sort_values(by=['injured_cyclists'], ascending=False).dropna(how="any")[:5])

else:
    st.write(original_data.query("injured_motorists >= 1")[["on_street_name", "injured_motorists"]].sort_values(by=['injured_motorists'], ascending=False).dropna(how="any")[:5])


if st.checkbox("Show Raw Data", False):
    st.subheader('Raw Data')
    st.write(original_data)

