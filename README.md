# GloFAS Flood Forecasting Pipeline

Automated pipeline for downloading, processing, and visualizing GloFAS (Global Flood Awareness System) flood forecast data for IFRC emergency response planning.

## Overview

This repository contains a complete automated pipeline that:

1. **Downloads** daily GloFAS ensemble forecast data from Copernicus Early Warning Data Store (EWDS)
2. **Merges** GRIB2 files into monthly NetCDF files
3. **Generates** hydrograph plots with flood threshold overlays
4. **Analyzes** forecasts against return period thresholds to identify flood triggers
5. **Sends** automated email alerts when high-risk conditions are detected
6. **Commits** results back to the repository

Key features:
- **Multi-country support** (Guatemala, Philippines, etc.)
- **Configurable river basins** with custom coordinates and thresholds
- **Automated daily downloads** via GitHub Actions
- **Return period threshold analysis** (2-year and 5-year)
- **Professional hydrograph plots** with threshold visualization
- **Automated email alerts** with IFRC branding for high-risk forecasts

## Pipeline Process Flow

The complete pipeline consists of five main stages:

### 1. Data Download (`download_glofas.py`)
Downloads GloFAS ensemble forecast data from the Copernicus Early Warning Data Store (EWDS).

**What it does:**
- Connects to EWDS API using credentials from `~/.cdsapirc`
- Downloads 30-day ensemble forecasts (51 ensemble members)
- Retrieves data for configured country bounding boxes
- Saves daily GRIB2 files to `data/{country}/ensemble_forecast/`
- Automatically handles multiple countries in a single run

**Output:** Daily GRIB2 files named `glofas_{country}_ensemble_{YYYY}_{MM}_{DD}.grib2`

**Usage:**
```bash
python scripts/download_glofas.py
```

### 2. Data Merging (`merge_grib_to_nc.py`)
Merges daily GRIB2 files into monthly NetCDF files for efficient analysis.

**What it does:**
- Reads all GRIB2 files for a given month
- Combines ensemble forecasts into single NetCDF file
- Organizes data by forecast date and step
- Compresses and optimizes for storage
- Processes multiple months if specified

**Output:** Monthly NetCDF files named `glofas_{country}_ensemble_{YYYY}_{MM}_combined.nc`

**Usage:**
```bash
python scripts/merge_grib_to_nc.py
```

### 3. Visualization (`plot_hydrographs.py`)
Creates hydrograph plots showing ensemble forecasts against return period thresholds.

**What it does:**
- Extracts forecast data at configured river coordinates
- Calculates ensemble statistics (median, percentiles)
- Loads 2-year and 5-year return period thresholds
- Generates professional plots with IFRC branding
- Creates separate plots for each basin (multi-basin countries)
- Organizes plots by year/month subdirectories

**Output:** PNG plots saved to `data/{country}/plots/{basin}/{YYYY}_{MM}/hydrograph_{YYYY}-{MM}-{DD}.png`

**Features:**
- Box plots showing ensemble spread
- Red dashed line: 2-year return period threshold
- Orange dash-dot line: 5-year return period threshold
- Median ensemble forecast line
- 30-day forecast horizon

**Usage:**
```bash
python scripts/plot_hydrographs.py
```

### 4. Flood Trigger Analysis (`analyze_flood_triggers.py`)
Analyzes forecasts to identify flood triggers based on exceedance probabilities.

**What it does:**
- Calculates probability of exceeding return period thresholds
- Compares probabilities against configured trigger levels
- Determines alert status (low, medium, high)
- Generates narrative analysis with risk assessments
- Creates Excel files with detailed trigger data
- Processes all basins for multi-basin countries

**Alert Status Logic:**
- **High Alert**: Probability > 70% of exceeding threshold
- **Medium Alert**: Probability between 50-70%
- **Low Alert**: Probability < 50%

**Output:** Excel files saved to `data/{country}/analysis/{basin}/trigger_analysis_{YYYY}_{MM}_{DD}.xlsx`

**Excel Contents:**
- Forecast date and step
- Return period probabilities
- Alert status
- Lead time
- Affected provinces (if configured)
- Narrative risk analysis

**Usage:**
```bash
python scripts/analyze_flood_triggers.py
```

### 5. Email Alert System 
Monitors trigger analysis and sends automated email alerts for high-risk forecasts.

**Deployment:** This pipeline is deployed on **Microsoft Fabric** as Jupyter notebooks, enabling cloud-based execution with integrated data storage and parameter management.

