# Pedestrian Safety Mapper - Mapbox Visualization

## Overview

This interactive Mapbox visualization displays pedestrian fatality data from the Fatality Analysis Reporting System (FARS). The visualization provides an intuitive way to explore geographic patterns of pedestrian fatalities across the United States.

## Features

- **Interactive Map**: Pan and zoom to explore different regions
- **Data Clustering**: Automatically groups nearby points for better performance and clarity
- **Year Filtering**: Filter data by specific years
- **Detailed Popups**: Click on points to see detailed information about each incident
- **Statistics Panel**: Real-time statistics showing total and visible fatalities
- **Dark Theme**: Easy-to-read dark mode map style
- **Responsive Design**: Works on desktop and mobile devices

## Setup Instructions

### 1. Get a Mapbox Access Token

1. Go to [https://account.mapbox.com/](https://account.mapbox.com/)
2. Sign up for a free account (if you don't have one)
3. Navigate to your [Access Tokens page](https://account.mapbox.com/access-tokens/)
4. Copy your default public token or create a new one

### 2. Configure the Application

1. Copy `config.example.js` to `config.js`:
   ```bash
   cp config.example.js config.js
   ```

2. Edit `config.js` and replace the placeholder with your Mapbox token:
   ```javascript
   const MAPBOX_ACCESS_TOKEN = 'your_actual_token_here';
   ```

### 3. Prepare the Data

You have two options:

#### Option A: Use Sample Data (Quick Start)
The repository includes sample GeoJSON data (`data/pedestrian_fatalities.geojson`) for testing. You can open `index.html` directly in your browser.

#### Option B: Process Real FARS Data

1. Install Python dependencies:
   ```bash
   pip install pandas
   ```

2. Run the data processing script:
   ```bash
   python scripts/process_fars_to_geojson.py
   ```

   This script will:
   - Extract ZIP files in the `data/raw/` directory
   - Parse FARS CSV files (ACCIDENT and PERSON tables)
   - Filter for pedestrian fatalities
   - Extract geographic coordinates
   - Generate a GeoJSON file at `data/pedestrian_fatalities.geojson`

### 4. View the Visualization

#### Option 1: Simple File Server (Python)
```bash
python -m http.server 8000
```
Then open: `http://localhost:8000`

#### Option 2: Node.js Server
```bash
npx http-server
```

#### Option 3: Open Directly
You can also open `index.html` directly in your browser (though some features may work better with a local server).

## Using the Visualization

### Controls

- **Year Filter**: Select a specific year from the dropdown to filter the data
- **Enable Clustering**: Toggle clustering on/off to see individual points vs. grouped clusters
- **Reset View**: Return to the default map view (centered on the US)

### Interacting with the Map

- **Click Clusters**: Click on orange cluster circles to zoom in and see individual points
- **Click Points**: Click on red points to see detailed information about that fatality
- **Pan**: Click and drag to move around the map
- **Zoom**: Use the mouse wheel, pinch gesture, or the +/- buttons

### Statistics Panel

The statistics panel (top right) shows:
- **Total Fatalities**: Total number of fatalities in the dataset
- **Currently Visible**: Number of fatalities visible with current filters
- **Year Range**: The range of years included in the dataset

## Data Structure

The GeoJSON file follows this structure:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [longitude, latitude]
      },
      "properties": {
        "year": 2020,
        "state": 6,
        "case": 60001,
        "county": 37,
        "age": 45,
        "sex": 1,
        "injury_severity": 4
      }
    }
  ]
}
```

## Customization

### Map Style

To change the map style, edit the `style` parameter in `index.html`:

```javascript
const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/dark-v11', // Change this
    center: [-98.5795, 39.8283],
    zoom: 4
});
```

Available styles:
- `mapbox://styles/mapbox/dark-v11` (current)
- `mapbox://styles/mapbox/light-v11`
- `mapbox://styles/mapbox/streets-v12`
- `mapbox://styles/mapbox/outdoors-v12`
- `mapbox://styles/mapbox/satellite-v9`

### Colors

To change the point and cluster colors, modify the paint properties in the layer definitions:

```javascript
paint: {
    'circle-color': '#f44336', // Change this hex color
    ...
}
```

## Troubleshooting

### Map Not Loading

- Verify your Mapbox token is correct in `config.js`
- Check the browser console (F12) for error messages
- Ensure you're serving the files through a web server (not just `file://`)

### No Data Showing

- Verify `data/pedestrian_fatalities.geojson` exists
- Check that the file contains valid GeoJSON
- Look for console errors

### Slow Performance

- Enable clustering (should be on by default)
- Reduce the number of data points by filtering by year
- Consider aggregating data at a county or state level

## Technology Stack

- **Mapbox GL JS v2.15.0**: Interactive map rendering
- **JavaScript (ES6)**: Client-side logic
- **Python 3**: Data processing scripts
- **Pandas**: Data manipulation

## Data Source

Data sourced from the [Fatality Analysis Reporting System (FARS)](https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars) provided by the National Highway Traffic Safety Administration (NHTSA).

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Future Enhancements

Potential improvements:
- [ ] Heat map layer option
- [ ] Time-series animation
- [ ] Statistical charts and graphs
- [ ] Export filtered data
- [ ] Additional filtering options (age groups, time of day, etc.)
- [ ] Compare multiple years side-by-side
- [ ] State/county boundary overlays

## Support

For issues or questions, please open an issue on the GitHub repository.
