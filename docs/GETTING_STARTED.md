# Getting Started with FARS Multi-Sensory Database

This guide will walk you through setting up and running the FARS Multi-Sensory Database for the first time.

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.8+** installed
- **PostgreSQL 12+** with PostGIS extension
- **Git** for version control
- **4GB+ RAM** recommended
- **Basic SQL knowledge** (helpful but not required)

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/eddielathamjones/pedestrian-safety-mapper.git
cd pedestrian-safety-mapper
```

---

## Step 2: Set Up Python Environment

### Create Virtual Environment

```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

This will install ~60 packages. It may take 5-10 minutes.

**Note:** If you get errors with some packages:
- For PyTorch: Visit https://pytorch.org/get-started/locally/ for platform-specific install
- For GDAL: May require system dependencies on Linux

---

## Step 3: Set Up PostgreSQL Database

### Install PostgreSQL with PostGIS

**macOS (using Homebrew):**
```bash
brew install postgresql postgis
brew services start postgresql
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib postgis
sudo systemctl start postgresql
```

**Windows:**
- Download installer: https://www.postgresql.org/download/windows/
- Make sure to install PostGIS extension when prompted

### Create Database User (Optional)

```bash
# Connect to PostgreSQL
psql postgres

# Create user
CREATE USER fars_user WITH PASSWORD 'your_secure_password';
ALTER USER fars_user WITH CREATEDB;
```

---

## Step 4: Configure Database Connection

### Create config/database.yaml

```bash
# The template doesn't exist yet, so create the file manually
```

Edit `config/database.yaml`:

```yaml
database:
  host: localhost
  port: 5432
  database: fars_multisensory
  user: fars_user  # or your PostgreSQL username
  password: your_secure_password  # CHANGE THIS!

  pool:
    min_connections: 2
    max_connections: 10

  schema: public
  enable_postgis: true
```

**Security Note:** Never commit `database.yaml` to git! It's already in `.gitignore`.

---

## Step 5: Initialize Database

Run the setup script:

```bash
python scripts/01_setup_database.py
```

This will:
1. ✓ Create the `fars_multisensory` database
2. ✓ Enable PostGIS extension
3. ✓ Create all 18+ tables
4. ✓ Create 10+ analysis views
5. ✓ Verify setup

You should see:

```
✓ Database setup completed successfully!
Tables: 18
Views: 10
```

---

## Step 6: Get API Keys

Follow the [API Access Guide](API_ACCESS_GUIDE.md) to obtain free API keys for:

1. **Mapillary** (street view) - https://www.mapillary.com/dashboard/developers
2. **PurpleAir** (air quality) - Email: contact@purpleair.com
3. **Visual Crossing** (weather) - https://www.visualcrossing.com/

### Create config/api_keys.yaml

```bash
cp config/api_keys.yaml.template config/api_keys.yaml
```

Edit `config/api_keys.yaml`:

```yaml
mapillary:
  api_key: "MLY|your_mapillary_token_here"

purpleair:
  api_key: "your_purpleair_key_here"

visual_crossing:
  api_key: "your_visual_crossing_key_here"
```

**Note:** You can start without all API keys - get them as needed.

---

## Step 7: Import FARS Crash Data

### Option A: Import from Existing FARS Files

If you already have FARS data in `data/raw/`:

```bash
# Import specific year for a state
python scripts/02_import_fars_data.py --year 2022 --state AZ

# Import all years
python scripts/02_import_fars_data.py --state AZ --all-years

# Dry run (validate without inserting)
python scripts/02_import_fars_data.py --year 2022 --dry-run
```

### Option B: Download FARS Data First

Download from NHTSA:

```bash
# Use existing download script
python scripts/data_download.py
```

Or manually:
1. Go to: https://www.nhtsa.gov/file-downloads?p=nhtsa/downloads/FARS/
2. Download year(s) you need (e.g., 2022/)
3. Extract to `data/raw/2022/`

---

## Step 8: Verify Import

Check your data:

```bash
# Connect to PostgreSQL
psql -d fars_multisensory

# Count crashes
SELECT COUNT(*) FROM crashes;

# View sample
SELECT crash_id, city, state, crash_date FROM crashes LIMIT 10;

# Check data completeness
SELECT * FROM vw_database_summary;
```

Expected output:
```
 total_crashes | states_covered | counties_covered
---------------+----------------+------------------
           100 |              1 |               15
```

---

## Step 9: Test Data Collection (Optional)

### Test Street View Download

```bash
# Download street view images for 5 crashes
python scripts/03_download_streetview.py --limit 5
```

This will:
- Connect to Mapillary API
- Download images near crash locations
- Save to `data/streetview/CRASH_ID/`
- Update `streetview_images` table

### Test Air Quality Collection

```bash
# Collect air quality for 5 crashes
python scripts/05_collect_air_quality.py --limit 5
```

