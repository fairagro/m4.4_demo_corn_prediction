#!/usr/bin/env python3
import pandas as pd
import geopandas as gpd
from optparse import OptionParser
from scipy.spatial import cKDTree
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def nearest_merge(df_base, df_feat, lat_col="lat", lon_col="lon"):
    """
    Merge features from df_feat into df_base using nearest-neighbor matching based on coordinates.
    """
    tree = cKDTree(df_feat[[lat_col, lon_col]].values)
    dists, idxs = tree.query(df_base[["centroid_lat", "centroid_lon"]].values, k=1)
    merged = pd.concat([df_base.reset_index(drop=True), df_feat.iloc[idxs].reset_index(drop=True)], axis=1)
    return merged


def add_derived_features(df):
    """
    Add calculated features.
    """
    df["temp_range"] = df["temp_std"] * 2
    df["rain_per_month"] = df["rain_sum"] / 12
    df["clay_silt_ratio"] = df["clay"] / (df["silt"] + 1e-6)
    return df


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-g", "--geojson", dest="geojson", help="County GeoJSON file")
    parser.add_option("-w", "--weather", dest="weather", help="Weather CSV")
    parser.add_option("-s", "--soil", dest="soil", help="Soil CSV")
    (options, args) = parser.parse_args()

    if not all([options.geojson, options.weather, options.soil]):
        parser.error("-geojson, --weather, --soil required")

    # Load GeoJSON
    gdf = gpd.read_file(options.geojson)
    if "county_name_norm" not in gdf.columns:
        gdf["county_name_norm"] = gdf.get("NAME", gdf.index.astype(str)).str.upper()

    # Compute centroids in WGS84
    centroids = gdf.to_crs(epsg=5070).geometry.centroid.to_crs(epsg=4326)
    gdf["centroid_lon"] = centroids.x.values
    gdf["centroid_lat"] = centroids.y.values

    # Load weather and soil data
    weather_df = pd.read_csv(options.weather)
    soil_df = pd.read_csv(options.soil)

    weather_features = nearest_merge(gdf, weather_df, lat_col="lat", lon_col="lon")

    soil_features = nearest_merge(gdf, soil_df, lat_col="lat", lon_col="lon")

    # Drop geometry columns to avoid conflicts and remove duplicate centroid columns
    weather_features_clean = weather_features.drop(columns=["geometry"])
    soil_features_clean = soil_features.drop(columns=["geometry", "centroid_lat", "centroid_lon"])

    # Combine weather and soil features
    features_df = pd.concat([weather_features_clean.reset_index(drop=True),
                             soil_features_clean.reset_index(drop=True)], axis=1)

    # Add derived features
    features_df = add_derived_features(features_df)

    # Save output
    features_df.to_csv("county_features.csv", index=False)
