#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

requirements:
- class: InitialWorkDirRequirement
  listing:
  - entryname: code/get_weather.py
    entry:
      $include: ../../code/get_weather.py
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

outputs:
- id: weather
  type: File
  outputBinding:
    glob: weather.csv

baseCommand:
- python
- code/get_weather.py
