"""
Analysis utilities package for GloFAS flood trigger analysis.
"""
from .analysis_utils import (
    interpolate_return_period,
    get_return_period_value,
    calculate_ensemble_statistics,
    determine_alert_status
)
from .single_point_analysis import analyze_singlepoint_triggers
from .multibasin_analysis import analyze_multibasin_triggers

__all__ = [
    'interpolate_return_period',
    'get_return_period_value',
    'calculate_ensemble_statistics',
    'determine_alert_status',
    'analyze_singlepoint_triggers',
    'analyze_multibasin_triggers'
]
