import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
import re
import sys

# Add config to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
config_path = os.path.join(project_root, 'config')
sys.path.insert(0, config_path)

from countries import COUNTRIES

def get_return_period_value(ds, lat, lon, varname):
    ilat = np.abs(ds['lat'].values - lat).argmin()
    ilon = np.abs(ds['lon'].values - lon).argmin()
    return ds[varname].values[ilat, ilon], ds['lat'].values[ilat], ds['lon'].values[ilon]

def interpolate_return_period(val_2yr, val_5yr, target_rp=3.0):
    log_2 = np.log(2.0)
    log_5 = np.log(5.0)
    log_target = np.log(target_rp)
    val_target = val_2yr + (val_5yr - val_2yr) * (log_target - log_2) / (log_5 - log_2)
    return val_target

def plot_country_hydrographs(country_code):
    if country_code not in COUNTRIES:
        print(f"Country not found")
        return
    country_config = COUNTRIES[country_code]
    if 'river_basins' in country_config:
        for basin_code, basin_config in country_config['river_basins'].items():
            print(f"Plotting {basin_config['name']}")
            plot_basin_hydrographs(country_code, country_config, basin_code, basin_config)
    else:
        plot_single_point_hydrographs(country_code, country_config)

def plot_single_point_hydrographs(country_code, country_config):
    ensemble_folder = f"data/{country_code}/ensemble_forecast"
    plots_root = f"data/{country_code}/plots"
    nc_pattern = os.path.join(ensemble_folder, f"glofas_{country_code}_ensemble_*_combined.nc")
    nc_files = sorted([f for f in glob.glob(nc_pattern) if os.path.isfile(f)])
    if not nc_files:
        print(f"No files found")
        return
    target_lat = country_config["lisflood_coords"]["lat"]
    target_lon = country_config["lisflood_coords"]["lon"]
    rp_folder = f"data/{country_code}/return_periods"
    rp_file_2yr = os.path.join(rp_folder, "flood_threshold_glofas_v4_rl_2.0.nc")
    rp_file_5yr = os.path.join(rp_folder, "flood_threshold_glofas_v4_rl_5.0.nc")
    if not os.path.exists(rp_file_2yr) or not os.path.exists(rp_file_5yr):
        print("Return period files not found")
        return
    ds_2yr = xr.open_dataset(rp_file_2yr)
    ds_5yr = xr.open_dataset(rp_file_5yr)
    val_2yr, grid_lat, grid_lon = get_return_period_value(ds_2yr, target_lat, target_lon, 'rl_2.0')
    val_5yr, _, _ = get_return_period_value(ds_5yr, target_lat, target_lon, 'rl_5.0')
    val_3yr = interpolate_return_period(val_2yr, val_5yr, target_rp=3.0)
    print(f"Thresholds: 2yr={val_2yr:.2f}, 3yr={val_3yr:.2f} m3/s")
    plot_hydrographs_for_location(nc_files, plots_root, target_lat, target_lon, val_2yr, val_3yr, country_config, "guatemala")
    ds_2yr.close()
    ds_5yr.close()

def plot_basin_hydrographs(country_code, country_config, basin_code, basin_config):
    ensemble_folder = f"data/{country_code}/ensemble_forecast"
    plots_root = f"data/{country_code}/plots"
    nc_pattern = os.path.join(ensemble_folder, f"glofas_{country_code}_ensemble_*_combined.nc")
    nc_files = sorted([f for f in glob.glob(nc_pattern) if os.path.isfile(f)])
    if not nc_files:
        print("No files found")
        return
    target_lat = basin_config["lisflood_coords"]["lat"]
    target_lon = basin_config["lisflood_coords"]["lon"]
    rp_folder = f"data/{country_code}/return_periods"
    rp_file_5yr = os.path.join(rp_folder, "flood_threshold_glofas_v4_rl_5.0.nc")
    if not os.path.exists(rp_file_5yr):
        print("Return period file not found")
        return
    ds_5yr = xr.open_dataset(rp_file_5yr)
    val_5yr, grid_lat, grid_lon = get_return_period_value(ds_5yr, target_lat, target_lon, 'rl_5.0')
    print(f"Threshold: 5yr={val_5yr:.2f} m3/s")
    plot_hydrographs_for_location(nc_files, plots_root, target_lat, target_lon, val_5yr, None, basin_config, "philippines", basin_code)
    ds_5yr.close()

