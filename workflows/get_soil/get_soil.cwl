#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

requirements:
- class: InitialWorkDirRequirement
  listing:
  - entryname: code/get_soil.py
    entry:
      $include: ../../code/get_soil.py
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
- id: soil_cache
  type: File
  default:
    class: File
    location: ../../data/soil_data.csv
  inputBinding:
    prefix: --soil_cache

outputs:
- id: soil
  type: File
  outputBinding:
    glob: soil.csv

baseCommand:
- python
- code/get_soil.py
