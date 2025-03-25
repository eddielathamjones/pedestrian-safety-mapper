# Pedestrian Safety Mapper

## Overview

Pedestrian Safety Mapper is an open-source web application that visualizes pedestrian fatality data from the Fatality Analysis Reporting System (FARS). Designed for policy makers, transportation advocates, and urban planners, this tool provides interactive, data-driven insights into road safety.

![Project Status: In Development](https://img.shields.io/badge/status-in%20development-yellow)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

## Project Goals

- Visualize pedestrian fatality data across geographic regions
- Provide interactive, data-driven insights for urban safety planning
- Demonstrate advanced GIS and data analysis techniques
- Support evidence-based transportation policy decisions

## Features (Planned)

- Interactive geographic visualization of FARS data
- Animated time-series analysis of pedestrian fatalities
- Customizable filters for:
  - Geographic regions
  - Time periods
  - Road types
  - Additional contextual factors
- Statistical summaries and trend analysis
- Exportable reports and visualizations

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


## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL
- PostGIS extension
- Node.js (for frontend dependencies)

### Setup Steps

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/pedestrian-safety-mapper.git
   cd pedestrian-safety-mapper
   ```

2. Create virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   npm install
   ```

4. Set up database
   ```bash
   # Detailed database setup instructions will be added
   ```

## Data Sources

- [Fatality Analysis Reporting System (FARS)](https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system)
- Additional open data sources to be integrated

## Roadmap

- [ ] Data ingestion and preprocessing
- [ ] Basic map visualization
- [ ] Time-series animations
- [ ] Advanced filtering mechanisms
- [ ] Report generation tools
- [ ] Performance optimization

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
