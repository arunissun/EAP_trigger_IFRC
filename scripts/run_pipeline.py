"""
GloFAS EAP Pipeline Orchestrator

This script runs the complete flood forecasting pipeline in the correct sequence:
1. Download GloFAS ensemble forecast data
2. Merge daily GRIB2 files into monthly NetCDF files
3. Generate hydrograph plots with flood thresholds
4. Analyze flood triggers and generate alerts

Usage:
    python scripts/run_pipeline.py
"""

import subprocess
import sys
import os
from datetime import datetime

# Get the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# Define the pipeline stages
PIPELINE_STAGES = [
    {
        "name": "Download GloFAS Data",
        "script": "download_glofas.py",
        "description": "Downloading ensemble forecasts from Copernicus EWDS..."
    },
    {
        "name": "Merge GRIB to NetCDF",
        "script": "merge_grib_to_nc.py",
        "description": "Merging daily GRIB2 files into monthly NetCDF files..."
    },
    {
        "name": "Plot Hydrographs",
        "script": "plot_hydrographs.py",
        "description": "Generating hydrograph plots with flood thresholds..."
    },
    {
        "name": "Analyze Flood Triggers",
        "script": "analyze_flood_triggers.py",
        "description": "Analyzing forecasts and generating trigger alerts..."
    }
]

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def run_stage(stage_num, total_stages, stage_config):
    """Run a single pipeline stage"""
    script_name = stage_config["script"]
    script_path = os.path.join(script_dir, script_name)
    
    print(f"\nStage {stage_num}/{total_stages}: {stage_config['name']}")
    
    # Check if script exists
    if not os.path.isfile(script_path):
        print(f"ERROR: Script not found: {script_path}")
        return False
    
    try:
        # Run the script
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=script_dir,
            check=True,
            capture_output=False
        )
        
        print(f"Stage {stage_num} completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Stage {stage_num} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Run the complete pipeline"""
    print_header("GloFAS EAP PIPELINE ORCHESTRATOR")
    
    # Print pipeline overview
    print("\nPipeline Overview:")
    for i, stage in enumerate(PIPELINE_STAGES, 1):
        print(f"  {i}. {stage['name']}")
    
    print(f"\nStarting: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run each stage in sequence
    completed_stages = 0
    total_stages = len(PIPELINE_STAGES)
    
    for stage_num, stage_config in enumerate(PIPELINE_STAGES, 1):
        success = run_stage(stage_num, total_stages, stage_config)
        
        if success:
            completed_stages += 1
        else:
            print(f"\nPipeline stopped at stage {stage_num}")
            print(f"Completed {completed_stages}/{total_stages} stages\n")
            return False
    
    # Pipeline completed successfully
    print_header("PIPELINE COMPLETED SUCCESSFULLY")
    print(f"All {total_stages} stages completed successfully")
    print(f"Completion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nPipeline interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