**What it does:**
- Scans Excel files for latest forecast data
- Filters for high alert status on most recent forecasts
- Generates professional HTML emails with IFRC branding
- Embeds hydrograph plots as inline images
- Attaches full Excel analysis files
- Sends via Gmail SMTP with secure authentication

**Alert Trigger Logic:**
- Groups data by station/basin
- Sorts by forecast date to find latest forecast
- Only sends alerts if latest forecast shows "high" alert_status
- Prevents alerts for old forecasts

**Email Features:**
- IFRC GO logo from CDN
- Table-based HTML (compatible with Outlook Desktop)
- Embedded hydrograph images
- Risk-based narrative recommendations
- Excel file attachments with full analysis
- Professional formatting across all email clients

**Configuration (Fabric Notebook Parameters):**
- `SENDER_EMAIL`: Gmail address (e.g., `your.email@gmail.com`)
- `SENDER_PASSWORD`: Gmail App Password (16-character code)
- `RECIPIENT_EMAIL`: Alert recipient address
- `SMTP_SERVER`: `smtp.gmail.com`
- `SMTP_PORT`: `587`

**Setup Requirements:**
1. Enable 2-Step Verification on Gmail account
2. Generate App Password at https://myaccount.google.com/apppasswords
3. Configure Fabric notebook parameters with credentials
4. Run notebook in Microsoft Fabric environment

**Usage:**
Run the Jupyter notebook cells sequentially in Microsoft Fabric to send alerts.

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GLOFAS EAP PIPELINE                         │
└─────────────────────────────────────────────────────────────────────┘

