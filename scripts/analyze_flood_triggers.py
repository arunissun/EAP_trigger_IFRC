import xarray as xr
import numpy as np
import pandas as pd
import os
import glob
import sys

# Add config to path
sys.path.append('config')
from countries import COUNTRIES

def interpolate_return_period(val_2yr, val_5yr, target_rp=3.0):
    """
    Interpolate return period value using logarithmic interpolation.
    
    Return periods follow a logarithmic relationship in flood frequency analysis.
    This method interpolates between known return periods to estimate intermediate values.
    
    Args:
        val_2yr: 2-year return period discharge value (m³/s)
        val_5yr: 5-year return period discharge value (m³/s)
        target_rp: Target return period in years (default 3.0)
    
    Returns:
        Interpolated discharge value for target return period (m³/s)
    """
    # Logarithmic interpolation formula
    log_2 = np.log(2.0)
    log_5 = np.log(5.0)
    log_target = np.log(target_rp)
    
    # Linear interpolation in log space
    val_target = val_2yr + (val_5yr - val_2yr) * (log_target - log_2) / (log_5 - log_2)
    
    return val_target

def get_return_period_value(ds, lat, lon, varname):
    """
    Find the nearest return period value at the given lat/lon coordinates.
    
    Args:
        ds: xarray Dataset containing return period data
        lat: Target latitude
        lon: Target longitude
        varname: Variable name (e.g., 'rl_2.0', 'rl_5.0')
    
    Returns:
        Tuple of (value, actual_lat, actual_lon)
    """
    ilat = np.abs(ds['lat'].values - lat).argmin()
    ilon = np.abs(ds['lon'].values - lon).argmin()
    return ds[varname].values[ilat, ilon], ds['lat'].values[ilat], ds['lon'].values[ilon]

