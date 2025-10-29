"""
Multi-basin flood trigger analysis (e.g., Philippines).
Analyzes ensemble forecasts for countries with multiple river basins.
Supports multiple stations per basin.
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

def analyze_station_location(ds_2yr, ds_5yr, ensemble_folder, country_code, country_config,
                            basin_code, basin_config, station_config, station_type,
                            lead_time_days, target_rp, probability_threshold):
    """
    Analyze a single station location within a basin.
    
    Args:
        ds_2yr: Dataset with 2-year return period data
        ds_5yr: Dataset with 5-year return period data
        ensemble_folder: Path to ensemble forecast files
        country_code: Country code
        country_config: Country configuration
        basin_code: Basin code
        basin_config: Basin configuration
        station_config: Station configuration (can be basin_config or secondary_station dict)
        station_type: 'primary' or 'secondary'
        lead_time_days: Lead time to analyze
        target_rp: Target return period
        probability_threshold: Probability threshold for alerts
    
    Returns:
        Dictionary of results by month {year_month: list of result dicts}
    """
    station_name = station_config['station_name']
    station_id = station_config['station_id']
    target_lat = station_config['lisflood_coords']['lat']
    target_lon = station_config['lisflood_coords']['lon']
    
    print(f"\n   >>> Analyzing Station: {station_name} ({station_id}) [{station_type.upper()}]")
    
    # Get thresholds
    val_2yr, grid_lat, grid_lon = get_return_period_value(ds_2yr, target_lat, target_lon, 'rl_2.0')
    val_5yr, _, _ = get_return_period_value(ds_5yr, target_lat, target_lon, 'rl_5.0')
    val_target_rp = interpolate_return_period(val_2yr, val_5yr, target_rp=target_rp)
    
    print(f"       Location: Lat {grid_lat:.3f}, Lon {grid_lon:.3f}")
    print(f"       Thresholds: 2yr={val_2yr:.1f}, {target_rp}yr={val_target_rp:.1f}, 5yr={val_5yr:.1f} m3/s")
    
    # Find ensemble files
    nc_pattern = os.path.join(ensemble_folder, f"glofas_{country_code}_ensemble_*_combined.nc")
    nc_files = sorted(glob.glob(nc_pattern))
    
    if not nc_files:
        print(f"       WARNING: No ensemble files found")
        return {}
    
    results_by_month = {}
    
    for nc_file in nc_files:
        filename = os.path.basename(nc_file)
        match = re.search(r'ensemble_(\d{4})_(\d{2})_combined\.nc', filename)
        if not match:
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
            print(f"       WARNING: {lead_time_days}-day lead time not available")
            ds.close()
            continue
        
        lead_idx = np.where(lead_times_days_array == lead_time_days)[0][0]
        dates = ds.time.values.astype('datetime64[D]').astype(str)
        
        # Analyze each date
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
                'basin_name': basin_config['name'],
                'basin_code': basin_code,
                'station_name': station_name,
                'station_id': station_id,
                'station_type': station_type,
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
    
    return results_by_month

def analyze_multibasin_triggers(country_code, country_config, lead_time_days, target_rp, probability_threshold):
    """
    Analyze triggers for countries with multiple river basins (e.g., Philippines).
    Supports multiple stations per basin (primary + secondary).
    
    Args:
        country_code: Country code
        country_config: Country configuration dictionary
        lead_time_days: Lead time to analyze
        target_rp: Target return period
        probability_threshold: Probability threshold for alerts
    
    Returns:
        Nested dictionary {basin_code: {station_type: {year_month: df}}}
    """
    ensemble_folder = f"data/{country_code}/ensemble_forecast"
    
    # Load return period data
    rp_folder = f"data/{country_code}/return_periods"
    rp_file_2yr = os.path.join(rp_folder, "flood_threshold_glofas_v4_rl_2.0.nc")
    rp_file_5yr = os.path.join(rp_folder, "flood_threshold_glofas_v4_rl_5.0.nc")
    
    if not os.path.exists(rp_file_2yr) or not os.path.exists(rp_file_5yr):
        print(f"ERROR: Return period files not found for {country_code}")
        return None
    
    ds_2yr = xr.open_dataset(rp_file_2yr)
    ds_5yr = xr.open_dataset(rp_file_5yr)
    
    print(f"\n{'='*70}")
    print(f"MULTI-BASIN FLOOD TRIGGER ANALYSIS: {country_config['name']}")
    print(f"{'='*70}")
    print(f"Trigger Criteria:")
    print(f"   - Return Period: {target_rp}-year")
    print(f"   - Probability Threshold: {probability_threshold*100:.0f}%")
    print(f"   - Lead Time: {lead_time_days} days")
    print(f"   - Activation Rule: {country_config['trigger'].get('activation_rule', 'ANY_BASIN')}")
    print(f"   - Number of Basins: {len(country_config['river_basins'])}")
    print(f"{'='*70}\n")
    
    # Store results for each basin and station
    all_basins_results = {}
    
    for basin_code, basin_config in country_config['river_basins'].items():
        print(f"\n>>> Analyzing Basin: {basin_config['name']}")
        print(f"    Provinces: {', '.join(basin_config['provinces'])}")
        
        basin_results = {}
        
        # Analyze primary station
        primary_results = analyze_station_location(
            ds_2yr, ds_5yr, ensemble_folder, country_code, country_config,
            basin_code, basin_config, basin_config, 'primary',
            lead_time_days, target_rp, probability_threshold
        )
        
        if primary_results:
            basin_results['primary'] = primary_results
        
        # Analyze secondary station if it exists
        if 'secondary_station' in basin_config:
            secondary_results = analyze_station_location(
                ds_2yr, ds_5yr, ensemble_folder, country_code, country_config,
                basin_code, basin_config, basin_config['secondary_station'], 'secondary',
                lead_time_days, target_rp, probability_threshold
            )
            
            if secondary_results:
                basin_results['secondary'] = secondary_results
        
        if basin_results:
            all_basins_results[basin_code] = basin_results
    
    ds_2yr.close()
    ds_5yr.close()
    
    if not all_basins_results:
        print(f"\nERROR: No results generated for any basin")
        return None
    
    # Convert to DataFrames
    final_results = {}
    for basin_code, station_results in all_basins_results.items():
        final_results[basin_code] = {}
        for station_type, results_by_month in station_results.items():
            station_dfs = {}
            for year_month, results in results_by_month.items():
                df = pd.DataFrame(results)
                df = df.sort_values('forecast_date').reset_index(drop=True)
                station_dfs[year_month] = df
            final_results[basin_code][station_type] = station_dfs
    
    return final_results
