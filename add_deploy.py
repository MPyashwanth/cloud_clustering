import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('cloud_Clustering_fixed.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# ── Streamlit app source (written to app.py at runtime) ──────────────────────
APP_CODE = r"""import streamlit as st
import pandas as pd
import numpy as np
import joblib

# ── Load artefacts ────────────────────────────────────────────────────────────
kmeans_model  = joblib.load("kmeans_model.pkl")
scaler        = joblib.load("scaler.pkl")
feature_names = joblib.load("feature_names.pkl")

CLUSTER_LABELS = {
    0: "Cluster 0 — Developing Nations",
    1: "Cluster 1 — Developed Nations",
}
CLUSTER_DESC = {
    0: ("High birth rates, elevated infant mortality, lower internet usage, "
        "lower life expectancy, and limited healthcare spending per capita."),
    1: ("Low birth rates, high internet penetration, high life expectancy, "
        "strong healthcare spending, and higher GDP."),
}

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Global Dev Clustering", page_icon="🌍", layout="wide")

st.title("🌍 Global Development Cluster Predictor")
st.markdown(
    "Enter country-level indicators in the sidebar to find out which "
    "**development cluster** the country belongs to."
)

# ── Sidebar inputs ────────────────────────────────────────────────────────────
st.sidebar.header("🔧 Input Features")

FEATURE_DEFAULTS = {
    "Birth Rate":            0.022,
    "CO2 Emissions":         100000.0,
    "GDP":                   2.5e11,
    "Health Exp % GDP":      0.06,
    "Health Exp/Capita":     700.0,
    "Infant Mortality Rate": 0.03,
    "Internet Usage":        0.45,
    "Life Expectancy Female":72.0,
    "Mobile Phone Usage":    0.9,
    "Population 0-14":       0.28,
    "Population 15-64":      0.64,
    "Population 65+":        0.08,
    "Population Total":      5e7,
    "Population Urban":      0.55,
    "Tourism Inbound":       5e9,
    "Tourism Outbound":      3e9,
}

user_input = {}
for feat in feature_names:
    user_input[feat] = st.sidebar.number_input(
        feat,
        value=float(FEATURE_DEFAULTS.get(feat, 0.0)),
        format="%g",
    )

# ── Predict ───────────────────────────────────────────────────────────────────
if st.sidebar.button("Predict Cluster", type="primary"):
    log_cols = ["CO2 Emissions", "GDP", "Population Total",
                "Tourism Inbound", "Tourism Outbound", "Health Exp/Capita"]

    df = pd.DataFrame([user_input])
    for col in log_cols:
        if col in df.columns:
            df[col] = np.log1p(df[col])

    df_scaled = scaler.transform(df[feature_names])
    cluster   = int(kmeans_model.predict(df_scaled)[0])

    st.subheader("Prediction Result")
    st.success(f"This country belongs to: **{CLUSTER_LABELS[cluster]}**")
    st.info(CLUSTER_DESC[cluster])

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Input Summary")
        st.dataframe(pd.DataFrame([user_input]).T.rename(columns={0: "Value"}))
    with col2:
        st.subheader("Cluster Profiles (mean values)")
        try:
            data = pd.read_csv("country_clustering_data.csv")
            profile = data.groupby("KMeans_Cluster")[feature_names].mean()
            st.dataframe(profile.T)
        except FileNotFoundError:
            st.warning("country_clustering_data.csv not found.")
"""

# ── Notebook cells to append ──────────────────────────────────────────────────
new_cells = [
    # --- Section header ---
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": (
            "---\n"
            "## 🚀 Deployment\n\n"
            "The best-performing model **(K-Means, K=2)** is saved using `joblib` "
            "along with the `StandardScaler` and feature list, then served via a "
            "**Streamlit** web application that lets users enter country-level "
            "indicators and receive an instant cluster prediction.\n"
        )
    },
    # --- Save artefacts ---
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": (
            "import joblib, os\n"
            "\n"
            "# Save trained K-Means model\n"
            "joblib.dump(kmeans_final,  'kmeans_model.pkl')\n"
            "\n"
            "# Save the StandardScaler\n"
            "joblib.dump(scaler,        'scaler.pkl')\n"
            "\n"
            "# Save feature names list\n"
            "joblib.dump(final_features,'feature_names.pkl')\n"
            "\n"
            "print('Model artefacts saved:')\n"
            "for fname in ['kmeans_model.pkl', 'scaler.pkl', 'feature_names.pkl']:\n"
            "    print(f'  {fname}  —  {os.path.getsize(fname)} bytes')\n"
        )
    },
    # --- Write app.py ---
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": (
            "### Streamlit App — `app.py`\n\n"
            "The cell below writes `app.py` to disk.  "
            "Start the app from a terminal with:\n\n"
            "```bash\n"
            "streamlit run app.py\n"
            "```\n\n"
            "The app opens at **http://localhost:8501**.\n"
        )
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": (
            "APP_CODE = '''" + APP_CODE + "'''\n"
            "\n"
            "with open('app.py', 'w', encoding='utf-8') as _f:\n"
            "    _f.write(APP_CODE)\n"
            "\n"
            "print('app.py written successfully!')\n"
            "print('Run:  streamlit run app.py')\n"
        )
    },
    # --- Launch note ---
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": (
            "### ▶️ How to Launch\n\n"
            "1. Open a terminal / Anaconda Prompt in this folder.\n"
            "2. Run:\n\n"
            "```bash\n"
            "streamlit run app.py\n"
            "```\n\n"
            "3. The browser will open at **http://localhost:8501**.\n"
            "4. Use the sidebar sliders to enter country indicators and click **Predict Cluster**.\n"
        )
    }
]

nb['cells'].extend(new_cells)

with open('cloud_Clustering_with_deploy.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f'Done! Saved as cloud_Clustering_with_deploy.ipynb  (total cells: {len(nb["cells"])})')
