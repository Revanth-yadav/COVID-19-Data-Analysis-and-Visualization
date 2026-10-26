# COVID-19 Data Analysis and Visualization

## Project features
- Loads a public COVID-19 dataset from Our World in Data (or accepts a CSV upload)
- Performs basic cleaning and type conversion
- Filters by country/region and date range
- Shows case, death, vaccination summary metrics
- Visualizes trends, country comparisons, and a choropleth map when ISO codes are available
- Allows filtered data to be downloaded as CSV

## Run on Windows
1. Install Python 3.10 or newer from https://www.python.org/downloads/
2. Extract this ZIP folder.
3. Open Command Prompt or the VS Code terminal in the extracted project folder.
4. Run:
   `python -m pip install -r requirements.txt`
5. Run:
   `python -m streamlit run app.py`
6. Open the local URL printed in the terminal (usually http://localhost:8501).

## Data source
Our World in Data COVID-19 dataset:
https://covid.ourworldindata.org/data/owid-covid-data.csv

Documentation:
https://docs.owid.io/projects/etl/api/covid/

## Important data note
The default dataset is strongest for reported cases, deaths, and vaccination indicators. It does not consistently provide recovered-case counts for all countries. The dashboard will show a recovery trend only if the uploaded CSV includes `total_recovered` or `recovered`.

## Suggested presentation
Explain the workflow as:
Data collection -> Data cleaning -> Exploratory analysis -> Visualization -> Findings.
Mention that reported totals and trends are affected by differences in testing, reporting practices, and retrospective corrections.
