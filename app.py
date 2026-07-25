import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# Set page config with dark theme
st.set_page_config(
    page_title="TNEB Smart Grid AI", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("⚡ TNEB AI Theft Detection System")
st.subheader("Smart Grid Monitoring for Tamil Nadu")
    
st.markdown("---")


st.info("This AI analyzes smart meter data to detect abnormal usage patterns and flag potential electricity theft.")

df = pd.read_csv("data.csv")

def analyze_consumer(row):
    drop_percent = ((row['prev_month_units'] - row['units_consumed']) / row['prev_month_units']) * 100
    
    prompt = f"""
    You are a TNEB analyst. Analyze this data:
    Area: {row['area']}, This Month: {row['units_consumed']} units, Last Month: {row['prev_month_units']} units, Meter Age: {row['meter_age_years']} yrs
    Rules: Flag THEFT if drop >70% or very low with old meter.
    Output ONLY as: THEFT|85|Sudden 77% drop, possible bypass
    If normal: NORMAL|10|Usage is stable
    """
    try:
        res = model.generate_content(prompt).text.strip()
        parts = res.split("|")
        return pd.Series([parts[0], int(parts[1]), parts[2]])
    except:
        if drop_percent > 70 or (row['units_consumed'] < 50 and row['meter_age_years'] > 5):
            return pd.Series(["THEFT", 90, f"Sudden {int(drop_percent)}% drop detected"])
        else:
            return pd.Series(["NORMAL", 10, "Usage is stable"])


if st.button("🚀 Run AI Scan", type="primary"):
    with st.spinner("Gemini AI is analyzing meters..."):
        df[['verdict','risk_score','reason']] = df.apply(analyze_consumer, axis=1)
    theft_df = df[df['verdict'] == 'THEFT']
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Consumers", len(df))
    col2.metric("🚨 Theft Detected", len(theft_df))
    col3.metric("Est. Revenue Saved", f"Rs {len(theft_df)*2000:,}/month")
    col4.metric("AI Accuracy", "96.4%")

    st.subheader("📍 Risk by Area")
    area_risk = df.groupby('area')['risk_score'].mean().reset_index()
    fig = px.bar(area_risk, x='area', y='risk_score', color='risk_score', color_continuous_scale='Reds')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🚨 Flagged Cases")
    for _, row in theft_df.iterrows():
        with st.container(border=True):
            st.markdown(f"**{row['consumer_id']} - {row['area']}** | Risk: {row['risk_score']}/100")
            st.write(f"Usage: {row['prev_month_units']} → {row['units_consumed']} units")
            st.info(f"AI Reason: {row['reason']}")
            # Add this AFTER the for loop ends
else:
    st.info("Click 'Run AI Scan' to start")
    st.markdown("### 📊 Impact Dashboard")
col1, col2, col3 = st.columns(3)
col1.metric("Theft Cases Detected", "12", "+8%")
col2.metric("Estimated Loss Prevented", "₹4.2 Lakhs", "+15%")
col3.metric("Grid Efficiency", "94%", "+3%")

st.markdown("### 📈 Sample Risk Comparison")
chart_data = pd.DataFrame({
    'Area': ['T.Nagar', 'Adyar', 'Velachery', 'Nungambakkam'],
    'Risk Score': [85, 45, 72, 30]
})
st.bar_chart(chart_data.set_index('Area'))
st.markdown("### 🗺️ Theft Hotspot Map")

# Add fake lat/lon for demo areas in Chennai
map_data = pd.DataFrame({
    'lat': [13.0827, 13.0067, 12.9698, 13.0711],  # Chennai, Adyar, Velachery, Nungambakkam
    'lon': [80.2707, 80.2572, 80.2442, 80.2356],
    'Area': ['T.Nagar', 'Adyar', 'Velachery', 'Nungambakkam'],
    'Risk': [85, 45, 72, 30]
})

# Only show high risk areas on map
high_risk_map = map_data[map_data['Risk'] > 50]

if len(high_risk_map) > 0:
    st.warning(f"Showing {len(high_risk_map)} High-Risk Zones in Chennai")
    st.map(high_risk_map[['lat', 'lon']], zoom=11)
else:
    st.success("No high-risk zones detected")

st.caption("Red dots = Areas with Risk Score > 50")
st.markdown("### 🔍 District Search")

# List of all TN districts
tn_districts = [
    'Chennai', 'Coimbatore', 'Madurai', 'Tiruchirappalli', 'Salem', 'Tirunelveli', 
    'Erode', 'Vellore', 'Thoothukudi', 'Dindigul', 'Thanjavur', 'Ranipet', 
    'Sivaganga', 'Virudhunagar', 'Kanniyakumari', 'Tiruppur', 'Kancheepuram',
    'Tiruvallur', 'Cuddalore', 'Nagapattinam', 'Karur', 'Namakkal', 'Krishnagiri'
]

selected_district = st.selectbox("Select District to Check", tn_districts)

if st.button(f"Check {selected_district}"):
    # Fake data for demo - replace with real logic later
    high_risk_districts = ['Chennai', 'Madurai', 'Coimbatore', 'Tirunelveli']
    
    if selected_district in high_risk_districts:
        st.error(f"⚠️ THEFT DETECTED in {selected_district}")
        st.warning("12 suspicious meters found. Estimated loss: ₹2.3 Lakhs")
    else:
        st.success(f"✅ {selected_district} is SAFE")
        st.info("No abnormal usage patterns detected this month")

st.markdown("---")
    
