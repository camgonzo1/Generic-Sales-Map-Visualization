import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import openrouteservice

# Load Data
@st.cache_data
def load_data():
    # Load local CSV file
    df = pd.read_csv('geocoded_addresses_obfuscated.csv')
    df.columns = df.columns.str.strip()
    
    # Full_Name already exists in the obfuscated CSV
    # Replace 0 priority with 5 for better visualization
    df["Priority"] = df["Priority"].replace(0, 5)

    return df


df = load_data()

# Sidebar Filters
not_include_columns = ['City', 'State', 'Address', 'Zip', 'Latitude', 'Longitude', 'Full_Address', 'Full Name']
filter_columns = ["Number of Practitioners"] + sorted([
    col for col in df.columns
    if pd.api.types.is_numeric_dtype(df[col]) and col not in not_include_columns
])

selected_filter = st.sidebar.selectbox("Select Filter", filter_columns, index=filter_columns.index('Number of Practitioners'))

checkbox_columns = sorted([
    col for col in df.columns
    if col not in ['City', 'State', 'Address', 'Zip', 'Latitude', 'Longitude', 'Full_Address']
])


selected_columns = st.sidebar.multiselect("Select Data Columns for Popups", checkbox_columns, default=['First Name', 'Last Name', 'Specialty', 'Priority', 'Total Product1 Scripts 2024', 'Total Product1 Scripts 2025'])

search_query = st.sidebar.text_input("Search (by name or address):")

if 'map_initialized' not in st.session_state:
    st.session_state.map_initialized = False
    st.session_state.map_object = None

with st.sidebar:
    update_map = st.button("Generate Map")


# Filtered Data
# Alignment column has been removed in obfuscated data
grouped_df = df.groupby(["Latitude", "Longitude"]).agg(lambda x: list(x) if len(x) > 1 else [x.iloc[0]]).reset_index()

# Search Coordinates
def find_coordinates(query):
    for _, row in df.iterrows():
        if query.lower() in row['Full_Address'].lower() or query.lower() in row['Full Name'].lower():
            return [row['Latitude'], row['Longitude']]
    return None

search_coords = find_coordinates(search_query) if search_query else None

# Create Map
if selected_filter == 'Number of Practitioners':
    norm = mcolors.Normalize(vmin=-grouped_df['First Name'].apply(len).min()/2,
        vmax=grouped_df['First Name'].apply(len).max())
elif selected_filter == 'Priority':
    norm = mcolors.LogNorm(vmin=1, vmax=5)
else:
    norm = mcolors.Normalize(vmin=-df[selected_filter].max()/2, vmax=df[selected_filter].max())

colormap = plt.colormaps.get_cmap("viridis_r") if selected_filter == 'Priority' else plt.colormaps.get_cmap("viridis")
m = folium.Map(location=[df["Latitude"].mean(), df["Longitude"].mean()], zoom_start=6)
marker_cluster = MarkerCluster().add_to(m)

for _, row in grouped_df.iterrows():
    if selected_filter == 'Number of Practitioners':
        color_value = len(row['First Name'])
    elif selected_filter == 'Priority':
        valid_priorities = [p for p in row['Priority'] if p != -1]
        color_value = min(valid_priorities) if valid_priorities else -1
    else:
        sum(row[selected_filter])
    color = mcolors.to_hex(colormap(norm(color_value)))
    popup_html = f"""
        <div style='position: relative;'>
            <button onclick="navigator.clipboard.writeText('{row['Full_Address'][0]}')"
                    style='position: absolute; top: 0; right: 0;
                           background-color: #4CAF50; color: white; 
                           border: none; padding: 4px 8px; 
                           border-radius: 4px; font-size: 11px; 
                           cursor: pointer;'>
                Copy Address
            </button>
        
            <p style='font-size:12px; margin-top: 22px;'>
                <b style='font-size:12px'>Address:</b> {row['Full_Address'][0]}
            </p>
            <table border='1' style='font-size:12px; border-collapse: collapse; width:100%;'>
                <tr>
        """
    for col in selected_columns:
        popup_html += f"<th style='text-align: center; border:1px solid black;'>{col}</th>"
    popup_html += "</tr>"
    for i in range(len(row["First Name"])):
        popup_html += "<tr>" + "".join(
            f"<td style='text-align:center; border:1px solid black;'>{row[col][i]}</td>" for col in selected_columns
        ) + "</tr>"
    popup_html += "</table>"
    popup = folium.Popup(popup_html, max_width=800)
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=8,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=popup
    ).add_to(m)

# Add Search Marker
if search_coords:
    folium.Marker(location=[search_coords[0] + 0.0005, search_coords[1]], icon=folium.Icon(color="red")).add_to(m)
    m.fit_bounds([[search_coords[0]-0.01, search_coords[1]-0.01], [search_coords[0]+0.01, search_coords[1]+0.01]])

# Route Planner
st.markdown("## Route Planner")

add_address = st.text_input("Enter address to add to route:")

if "route_addresses" not in st.session_state:
    st.session_state.route_addresses = []

if st.button("Add Address"):
    matches = df[df['Full_Address'].str.lower().str.contains(add_address.lower())]
    if not matches.empty:
        for address in matches['Full_Address']:
            if address not in st.session_state.route_addresses:
                st.session_state.route_addresses.append(address)

if st.button("Clear Route"):
    st.session_state.route_addresses = []

st.write("Selected Addresses:")
for addr in st.session_state.route_addresses:
    st.markdown(f"- {addr}")

if st.button("Generate Route") and st.session_state.route_addresses:
    ORS_API_KEY = "5b3ce3597851110001cf6248e9c6da4b46ae4c048d4997c54b6f01e1"
    coords = []
    # Always start at the first selected address
    row = df[df['Full_Address'] == st.session_state.route_addresses[0]].iloc[0]
    start_coord = [row['Longitude'], row['Latitude']]

    for address in st.session_state.route_addresses:
        row = df[df['Full_Address'] == address].iloc[0]
        coords.append([row['Longitude'], row['Latitude']])

    jobs = [{"id": i + 1, "location": coords[i]} for i in range(len(coords))]
    vehicles = [{"id": 1, "start": start_coord, "profile": "driving-car"}]
    payload = {"jobs": jobs, "vehicles": vehicles}
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    r = requests.post("https://api.openrouteservice.org/optimization", json=payload, headers=headers)

    if r.status_code == 200:
        result = r.json()
        steps = result['routes'][0]['steps']
        ordered_coords = []
        for step in steps:
            if step['type'] == 'job':
                ordered_coords.append(coords[step['id'] - 1])
        st.markdown("### Optimized Route:")
        ordered_addresses = []
        for lon, lat in ordered_coords:
            match = df[(df['Latitude'] == lat) & (df['Longitude'] == lon)]
            if not match.empty:
                ordered_addresses.append(match['Full_Address'].values[0])
        
        # Display only the addresses
        for i, address in enumerate(ordered_addresses, 1):
            st.write(f"{i}. {address}")
    else:
        st.error(f"Route generation failed: {r.status_code}")

with st.form(key='my_form'):
    st_folium(m, width=800, height=600)
    st.form_submit_button("")













