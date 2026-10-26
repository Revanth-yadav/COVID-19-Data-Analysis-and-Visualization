import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="COVID-19 Data Analysis", page_icon="🦠", layout="wide")

DATA_URL = "https://covid.ourworldindata.org/data/owid-covid-data.csv"

st.title("🦠 COVID-19 Data Analysis and Visualization")
st.caption("Explore reported COVID-19 cases, deaths, and vaccination data by country and date.")

@st.cache_data(ttl=3600, show_spinner=False)
def load_online_data():
    df = pd.read_csv(DATA_URL, usecols=lambda c: c in {
        "iso_code", "continent", "location", "date", "total_cases", "new_cases",
        "total_deaths", "new_deaths", "people_vaccinated", "people_fully_vaccinated",
        "population", "reproduction_rate"
    }, low_memory=False)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df

def normalize_columns(df):
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    aliases = {
        "country": "location", "country_name": "location", "region": "location",
        "confirmed": "total_cases", "confirmed_cases": "total_cases",
        "cases": "total_cases", "deaths": "total_deaths",
        "recovered": "total_recovered", "recoveries": "total_recovered"
    }
    for old, new in aliases.items():
        if old in df.columns and new not in df.columns:
            df.rename(columns={old: new}, inplace=True)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df

with st.sidebar:
    st.header("Data source")
    upload = st.file_uploader("Optional: upload your own COVID-19 CSV", type=["csv"])
    st.caption("Default source: Our World in Data (WHO-reported cases and deaths).")
    st.caption("If online loading fails, download the dataset from the source link shown in the project notes and upload it here.")

try:
    if upload is not None:
        data = normalize_columns(pd.read_csv(upload, low_memory=False))
        source_name = "Uploaded CSV"
    else:
        data = load_online_data()
        source_name = "Our World in Data"
except Exception as exc:
    st.error("The online dataset could not be loaded. Check your internet connection, or upload a CSV file in the sidebar.")
    st.code(str(exc))
    st.stop()

required = ["location", "date"]
missing = [c for c in required if c not in data.columns]
if missing:
    st.error("The CSV is missing required columns: " + ", ".join(missing) + ". Please use a country/date COVID-19 dataset.")
    st.stop()

for col in ["total_cases", "new_cases", "total_deaths", "new_deaths",
            "people_vaccinated", "people_fully_vaccinated", "population",
            "total_recovered", "recovered"]:
    if col in data.columns:
        data[col] = pd.to_numeric(data[col], errors="coerce")

data = data.dropna(subset=["location", "date"])
if "continent" in data.columns:
    data = data[~data["location"].isin(["World", "European Union", "High income", "Low income",
                                        "Lower middle income", "Upper middle income"])]

numeric_cols = [c for c in ["total_cases", "new_cases", "total_deaths", "new_deaths",
                             "people_vaccinated", "people_fully_vaccinated", "population",
                             "total_recovered", "recovered"] if c in data.columns]
if numeric_cols:
    data[numeric_cols] = data[numeric_cols].fillna(0)

st.write(f"**Data source:** {source_name}  ·  **Rows after basic cleaning:** {len(data):,}")
st.info("Data note: COVID-19 reporting methods and completeness vary by country and over time. The default Our World in Data dataset provides cases and deaths, but does not consistently provide recoveries for every country. A recovery chart appears only when your uploaded dataset contains a recovery column.")

locations = sorted(data["location"].dropna().astype(str).unique().tolist())
default_countries = [x for x in ["India", "United States", "Brazil", "United Kingdom"] if x in locations]
with st.sidebar:
    st.header("Dashboard filters")
    chosen = st.multiselect("Choose countries/regions", locations, default=default_countries or locations[:3])
    min_date = data["date"].min().date()
    max_date = data["date"].max().date()
    date_range = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

if not chosen:
    st.warning("Select at least one country or region in the sidebar.")
    st.stop()
if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.warning("Please select both a start and end date.")
    st.stop()

start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
filtered = data[data["location"].isin(chosen) & data["date"].between(start_date, end_date)].copy()
if filtered.empty:
    st.warning("No rows match the selected filters.")
    st.stop()

