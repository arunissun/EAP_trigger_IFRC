import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
import re
import sys

# Add config to path
sys.path.append('config')
from countries import COUNTRIES

def get_return_period_value(ds, lat, lon, varname):
    """Find the nearest value for a return period at the given lat/lon."""
    ilat = np.abs(ds['lat'].values - lat).argmin()
    ilon = np.abs(ds['lon'].values - lon).argmin()
    return ds[varname].values[ilat, ilon], ds['lat'].values[ilat], ds['lon'].values[ilon]

def plot_country_hydrographs(country_code):
    if country_code not in COUNTRIES:
        print(f"Country '{country_code}' not found in configuration")
        return
    
    country_config = COUNTRIES[country_code]
    ensemble_folder = f"data/{country_code}/ensemble_forecast"
    plots_root = f"data/{country_code}/plots"
    nc_pattern = os.path.join(ensemble_folder, f"glofas_{country_code}_ensemble_*_combined.nc")
    nc_files = sorted([f for f in glob.glob(nc_pattern) if os.path.isfile(f)])

    # Check if any NetCDF files exist
    if not nc_files:
        print(f"⚠ No merged NetCDF files found for {country_config['name']} in {ensemble_folder}")
        print(f"Please run merge_grib_to_nc.py first to create combined NetCDF files.")
        return

    target_lat = country_config["river_coords"]["lat"]
    target_lon = country_config["river_coords"]["lon"]

    # Load flood thresholds from country-specific folder
    rp_folder = f"data/{country_code}/return_periods"
    rp_file_2yr = os.path.join(rp_folder, "flood_threshold_glofas_v4_rl_2.0.nc")
    rp_file_5yr = os.path.join(rp_folder, "flood_threshold_glofas_v4_rl_5.0.nc")
    
    # Check if return period files exist
    if not os.path.exists(rp_file_2yr):
        print(f"⚠ Return period file not found: {rp_file_2yr}")
        print(f"Skipping {country_config['name']} - return period data is required for plotting.")
        return
    if not os.path.exists(rp_file_5yr):
        print(f"⚠ Return period file not found: {rp_file_5yr}")
        print(f"Skipping {country_config['name']} - return period data is required for plotting.")
        return
    
    ds_2yr = xr.open_dataset(rp_file_2yr)
    ds_5yr = xr.open_dataset(rp_file_5yr)
    val_2yr, grid_lat, grid_lon = get_return_period_value(ds_2yr, target_lat, target_lon, 'rl_2.0')
    val_5yr, _, _ = get_return_period_value(ds_5yr, target_lat, target_lon, 'rl_5.0')

    print(f"Overlay thresholds for {country_config['name']}:")
    print(f"  2-year: {val_2yr:.2f} m³/s, 5-year: {val_5yr:.2f} m³/s at grid {grid_lat:.3f}, {grid_lon:.3f}")

    for nc_file in nc_files:
        # Extract year/month from filename
        fname = os.path.basename(nc_file)
        match = re.search(rf"ensemble_(\d{{4}})_(\d{{2}})_combined\.nc", fname)
        if not match:
            print(f"Could not extract year/month from {fname}, skipping.")
            continue
        year, month = match.groups()
        month_plot_dir = os.path.join(plots_root, f"{year}_{month}")
        os.makedirs(month_plot_dir, exist_ok=True)

        ds = xr.open_dataset(nc_file)
        ilat = np.abs(ds.latitude.values - target_lat).argmin()
        ilon = np.abs(ds.longitude.values - target_lon).argmin()
        discharge_data = ds.dis24.isel(latitude=ilat, longitude=ilon).values
        lead_times_days = ds.step.values.astype('timedelta64[D]').astype(int)
        dates = ds.time.values.astype('datetime64[D]').astype(str)

        for t in range(discharge_data.shape[0]):
            output_file = os.path.join(month_plot_dir, f"hydrograph_{dates[t]}.png")
            if os.path.exists(output_file):
                print(f"Hydrograph for {dates[t]} already exists, skipping.")
                continue

            plt.figure(figsize=(12, 7))
            boxplot_data_per_day = []
            for lead in range(discharge_data.shape[2]):
                data = discharge_data[t, :, lead]
                # Remove outliers via IQR
                q1 = np.nanpercentile(data, 25)
                q3 = np.nanpercentile(data, 75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                filtered_data = data[(data >= lower_bound) & (data <= upper_bound)]
                boxplot_data_per_day.append(filtered_data)
            plt.boxplot(
                boxplot_data_per_day,
                positions=lead_times_days,
                widths=0.4,
                patch_artist=True,
                showfliers=False,
                boxprops=dict(facecolor="lightblue", alpha=0.7),
                medianprops=dict(color="black", linewidth=1.5),
            )
            plt.xlabel("Lead Time (days)", fontsize=14)
            plt.ylabel("River Discharge (m³/s)", fontsize=14)
            plt.title(
                f"GloFAS Ensemble Forecast Hydrograph\n{country_config['name']} Region\nLat: {ds.latitude.values[ilat]:.2f}, Lon: {ds.longitude.values[ilon]:.2f}, Date: {dates[t]}",
                fontsize=14,
                fontweight="bold",
            )
            # Overlay threshold lines
            plt.axhline(val_2yr, color='red', linestyle='--', linewidth=2, label='2-year RP')
            plt.axhline(val_5yr, color='orange', linestyle='-.', linewidth=2, label='5-year RP')
            plt.grid(True, alpha=0.3)
            plt.ylim(bottom=0)
            plt.legend()
            plt.tight_layout()
            plt.savefig(output_file)
            plt.close()
            print(f"Saved hydrograph for {country_config['name']} {dates[t]} → {output_file}")

if __name__ == "__main__":
    # Plot hydrographs for all countries configured
    for country in COUNTRIES.keys():
        print(f"\n=== Plotting hydrographs for {COUNTRIES[country]['name']} ===")
        plot_country_hydrographs(country)
