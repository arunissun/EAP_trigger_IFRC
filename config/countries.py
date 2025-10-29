# Country configurations with bounding boxes and river coordinates
COUNTRIES = {
    "guatemala": {
        "name": "Guatemala",
        "bbox": [17.82, -92.23, 13.73, -88.23],  # [north, west, south, east]
        "river_coords": {
            "lat": 14.211,
            "lon": -90.341
        },
        "lisflood_coords": {
            "lat": 14.225,
            "lon": -90.325
        },
        "trigger": {
            "return_period": 3.0,  # 3-year return period
            "probability_threshold": 0.5,  # 50% probability
            "lead_time_days": 3
        }
    },
    "philippines": {
        "name": "Philippines", 
        "bbox": [18.51, 117.17, 5.58, 126.54],  # [north, west, south, east]
        "river_basins": {
            "cagayan": {
                "name": "Cagayan River Basin",
                "station_name": "Tuguegarao Buntun Bridge",
                "station_id": "G4630",
                "river_coords": {
                    "lat": 17.614,  # GloFAS reporting point
                    "lon": 121.688
                },
                "lisflood_coords": {
                    "lat": 17.614,
                    "lon": 121.688
                },
                "drainage_area_km2": 19910,
                "provinces": ["Cagayan", "Isabela"]
            },
            "bicol": {
                "name": "Bicol River Basin",
                "station_name": "Nabua",
                "station_id": "G4611",
                "river_coords": {
                    "lat": 13.404,  # GloFAS reporting point
                    "lon": 123.325
                },
                "lisflood_coords": {
                    "lat": 13.375,
                    "lon": 123.325
                },
                "drainage_area_km2": 869,
                "provinces": ["Camarines Sur", "Albay"]
            },
            "panay": {
                "name": "Panay River Basin",
                "station_name": "Dao Bridge",
                "station_id": "G5369",
                "river_coords": {
                    "lat": 11.392,  # GloFAS reporting point
                    "lon": 122.687
                },
                "lisflood_coords": {
                    "lat": 11.425,
                    "lon": 122.725
                },
                "drainage_area_km2": 1510,
                "provinces": ["Capiz"]
            },
            "agusan": {
                "name": "Agusan River Basin",
                "station_name": "Nia Pumping Station",
                "station_id": "G5368",
                "river_coords": {
                    "lat": 8.886,  # GloFAS reporting point
                    "lon": 125.541
                },
                "lisflood_coords": {
                    "lat": 8.875,
                    "lon": 125.575
                },
                "drainage_area_km2": 11514,
                "provinces": ["Agusan del Norte", "Agusan del Sur", "Compostela Valley"],
                "secondary_station": {
                    "station_name": "Talacogon Municipal Hall",
                    "station_id": "G4945",
                    "river_coords": {
                        "lat": 8.449,
                        "lon": 125.785
                    },
                    "lisflood_coords": {
                        "lat": 8.425,
                        "lon": 125.775
                    },
                    "drainage_area_km2": 7862
                }
            }
        },
        "trigger": {
            "return_period": 5.0,  # 5-year return period
            "probability_threshold": 0.7,  # 70% probability
            "lead_time_days": 3,
            "activation_rule": "ANY_BASIN"  # Activate if ANY basin meets threshold
        }
    }
}
