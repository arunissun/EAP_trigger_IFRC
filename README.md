# GloFAS Flood Forecasting Pipeline

Automated pipeline for downloading, processing, and visualizing GloFAS (Global Flood Awareness System) flood forecast data for IFRC emergency response planning.

## Overview

This repository contains a complete automated pipeline that:

1. **Downloads** daily GloFAS ensemble forecast data from Copernicus Climate Data Store
2. **Merges** GRIB2 files into monthly NetCDF files
3. **Generates** hydrograph plots with flood threshold overlays
4. **Commits** results back to the repository

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

3. **Configure CDS API credentials:**
   Create `~/.cdsapirc` with your credentials:
   ```
   url: https://cds.climate.copernicus.eu/api/v2
   key: YOUR_UID:YOUR_API_KEY
   ```

4. **Run the pipeline:**
   ```bash
   python scripts/download_glofas.py
   python scripts/merge_grib_to_nc.py
   python scripts/plot_hydrographs.py
   ```

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

Edit `config/countries.py` to add new countries:

```python
COUNTRIES = {
    "country_code": {
        "name": "Country Name",
        "bbox": [min_lon, min_lat, max_lon, max_lat],  # Bounding box
        "river_coords": {
            "lat": latitude,
            "lon": longitude
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