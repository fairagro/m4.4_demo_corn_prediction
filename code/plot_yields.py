import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-p", "--predictions", dest="predictions", default="county_predictions.csv")
parser.add_option("-g", "--geojson", dest="geojson", default="iowa_counties.geojson")
(options, args) = parser.parse_args()

# Load Iowa counties GeoJSON
counties_gdf = gpd.read_file(options.geojson)

# Load predictions
pred_df = pd.read_csv(options.predictions)

# Merge on county name
gdf = counties_gdf.merge(
    pred_df[["county_name_norm","Predicted_Yield"]],
    on="county_name_norm",
    how="left"
)

# Plot nicer choropleth
fig, ax = plt.subplots(figsize=(10, 10))
gdf.plot(
    column="Predicted_Yield",
    cmap="YlGn",
    linewidth=0.5,
    edgecolor="white",
    legend=True,
    legend_kwds={
        "label": "Predicted Yield (bushels/acre)",
        "orientation": "horizontal",
        "shrink": 0.6,
        "pad": 0.02
    },
    ax=ax
)

# Style tweaks
ax.set_title("Predicted Corn Yield per Iowa County", fontsize=18, pad=15, weight="bold")
ax.set_axis_off()
fig.set_facecolor("white")

# Save
plt.savefig("iowa_county_yields.png", dpi=300, bbox_inches="tight")
