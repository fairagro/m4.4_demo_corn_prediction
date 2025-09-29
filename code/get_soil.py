#!/usr/bin/env python3
import pandas as pd
import numpy as np
import requests
import geopandas as gpd
from optparse import OptionParser
import time
import os


def get_soil(lat, lon, max_retries=1, wait=2, session=None):
    """Fetch soil data for a lat/lon with retries until valid values are returned."""
    # use shared session or create new    
    use_temp_session = session is None
    if use_temp_session:
        session = requests.Session()
    
    for attempt in range(max_retries):
        try:
            print(f"Fetching soil data for lat={lat:.4f}, lon={lon:.4f} (attempt {attempt+1})")
            params = {
                'lon': lon,
                'lat': lat,
                'property': ['clay', 'silt', 'sand', 'soc', 'phh2o'],
                'value': 'mean'
            }
            url = f"https://rest.isric.org/soilgrids/v2.0/properties/query"
            resp = session.get(url, params=params, timeout=30).json()
            props = resp.get("properties", {}).get("layers", [])

            def extract_mean(props, layer_name, scale=1.0):
                for layer in props:
                    if layer["name"] == layer_name:
                        vals = [d["values"].get("mean", np.nan) for d in layer["depths"]]
                        vals = [v for v in vals if v is not None]
                        if vals:
                            return np.nanmean(vals) * scale
                return np.nan

            clay = extract_mean(props, "clay")
            silt = extract_mean(props, "silt")
            sand = extract_mean(props, "sand")
            soc  = extract_mean(props, "soc")
            ph   = extract_mean(props, "phh2o", scale=0.1)

            values = np.array([clay, silt, sand, soc, ph])

            if not np.isnan(values).all():
                return values

        except Exception as e:
            print(f"⚠️ Soil fetch failed for lat={lat:.4f}, lon={lon:.4f}: {e}")

        time.sleep(wait)

    if use_temp_session:
            session.close()
    return np.array([np.nan] * 5)


def load_county_centroids(geojson_file):
    """Load county centroids from GeoJSON."""
    gdf = gpd.read_file(geojson_file)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    if "NAME" in gdf.columns:
        gdf["county_name_norm"] = gdf["NAME"].str.upper()
    else:
        gdf["county_name_norm"] = gdf.index.astype(str)
    gdf_proj = gdf.to_crs(epsg=5070)
    centroids_proj = gdf_proj.geometry.centroid
    centroids_wgs84 = gpd.GeoSeries(centroids_proj, crs=gdf_proj.crs).to_crs(epsg=4326)
    gdf["centroid_lon"] = centroids_wgs84.x.values
    gdf["centroid_lat"] = centroids_wgs84.y.values
    return gdf[["county_name_norm", "centroid_lat", "centroid_lon"]]


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-g", "--geojson", dest="geojson", help="Counties GeoJSON file")
    parser.add_option("-s", "--soil_cache", dest="soil", help="Soil cache CSV file (existing or new)")
    (options, args) = parser.parse_args()

    if not options.geojson or not options.soil:
        parser.error("Please provide --geojson and --soil")

    # Load centroids
    counties_df = load_county_centroids(options.geojson)

    # Load existing soil CSV if provided
    soil_df = pd.DataFrame(columns=["lat", "lon", "clay", "silt", "sand", "soc", "ph"])
    if os.path.exists(options.soil):
        try:
            soil_df = pd.read_csv(options.soil)
        except Exception:
            pass

    failed_rows = []
    repaired = 0
    added = 0

    # create shared session
    session = requests.Session()
    session.headers.update({
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'User-Agent': 'SoilDataFetcher/1.0'
    })
    
    # Iterate over counties
    for _, row in counties_df.iterrows():
        lat, lon = row["centroid_lat"], row["centroid_lon"]

        match = soil_df[
            np.isclose(soil_df["lat"], lat, atol=1e-3) &
            np.isclose(soil_df["lon"], lon, atol=1e-3)
        ]

        if not match.empty:
            idx = match.index[0]
            if pd.isna(match.loc[idx, ["clay", "silt", "sand", "soc", "ph"]]).all():
                soil_values = get_soil(lat, lon, session=session)
                if not np.isnan(soil_values).all():
                    soil_df.loc[idx, ["clay", "silt", "sand", "soc", "ph"]] = soil_values
                    repaired += 1
                else:
                    failed_rows.append([lat, lon])
        else:
            soil_values = get_soil(lat, lon, session=session)
            new_row = {
                "lat": lat, "lon": lon,
                "clay": soil_values[0], "silt": soil_values[1],
                "sand": soil_values[2], "soc": soil_values[3],
                "ph": soil_values[4]
            }
            soil_df = pd.concat([soil_df, pd.DataFrame([new_row])], ignore_index=True)
            if not np.isnan(soil_values).all():
                added += 1
            else:
                failed_rows.append([lat, lon])
                
    session.close()
    soil_df.to_csv("soil.csv", index=False)
