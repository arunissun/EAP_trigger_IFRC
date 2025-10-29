"""
Single-point flood trigger analysis (e.g., Guatemala).
Analyzes ensemble forecasts for countries with one monitoring location.
"""
import os
import glob
import re
import numpy as np
import pandas as pd
import xarray as xr
from analysis_utils import (
    interpolate_return_period, 
    get_return_period_value,
    calculate_ensemble_statistics,
    determine_alert_status
)

def analyze_singlepoint_triggers(country_code, country_config, lead_time_days, target_rp, probability_threshold):
    """
    Analyze triggers for countries with single monitoring point (e.g., Guatemala).
    
    Args:
        country_code: Country code
        country_config: Country configuration dictionary
        lead_time_days: Lead time to analyze
        target_rp: Target return period
        probability_threshold: Probability threshold for HIGH alerts
    
    Returns:
        Dictionary of DataFrames by month {year_month: df}
    """
    ensemble_folder = f"data/{country_code}/ensemble_forecast"
    target_lat = country_config["lisflood_coords"]["lat"]
    target_lon = country_config["lisflood_coords"]["lon"]
    
    # Load return period data
    rp_folder = f"data/{country_code}/return_periods"
    rp_file_2yr = os.path.join(rp_folder, "flood_threshold_glofas_v4_rl_2.0.nc")
    rp_file_5yr = os.path.join(rp_folder, "flood_threshold_glofas_v4_rl_5.0.nc")
    
    if not os.path.exists(rp_file_2yr) or not os.path.exists(rp_file_5yr):
        print(f"ERROR: Return period files not found for {country_code}")
        return None
    
    ds_2yr = xr.open_dataset(rp_file_2yr)
    ds_5yr = xr.open_dataset(rp_file_5yr)
    
    val_2yr, grid_lat, grid_lon = get_return_period_value(ds_2yr, target_lat, target_lon, 'rl_2.0')
    val_5yr, _, _ = get_return_period_value(ds_5yr, target_lat, target_lon, 'rl_5.0')
    val_target_rp = interpolate_return_period(val_2yr, val_5yr, target_rp=target_rp)
    
    print(f"\n{'='*70}")
    print(f"FLOOD TRIGGER ANALYSIS: {country_config['name']}")
    print(f"{'='*70}")
    print(f"Location: Lat {grid_lat:.3f}, Lon {grid_lon:.3f}")
    print(f"Return Period Thresholds:")
    print(f"   - 2-year RP:  {val_2yr:.2f} m3/s")
    print(f"   - {target_rp}-year RP:  {val_target_rp:.2f} m3/s (interpolated)")
    print(f"   - 5-year RP:  {val_5yr:.2f} m3/s")
    print(f"Lead time:   {lead_time_days} days")
    print(f"Alert threshold: {probability_threshold*100:.0f}% probability")
    print(f"{'='*70}\n")
    
    # Find all ensemble NetCDF files
    nc_pattern = os.path.join(ensemble_folder, f"glofas_{country_code}_ensemble_*_combined.nc")
    nc_files = sorted(glob.glob(nc_pattern))
    
    if not nc_files:
        print(f"WARNING: No ensemble NetCDF files found in {ensemble_folder}")
        return None
    
    print(f"Found {len(nc_files)} ensemble file(s) to analyze")
    
    # Group results by month
    results_by_month = {}
    
    for nc_file in nc_files:
        filename = os.path.basename(nc_file)
        print(f"\nProcessing: {filename}")
        
        match = re.search(r'ensemble_(\d{4})_(\d{2})_combined\.nc', filename)
        if not match:
            print(f"WARNING: Could not extract year/month from filename, skipping")
            continue
        
        year, month = match.groups()
        year_month = f"{year}_{month}"
        
        if year_month not in results_by_month:
            results_by_month[year_month] = []
        
        ds = xr.open_dataset(nc_file)
        
        # Find nearest grid point
        ilat = np.abs(ds.latitude.values - target_lat).argmin()
        ilon = np.abs(ds.longitude.values - target_lon).argmin()
        
        discharge_data = ds.dis24.isel(latitude=ilat, longitude=ilon).values
        lead_times_days_array = ds.step.values.astype('timedelta64[D]').astype(int)
        
        if lead_time_days not in lead_times_days_array:
            print(f"WARNING: {lead_time_days}-day lead time not available in data")
            ds.close()
            continue
        
        lead_idx = np.where(lead_times_days_array == lead_time_days)[0][0]
        dates = ds.time.values.astype('datetime64[D]').astype(str)
        
        # Analyze each forecast date
        for t in range(discharge_data.shape[0]):
            ensemble_values = discharge_data[t, :, lead_idx]
            
            stats = calculate_ensemble_statistics(ensemble_values, val_target_rp)
            if stats is None:
                continue
            
            alert_status = determine_alert_status(stats['exceedance_probability'], probability_threshold)
            
            # Store results
            results_by_month[year_month].append({
                'country': country_config['name'],
                'country_code': country_code,
                'station_name': country_config.get('station_name', 'Primary Station'),
                'station_id': country_config.get('station_id', 'N/A'),
                'forecast_date': dates[t],
                'lead_time_days': lead_time_days,
                'latitude': ds.latitude.values[ilat],
                'longitude': ds.longitude.values[ilon],
                'threshold_rp_years': target_rp,
                'threshold_discharge_m3s': val_target_rp,
                'alert_status': alert_status,
                'threshold_2yr_m3s': val_2yr,
                'threshold_5yr_m3s': val_5yr,
                **stats
            })
        
        ds.close()
    
    ds_2yr.close()
    ds_5yr.close()
    
    if not results_by_month:
        print(f"ERROR: No results generated for {country_config['name']}")
        return None
    
    # Convert to DataFrames
    dfs_by_month = {}
    for year_month, results in results_by_month.items():
        df = pd.DataFrame(results)
        df = df.sort_values('forecast_date').reset_index(drop=True)
        dfs_by_month[year_month] = df
    
    return dfs_by_month
