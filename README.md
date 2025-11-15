# FARS Multi-Sensory Pedestrian Crash Database

[![Project Status: In Development](https://img.shields.io/badge/status-in%20development-yellow)](https://github.com/eddielathamjones/pedestrian-safety-mapper)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Overview

A comprehensive multi-sensory database system that collects and analyzes environmental data for pedestrian crash locations from FARS (Fatality Analysis Reporting System). Goes beyond visual analysis to include sound, air quality, weather, terrain, demographics, and dozens of other environmental factors.

**Primary Data Sources:**
- 🖼️ Street View Images (Mapillary API)
- 🔊 Sound Data (Aporee.org, modeled traffic noise)
- 🌫️ Air Quality (PurpleAir API)
- 🌤️ Weather (Visual Crossing API)
- 💡 Lighting (City data, NASA VIIRS)

**Additional Data Sources:**
- 🗺️ OpenStreetMap (road network, infrastructure)
- 📊 US Census (demographics, socioeconomics)
- 🚌 GTFS Transit Data, Schools, Terrain, Traffic Counts, Tree Canopy, and many more...

## Project Goals

- Create the most comprehensive pedestrian crash environmental database
- Enable multi-factor risk modeling and pattern detection
- Support evidence-based transportation safety decisions
- Identify environmental justice issues in pedestrian safety
- Provide open-source tools for crash analysis researchers

## Features

- **Multi-Sensory Analysis**: Comprehensive environmental profiling beyond traditional crash analysis
- **Database Schema**: PostgreSQL with PostGIS for 18+ data tables
- **API Integration**: Automated data collection from free public APIs
- **Computer Vision**: Infrastructure detection from street view images
- **Geospatial Analysis**: Advanced spatial queries and hotspot detection
- **Environmental Justice**: Analyze disparities across communities
- **Interactive Visualizations**: Maps, charts, and detailed crash report cards

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+ with PostGIS extension
- 4GB+ RAM recommended

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/eddielathamjones/pedestrian-safety-mapper.git
   cd pedestrian-safety-mapper
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure database**
   ```bash
   # Edit config/database.yaml with your PostgreSQL credentials
   ```

5. **Set up API keys**
   ```bash
   # Copy template and add your API keys
   cp config/api_keys.yaml.template config/api_keys.yaml
   # Get free API keys from:
   # - Mapillary: https://www.mapillary.com/dashboard/developers
   # - PurpleAir: https://www2.purpleair.com/pages/contact-us
   # - Visual Crossing: https://www.visualcrossing.com/
   ```

6. **Initialize database**
   ```bash
   python scripts/01_setup_database.py
   ```

## Database Schema

The database includes 18+ interconnected tables organized by data type:

**Core Environmental Data:**
- `crashes` - Main crash records with location, timing, and victim information
- `streetview_images` - Mapillary/Google images with CV analysis results
- `sound_data` - Ambient sound recordings and acoustic measurements
- `air_quality` - PM2.5, PM10, AQI from PurpleAir sensors
- `weather` - Temperature, precipitation, visibility, wind
- `lighting` - Street lights, nighttime brightness, dawn/dusk times
- `analysis_results` - Computer vision outputs and composite scores

**Infrastructure & Built Environment:**
- `osm_infrastructure` - Road characteristics from OpenStreetMap
- `traffic_data` - AADT, speed limits, pedestrian/bike counts
- `land_use` - Zoning, density, tree canopy, activity generators
- `transit_access` - GTFS stops, service frequency, accessibility
- `parking` - On-street parking, restrictions, occupancy
- `terrain` - Elevation, slope, aspect, viewshed analysis

**Demographic & Social Data:**
- `demographics` - Census data, income, employment, transportation modes
- `crime_data` - Safety perception and incident counts
- `schools` - School zones, enrollment, crossing guards

**Temporal Data:**
- `historical_changes` - Infrastructure interventions and timeline
- `special_events` - Festivals, road closures, unusual activity

See [sql/schema.sql](sql/schema.sql) for complete schema and [sql/create_views.sql](sql/create_views.sql) for pre-built analysis views.

## Implementation Phases

### ✅ Phase 1: Foundation (Complete)
- [x] Database schema with 18+ tables
- [x] Configuration system (database, settings, API keys)
- [x] Database connection module with pooling
- [x] Utility functions (geo, time, file operations)
- [x] Setup and initialization scripts

### 🚧 Phase 2: Data Collection (Next)
- [ ] Mapillary street view image downloader
- [ ] PurpleAir air quality collector
- [ ] Visual Crossing weather integration
- [ ] OpenStreetMap data extractor
- [ ] Census/ACS demographics collector
- [ ] GTFS transit data parser

### 📋 Phase 3: Analysis
- [ ] Computer vision for infrastructure detection
- [ ] Audio analysis pipeline
- [ ] Multi-sensory scoring algorithms
- [ ] Environmental justice metrics
- [ ] Risk factor identification

### 📋 Phase 4: Visualization
- [ ] Interactive multi-layer crash maps
- [ ] Individual crash report cards
- [ ] Statistical dashboards
- [ ] Time-series animations
- [ ] Export functionality (CSV, GeoJSON, reports)

## Example Usage

See [sql/example_queries.sql](sql/example_queries.sql) for dozens of analysis examples:

```sql
-- Find crashes with multiple environmental stressors
SELECT crash_id, intersection, city, risk_factor_count
FROM vw_high_risk_crashes
WHERE risk_factor_count >= 3
ORDER BY environmental_stress_score DESC;

-- Environmental justice analysis by county
SELECT county, avg_pm25, avg_noise_db, no_crosswalk_count, avg_safety_score
FROM vw_county_environmental_summary
ORDER BY crash_count DESC;
```

## Contributing

Contributions welcome! Areas needing help:

- **Data Collectors**: Implement API clients for new sources
- **Computer Vision**: Improve infrastructure detection
- **Analysis**: New risk scoring algorithms
- **Visualization**: Interactive dashboards and maps
- **Documentation**: Tutorials and examples

## Data Sources & Credits

This project leverages many free and open data sources:

- [FARS](https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system) - NHTSA
- [Mapillary](https://www.mapillary.com/) - Street view images
- [PurpleAir](https://www.purpleair.com/) - Air quality sensors
- [Visual Crossing](https://www.visualcrossing.com/) - Weather data
- [OpenStreetMap](https://www.openstreetmap.org/) - Infrastructure data
- [US Census Bureau](https://www.census.gov/) - Demographics
- [USGS](https://www.usgs.gov/) - Elevation data

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Contact

**Eddie Latham-Jones**
GitHub: [@eddielathamjones](https://github.com/eddielathamjones)

## Acknowledgments

- NHTSA for FARS data
- Mapillary community for street-level imagery
- PurpleAir sensor network operators
- OpenStreetMap contributors
- Open-source GIS and data science communities

---

**Disclaimer**: This project is for research and educational purposes. Always consult official sources for critical transportation safety information.
