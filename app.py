from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler


FEATURES = [
    "Birth Rate",
    "CO2 Emissions",
    "GDP",
    "Health Exp % GDP",
    "Health Exp/Capita",
    "Infant Mortality Rate",
    "Internet Usage",
    "Life Expectancy Female",
    "Mobile Phone Usage",
    "Population 0-14",
    "Population 15-64",
    "Population 65+",
    "Population Total",
    "Population Urban",
    "Tourism Inbound",
    "Tourism Outbound",
]

st.set_page_config(
    page_title="Global Development Country Clustering",
    page_icon="🌍",
    layout="wide",
)

st.title("🌍 Global Development Measurement")
st.subheader("Country Clustering using K-Means")
st.write(
    "Explore country groups built from economic, health, demographic, "
    "infrastructure, tourism, and development indicators."
)
st.divider()

st.sidebar.header("Application Settings")
uploaded_file = st.sidebar.file_uploader(
    "Upload a World Development dataset (optional)",
    type=["xlsx", "xls", "csv"],
)


def read_dataset(upload):
    if upload is not None:
        if Path(upload.name).suffix.lower() == ".csv":
            return pd.read_csv(upload)
        return pd.read_excel(upload)

    exported_data = Path(__file__).resolve().parent / "country_clustering_data.csv"
    if exported_data.exists():
        return pd.read_csv(exported_data)

    return None


def clean_numeric_column(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip(),
        errors="coerce",
    )


try:
    data = read_dataset(uploaded_file)
except Exception as error:
    st.error(f"Could not read the dataset: {error}")
    st.stop()

if data is None:
    st.info(
        "Run the final export cell in `_Clustering_.ipynb` first, or upload "
        "a World Development Excel/CSV dataset from the sidebar."
    )
    st.stop()

if "Country" not in data.columns:
    st.error("The dataset must contain a 'Country' column.")
    st.stop()

st.success("Notebook dataset loaded." if uploaded_file is None else "Uploaded dataset loaded.")
st.header("Dataset Overview")
metric_columns = st.columns(4)
metric_columns[0].metric("Rows", data.shape[0])
metric_columns[1].metric("Columns", data.shape[1])
metric_columns[2].metric("Missing values", int(data.isna().sum().sum()))
metric_columns[3].metric("Countries", data["Country"].nunique())
st.dataframe(data.head(10), use_container_width=True)

available_features = [feature for feature in FEATURES if feature in data.columns]
missing_features = [feature for feature in FEATURES if feature not in data.columns]
if missing_features:
    st.warning("Some expected features are missing: " + ", ".join(missing_features))
if len(available_features) < 2:
    st.error("At least two expected clustering features are required.")
    st.stop()

st.header("Data Preprocessing")
feature_data = data[available_features].copy()
for column in feature_data:
    feature_data[column] = clean_numeric_column(feature_data[column])

missing_before = int(feature_data.isna().sum().sum())
feature_data = feature_data.dropna(axis=1, how="all")
feature_data = feature_data.fillna(feature_data.median())
missing_after = int(feature_data.isna().sum().sum())
constant_columns = [column for column in feature_data if feature_data[column].nunique() <= 1]
if constant_columns:
    feature_data = feature_data.drop(columns=constant_columns)
    st.warning("Constant features removed: " + ", ".join(constant_columns))

if feature_data.shape[1] < 2:
    st.error("Fewer than two usable numeric features remain after cleaning.")
    st.stop()
if len(feature_data) < 3:
    st.error("At least three country rows are required for clustering.")
    st.stop()

preprocessing_columns = st.columns(2)
preprocessing_columns[0].metric("Missing values before", missing_before)
preprocessing_columns[1].metric("Missing values after", missing_after)
scaled_data = StandardScaler().fit_transform(feature_data)
scaled_df = pd.DataFrame(scaled_data, columns=feature_data.columns, index=feature_data.index)
st.success(f"Preprocessing complete: {scaled_df.shape[1]} features ready for clustering.")

max_k = min(10, len(scaled_df) - 1)
k_values = list(range(2, max_k + 1))
inertia = []
silhouette_scores = []
valid_k_values = []
for cluster_count in k_values:
    model = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
    labels = model.fit_predict(scaled_df)
    label_count = np.unique(labels).size
    if 1 < label_count < len(scaled_df):
        valid_k_values.append(cluster_count)
        inertia.append(model.inertia_)
        silhouette_scores.append(silhouette_score(scaled_df, labels))

if not valid_k_values:
    st.error("K-Means could not form at least two valid clusters from these rows.")
    st.stop()

best_index = int(np.argmax(silhouette_scores))
best_k = valid_k_values[best_index]
best_silhouette = silhouette_scores[best_index]

