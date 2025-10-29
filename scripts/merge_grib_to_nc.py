import xarray as xr
import glob
import os
import sys

# Add config to path (use absolute path based on script location)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
config_path = os.path.join(project_root, 'config')
sys.path.insert(0, config_path)

from countries import COUNTRIES

def merge_country_data(country_code):
    if country_code not in COUNTRIES:
        print(f"Country '{country_code}' not found in configuration")
        return
    
    country_config = COUNTRIES[country_code]
    folder = f"data/{country_code}/ensemble_forecast"
    file_pattern = "*.grib2"
    file_list = sorted(glob.glob(os.path.join(folder, file_pattern)))

    if not file_list:
        print(f"No GRIB2 files found for {country_config['name']}, nothing to merge.")
        return

    

    # Sort files by year-month for monthly NetCDF creation
    files_by_month = {}
    for fpath in file_list:
        try:
            ds = xr.open_dataset(fpath, engine="cfgrib", backend_kwargs={"indexpath": ""})
            if "time" in ds.coords:
                # Handle both scalar and array time values
                time_vals = ds.time.values
                if time_vals.ndim == 0:  # scalar
                    ymd = str(time_vals.astype('datetime64[D]'))
                else:  # array
                    ymd = str(time_vals.astype('datetime64[D]')[0])
                year_month = f"{ymd[:4]}_{ymd[5:7]}"
                files_by_month.setdefault(year_month, []).append(fpath)
            ds.close()
        except Exception as e:
            print(f"Could not read {fpath}: {e}")

    # Create monthly NetCDF files
    for year_month, month_files in files_by_month.items():
        output_nc = os.path.join(folder, f"glofas_{country_code}_ensemble_{year_month}_combined.nc")

        # Get already-merged days
        ds_old = None
        old_days = set()
        
        if os.path.exists(output_nc):
            try:
                ds_old = xr.open_dataset(output_nc)
                old_days = set(ds_old.time.values.astype('datetime64[D]').astype(str))
            except Exception as e:
                print(f"Warning: Could not read existing file {output_nc}: {e}")
                print("Will overwrite the file.")
                ds_old = None
                old_days = set()

        # Find new files
        new_files = []
        for fpath in month_files:
            try:
                ds_test = xr.open_dataset(fpath, engine="cfgrib", backend_kwargs={"indexpath": ""})
                if "time" in ds_test.coords:
                    # Handle both scalar and array time values
                    time_vals = ds_test.time.values
                    if time_vals.ndim == 0:  # scalar
                        day_strs = [str(time_vals.astype('datetime64[D]'))]
                    else:  # array
                        day_strs = time_vals.astype('datetime64[D]').astype(str)
                    if any(day not in old_days for day in day_strs):
                        new_files.append(fpath)
                ds_test.close()
            except Exception as e:
                print(f"Skipping {fpath}: {e}")

        if not new_files:
            print(f"No new GRIB2 files to merge for {country_config['name']} {year_month}")
            continue

        ds_new = xr.open_mfdataset(
            new_files,
            engine="cfgrib",
            combine="nested", 
            concat_dim="time",
            parallel=False,
            backend_kwargs={"indexpath": ""},
        )

        # Longitude correction
        if "longitude" in ds_new.coords:
            ds_new = ds_new.assign_coords(longitude=ds_new.longitude.where(ds_new.longitude < 180, ds_new.longitude - 360))

        # Combine and save
        if ds_old is not None:
            ds_combined = xr.concat([ds_old, ds_new], dim='time')
            ds_old.close()  # Close the old dataset
        else:
            ds_combined = ds_new

        ds_combined = ds_combined.sortby('time')
        
        # Close the new dataset
        ds_new.close()
        
        # Save to a temporary file first, then rename to avoid permission issues
        import tempfile
        temp_fd, temp_path = tempfile.mkstemp(suffix='.nc', dir=os.path.dirname(output_nc))
        os.close(temp_fd)  # Close the file descriptor
        
        try:
            ds_combined.to_netcdf(temp_path)
            ds_combined.close()  # Close the combined dataset
            
            # Now move the temp file to the final location
            if os.path.exists(output_nc):
                os.remove(output_nc)  # Remove the old file
            os.rename(temp_path, output_nc)
            
            print(f"Merged data for {country_config['name']}, updated monthly NetCDF: {output_nc}")
        except Exception as e:
            # Clean up temp file if something went wrong
            if os.path.exists(temp_path):
                os.remove(temp_path)
            print(f"Error saving NetCDF file {output_nc}: {e}")
            print("This might be due to file permissions or the file being used by another process.")
            ds_combined.close()  # Make sure to close the dataset
            return

if __name__ == "__main__":
    # Merge data for both countries
    for country in COUNTRIES.keys():
        print(f"\n=== Merging data for {COUNTRIES[country]['name']} ===")
        merge_country_data(country)
