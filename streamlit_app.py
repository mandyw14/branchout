# app.py
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Branch Out: Recipients Search", layout="wide")

CSV_PATH = "BONF Research Table MASTER Recipients.csv"

# Expected column names
COL_RECIPIENTS = "Recipients"
COL_SUPS       = "Supervisors"
COL_PROPOSAL   = "Proposal"
COL_LAY        = "Lay_Summary"

@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path, encoding_errors="ignore")
    except FileNotFoundError:
        st.error(f"File not found: {path}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Could not read CSV: {e}")
        return pd.DataFrame()

df = load_data(CSV_PATH)

st.title("Branch Out Science Search")

if df.empty:
    st.stop()

# Validate required columns
required = [COL_RECIPIENTS, COL_SUPS, COL_PROPOSAL, COL_LAY]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"Missing expected column(s): {', '.join(missing)}")
    st.caption(f"Available columns include: {', '.join(map(str, df.columns[:20]))}...")
    st.stop()

# ---------------------------
# Sidebar: Filters
# ---------------------------
st.sidebar.header("Filters")

recipient_query = st.sidebar.text_input(
    "Recipients contains",
    value="",
    placeholder="e.g., Wintink"
)

content_query = st.sidebar.text_input(
    "Content keyword",
    value="",
    placeholder="e.g., neurofeedback"
)

field_options = ["Proposal", "Lay_Summary", "Supervisors"]
selected_fields = st.sidebar.multiselect(
    "Search keyword in:",
    options=field_options,
    default=["Proposal", "Lay_Summary"]  # typical text-heavy fields
)

# ---------------------------
# Filtering logic
# ---------------------------
results = df.copy()

# Recipients filter (case-insensitive substring)
if recipient_query.strip():
    results = results[results[COL_RECIPIENTS].astype(str).str.contains(recipient_query.strip(), case=False, na=False)]

# Content keyword filter (OR across selected fields)
if content_query.strip() and selected_fields:
    masks = []
    for field in selected_fields:
        col = {
            "Proposal": COL_PROPOSAL,
            "Lay_Summary": COL_LAY,
            "Supervisors": COL_SUPS
        }[field]
        masks.append(results[col].astype(str).str.contains(content_query, case=False, na=False))
    if masks:
        any_mask = masks[0]
        for m in masks[1:]:
            any_mask |= m
        results = results[any_mask]

# ---------------------------
# KPIs
# ---------------------------
c1, c2 = st.columns(2)
c1.metric("Total rows", f"{len(df):,}")
c2.metric("Matches", f"{len(results):,}")

# ---------------------------
# Table
# ---------------------------
front_cols = [COL_RECIPIENTS, COL_SUPS, COL_PROPOSAL, COL_LAY]
other_cols = [c for c in results.columns if c not in front_cols]
ordered = results[front_cols + other_cols] if front_cols else results

st.subheader("Results")
st.dataframe(ordered, use_container_width=True)

# ---------------------------
# Download
# ---------------------------
st.download_button(
    "Download results (CSV)",
    data=ordered.to_csv(index=False).encode("utf-8-sig"),
    file_name="BONF_recipients_filtered_results.csv",
    mime="text/csv",
)

# ---------------------------
# Notes
# ---------------------------
with st.expander("Notes"):
    st.markdown(
        """
- **Recipients contains**: case-insensitive substring match on the *Recipients* column.
- **Content keyword**: case-insensitive substring match across the selected fields (OR logic).
- Default keyword search checks **Proposal** and **Lay_Summary**; you can add **Supervisors** as needed.
        """
    )