st.header("Elbow and Silhouette Analysis")
chart_columns = st.columns(2)
with chart_columns[0]:
    figure, axis = plt.subplots(figsize=(7, 4))
    axis.plot(valid_k_values, inertia, marker="o")
    axis.set(xlabel="Number of clusters (K)", ylabel="Inertia", title="Elbow Method")
    axis.grid(True, alpha=0.3)
    st.pyplot(figure)
    plt.close(figure)
with chart_columns[1]:
    figure, axis = plt.subplots(figsize=(7, 4))
    axis.plot(valid_k_values, silhouette_scores, marker="o", color="#187c70")
    axis.set(xlabel="Number of clusters (K)", ylabel="Silhouette score", title="Silhouette by K")
    axis.grid(True, alpha=0.3)
    st.pyplot(figure)
    plt.close(figure)

best_columns = st.columns(2)
best_columns[0].metric("Best K", best_k)
best_columns[1].metric("Best silhouette score", f"{best_silhouette:.4f}")

st.header("K-Means Clustering")
use_best_k = st.checkbox("Use best K based on silhouette score", value=True)
if use_best_k:
    selected_k = best_k
else:
    selected_k = st.slider(
        "Number of clusters",
        min_value=min(valid_k_values),
        max_value=max(valid_k_values),
        value=best_k,
    )

kmeans_final = KMeans(n_clusters=selected_k, random_state=42, n_init=10)
kmeans_labels = kmeans_final.fit_predict(scaled_df)
label_count = np.unique(kmeans_labels).size
if not 1 < label_count < len(scaled_df):
    st.error("The selected K did not produce valid clusters for metric evaluation.")
    st.stop()

result = data.copy()
result[feature_data.columns] = feature_data
result["KMeans_Cluster"] = kmeans_labels
final_silhouette = silhouette_score(scaled_df, kmeans_labels)
davies_score = davies_bouldin_score(scaled_df, kmeans_labels)
calinski_score = calinski_harabasz_score(scaled_df, kmeans_labels)

st.subheader("Model Performance")
metric_columns = st.columns(4)
metric_columns[0].metric("Number of clusters", selected_k)
metric_columns[1].metric("Silhouette score", f"{final_silhouette:.4f}")
metric_columns[2].metric("Davies-Bouldin score", f"{davies_score:.4f}")
metric_columns[3].metric("Calinski-Harabasz score", f"{calinski_score:.2f}")

st.header("Cluster Distribution")
cluster_counts = result["KMeans_Cluster"].value_counts().sort_index()
chart_column, table_column = st.columns([1, 1])
with chart_column:
    figure, axis = plt.subplots(figsize=(7, 4))
    axis.bar(cluster_counts.index.astype(str), cluster_counts.values, color="#187c70")
    axis.set(xlabel="Cluster", ylabel="Number of countries", title="Countries per cluster")
    st.pyplot(figure)
    plt.close(figure)
with table_column:
    cluster_table = pd.DataFrame(
        {
            "Cluster": cluster_counts.index,
            "Number of countries": cluster_counts.values,
            "Percentage": (cluster_counts.values / len(result) * 100).round(2),
        }
    )
    st.dataframe(cluster_table, use_container_width=True, hide_index=True)

st.header("Country Cluster Lookup")
country_list = sorted(result["Country"].dropna().astype(str).unique())
if country_list:
    selected_country = st.selectbox("Select a country", country_list)
    country_result = result[result["Country"].astype(str) == selected_country]
    cluster_number = int(country_result["KMeans_Cluster"].iloc[0])
    st.success(f"{selected_country} belongs to Cluster {cluster_number}.")
    st.dataframe(country_result, use_container_width=True, hide_index=True)

st.header("Cluster Profile")
profile = result.groupby("KMeans_Cluster")[list(feature_data.columns)].mean()
st.dataframe(profile.round(3), use_container_width=True)

selected_cluster = st.selectbox("Countries in cluster", sorted(cluster_counts.index))
cluster_countries = result.loc[
    result["KMeans_Cluster"] == selected_cluster,
    ["Country", "KMeans_Cluster"],
]
st.dataframe(cluster_countries, use_container_width=True, hide_index=True)

st.header("Download Results")
download_columns = st.columns(2)
download_columns[0].download_button(
    "Download country cluster results",
    data=result.to_csv(index=False).encode("utf-8"),
    file_name="country_kmeans_clusters.csv",
    mime="text/csv",
)
download_columns[1].download_button(
    "Download cluster profile",
    data=profile.to_csv().encode("utf-8"),
    file_name="cluster_profile.csv",
    mime="text/csv",
)

st.divider()
st.caption(
    f"K-Means | K={selected_k} | {len(feature_data.columns)} features | "
    f"Best silhouette K={best_k} ({best_silhouette:.4f})"
)