### Test Weather Collection

```bash
# Collect weather for 5 crashes
python scripts/06_collect_weather.py --limit 5
```

---

## Step 10: Explore Your Data

### Using Jupyter Notebooks

```bash
# Start Jupyter
jupyter notebook

# Open: notebooks/01_exploratory_analysis.ipynb
```

The notebook includes:
- Database connection examples
- Geographic visualizations
- Data quality checks
- Multi-sensory analysis

### Using SQL

```sql
-- Find crashes with missing data
SELECT * FROM vw_data_completeness
WHERE completeness_percentage < 80;

-- High-risk locations
SELECT * FROM vw_high_risk_crashes
ORDER BY risk_factor_count DESC
LIMIT 10;

-- Environmental justice by county
SELECT * FROM vw_county_environmental_summary
ORDER BY crash_count DESC;
```

More examples in `sql/example_queries.sql`.

---

## Common Issues & Solutions

### Issue: Database connection fails

**Solution:**
1. Verify PostgreSQL is running: `pg_isready`
2. Check credentials in `config/database.yaml`
3. Ensure database was created: `psql -l | grep fars`

### Issue: PostGIS extension error

**Solution:**
```bash
psql -d fars_multisensory -c "CREATE EXTENSION postgis;"
```

### Issue: Python package import errors

**Solution:**
```bash
# Reinstall specific package
pip install --force-reinstall package_name

# Or reinstall all
pip install --force-reinstall -r requirements.txt
```

### Issue: API returns 401/403 errors

**Solution:**
1. Verify API key is correct in `config/api_keys.yaml`
2. Check for extra spaces or quotes
3. Test API key directly: `curl -H "Authorization: Bearer YOUR_KEY" API_URL`

### Issue: Out of memory during import

**Solution:**
```bash
# Import in smaller batches
python scripts/02_import_fars_data.py --year 2022 --limit 100
```

---

## Directory Structure After Setup

```
fars-multisensory/
├── config/
│   ├── database.yaml          # Your database config
│   ├── api_keys.yaml           # Your API keys
│   └── settings.yaml           # App settings
├── data/
│   ├── raw/                    # Original FARS data
│   ├── streetview/             # Downloaded images
│   │   └── CRASH_ID/
│   ├── sound/                  # Audio files
│   └── processed/              # Processed datasets
├── logs/                       # Application logs
│   ├── database_setup.log
│   └── fars_import.log
├── outputs/
│   ├── reports/                # Generated reports
│   ├── visualizations/         # Maps and charts
│   └── exports/                # CSV/GeoJSON exports
└── venv/                       # Python virtual environment
```

---

## Next Steps

Now that you're set up:

1. **Collect more environmental data:**
   - Street view images
   - Air quality measurements
   - Weather conditions
   - OpenStreetMap infrastructure

2. **Run analyses:**
   - Computer vision on street view images
   - Multi-sensory risk scoring
   - Environmental justice assessments

3. **Generate visualizations:**
   - Interactive crash maps
   - Individual crash report cards
   - Statistical dashboards

4. **Contribute:**
   - Implement new data collectors
   - Improve analysis algorithms
   - Create visualizations

---

## Learning Resources

### SQL & PostGIS
- [PostGIS Documentation](https://postgis.net/documentation/)
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)

### Python & Data Science
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [GeoPandas Tutorial](https://geopandas.org/en/stable/getting_started.html)

### APIs
- [Mapillary API Docs](https://www.mapillary.com/developer/api-documentation)
- [PurpleAir API Docs](https://api.purpleair.com/)
- [Visual Crossing API Docs](https://www.visualcrossing.com/resources/documentation/weather-api/)

---

## Getting Help

- **Documentation:** Check `docs/` directory
- **Example Queries:** See `sql/example_queries.sql`
- **Issues:** https://github.com/eddielathamjones/pedestrian-safety-mapper/issues
- **Discussions:** GitHub Discussions tab

---

## Quick Reference

### Essential Commands

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Setup database
python scripts/01_setup_database.py

# Import FARS data
python scripts/02_import_fars_data.py --year 2022 --state AZ

# Download street view (5 crashes)
python scripts/03_download_streetview.py --limit 5

# Start Jupyter notebook
jupyter notebook

# Connect to database
psql -d fars_multisensory

# View logs
tail -f logs/database_setup.log
```

### Useful SQL Queries

```sql
-- Total crashes
SELECT COUNT(*) FROM crashes;

-- Data completeness
SELECT * FROM vw_database_summary;

-- Recent crashes
SELECT * FROM crashes ORDER BY crash_date DESC LIMIT 10;

-- Crashes by state
SELECT state, COUNT(*) as crash_count
FROM crashes
GROUP BY state
ORDER BY crash_count DESC;
```

---

**You're all set! 🎉**

Start exploring your pedestrian crash data with multi-sensory environmental context.
