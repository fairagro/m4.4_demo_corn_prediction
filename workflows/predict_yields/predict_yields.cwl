#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

requirements:
- class: InitialWorkDirRequirement
  listing:
  - entryname: code/predict_yields.py
    entry:
      $include: ../../code/predict_yields.py
- class: DockerRequirement
  dockerFile:
    $include: ../../Dockerfile
  dockerImageId: pyplot
- class: NetworkAccess
  networkAccess: true

inputs:
- id: features
  type: File
  default:
    class: File
    location: ../../county_features.csv
  inputBinding:
    prefix: --features
- id: model
  type: File
  default:
    class: File
    location: ../../model.pkl
  inputBinding:
    prefix: --model
- id: scaler
  type: File
  default:
    class: File
    location: ../../scaler.pkl
  inputBinding:
    prefix: --scaler

outputs:
- id: county_predictions
  type: File
  outputBinding:
    glob: county_predictions.csv

baseCommand:
- python
- code/predict_yields.py
