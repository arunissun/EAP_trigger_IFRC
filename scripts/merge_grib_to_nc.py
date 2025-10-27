import xarray as xr
import glob
import os
import sys

# Add config to path
sys.path.append('config')
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

    # Remove .idx files
    for idx_file in glob.glob(os.path.join(folder, "*.idx")):
        try:
            os.remove(idx_file)
        except Exception:
            pass

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
        if os.path.exists(output_nc):
            ds_old = xr.open_dataset(output_nc)
            old_days = set(ds_old.time.values.astype('datetime64[D]').astype(str))
        else:
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
        else:
            ds_combined = ds_new

        ds_combined = ds_combined.sortby('time')
        ds_combined.to_netcdf(output_nc)
        print(f"Merged data for {country_config['name']}, updated monthly NetCDF: {output_nc}")

if __name__ == "__main__":
    # Merge data for both countries
    for country in COUNTRIES.keys():
        print(f"\n=== Merging data for {COUNTRIES[country]['name']} ===")
        merge_country_data(country)