1. DOWNLOAD (download_glofas.py)
   ├─> Copernicus CDS API
   └─> data/{country}/ensemble_forecast/*.grib2

2. MERGE (merge_grib_to_nc.py)
   ├─> Read: data/{country}/ensemble_forecast/*.grib2
   └─> Write: data/{country}/ensemble_forecast/*_combined.nc

3. PLOT (plot_hydrographs.py)
   ├─> Read: *_combined.nc + return_periods/*.nc
   └─> Write: data/{country}/plots/{basin}/{year_month}/*.png

4. ANALYZE (analyze_flood_triggers.py)
   ├─> Read: *_combined.nc + return_periods/*.nc
   └─> Write: data/{country}/analysis/{basin}/*.xlsx

5. ALERT 
   ├─> Read: data/{country}/analysis/{basin}/*.xlsx
   ├─> Attach: data/{country}/plots/{basin}/{year_month}/*.png
   └─> Send: Email via Gmail SMTP
```

## Repository Structure

```
├── config/
│   └── countries.py                  # Country configurations
├── data/
│   ├── global_temp/                  # Global temporary data (ignored)
│   ├── guatemala/
│   │   ├── analysis/                 # Flood trigger analysis CSVs
│   │   ├── ensemble_forecast/        # Downloaded GRIB2 files and combined NetCDF
│   │   ├── plots/                    # Generated hydrographs
│   │   └── return_periods/           # Flood threshold NetCDF files
│   └── philippines/
│       ├── analysis/                 # Flood trigger analysis CSVs
│       ├── ensemble_forecast/        # Downloaded GRIB2 files and combined NetCDF
│       ├── plots/                    # Generated hydrographs
│       └── return_periods/           # Flood threshold NetCDF files
├── scripts/
│   ├── analyze_flood_triggers.py     # Flood trigger analysis
│   ├── crop_return_periods.py        # Crop global return periods to country boundaries
│   ├── download_glofas.py            # Data download script
│   ├── merge_grib_to_nc.py           # GRIB to NetCDF conversion
│   └── plot_hydrographs.py           # Plot generation
|   └── run_pipeline.py               # run the pipeline
├── requirements.txt                  # Python dependencies
└── .gitignore                        # Git ignore rules
```

## Setup

### Prerequisites

- Python 3.9+
- Copernicus Climate Data Store account
- GitHub repository with Actions enabled

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/arunissun/EAP_trigger_IFRC.git
   cd EAP_trigger_IFRC
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure EWDS API credentials:**
   Create `~/.cdsapirc` with your credentials:
   ```
   url: https://ewds.climate.copernicus.eu/api
   key: YOUR_UID:YOUR_API_KEY
   ```

4. **Run Pipeline Script (`run_pipeline.py`)**

The `run_pipeline.py` script orchestrates the complete flood forecasting pipeline by running all stages in the correct sequence. It provides:

**Features:**
- Runs all 4 stages automatically in order
- Validates that each script exists before execution
- Displays progress for each stage (Stage 1/4, Stage 2/4, etc.)
- Stops gracefully if any stage fails and reports which stage failed
- Shows start and completion timestamps
- Returns appropriate exit codes for automation/scheduling

**Output Example:**
```
======================================================================
  GloFAS EAP PIPELINE ORCHESTRATOR
======================================================================

Pipeline Overview:
  1. Download GloFAS Data
  2. Merge GRIB to NetCDF
  3. Plot Hydrographs
  4. Analyze Flood Triggers

Starting: 2025-11-24 10:30:45

Stage 1/4: Download GloFAS Data
Stage 1 completed successfully!

Stage 2/4: Merge GRIB to NetCDF
Stage 2 completed successfully!

[continues for remaining stages...]

======================================================================
  PIPELINE COMPLETED SUCCESSFULLY
======================================================================
All 4 stages completed successfully
Completion: 2025-11-24 10:35:12
```

**Usage:**
```bash
python scripts/run_pipeline.py
```

**Exit Codes:**
- `0`: All stages completed successfully
- `1`: Pipeline failed at one of the stages

### Crop Return Periods Script

The `crop_return_periods.py` script crops global GloFAS return period data to specific country boundaries for efficient processing.

**Usage:**
```bash
python scripts/crop_return_periods.py --country <country_code> --return_period <2_or_5>
```

**Parameters:**
- `--country`: Country code (e.g., `guatemala`, `philippines`)
- `--return_period`: Return period (2 or 5 years)

**Example:**
```bash
python scripts/crop_return_periods.py --country guatemala --return_period 2
```

This generates cropped NetCDF files in `data/{country_code}/return_periods/` for use in flood threshold analysis.

### GitHub Actions Setup

The pipeline runs automatically via GitHub Actions. See `.github/GITHUB_ACTIONS_SETUP.md` for detailed setup instructions.

**Required GitHub Secrets:**
- `CDSAPI_URL`: `https://cds.climate.copernicus.eu/api/v2`
- `CDSAPI_KEY`: Your Copernicus CDS API key

## Configuration

### Adding New Countries

Edit `config/countries.py` to add new countries. The structure varies by country:

**For simple countries (like Guatemala):**
```python
COUNTRIES = {
    "country_code": {
        "name": "Country Name",
        "bbox": [north, west, south, east],  # Bounding box coordinates
        "river_coords": {
            "lat": latitude,
            "lon": longitude
        },
        "trigger": {
            "return_period": 3.0,  # Return period in years
            "probability_threshold": 0.5,  # Probability threshold (0-1)
            "lead_time_days": 3
        }
    }
}
```

**For countries with multiple river basins (like Philippines):**
```python
COUNTRIES = {
    "country_code": {
        "name": "Country Name",
        "bbox": [north, west, south, east],  # Country bounding box
        "river_basins": {
            "basin_code": {
                "name": "Basin Name",
                "station_name": "Station Name",
                "station_id": "GXXXX",
                "river_coords": {
                    "lat": latitude,
                    "lon": longitude
                },
                "lisflood_coords": {
                    "lat": latitude,
                    "lon": longitude
                },
                "drainage_area_km2": area,
                "provinces": ["Province1", "Province2"]
            }
        },
        "trigger": {
            "return_period": 5.0,
            "probability_threshold": 0.7,
            "lead_time_days": 3,
            "activation_rule": "ANY_BASIN"  # or "ALL_BASINS"
        }
    }
}
```

### Flood Thresholds

Return period threshold files should be placed in:
```
data/{country_code}/return_periods/
├── flood_threshold_glofas_v4_rl_2.0.nc  # 2-year return period
└── flood_threshold_glofas_v4_rl_5.0.nc  # 5-year return period
```

## Output

### Hydrograph Plots

Generated plots are saved in `data/{country_code}/plots/{year}_{month}/` with filenames like:
- `hydrograph_2025-10-01.png`
- `hydrograph_2025-10-02.png`

Each plot shows:
- Ensemble forecast spread (box plots)
- 2-year return period threshold (red dashed line)
- 5-year return period threshold (orange dash-dot line)

### NetCDF Files

Merged monthly files are saved as:
```
glofas_{country_code}_ensemble_{year}_{month}_combined.nc
```

## Data Sources

- **GloFAS Forecasts**: Copernicus Climate Data Store (CDS)
- **Flood Thresholds**: GloFAS return period data
- **Geographic Boundaries**: Custom country configurations

## License

This project is part of IFRC's emergency response systems.

## Contact

For questions or issues, please contact the repository maintainer.