def analyze_flood_triggers(country_code, lead_time_days=3, target_rp=3.0, probability_threshold=0.5):
    """
    Analyze GloFAS ensemble forecasts for flood trigger conditions.
    
    This function checks when the ensemble forecast exceeds a specified probability
    threshold for a given return period at a specific lead time.
    
    Args:
        country_code: Country code from COUNTRIES config
        lead_time_days: Lead time to analyze (default 3 days)
        target_rp: Target return period in years (default 3.0)
        probability_threshold: Probability threshold for alerts (default 0.5 = 50%)
    
    Returns:
        DataFrame with analysis results for all forecast dates
    """
    if country_code not in COUNTRIES:
        print(f"ERROR: Country '{country_code}' not found in configuration")
        return None
    
    country_config = COUNTRIES[country_code]
    ensemble_folder = f"data/{country_code}/ensemble_forecast"
    
    target_lat = country_config["river_coords"]["lat"]
    target_lon = country_config["river_coords"]["lon"]
    
    # Load return period data
    rp_folder = f"data/{country_code}/return_periods"
    rp_file_2yr = os.path.join(rp_folder, "flood_threshold_glofas_v4_rl_2.0.nc")
    rp_file_5yr = os.path.join(rp_folder, "flood_threshold_glofas_v4_rl_5.0.nc")
    
    if not os.path.exists(rp_file_2yr) or not os.path.exists(rp_file_5yr):
        print(f"ERROR: Return period files not found for {country_code}")
        print(f"   Expected: {rp_file_2yr}")
        print(f"   Expected: {rp_file_5yr}")
        return None
    
    # Load and interpolate return periods
    ds_2yr = xr.open_dataset(rp_file_2yr)
    ds_5yr = xr.open_dataset(rp_file_5yr)
    
    val_2yr, grid_lat, grid_lon = get_return_period_value(ds_2yr, target_lat, target_lon, 'rl_2.0')
    val_5yr, _, _ = get_return_period_value(ds_5yr, target_lat, target_lon, 'rl_5.0')
    
    # Interpolate target return period (3-year)
    val_target_rp = interpolate_return_period(val_2yr, val_5yr, target_rp=target_rp)
    
    print(f"\n{'='*70}")
    print(f"FLOOD TRIGGER ANALYSIS: {country_config['name']}")
    print(f"{'='*70}")
    print(f"Location: Lat {grid_lat:.3f}, Lon {grid_lon:.3f}")
    print(f"Return Period Thresholds:")
    print(f"   - 2-year RP:  {val_2yr:.2f} m3/s")
    print(f"   - 3-year RP:  {val_target_rp:.2f} m3/s (interpolated)")
    print(f"   - 5-year RP:  {val_5yr:.2f} m3/s")
    print(f"Lead time:   {lead_time_days} days")
    print(f"Alert threshold: {probability_threshold*100:.0f}% probability")
    print(f"{'='*70}\n")
    
    # Find all ensemble NetCDF files
    nc_pattern = os.path.join(ensemble_folder, f"glofas_{country_code}_ensemble_*_combined.nc")
    nc_files = sorted(glob.glob(nc_pattern))
    
    if not nc_files:
        print(f"WARNING: No ensemble NetCDF files found in {ensemble_folder}")
        print(f"   Pattern searched: {nc_pattern}")
        return None
    
    print(f"Found {len(nc_files)} ensemble file(s) to analyze")
    
    # Group results by month for proper CSV organization
    results_by_month = {}
    
    for nc_file in nc_files:
        filename = os.path.basename(nc_file)
        print(f"\nProcessing: {filename}")
        
        # Extract year and month from filename
        # Expected pattern: glofas_{country}_ensemble_2025_10_combined.nc
        import re
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
        
        # Get discharge data: shape (time, ensemble_members, lead_time)
        discharge_data = ds.dis24.isel(latitude=ilat, longitude=ilon).values
        
        # Convert step to days
        lead_times_days_array = ds.step.values.astype('timedelta64[D]').astype(int)
        
        # Find index for specified lead time
        if lead_time_days not in lead_times_days_array:
            print(f"WARNING: {lead_time_days}-day lead time not available in data")
            print(f"   Available lead times: {lead_times_days_array}")
            ds.close()
            continue
        
        lead_idx = np.where(lead_times_days_array == lead_time_days)[0][0]
        
        # Get forecast dates
        dates = ds.time.values.astype('datetime64[D]').astype(str)
        
        # Analyze each forecast date
        for t in range(discharge_data.shape[0]):
            # Get ensemble members at specified lead time
            ensemble_values = discharge_data[t, :, lead_idx]
            
            # Remove NaN values
            valid_ensemble = ensemble_values[~np.isnan(ensemble_values)]
            
            if len(valid_ensemble) == 0:
                print(f"WARNING: No valid ensemble data for {dates[t]}, skipping")
                continue
            
            # Calculate statistics
            total_members = len(valid_ensemble)
            exceeding_members = np.sum(valid_ensemble > val_target_rp)
            probability = exceeding_members / total_members
            
            # Discharge statistics
            median_discharge = np.median(valid_ensemble)
            mean_discharge = np.mean(valid_ensemble)
            min_discharge = np.min(valid_ensemble)
            max_discharge = np.max(valid_ensemble)
            p25_discharge = np.percentile(valid_ensemble, 25)
            p75_discharge = np.percentile(valid_ensemble, 75)
            
            # Check if median exceeds threshold (alternative trigger)
            median_exceeds = median_discharge > val_target_rp
            
            # Calculate exceedance magnitude
            median_exceedance_pct = ((median_discharge / val_target_rp) - 1) * 100
            
            # Determine alert status
            alert_status = "HIGH" if probability >= probability_threshold else "MODERATE" if probability >= 0.3 else "LOW"
            
            # Store results
            results_by_month[year_month].append({
                'country': country_config['name'],
                'country_code': country_code,
                'forecast_date': dates[t],
                'lead_time_days': lead_time_days,
                'latitude': ds.latitude.values[ilat],
                'longitude': ds.longitude.values[ilon],
                'threshold_rp_years': target_rp,
                'threshold_discharge_m3s': val_target_rp,
                'exceedance_probability': probability,
                'exceeding_members': exceeding_members,
                'total_members': total_members,
                'median_discharge_m3s': median_discharge,
                'mean_discharge_m3s': mean_discharge,
                'min_discharge_m3s': min_discharge,
                'max_discharge_m3s': max_discharge,
                'p25_discharge_m3s': p25_discharge,
                'p75_discharge_m3s': p75_discharge,
                'median_exceeds_threshold': median_exceeds,
                'median_exceedance_pct': median_exceedance_pct,
                'alert_status': alert_status,
                'threshold_2yr_m3s': val_2yr,
                'threshold_5yr_m3s': val_5yr
            })
        
        ds.close()
    
    # Return dictionary of DataFrames by month
    if not results_by_month:
        print(f"ERROR: No results generated for {country_config['name']}")
        return None
    
    # Convert to DataFrames and return
    dfs_by_month = {}
    for year_month, results in results_by_month.items():
        df = pd.DataFrame(results)
        df = df.sort_values('forecast_date').reset_index(drop=True)
        dfs_by_month[year_month] = df
    
    return dfs_by_month

