# API Access Guide - FARS Multi-Sensory Database

This guide walks you through obtaining free API keys for all data sources used in the project.

---

## Priority 1: Essential APIs (Free, No Usage Limits)

### 1. Mapillary API (Street View Images)

**What it provides:** Street-level imagery from around the world, contributed by users
**Cost:** 100% Free, no usage limits
**Coverage:** Excellent in urban areas, especially major cities

**How to get access:**

1. **Create a Mapillary account**
   - Go to: https://www.mapillary.com/
   - Click "Sign Up" in the top right
   - Use email or social login (Facebook, Google)

2. **Register as a developer**
   - Go to: https://www.mapillary.com/dashboard/developers
   - Click "Register as a Developer" (if not already registered)
   - Accept the Developer Terms

3. **Create an application**
   - Click "Create Application" or "Register Application"
   - Fill in:
     - **Application Name:** "FARS Multi-Sensory Database" (or your project name)
     - **Description:** "Pedestrian crash environmental analysis research"
     - **Application Type:** Select "Other" or "Research"
     - **Application URL:** Your GitHub repo URL or "http://localhost" for development

4. **Get your Client Token**
   - After creating the app, you'll see your **Client Token** (MLY|...)
   - Copy this token
   - Add to `config/api_keys.yaml`:
     ```yaml
     mapillary:
       api_key: "MLY|your_actual_token_here"
     ```

**API Documentation:** https://www.mapillary.com/developer/api-documentation

**Notes:**
- Images are community-contributed, so coverage varies by location
- No daily limits or rate limiting (as of 2024)
- Great alternative to Google Street View (which is expensive)

---

### 2. PurpleAir API (Air Quality Data)

**What it provides:** Real-time and historical PM2.5, PM10 air quality from crowd-sourced sensors
**Cost:** Free for research/non-commercial use
**Coverage:** Dense in US urban areas, growing globally

**How to get access:**

1. **Request an API key**
   - Go to: https://www2.purpleair.com/pages/contact-us
   - Or email: contact@purpleair.com
   - Subject: "API Key Request for Research"

2. **In your request, include:**
   ```
   Subject: API Key Request - Pedestrian Safety Research

   Hello,

   I am requesting a free API key for non-commercial research purposes.

   Project: FARS Multi-Sensory Pedestrian Crash Database
   Purpose: Analyzing air quality conditions at pedestrian crash locations
   Research Type: Academic/Public Safety Research
   Institution: [Your affiliation, or "Independent Researcher"]
   GitHub: https://github.com/eddielathamjones/pedestrian-safety-mapper

   I will use the API to:
   - Query historical air quality data near crash locations
   - Analyze correlations between air quality and crash patterns
   - Support evidence-based transportation safety policy

   Expected usage: ~100-500 API calls per day during data collection phase

   Thank you for supporting open safety research.

   [Your Name]
   [Your Email]
   ```

3. **Wait for response**
   - Usually responds within 1-3 business days
   - They'll send you a Read API key

4. **Add to config**
   ```yaml
   purpleair:
     api_key: "your_purpleair_key_here"
   ```

**API Documentation:** https://api.purpleair.com/

**Notes:**
- Be honest about your usage - they support research
- Don't hammer the API - respect rate limits (1 request/second recommended)
- Historical data available, but real-time is more reliable

---

### 3. Visual Crossing Weather API

**What it provides:** Historical and current weather data (temp, precipitation, visibility)
**Cost:** Free tier: 1,000 API calls/day
**Coverage:** Global

**How to get access:**

1. **Sign up for free account**
   - Go to: https://www.visualcrossing.com/weather-api
   - Click "Sign Up" in top right

2. **Create account**
   - Enter email and create password
   - Or use Google/GitHub sign-in

3. **Verify email**
   - Check your inbox for verification email
   - Click verification link

4. **Get your API key**
   - After login, go to: https://www.visualcrossing.com/account
   - Your API key will be displayed on the Account page
   - Copy the key

5. **Add to config**
   ```yaml
   visual_crossing:
     api_key: "your_visual_crossing_key_here"
   ```

