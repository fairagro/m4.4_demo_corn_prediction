#!/usr/bin/env python3
import pandas as pd
import numpy as np
import requests
import geopandas as gpd
import concurrent.futures
from optparse import OptionParser


def get_weather(coord, start="2020-01-01", end="2020-12-31"):
    lat, lon = coord
    url = (
        f"https://power.larc.nasa.gov/api/temporal/daily/point?"
        f"parameters=T2M,PRECTOT&community=AG&longitude={lon}&latitude={lat}"
        f"&start={start.replace('-', '')}&end={end.replace('-', '')}&format=JSON"
    )

    try:
        resp = requests.get(url, timeout=40).json()
        data = resp["properties"]["parameter"]
        temp = data.get("T2M", {})
        rain = data.get("PRECTOT", data.get("PRECTOTCORR", {}))
        df = pd.DataFrame(
            {
                "Date": list(temp.keys()),
                "Temperature": list(temp.values()),
                "Rainfall": list(rain.values()) if rain else [0] * len(temp),
            }
        )
        return df
    except Exception as e:
        print(f"Weather fetch failed for lat={lat}, lon={lon}: {e}")
        return pd.DataFrame(columns=["Date", "Temperature", "Rainfall"])


def summarize_weather(weather_df):
    if weather_df.empty:
        return np.zeros(4)
    temp = weather_df["Temperature"].values
    rain = weather_df["Rainfall"].values
    return np.array([np.mean(temp), np.std(temp), np.sum(rain), np.std(rain)])


def load_county_centroids(geojson_file):
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


# --- CLI ---
if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-g", "--geojson", dest="geojson", help="Counties GeoJSON file")
    (options, args) = parser.parse_args()

    if not options.geojson:
        parser.error("Please provide --geojson")

    counties_df = load_county_centroids(options.geojson)
    rows = []

    coord_list = list(zip(counties_df["centroid_lat"], counties_df["centroid_lon"]))
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        weather = list(executor.map(get_weather, coord_list))
    
    for i, (_, row) in enumerate(counties_df.iterrows()):
        lat, lon = row["centroid_lat"], row["centroid_lon"]
        summary = summarize_weather(weather[i])
        rows.append([lat, lon] + summary.tolist())

    weather_summary_df = pd.DataFrame(
        rows, columns=["lat", "lon", "temp_mean", "temp_std", "rain_sum", "rain_std"]
    )
    weather_summary_df.to_csv("weather.csv", index=False)
