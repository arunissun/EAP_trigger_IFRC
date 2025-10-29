"""
Utility functions for flood trigger analysis.
Contains shared functions for return period calculations and data extraction.
"""
import numpy as np
import xarray as xr

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
    log_2 = np.log(2.0)
    log_5 = np.log(5.0)
    log_target = np.log(target_rp)
    
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

def calculate_ensemble_statistics(ensemble_values, threshold):
    """
    Calculate statistics for ensemble forecast values.
    
    Args:
        ensemble_values: Array of ensemble member values
        threshold: Threshold value for exceedance calculation
    
    Returns:
        Dictionary of statistics or None if no valid data
    """
    valid_ensemble = ensemble_values[~np.isnan(ensemble_values)]
    
    if len(valid_ensemble) == 0:
        return None
    
    total_members = len(valid_ensemble)
    exceeding_members = np.sum(valid_ensemble > threshold)
    probability = exceeding_members / total_members
    
    median_discharge = np.median(valid_ensemble)
    mean_discharge = np.mean(valid_ensemble)
    min_discharge = np.min(valid_ensemble)
    max_discharge = np.max(valid_ensemble)
    p25_discharge = np.percentile(valid_ensemble, 25)
    p75_discharge = np.percentile(valid_ensemble, 75)
    
    median_exceeds = median_discharge > threshold
    median_exceedance_pct = ((median_discharge / threshold) - 1) * 100
    
    return {
        'total_members': total_members,
        'exceeding_members': exceeding_members,
        'exceedance_probability': probability,
        'median_discharge_m3s': median_discharge,
        'mean_discharge_m3s': mean_discharge,
        'min_discharge_m3s': min_discharge,
        'max_discharge_m3s': max_discharge,
        'p25_discharge_m3s': p25_discharge,
        'p75_discharge_m3s': p75_discharge,
        'median_exceeds_threshold': median_exceeds,
        'median_exceedance_pct': median_exceedance_pct
    }

def determine_alert_status(probability, probability_threshold):
    """
    Determine alert status based on exceedance probability.
    
    HIGH: Probability meets or exceeds the configured threshold
    MODERATE: Probability is between (threshold - 20%) and threshold
    LOW: Probability is below (threshold - 20%)
    
    Examples:
        Guatemala (threshold=0.5): HIGH ≥50%, MODERATE 30-49%, LOW <30%
        Philippines (threshold=0.7): HIGH ≥70%, MODERATE 50-69%, LOW <50%
    
    Args:
        probability: Exceedance probability (0-1)
        probability_threshold: Threshold for HIGH alert
    
    Returns:
        Alert status string: 'HIGH', 'MODERATE', or 'LOW'
    """
    if probability >= probability_threshold:
        return "HIGH"
    elif probability >= (probability_threshold - 0.2):
        return "MODERATE"
    else:
        return "LOW"
