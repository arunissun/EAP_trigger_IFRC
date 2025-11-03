import cdsapi
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import sys
from datetime import datetime

# Add config to path (use absolute path based on script location)
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
config_path = os.path.join(project_root, 'config')
sys.path.insert(0, config_path)

from countries import COUNTRIES

def download_country_data(country_code):
    if country_code not in COUNTRIES:
        print(f"Country '{country_code}' not found in configuration")
        return
    
    country_config = COUNTRIES[country_code]
    folder = f"data/{country_code}/ensemble_forecast"
    os.makedirs(folder, exist_ok=True)

    area = country_config["bbox"]
    dataset = "cems-glofas-forecast"
    
    # Automatically get current year and month
    today = datetime.now()
    year = str(today.year)
    month = f"{today.month:02d}"
    n_days = today.day
    
    print(f"Downloading data for {country_config['name']}: {year}-{month} (Days 1-{n_days})")
    
    leadtime_hours = [str(h) for h in range(24, 241, 24)]

    requests = []
    for day in range(1, n_days + 1):
        day_str = f"{day:02d}"
        filename = os.path.join(folder, f"glofas_{country_code}_ensemble_{year}_{month}_{day_str}.grib2")
        if not os.path.isfile(filename):
            req = {
                "system_version": "operational",
                "hydrological_model": "lisflood",
                "product_type": "ensemble_perturbed_forecasts",
                "variable": "river_discharge_in_the_last_24_hours",
                "year": year,
                "month": month,
                "day": day_str,
                "leadtime_hour": leadtime_hours,
                "data_format": "grib2",
                "download_format": "unarchived",
                "area": area,
            }
            requests.append((req, filename))
        else:
            print(f"File already exists, skipping: {filename}")

    def fetch_data(cds_req, filename):
        c = cdsapi.Client()
        c.retrieve(dataset, cds_req, filename)
        print(f"Downloaded: {filename}")

    if requests:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_data, r[0], r[1]) for r in requests]
            for f in as_completed(futures):
                try:
                    f.result()
                    print("Download completed for one file")
                except Exception as e:
                    print("Download failed:", e)
    else:
        print(f"All files already downloaded for {country_config['name']}!")

if __name__ == "__main__":
    # Download data for both countries
    for country in COUNTRIES.keys():
        print(f"\n=== Downloading data for {COUNTRIES[country]['name']} ===")
        download_country_data(country)
