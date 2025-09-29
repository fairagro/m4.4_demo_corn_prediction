#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

requirements:
- class: InitialWorkDirRequirement
  listing:
  - entryname: code/merge_features.py
    entry:
      $include: ../../code/merge_features.py
- class: DockerRequirement
  dockerFile:
    $include: ../../Dockerfile
  dockerImageId: pyplot
- class: NetworkAccess
  networkAccess: true

inputs:
- id: geojson
  type: File
  default:
    class: File
    location: ../../data/iowa_counties.geojson
  inputBinding:
    prefix: --geojson
- id: weather
  type: File
  default:
    class: File
    location: ../../weather.csv
  inputBinding:
    prefix: --weather
- id: soil
  type: File
  default:
    class: File
    location: ../../soil.csv
  inputBinding:
    prefix: --soil

outputs:
- id: county_features
  type: File
  outputBinding:
    glob: county_features.csv

baseCommand:
- python
- code/merge_features.py
