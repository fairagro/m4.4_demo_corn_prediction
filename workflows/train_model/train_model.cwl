#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

requirements:
- class: InitialWorkDirRequirement
  listing:
  - entryname: code/train_model.py
    entry:
      $include: ../../code/train_model.py
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
- id: yield
  type: File
  default:
    class: File
    location: ../../data/iowa_yield.csv
  inputBinding:
    prefix: --yield

outputs:
- id: model
  type: File
  outputBinding:
    glob: model.pkl
- id: scaler
  type: File
  outputBinding:
    glob: scaler.pkl

baseCommand:
- python
- code/train_model.py
