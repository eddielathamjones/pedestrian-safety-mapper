# Quick Start Guide - Tucson Pedestrian Safety Mapper

## Step-by-Step Setup (5 minutes)

### 1. Get a Free MapBox Token

MapBox provides free access for up to 50,000 map loads per month - more than enough for this project.

1. Go to **https://www.mapbox.com/signup/**
2. Create a free account (email + password)
3. After logging in, you'll see your **Access Token** on the dashboard
4. Copy the token (it starts with `pk.`)

### 2. Add Your Token to the Application

Open `src/frontend/js/app.js` and find line 2:

```javascript
mapboxgl.accessToken = 'pk.eyJ1IjoiZXhhbXBsZSIsImEiOiJjbGV4YW1wbGUifQ.example';
```

Replace the placeholder with your actual token:

```javascript
mapboxgl.accessToken = 'pk.eyJ1Ijoiam9obmRvZSIsImEiOiJjbHJhYmMxMjMifQ.XYZ...';
```

Save the file.

### 3. Install Python Requirements

Open a terminal in the project root directory and run:

```bash
pip install flask flask-cors
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

### 4. Start the Server

```bash
python3 src/backend/app.py
```

You should see:

```
============================================================
Tucson Pedestrian Safety Mapper - Backend API
============================================================
Data loaded: 445 incidents
Server starting on http://localhost:5000
============================================================
```

### 5. Open in Your Browser

Navigate to:

**http://localhost:5000**

You should see:
- An interactive map of Tucson centered at coordinates (32.22, -110.97)
- Incident markers color-coded by road type
- Filtering controls in the left sidebar
- Charts on the right showing temporal and road type analysis
- Statistics in the header showing 719 total fatalities

## Using the Application

### Basic Exploration

1. **Zoom and Pan**: Use mouse wheel to zoom, click and drag to pan
2. **Click Markers**: Click any incident marker to see details (date, time, location, conditions)
3. **Click Clusters**: Click cluster circles to zoom in and expand

### Filtering Data

1. **Year Range**: Change to `2020` - `2022` to see recent trends
2. **Time of Day**: Enter `18` to `22` to see evening incidents (6pm-10pm)
3. **Road Type**: Select "Principal Arterial - Other" to see major road incidents
4. **Click "Apply Filters"** to update the map and charts

### Analyzing Hot Spots

1. Look at the **High-Risk Streets** panel in the left sidebar
2. Click any street name (e.g., "W VALENCIA RD") to zoom to that location
3. Streets listed have 3 or more incidents

### Map Layers

Toggle these options in the **Map Layers** section:
- **Show Incident Markers**: Turn markers on/off
- **Show Heatmap**: Toggle heat density visualization
- **Cluster Markers**: Enable/disable marker grouping

### Understanding the Charts

- **Temporal Trends**: Line chart showing fatalities by year (note the sharp increase 2018-2022)
- **Time of Day**: Bar chart showing dangerous hours (peak at 6pm-10pm)
- **Road Type Distribution**: Pie chart showing principal arterials account for 45%
- **Lighting Conditions**: Most incidents occur in dark conditions

## Troubleshooting

### "Failed to load map"
- Check that you added your MapBox token correctly
- Verify the token starts with `pk.`
- Make sure you saved the file after editing

### "Error loading data"
- Ensure the Flask server is running (`python3 src/backend/app.py`)
- Check that you're accessing `http://localhost:5000` (not file://)

### "No incidents showing"
- Reset filters by clicking "Reset All"
- Make sure "Show Incident Markers" is checked
- Try zooming out to see the full Tucson area

### Port 5000 already in use
- Another application is using port 5000
- Stop the other application, or edit `src/backend/app.py` line 204 to use a different port:
  ```python
  app.run(debug=True, host='0.0.0.0', port=5001)  # Changed to 5001
  ```

## Data Summary

- **Total Incidents**: 719 pedestrian fatalities (1991-2022)
- **With GPS Coordinates**: 445 incidents (62%)
- **Most Dangerous Year**: 2022 with 64 fatalities
- **Most Dangerous Time**: 6pm-10pm (evening hours)
- **Most Dangerous Roads**: Principal Arterials (major roads)
- **Location Pattern**: 67% occur mid-block (not at intersections)

## Next Steps

- Explore different time periods and road types
- Identify specific high-risk corridors in your neighborhood
- Export findings for Vision Zero initiatives
- Use the API endpoints to build custom analyses

## Need Help?

- Check the main [README.md](README.md) for detailed documentation
- Review API endpoints for programmatic access
- Open an issue on GitHub if you encounter problems

---

**Built for safer streets in Tucson** 🌵
