#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: Workflow

inputs:
- id: geojson
  type: File
- id: soil
  type: File
- id: yield
  type: File

outputs:
- id: iowa_county_yields
  type: File
  outputSource: plot_yields/iowa_county_yields

steps:
- id: get_soil
  in:
  - id: geojson
    source: geojson
  - id: soil_cache
    source: soil
  run: ../get_soil/get_soil.cwl
  out:
  - soil
- id: get_weather
  in:
  - id: geojson
    source: geojson
  run: ../get_weather/get_weather.cwl
  out:
  - weather
- id: merge_features
  in:
  - id: geojson
    source: geojson
  - id: soil
    source: get_soil/soil
  - id: weather
    source: get_weather/weather
  run: ../merge_features/merge_features.cwl
  out:
  - county_features
- id: train_model
  in:
  - id: yield
    source: yield
  - id: features
    source: merge_features/county_features
  run: ../train_model/train_model.cwl
  out:
  - model
  - scaler
- id: predict_yields
  in:
  - id: model
    source: train_model/model
  - id: scaler
    source: train_model/scaler
  - id: features
    source: merge_features/county_features
  run: ../predict_yields/predict_yields.cwl
  out:
  - county_predictions
- id: plot_yields
  in:
  - id: predictions
    source: predict_yields/county_predictions
  - id: geojson
    source: geojson
  run: ../plot_yields/plot_yields.cwl
  out:
  - iowa_county_yields
