"""
Crop global return period files to country-specific bounding boxes.

This script:
1. Reads global return period NetCDF files (from data/global/ or data/return_periods/)
2. Crops them to each country's bbox defined in config/countries.py
3. Saves cropped files to data/{country}/return_periods/
4. Reports file size reduction (~99% smaller)

Important:
- Global files are KEPT (not deleted) for reference and future use
- Only cropped country files are tracked by Git LFS
- Global files are ignored via .gitignore (kept locally but not pushed)

Usage:
    python scripts/crop_return_periods.py

This script can be reused for adding new countries in the future.
"""

import xarray as xr
import os
import sys
import shutil

# Add config to path (use absolute path based on script location)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # Go up one level from scripts/
config_path = os.path.join(project_root, 'config')
sys.path.insert(0, config_path)

from countries import COUNTRIES

def get_file_size_mb(filepath):
    """Get file size in MB"""
    if os.path.exists(filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    return 0

def crop_return_period_file(global_file, country_code, return_period):
    """
    Crop a global return period file to a country's bounding box.
    
    Args:
        global_file: Path to global NetCDF file
        country_code: Country code from COUNTRIES config
        return_period: Return period value (e.g., '2.0', '5.0')
    
    Returns:
        Path to cropped file if successful, None otherwise
    """
    if not os.path.exists(global_file):
        print(f"ERROR: Global file not found: {global_file}")
        return None
    
    country_config = COUNTRIES[country_code]
    bbox = country_config["bbox"]  # [north, west, south, east]
    
    # Create output directory (use absolute path)
    output_dir = os.path.join(project_root, f"data/{country_code}/return_periods")
    os.makedirs(output_dir, exist_ok=True)
    
    # Output filename
    output_file = os.path.join(output_dir, f"flood_threshold_glofas_v4_rl_{return_period}.nc")
    
    print(f"\nProcessing: {country_config['name']} - {return_period}-year RP")
    print(f"  Input: {global_file}")
    print(f"  Bbox: N={bbox[0]}, W={bbox[1]}, S={bbox[2]}, E={bbox[3]}")
    
    try:
        # Open global dataset
        ds = xr.open_dataset(global_file)
        
        print(f"  Global dimensions: {dict(ds.dims)}")
        
        # Check if lat is ascending or descending
        lat_values = ds['lat'].values
        lat_ascending = lat_values[0] < lat_values[-1]
        
        print(f"  Lat order: {'ascending' if lat_ascending else 'descending'} ({lat_values[0]:.2f} to {lat_values[-1]:.2f})")
        
        # Crop to bounding box
        # bbox = [north, west, south, east]
        if lat_ascending:
            # If lat is ascending, slice from south to north
            ds_cropped = ds.sel(
                lat=slice(bbox[2], bbox[0]),  # south to north
                lon=slice(bbox[1], bbox[3])   # west to east
            )
        else:
            # If lat is descending, slice from north to south
            ds_cropped = ds.sel(
                lat=slice(bbox[0], bbox[2]),  # north to south (reversed for descending)
                lon=slice(bbox[1], bbox[3])   # west to east
            )
        
        print(f"  Cropped dimensions: {dict(ds_cropped.dims)}")
        
        # Check if cropping was successful
        if ds_cropped.dims['lat'] == 0 or ds_cropped.dims['lon'] == 0:
            print(f"  ERROR: Cropping resulted in empty dataset!")
            print(f"  Lat range in data: {lat_values.min():.2f} to {lat_values.max():.2f}")
            print(f"  Lon range in data: {ds['lon'].values.min():.2f} to {ds['lon'].values.max():.2f}")
            print(f"  Requested bbox: N={bbox[0]}, W={bbox[1]}, S={bbox[2]}, E={bbox[3]}")
            ds.close()
            return None
        
        # Save cropped version
        ds_cropped.to_netcdf(output_file)
        
        # Report sizes
        original_size = get_file_size_mb(global_file)
        cropped_size = get_file_size_mb(output_file)
        reduction = ((original_size - cropped_size) / original_size) * 100
        
        print(f"  Original size: {original_size:.1f} MB")
        print(f"  Cropped size: {cropped_size:.2f} MB")
        print(f"  Size reduction: {reduction:.1f}%")
        print(f"  Saved to: {output_file}")
        
        ds.close()
        ds_cropped.close()
        
        return output_file
        
    except Exception as e:
        print(f"  ERROR: Failed to crop file: {e}")
        return None

def crop_all_return_periods():
    """
    Crop all return period files for all configured countries.
    
    Note: Global files in data/global_temp/ will be kept for reference.
    """
    print("="*70)
    print("CROPPING GLOBAL RETURN PERIOD FILES TO COUNTRY BOUNDING BOXES")
    print("="*70)
    
    # Define return periods to process
    return_periods = ["2.0", "5.0"]
    
    # Look for global files in the global_temp folder
    global_files_found = {}
    
    for rp in return_periods:
        # Use absolute path based on project root
        global_file = os.path.join(project_root, f"data/global_temp/flood_threshold_glofas_v4_rl_{rp}.nc")
        
        if os.path.exists(global_file):
            global_files_found[rp] = global_file
            size_mb = get_file_size_mb(global_file)
            print(f"\nFound global {rp}-year RP file: {global_file}")
            print(f"  Size: {size_mb:.1f} MB")
        else:
            print(f"\nERROR: Global {rp}-year RP file not found at: {global_file}")
    
    if not global_files_found:
        print("\nERROR: No global return period files found in data/global_temp/")
        print("Please move the global files there first using:")
        print("  mkdir data\\global_temp")
        print("  move data\\guatemala\\return_periods\\*.nc data\\global_temp\\")
        return
    
    # Process each country
    for country_code in COUNTRIES.keys():
        print(f"\n{'='*70}")
        print(f">>> Processing {COUNTRIES[country_code]['name']}")
        print("="*70)
        
        for rp in return_periods:
            if rp not in global_files_found:
                print(f"  WARNING: Global {rp}-year RP file not found, skipping")
                continue
            
            global_file = global_files_found[rp]
            
            # Crop the file
            print(f"\n  Cropping {rp}-year RP file...")
            cropped_file = crop_return_period_file(global_file, country_code, rp)
    
    print(f"\n{'='*70}")
    print("CROPPING COMPLETE")
    print("="*70)
    
    # Summary
    print("\nCropped files created:")
    for country_code in COUNTRIES.keys():
        rp_folder = os.path.join(project_root, f"data/{country_code}/return_periods")
        if os.path.exists(rp_folder):
            files = [f for f in os.listdir(rp_folder) if f.endswith('.nc')]
            total_size = sum(get_file_size_mb(os.path.join(rp_folder, f)) for f in files)
            print(f"  {COUNTRIES[country_code]['name']}: {len(files)} files, {total_size:.2f} MB")
    
    print(f"\nGlobal files remain in: data/global_temp/")
    print("You can move them to data/global/ for storage or delete after verification.")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Crop global return period files to country-specific bounding boxes.\n'
                    'Global files are kept for reference, only cropped files are tracked by Git LFS.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    args = parser.parse_args()
    
    crop_all_return_periods()

if __name__ == "__main__":
    main()
