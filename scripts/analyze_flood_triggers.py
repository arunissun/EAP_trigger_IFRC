"""
Main script for GloFAS flood trigger analysis.
Coordinates analysis for all configured countries and saves results.
"""
import os
import sys
import pandas as pd

# Add config to path (use absolute path based on script location)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
config_path = os.path.join(project_root, 'config')
sys.path.insert(0, config_path)

from countries import COUNTRIES
from analysis_utils import analyze_singlepoint_triggers, analyze_multibasin_triggers

def analyze_flood_triggers(country_code, lead_time_days=None, target_rp=None, probability_threshold=None):
    """
    Analyze GloFAS ensemble forecasts for flood trigger conditions.
    
    Supports both single-point (Guatemala) and multi-basin (Philippines) configurations.
    Uses country-specific trigger settings from COUNTRIES config.
    
    Args:
        country_code: Country code from COUNTRIES config
        lead_time_days: Lead time to analyze (overrides config if provided)
        target_rp: Target return period in years (overrides config if provided)
        probability_threshold: Probability threshold for alerts (overrides config if provided)
    
    Returns:
        Dictionary of DataFrames by month (and by basin for multi-basin countries)
    """
    if country_code not in COUNTRIES:
        print(f"ERROR: Country '{country_code}' not found in configuration")
        return None
    
    country_config = COUNTRIES[country_code]
    
    # Get trigger parameters from config or use provided overrides
    trigger_config = country_config.get('trigger', {})
    lead_time_days = lead_time_days or trigger_config.get('lead_time_days', 3)
    target_rp = target_rp or trigger_config.get('return_period', 3.0)
    
    # Require probability_threshold from config or override; no default
    if probability_threshold is None:
        probability_threshold = trigger_config.get('probability_threshold')
        if probability_threshold is None:
            raise ValueError(f"ERROR: No probability_threshold found in config for {country_code}. Provide as override.")
    
    # Check if multi-basin configuration (Philippines)
    if 'river_basins' in country_config:
        return analyze_multibasin_triggers(
            country_code, country_config, 
            lead_time_days, target_rp, probability_threshold
        )
    else:
        # Single-point configuration (Guatemala)
        return analyze_singlepoint_triggers(
            country_code, country_config,
            lead_time_days, target_rp, probability_threshold
        )

def save_results(df, country_code, year_month, lead_time_days, target_rp, basin_code=None, station_id=None):
    """
    Save analysis results to Excel file only (no CSV).
    
    For multi-station configurations, creates separate sheets named by station_id in a single Excel file.
    
    Args:
        df: DataFrame with analysis results
        country_code: Country code
        year_month: Year and month string (e.g., '2025_10')
        lead_time_days: Lead time analyzed
        target_rp: Target return period
        basin_code: Basin code (optional, for multi-basin countries)
        station_id: Station ID for sheet name (optional, for multi-station configs)
    
    Returns:
        Path to saved file or None
    """
    if df is None or df.empty:
        print(f"WARNING: No data to save")
        return None
    
    # Create output directory
    if basin_code:
        output_dir = os.path.join("data", country_code, "analysis", basin_code)
    else:
        output_dir = os.path.join("data", country_code, "analysis")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate Excel filename
    excel_file = os.path.join(
        output_dir,
        f"flood_trigger_analysis_{year_month}_{int(target_rp)}yr_lead{lead_time_days}d.xlsx"
    )
    
    # Determine sheet name
    sheet_name = station_id if station_id else 'results'
    
    # Check if Excel file exists
    if os.path.exists(excel_file):
        # Read existing Excel file and update/add sheet
        try:
            with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"Updated sheet '{sheet_name}' in {os.path.basename(excel_file)}")
        except Exception as e:
            print(f"ERROR: Could not update Excel file: {e}")
            return None
    else:
        # Create new Excel file
        try:
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"Created Excel file with sheet '{sheet_name}': {os.path.basename(excel_file)}")
        except Exception as e:
            print(f"ERROR: Could not create Excel file: {e}")
            return None
    
    # Print summary
    high_alerts = len(df[df['alert_status'] == 'HIGH'])
    moderate_alerts = len(df[df['alert_status'] == 'MODERATE'])
    low_alerts = len(df[df['alert_status'] == 'LOW'])
    
    print(f"   Total records: {len(df)}")
    print(f"   HIGH: {high_alerts}, MODERATE: {moderate_alerts}, LOW: {low_alerts}")
    
    if high_alerts > 0:
        print(f"   ⚠️  WARNING: {high_alerts} HIGH alert(s) detected!")
    
    return excel_file

def main():
    """Main execution function."""
    print("\n" + "="*70)
    print("GLOFAS FLOOD TRIGGER ANALYSIS")
    print("="*70)
    print("Analyzing ensemble forecasts for flood risk conditions")
    print("="*70 + "\n")
    
    # Analyze all configured countries
    for country_code in COUNTRIES.keys():
        results = analyze_flood_triggers(country_code=country_code)
        
        if results is not None:
            country_config = COUNTRIES[country_code]
            trigger_config = country_config.get('trigger', {})
            lead_time = trigger_config.get('lead_time_days', 3)
            target_rp = trigger_config.get('return_period', 3.0)
            
            # Check if multi-basin (Philippines) or single-point (Guatemala)
            if 'river_basins' in country_config:
                # Multi-basin: results = {basin_code: {station_type: {year_month: df}}}
                for basin_code, station_results in results.items():
                    print(f"\nSaving results for {basin_code} basin...")
                    for station_type, dfs_by_month in station_results.items():
                        print(f"  Processing {station_type} station...")
                        for year_month, df in dfs_by_month.items():
                            # Extract station_id from the first row of the dataframe
                            station_id = df.iloc[0]['station_id'] if not df.empty else station_type
                            save_results(
                                df=df,
                                country_code=country_code,
                                year_month=year_month,
                                lead_time_days=lead_time,
                                target_rp=target_rp,
                                basin_code=basin_code,
                                station_id=station_id
                            )
            else:
                # Single-point: results = {year_month: df}
                for year_month, df in results.items():
                    save_results(
                        df=df,
                        country_code=country_code,
                        year_month=year_month,
                        lead_time_days=lead_time,
                        target_rp=target_rp
                    )
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
