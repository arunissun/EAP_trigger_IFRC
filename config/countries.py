# Country configurations with bounding boxes and river coordinates
COUNTRIES = {
    "guatemala": {
        "name": "Guatemala",
        "bbox": [17.82, -92.23, 13.73, -88.23],  # [north, west, south, east]
        "river_coords": {
            "lat": 14.211,
            "lon": -90.341
        }
    },
    "philippines": {
        "name": "Philippines", 
        "bbox": [18.51, 117.17, 5.58, 126.54],  # [north, west, south, east] - from bounding box data
        "river_coords": {
            "lat": 14.5995,  # Manila area - adjust as needed
            "lon": 120.9842
        }
    }
}