**API Documentation:** https://www.visualcrossing.com/resources/documentation/weather-api/timeline-weather-api/

**Free Tier Limits:**
- 1,000 weather queries per day
- Historical data included
- No credit card required

**Example API call:**
```
https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/
[latitude],[longitude]/[date]?key=YOUR_KEY
```

**Notes:**
- Super easy to get started
- Generous free tier for research
- Historical weather is crucial for crash analysis

---

## Priority 2: Optional/Alternative APIs (Free)

### 4. OpenWeatherMap (Alternative Weather)

**What it provides:** Weather data (alternative to Visual Crossing)
**Cost:** Free tier: 1,000 calls/day
**Coverage:** Global

**How to get access:**

1. Sign up: https://home.openweathermap.org/users/sign_up
2. Verify email
3. Go to API Keys: https://home.openweathermap.org/api_keys
4. Copy default API key (or create new one)
5. Add to config:
   ```yaml
   openweathermap:
     api_key: "your_openweather_key"
   ```

**Notes:**
- Good alternative if Visual Crossing limits are hit
- Historical data requires paid plan ($60/month)
- Free tier only has current + 5-day forecast

---

### 5. Google Street View API (Optional - Not Free)

**What it provides:** Google's street view imagery
**Cost:** $7 per 1,000 requests (first $200/month free with trial)
**Coverage:** Best coverage globally

**Only use if:**
- Mapillary coverage is insufficient in your area
- You have Google Cloud credits
- Your institution has a Google Cloud account

**How to get access:**

1. Go to: https://console.cloud.google.com/
2. Create a new project
3. Enable "Street View Static API"
4. Create API credentials
5. Add billing information (required even for free tier)
6. Add to config:
   ```yaml
   google_streetview:
     api_key: "your_google_api_key"
   ```

**Warning:** Can get expensive quickly! Use Mapillary instead for this project.

---

### 6. NASA Earthdata (For VIIRS Nighttime Lights)

**What it provides:** Satellite nighttime brightness data
**Cost:** Free
**Coverage:** Global

**How to get access:**

1. **Register for Earthdata account**
   - Go to: https://urs.earthdata.nasa.gov/users/new
   - Fill out registration form
   - Agree to terms

2. **Verify email**
   - Check inbox for NASA Earthdata verification
   - Click link to activate account

3. **Add to config**
   ```yaml
   nasa_earthdata:
     username: "your_earthdata_username"
     password: "your_earthdata_password"
   ```

**Data Access:**
- VIIRS DNB (Day/Night Band) nighttime lights
- Download from: https://ladsweb.modaps.eosdis.nasa.gov/
- Requires authentication

**Notes:**
- Data is in raster format (HDF5, NetCDF)
- Processing required - we'll implement this in Phase 2
- Very useful for lighting analysis

---

### 7. US Census Bureau API (Demographics)

**What it provides:** Census and ACS demographic data
**Cost:** Free, no key required (but recommended)
**Coverage:** United States

**How to get access:**

1. **Request API key (optional but recommended)**
   - Go to: https://api.census.gov/data/key_signup.html
   - Enter name, email, organization
   - Key will be emailed immediately

2. **Add to config**
   ```yaml
   census:
     api_key: "your_census_api_key"
   ```

**Notes:**
- API works without key, but rate-limited
- With key: 500 requests/second (very generous)
- Use `cenpy` Python library (already in requirements.txt)

---

### 8. OpenAQ (Alternative Air Quality)

**What it provides:** Air quality data from government sensors worldwide
**Cost:** Free, no API key required
**Coverage:** Global, but sparser than PurpleAir

**How to use:**

1. **No registration needed!**
   - API is completely open
   - Documentation: https://docs.openaq.org/

2. **Add to config** (no key needed)
   ```yaml
   openaq:
     api_key: null  # No key required
   ```

**Notes:**
- Good supplement to PurpleAir
- Uses official government sensors
- Less dense coverage than PurpleAir in US

---

### 9. NOAA National Weather Service API

**What it provides:** Official US weather data
**Cost:** Free, no API key required
**Coverage:** United States only

**How to use:**

1. **No registration needed!**
   - Documentation: https://www.weather.gov/documentation/services-web-api
   - Base URL: https://api.weather.gov/

