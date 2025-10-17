# Sales Territory Map & Route Planner

A Streamlit-based interactive mapping application for visualizing sales territories and planning optimized routes. This application uses obfuscated demo data to showcase territory management and route optimization capabilities.

## Features

### 📍 Interactive Map Visualization

The application displays an interactive map with color-coded markers representing different locations in your territory. Key features include:

- **Dynamic Filtering**: Choose from multiple numeric filters to visualize data:
  - Number of Practitioners at each location
  - Priority levels
  - Product sales metrics (2019, 2024, 2025)
  - Script counts and changes year-over-year
  
- **Color-Coded Markers**: Markers are color-coded based on the selected filter using a viridis color scale
  - Priority filter uses reverse coloring (higher priority = warmer colors)
  - Other metrics use standard viridis coloring

- **Clustered Display**: Multiple practitioners at the same location are grouped together for easier visualization

### 🔍 Search Functionality

Search for specific locations or practitioners by:
- Name
- Address

The map will automatically zoom to and highlight the searched location with a red marker.

### 📊 Customizable Popups

Click on any marker to view detailed information in a popup window:

- **Address Display**: Shows the full address with a convenient "Copy Address" button
- **Customizable Data Columns**: Select which data columns to display in the popup table via the sidebar
- **Default columns include**:
  - First Name, Last Name
  - Specialty
  - Priority
  - Product sales and script data

All practitioners at the same location are displayed in a table format for easy comparison.

### 🗺️ Route Planning & Optimization

Plan and optimize multi-stop routes with the built-in route planner:

1. **Add Addresses**: Enter addresses to add them to your route
   - Search by partial address match
   - Multiple addresses can be added

2. **Route Generation**: Click "Generate Route" to create an optimized travel path
   - Uses OpenRouteService API for route optimization
   - Automatically starts at the first selected address
   - Provides turn-by-turn ordered address list

3. **Route Management**:
   - View all selected addresses in a list
   - Clear route to start over

The route optimizer calculates the most efficient path through all selected locations, saving time and reducing travel distance.

## Technical Details

### Built With
- **Streamlit**: Web application framework
- **Folium**: Interactive map visualization
- **Pandas**: Data manipulation
- **OpenRouteService**: Route optimization API
- **Matplotlib**: Color mapping and visualization

### Data
The application uses obfuscated data for demonstration purposes:
- Names are anonymized (FirstName# LastName#)
- Specialties are randomized
- Numeric values are randomized within realistic ranges
- Product references are genericized
- Real geographic coordinates are preserved for accurate mapping

## Installation

Visit hosted application at https://generic-sales-map-visualization.streamlit.app/ or run locally:

1. Clone this repository
2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

## Usage

1. **Select a Filter**: Choose from the dropdown in the sidebar to color-code markers
2. **Customize Popup Data**: Select which columns to display when clicking markers
3. **Search**: Enter a name or address to find specific locations
4. **Plan Routes**: Add addresses and generate optimized routes
5. **Click "Generate Map"**: Update the map with your selected filters

## Demo Data

This application uses obfuscated demonstration data. All personal information, sales figures, and product names have been anonymized while maintaining the functional capabilities of the mapping and routing features.

