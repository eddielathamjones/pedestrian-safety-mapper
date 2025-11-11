# 🚶 Pedestrian Safety Mapper - Tucson, AZ

## Overview

Pedestrian Safety Mapper is an open-source web application that visualizes pedestrian fatality data from the Fatality Analysis Reporting System (FARS). Designed for policy makers, transportation advocates, and urban planners, this tool provides interactive, street-level insights into road safety.

**Current Implementation: Tucson, Arizona (1991-2022)**
- 719 pedestrian fatalities analyzed
- 445 incidents with precise GPS coordinates
- Street-level visualization with MapBox GL JS
- Advanced filtering and temporal analysis

![Project Status: MVP Complete](https://img.shields.io/badge/status-MVP%20Complete-green)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

## Project Goals

- Visualize pedestrian fatality data across geographic regions
- Provide interactive, data-driven insights for urban safety planning
- Demonstrate advanced GIS and data analysis techniques
- Support evidence-based transportation policy decisions

## Features ✅

- ✅ **Interactive Street Map**: MapBox GL JS with precise GPS locations for every incident
- ✅ **Advanced Filtering**: Filter by year range, road type, time of day, lighting, and intersection type
- ✅ **Heatmap Visualization**: Toggle density heatmap to identify high-risk corridors
- ✅ **Temporal Analysis**: Interactive charts showing trends by year, hour, day of week
- ✅ **Road Type Breakdown**: Analysis by functional road classification (arterials, collectors, local)
- ✅ **Hot Spot Detection**: Automatically identifies streets with 3+ incidents
- ✅ **Coordinated Views**: Click charts to filter map, click hot spots to zoom to location
- ✅ **Cluster Mode**: Performance-optimized clustering for dense areas
- ✅ **REST API**: Full-featured API with multiple endpoints for data access

## Key Findings for Tucson

- **Alarming Trend**: Fatalities more than doubled from 30 (2018) to 64 (2022)
- **Principal Arterials**: 45% of fatalities occur on principal arterial roads
- **Evening Danger**: Peak danger hours are 6pm-10pm
- **Mid-Block Incidents**: 67% occur away from intersections
- **Dark Conditions**: Majority of fatalities occur during nighttime hours

## Technology Stack

- **Frontend**: 
  - MapBox GL JS
  - D3.js for visualizations
- **Backend**: 
  - Python (Flask/Django)
  - PostgreSQL with PostGIS
- **Data Processing**: 
  - Pandas
  - GeoPandas


## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- MapBox Account (free tier works - [Sign up here](https://www.mapbox.com/signup/))

### Setup Steps

**1. Get Your MapBox Access Token**

- Go to [MapBox Account](https://account.mapbox.com/)
- Copy your default public token (starts with `pk.`)

**2. Configure the Token**

Edit `src/frontend/js/app.js` (line 2):
```javascript
mapboxgl.accessToken = 'YOUR_MAPBOX_TOKEN_HERE';  // Replace with your token
```

**3. Install Python Dependencies**

```bash
pip install -r requirements.txt
```

**4. Run the Application**

```bash
python3 src/backend/app.py
```

**5. Open in Browser**

Navigate to: **http://localhost:5000**

That's it! The data is already processed and ready to visualize.

## 📁 Project Structure

```
pedestrian-safety-mapper/
├── data/
│   ├── raw/               # FARS CSV files by year (1975-2022)
│   └── processed/         # Extracted and filtered Tucson data
│       ├── tucson_pedestrian_fatalities.csv
│       ├── tucson_pedestrian_fatalities.geojson
│       └── tucson_statistics.json
├── src/
│   ├── backend/
│   │   ├── app.py                    # Flask REST API server
│   │   └── extract_tucson_data.py    # ETL pipeline
│   └── frontend/
│       ├── index.html
│       ├── css/styles.css
│       └── js/app.js                 # MapBox + Chart.js application
├── scripts/
│   ├── data_download.py              # Downloads FARS data
│   └── FARS_doc_download.py          # Downloads documentation
└── requirements.txt
```

## 🛠️ API Endpoints

The Flask backend provides comprehensive REST API access:

- `GET /api/incidents` - Get all incidents with optional filtering
  - Query params: `year_start`, `year_end`, `road_type`, `hour_start`, `hour_end`, `lighting`, `intersection_type`
- `GET /api/statistics` - Overall statistics summary
- `GET /api/statistics/temporal` - Temporal breakdown (year, month, hour, day of week)
- `GET /api/statistics/road_types` - Statistics by functional road classification
- `GET /api/statistics/intersections` - Intersection vs mid-block analysis
- `GET /api/statistics/lighting` - Lighting condition breakdown
- `GET /api/hot_spots` - High-risk streets with 3+ incidents
- `GET /api/trends` - Year-over-year trends and 3-year moving averages
- `GET /api/health` - API health check

Example:
```bash
curl "http://localhost:5000/api/incidents?year_start=2020&road_type=Principal%20Arterial%20-%20Other"
```

## 📊 Data Processing

The data has already been processed, but you can re-extract if needed:

```bash
python3 src/backend/extract_tucson_data.py
```

This extracts pedestrian fatality data for Tucson from all FARS years (1991-2022 available).

## Data Sources

- [Fatality Analysis Reporting System (FARS)](https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system) - NHTSA
- 719 pedestrian fatalities in Tucson (1991-2022)
- 445 incidents with precise GPS coordinates

## 🗺️ Features & Usage

### Map Controls

- **Show/Hide Markers**: Toggle incident markers on/off
- **Heatmap Layer**: Toggle density heatmap visualization
- **Cluster Mode**: Enable/disable marker clustering

### Filtering

Combine multiple filters to analyze specific scenarios:
- **Year Range**: Focus on recent trends (e.g., 2018-2022)
- **Time of Day**: Analyze morning commute vs evening hours
- **Road Type**: Compare arterials vs collectors vs local streets
- **Lighting**: Daylight vs dark conditions
- **Location Type**: Intersections vs mid-block

### Hot Spots

The sidebar automatically identifies high-risk streets:
- Streets with 3 or more incidents
- Click any street to zoom to its location
- Reveals dangerous corridors for targeted interventions

## Future Enhancements

- [ ] PostgreSQL + PostGIS database for better performance
- [ ] Time-of-day animation with slider control
- [ ] Before/after intervention analysis
- [ ] Multi-city comparison
- [ ] Crash narrative text analysis
- [ ] Weather data integration
- [ ] Census demographic correlation
- [ ] Export reports as PDF
- [ ] Mobile-responsive improvements

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

### Ways to Contribute
- Reporting bugs
- Suggesting features
- Writing documentation
- Implementing new visualizations

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Contact

Eddie Latham-Jones

## Acknowledgments

- NHTSA for providing FARS data
- Open-source community for supporting critical research tools

---

*Disclaimer: This project is for educational and research purposes. Always consult official sources for critical transportation safety information.*
