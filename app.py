import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import folium
from folium.plugins import MarkerCluster
from folium.features import DivIcon
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

selected_filter = st.sidebar.selectbox("Select Color Coding", filter_columns, index=filter_columns.index('Number of Practitioners'))

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

# --- ROUTE PLANNER SECTION ---
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
    if 'route_geometry' in st.session_state:
        del st.session_state.route_geometry
    if 'ordered_stops' in st.session_state:
        del st.session_state.ordered_stops
    if 'route_instructions' in st.session_state:
        del st.session_state.route_instructions

# Scrollable container for Selected Addresses
st.markdown("<b>Selected Addresses:</b>", unsafe_allow_html=True)
selected_html = "<ul style='margin: 0; padding-left: 20px;'>"
for addr in st.session_state.route_addresses:
    selected_html += f"<li>{addr}</li>"
selected_html += "</ul>"

st.markdown(
    f"""
    <div style="height: 150px; overflow-y: scroll; border: 1px solid #ddd; padding: 10px; border-radius: 5px; background-color: #f9f9f9; margin-bottom: 20px; color: black;">
        {selected_html}
    </div>
    """, 
    unsafe_allow_html=True
)

ORS_API_KEY = "5b3ce3597851110001cf6248e9c6da4b46ae4c048d4997c54b6f01e1"

if st.button("Generate Route") and st.session_state.route_addresses:
    coords = []
    # Always start at the first selected address
    row = df[df['Full_Address'] == st.session_state.route_addresses[0]].iloc[0]
    start_coord = [row['Longitude'], row['Latitude']]

    for address in st.session_state.route_addresses:
        row = df[df['Full_Address'] == address].iloc[0]
        coords.append([row['Longitude'], row['Latitude']])

    # 1. OPTIMIZATION API
    jobs = [{"id": i + 1, "location": coords[i]} for i in range(len(coords))]
    vehicles = [{"id": 1, "start": start_coord, "profile": "driving-car"}]
    payload = {"jobs": jobs, "vehicles": vehicles}
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    
    r = requests.post("https://api.openrouteservice.org/optimization", json=payload, headers=headers)

    if r.status_code == 200:
        result = r.json()
        steps = result['routes'][0]['steps']
        ordered_coords = []
        
        # Extract ordered coordinates
        for step in steps:
            if step['type'] == 'job':
                ordered_coords.append(coords[step['id'] - 1])
        
        # 2. DIRECTIONS API
        dir_headers = {
            'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
            'Authorization': ORS_API_KEY,
            'Content-Type': 'application/json; charset=utf-8'
        }
        dir_body = {"coordinates": ordered_coords}
        
        r_dir = requests.post('https://api.openrouteservice.org/v2/directions/driving-car/geojson', json=dir_body, headers=dir_headers)
        
        if r_dir.status_code == 200:
            dir_data = r_dir.json()
            
            if 'features' in dir_data and len(dir_data['features']) > 0:
                # 1. Extract Geometry
                geometry_coordinates = dir_data['features'][0]['geometry']['coordinates']
                path_lat_lon = [[coord[1], coord[0]] for coord in geometry_coordinates]
                
                # 2. Extract Text Instructions with Details
                segments = dir_data['features'][0]['properties']['segments']
                instructions = []
                
                for i, segment in enumerate(segments):
                    # Lookup the address for the destination of this segment
                    dest_lon, dest_lat = ordered_coords[i+1]
                    match = df[(df['Latitude'] == dest_lat) & (df['Longitude'] == dest_lon)]
                    
                    # Use the address if found, otherwise fall back to Stop #
                    dest_name = match['Full_Address'].values[0] if not match.empty else f"Stop {i+2}"
                    
                    instructions.append(f"<b>To {dest_name}:</b>")
                    
                    for step in segment['steps']:
                        instr = step.get('instruction', '')
                        name = step.get('name', '')
                        dist = step.get('distance', 0)
                        
                        # Format distance (e.g., 500m or 1.2km)
                        if dist < 1000:
                            dist_str = f"{int(dist)}m"
                        else:
                            dist_str = f"{dist/1000:.1f}km"
                        
                        # If the instruction is generic (doesn't include the street name), append it
                        if name and name != '-' and name not in instr:
                            instr += f" onto {name}"
                            
                        instructions.append(f"- {instr} ({dist_str})")
                
                # Save to Session State
                st.session_state.route_geometry = path_lat_lon
                st.session_state.ordered_stops = ordered_coords
                st.session_state.route_instructions = instructions
                
        else:
            st.error(f"Directions generation failed: {r_dir.status_code}")
    else:
        st.error(f"Optimization failed: {r.status_code}")

# Display Instructions in Scrollable Box
if 'route_instructions' in st.session_state:
    st.markdown("### Turn-by-Turn Directions")
    instructions_html = "<div style='font-family: sans-serif; font-size: 14px;'>"
    for line in st.session_state.route_instructions:
        instructions_html += f"{line}<br>"
    instructions_html += "</div>"
    
    st.markdown(
        f"""
        <div style="height: 200px; overflow-y: scroll; border: 1px solid #ddd; padding: 10px; border-radius: 5px; background-color: #f9f9f9; color: black;">
            {instructions_html}
        </div>
        """, 
        unsafe_allow_html=True
    )

# Render Route on Map
if 'route_geometry' in st.session_state:
    # Draw line
    folium.PolyLine(
        locations=st.session_state.route_geometry,
        color="blue",
        weight=5,
        opacity=0.7,
        tooltip="Optimized Route"
    ).add_to(m)
    
    # Draw Pins
    if 'ordered_stops' in st.session_state:
        for i, stop_coord in enumerate(st.session_state.ordered_stops):
            if i == 0:
                # STARTING POINT: Blue Pin
                folium.Marker(
                    location=[stop_coord[1] + 0.0001, stop_coord[0]],
                    popup="Start Point",
                    icon=folium.Icon(color="blue", icon="play")
                ).add_to(m)
            else:
                # SUBSEQUENT STOPS: Red Pin with Number
                # Using DivIcon to create a custom numbered marker
                folium.Marker(
                    location=[stop_coord[1] + 0.0001, stop_coord[0]],
                    popup=f"Stop #{i+1}",
                    icon=DivIcon(
                        icon_size=(30,30),
                        icon_anchor=(15,15),
                        html=f"""<div style="font-size: 12pt; color: white; background-color: #d32f2f;
                                width: 30px; height: 30px; border-radius: 50%; text-align: center;
                                line-height: 30px; font-weight: bold; border: 2px solid white; 
                                box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">{i+1}</div>"""
                    )
                ).add_to(m)

with st.form(key='my_form'):
    st_folium(m, width=800, height=600)
    st.form_submit_button("")