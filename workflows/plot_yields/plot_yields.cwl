#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

requirements:
- class: InitialWorkDirRequirement
  listing:
  - entryname: code/plot_yields.py
    entry:
      $include: ../../code/plot_yields.py
- class: DockerRequirement
  dockerFile:
    $include: ../../Dockerfile
  dockerImageId: pyplot
- class: NetworkAccess
  networkAccess: true

inputs:
- id: predictions
  type: File
  default:
    class: File
    location: ../../county_predictions.csv
  inputBinding:
    prefix: --predictions
- id: geojson
  type: File
  default:
    class: File
    location: ../../data/iowa_counties.geojson
  inputBinding:
    prefix: --geojson

outputs:
- id: iowa_county_yields
  type: File
  outputBinding:
    glob: iowa_county_yields.png

baseCommand:
- python
- code/plot_yields.py
