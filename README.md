# Project Title

DataLake - DWH - DataMarts for Bike Rent traffic

## Description

arriving 2 data types: rides.csv & pass_purchases.csv  
resulting Data marts, analytics by different departments  

## Getting Started

### Elements

engine on GCP, user access through customer website
- Terraform to setup architecture
  - github repo linked to local
  - GCP artifact repo triggered from github
  - cloud build based on GCP artifact repo
    - Deployment dbt image as Cloud Run service
    - Workflows 
      - running dbt in Cloud Run on arriving data
      - email notif on results 
  - Service with GKE or external Load Balancer 
- dbt to make data flow
  - DataLake taking raw input files
  - DWH a BiqQuery DataSet with tables on system status
  - DataMarts for Departments Access with specific tables/views

### Installing

* How/where to download your program
* Any modifications needed to be made to files/folders

### Executing program

* How to run the program
* Step-by-step bullets
```
code blocks for commands
```

## Help

Any advise for common problems or issues.
```
command to run if program contains helper info
```

## Authors

Contributors names and contact info

Gyorgy Feledi   
gfeledi@gmail.com

## Version History

* 0.2
    * Various bug fixes and optimizations
    * See [commit change]() or See [release history]()
* 0.1
    * Initial Release