def plot_hydrographs_for_location(nc_files, plots_root, target_lat, target_lon, threshold1, threshold2, config, threshold_type, basin_code=None):
    for nc_file in nc_files:
        fname = os.path.basename(nc_file)
        match = re.search(r"ensemble_(\d{4})_(\d{2})_combined\.nc", fname)
        if not match:
            continue
        year, month = match.groups()
        if basin_code:
            month_plot_dir = os.path.join(plots_root, basin_code, f"{year}_{month}")
        else:
            month_plot_dir = os.path.join(plots_root, f"{year}_{month}")
        os.makedirs(month_plot_dir, exist_ok=True)
        ds = xr.open_dataset(nc_file)
        ilat = np.abs(ds.latitude.values - target_lat).argmin()
        ilon = np.abs(ds.longitude.values - target_lon).argmin()
        discharge_data = ds.dis24.isel(latitude=ilat, longitude=ilon).values
        lead_times_days = ds.step.values.astype('timedelta64[D]').astype(int)
        dates = ds.time.values.astype('datetime64[D]').astype(str)
        
        for t in range(discharge_data.shape[0]):
            if basin_code:
                output_file = os.path.join(month_plot_dir, f"hydrograph_{basin_code}_{dates[t]}.png")
            else:
                output_file = os.path.join(month_plot_dir, f"hydrograph_{dates[t]}.png")
            if os.path.exists(output_file):
                continue
            
            # Prepare boxplot data for first 5 days with outlier removal
            boxplot_data_per_day = []
            lead_times_5days = []
            
            for lead in range(min(5, discharge_data.shape[2])):
                data = discharge_data[t, :, lead]
                lead_times_5days.append(lead_times_days[lead])
                
                # Remove outliers
                q1 = np.nanpercentile(data, 25)
                q3 = np.nanpercentile(data, 75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                filtered_data = data[(data >= lower_bound) & (data <= upper_bound)]
                boxplot_data_per_day.append(filtered_data)
            
            # Create plot
            plt.figure(figsize=(12, 7))
            
            # Plot boxplots only
            plt.boxplot(boxplot_data_per_day, positions=lead_times_5days, widths=0.4, 
                       patch_artist=True, showfliers=False,
                       boxprops=dict(facecolor="lightblue", alpha=0.7),
                       medianprops=dict(color="black", linewidth=1.5))
            
            # Add threshold lines based on country
            if threshold_type == "guatemala":
                plt.axhline(threshold1, color='red', linestyle='--', linewidth=2, label='2-year RP', alpha=0.7)
                plt.axhline(threshold2, color='orange', linestyle='-.', linewidth=2, label='3-year RP', alpha=0.7)
            elif threshold_type == "philippines":
                plt.axhline(threshold1, color='red', linestyle='--', linewidth=2, label='5-year RP', alpha=0.7)
            
            plt.xlabel("Lead Time (days)", fontsize=14)
            plt.ylabel("River Discharge (m³/s)", fontsize=14)
            
            if basin_code:
                title = f"GloFAS Ensemble Forecast Hydrograph (Outliers Removed)\n{config['name']} - {config['station_name']}\nLat: {ds.latitude.values[ilat]:.2f}°, Lon: {ds.longitude.values[ilon]:.2f}°"
            else:
                title = f"GloFAS Ensemble Forecast Hydrograph (Outliers Removed)\n{config['name']} Region\nLat: {ds.latitude.values[ilat]:.2f}°, Lon: {ds.longitude.values[ilon]:.2f}°"
            
            plt.title(title, fontsize=14, fontweight="bold")
            plt.grid(True, alpha=0.3)
            plt.ylim(bottom=0)
            plt.legend(fontsize=11, loc='best')
            plt.tight_layout()
            plt.savefig(output_file, dpi=100)
            plt.close()
            print(f"Saved: {dates[t]}")
        ds.close()

if __name__ == "__main__":
    for country in COUNTRIES.keys():
        print(f"\\nPlotting {COUNTRIES[country]['name']}")
        plot_country_hydrographs(country)
    print("\\nDONE")