latest = (filtered.sort_values("date").groupby("location", as_index=False).tail(1))
def latest_sum(col):
    return int(latest[col].fillna(0).sum()) if col in latest.columns else None

k1, k2, k3, k4 = st.columns(4)
k1.metric("Latest reported cases", f"{latest_sum('total_cases'):,}" if latest_sum("total_cases") is not None else "N/A")
k2.metric("Latest reported deaths", f"{latest_sum('total_deaths'):,}" if latest_sum("total_deaths") is not None else "N/A")
k3.metric("People vaccinated (at least 1 dose)", f"{latest_sum('people_vaccinated'):,}" if latest_sum("people_vaccinated") is not None else "N/A")
if "total_recovered" in latest.columns:
    k4.metric("Latest reported recoveries", f"{latest_sum('total_recovered'):,}")
elif "recovered" in latest.columns:
    k4.metric("Latest reported recoveries", f"{latest_sum('recovered'):,}")
else:
    k4.metric("Countries/regions selected", f"{len(chosen)}")

st.subheader("1. Cases over time")
case_col = "new_cases" if "new_cases" in filtered.columns else ("total_cases" if "total_cases" in filtered.columns else None)
if case_col:
    plot_df = filtered.sort_values("date")
    fig = px.line(plot_df, x="date", y=case_col, color="location",
                  title=("Daily new confirmed cases" if case_col == "new_cases" else "Total confirmed cases"),
                  labels={case_col: "Reported cases", "date": "Date", "location": "Country/region"})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No cases column found in this dataset.")

left, right = st.columns(2)
with left:
    st.subheader("2. Country comparison")
    compare_col = "total_cases" if "total_cases" in filtered.columns else case_col
    if compare_col:
        comp = filtered.sort_values("date").groupby("location", as_index=False).tail(1)
        comp = comp.sort_values(compare_col, ascending=False)
        fig = px.bar(comp, x="location", y=compare_col, color="location",
                     title="Latest reported cases by country/region",
                     labels={compare_col: "Cases", "location": "Country/region"})
        fig.update_layout(showlegend=False, xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("3. Deaths over time")
    death_col = "new_deaths" if "new_deaths" in filtered.columns else ("total_deaths" if "total_deaths" in filtered.columns else None)
    if death_col:
        fig = px.line(filtered.sort_values("date"), x="date", y=death_col, color="location",
                      title=("Daily new reported deaths" if death_col == "new_deaths" else "Total reported deaths"),
                      labels={death_col: "Reported deaths", "date": "Date", "location": "Country/region"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No deaths column found in the uploaded data.")

st.subheader("4. Latest country/region snapshot")
if "total_cases" in latest.columns:
    map_df = latest.dropna(subset=["iso_code"]) if "iso_code" in latest.columns else pd.DataFrame()
    if not map_df.empty:
        fig = px.choropleth(map_df, locations="iso_code", color="total_cases",
                            hover_name="location", hover_data=["total_deaths"] if "total_deaths" in map_df.columns else None,
                            color_continuous_scale="Reds", title="Reported cumulative cases by country/region",
                            labels={"total_cases": "Total cases", "total_deaths": "Total deaths"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("A world map is available when the dataset includes country ISO codes (for example, iso_code).")
else:
    st.caption("A map requires a total_cases column and, ideally, country ISO codes.")

recovery_col = next((c for c in ["total_recovered", "recovered"] if c in filtered.columns), None)
if recovery_col:
    st.subheader("5. Recovery trend")
    fig = px.line(filtered.sort_values("date"), x="date", y=recovery_col, color="location",
                  title="Reported recoveries over time",
                  labels={recovery_col: "Recoveries", "date": "Date", "location": "Country/region"})
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Data table")
display_cols = [c for c in ["date", "location", "total_cases", "new_cases", "total_deaths",
                             "new_deaths", "total_recovered", "recovered", "people_vaccinated"] if c in filtered.columns]
st.dataframe(filtered[display_cols].sort_values(["date", "location"], ascending=[False, True]),
             use_container_width=True, hide_index=True)
csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button("Download filtered data as CSV", csv, "covid19_filtered_data.csv", "text/csv")

st.markdown("---")
st.caption("Educational project only. Source: Our World in Data COVID-19 dataset, based largely on WHO-reported data. This dashboard is not medical advice.")