2. **Required: User Agent header**
   - Must identify your app in requests
   - Example: `User-Agent: (FARS-Multi-Sensory, your-email@example.com)`

**Notes:**
- Historical data more complex to access than Visual Crossing
- Real-time data is excellent
- Recommend Visual Crossing for historical weather

---

## Summary: Recommended API Setup

### Minimum Setup (Core Functionality)
```yaml
# config/api_keys.yaml

mapillary:
  api_key: "MLY|your_mapillary_token"     # REQUIRED - street view

purpleair:
  api_key: "your_purpleair_key"           # REQUIRED - air quality

visual_crossing:
  api_key: "your_visual_crossing_key"     # REQUIRED - weather
```

### Full Setup (All Features)
```yaml
# config/api_keys.yaml

# Essential (Priority 1)
mapillary:
  api_key: "MLY|your_mapillary_token"

purpleair:
  api_key: "your_purpleair_key"

visual_crossing:
  api_key: "your_visual_crossing_key"

# Optional alternatives
openweathermap:
  api_key: "your_openweather_key"

openaq:
  api_key: null  # No key needed

# For advanced features
nasa_earthdata:
  username: "your_nasa_username"
  password: "your_nasa_password"

census:
  api_key: "your_census_key"

# Only if needed
google_streetview:
  api_key: null  # Not recommended due to cost
```

---

## API Rate Limits & Best Practices

| API | Free Tier Limit | Recommended Rate | Cost if Exceeded |
|-----|----------------|------------------|------------------|
| Mapillary | Unlimited | No limit | N/A |
| PurpleAir | ~1,000/day* | 1 req/sec | Contact for pricing |
| Visual Crossing | 1,000/day | Any | $0.0001/call after |
| OpenWeatherMap | 1,000/day | 1 req/sec | $0.0015/call after |
| Census | 500 req/sec | Any | Free |
| OpenAQ | Unlimited | 1 req/sec (courtesy) | Free |
| NOAA | Unlimited | Be reasonable | Free |

*PurpleAir limits not officially published - be conservative

---

## Testing Your API Keys

After adding keys to `config/api_keys.yaml`, test them:

```bash
# Test all API connections (script to be created in Phase 2)
python scripts/test_api_connections.py

# Test individual APIs
python -c "from src.collectors.mapillary_client import MapillaryClient; \
           MapillaryClient().test_connection()"
```

---

## Common Issues & Troubleshooting

### Mapillary
- **Issue:** "Invalid token"
  - Solution: Make sure token starts with "MLY|"
  - Check for extra spaces in config file

### PurpleAir
- **Issue:** No response to API key request
  - Solution: Check spam folder
  - Try alternative email: sales@purpleair.com

### Visual Crossing
- **Issue:** "API key not found"
  - Solution: Check you copied the full key from Account page
  - Verify email was confirmed

### General
- **Issue:** YAML parsing errors
  - Solution: Check indentation (use spaces, not tabs)
  - Make sure quotes match (use double quotes for values with special chars)

---

## Cost Estimate for 1,000 Crashes

Assuming you process 1,000 crashes with full data collection:

| Data Source | API Calls | Cost |
|-------------|-----------|------|
| Mapillary (10 images/crash) | 10,000 | $0 |
| PurpleAir (1 query/crash) | 1,000 | $0 |
| Weather (1 query/crash) | 1,000 | $0 (within free tier) |
| OpenStreetMap | 1,000 | $0 |
| Census | 1,000 | $0 |
| **Total** | **~14,000** | **$0** |

**Note:** All costs are $0 if you stay within free tiers and use recommended APIs!

---

## Next Steps

1. ✅ Get your API keys (start with Priority 1)
2. ✅ Add them to `config/api_keys.yaml`
3. ✅ Test connections
4. 🚧 Ready for Phase 2: Implement data collectors!

---

## Questions?

If you have issues getting API access:
1. Check the API's documentation (links provided above)
2. Read the FAQ on each API's website
3. Contact the API provider's support (they're generally helpful for research)
4. Open an issue on this GitHub repo

Good luck! 🚀