def save_results(df, country_code, year_month, lead_time_days=3, target_rp=3.0):
    """
    Save analysis results to CSV file (monthly).
    
    File structure: data/{country}/analysis/flood_trigger_analysis_{year}_{month}_{rp}yr_lead{days}d.csv
    
    Args:
        df: DataFrame with analysis results
        country_code: Country code
        year_month: Year and month string (e.g., '2025_10')
        lead_time_days: Lead time analyzed
        target_rp: Target return period
    """
    if df is None or df.empty:
        print(f"WARNING: No data to save for {country_code}")
        return
    
    # Create output directory: country/analysis/
    output_dir = os.path.join("data", country_code, "analysis")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with year_month in the name
    output_file = os.path.join(
        output_dir, 
        f"flood_trigger_analysis_{year_month}_{int(target_rp)}yr_lead{lead_time_days}d.csv"
    )
    
    # Check if file exists and merge with existing data
    if os.path.exists(output_file):
        print(f"Existing file found: {os.path.basename(output_file)}")
        existing_df = pd.read_csv(output_file)
        
        # Get dates already in existing file
        existing_dates = set(existing_df['forecast_date'].values)
        new_dates = set(df['forecast_date'].values)
        
        # Filter out dates that already exist
        dates_to_add = new_dates - existing_dates
        
        if not dates_to_add:
            print(f"All dates already analyzed. No new data to add.")
            return output_file
        
        print(f"Found {len(dates_to_add)} new date(s) to add:")
        for date in sorted(dates_to_add):
            print(f"   + {date}")
        
        # Keep only new dates from df
        df_new = df[df['forecast_date'].isin(dates_to_add)].copy()
        
        # Combine with existing data
        df_combined = pd.concat([existing_df, df_new], ignore_index=True)
        df_combined = df_combined.sort_values('forecast_date').reset_index(drop=True)
        
        # Save combined data
        df_combined.to_csv(output_file, index=False, float_format='%.3f')
        print(f"Updated existing file with {len(df_new)} new record(s)")
        
        # Use combined df for summary
        df = df_combined
    else:
        print(f"Creating new file: {os.path.basename(output_file)}")
        # Save to CSV
        df.to_csv(output_file, index=False, float_format='%.3f')
        print(f"Saved {len(df)} new record(s)")
    
    print(f"\n{'='*70}")
    print(f"RESULTS SAVED")
    print(f"{'='*70}")
    print(f"File: {output_file}")
    print(f"Total records: {len(df)}")
    
    # Summary statistics
    high_risk_days = len(df[df['exceedance_probability'] >= 0.5])
    moderate_risk_days = len(df[(df['exceedance_probability'] >= 0.3) & (df['exceedance_probability'] < 0.5)])
    low_risk_days = len(df[df['exceedance_probability'] < 0.3])
    
    print(f"\nRISK SUMMARY:")
    print(f"   HIGH Risk (>=50% probability):     {high_risk_days} days")
    print(f"   MODERATE Risk (30-50% probability): {moderate_risk_days} days")
    print(f"   LOW Risk (<30% probability):       {low_risk_days} days")
    
    if high_risk_days > 0:
        print(f"\nHIGH RISK DAYS:")
        high_risk_df = df[df['exceedance_probability'] >= 0.5].copy()
        for _, row in high_risk_df.iterrows():
            print(f"   - {row['forecast_date']}: {row['exceedance_probability']*100:.1f}% probability")
            print(f"     Median: {row['median_discharge_m3s']:.1f} m3/s ({row['median_exceedance_pct']:+.1f}% vs threshold)")
    
    print(f"{'='*70}\n")
    
    return output_file

def main():
    """Main execution function."""
    print("\n" + "="*70)
    print("GLOFAS FLOOD TRIGGER ANALYSIS")
    print("="*70)
    print("Analyzing ensemble forecasts for flood risk conditions")
    print("="*70 + "\n")
    
    # Configuration
    LEAD_TIME_DAYS = 3
    TARGET_RETURN_PERIOD = 3.0
    PROBABILITY_THRESHOLD = 0.5
    
    # Analyze all configured countries
    for country_code in COUNTRIES.keys():
        dfs_by_month = analyze_flood_triggers(
            country_code=country_code,
            lead_time_days=LEAD_TIME_DAYS,
            target_rp=TARGET_RETURN_PERIOD,
            probability_threshold=PROBABILITY_THRESHOLD
        )
        
        if dfs_by_month is not None:
            # Save each month's results separately
            for year_month, df in dfs_by_month.items():
                save_results(
                    df=df,
                    country_code=country_code,
                    year_month=year_month,
                    lead_time_days=LEAD_TIME_DAYS,
                    target_rp=TARGET_RETURN_PERIOD
                )
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
