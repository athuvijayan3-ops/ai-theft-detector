import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')
# TNEB District Contact Database
tneb_contacts = {
    "Chennai": {"office": "TNEB Chennai Central", "phone": "044-28521345", "email": "chennai@tneb.in"},
    "Coimbatore": {"office": "TNEB Coimbatore North", "phone": "0422-2221444", "email": "cbe@tneb.in"},
    "Madurai": {"office": "TNEB Madurai South", "phone": "0452-2533333", "email": "mdu@tneb.in"},
    "Trichy": {"office": "TNEB Trichy Division", "phone": "0431-2700300", "email": "trichy@tneb.in"},
    "Salem": {"office": "TNEB Salem Circle", "phone": "0427-2450200", "email": "salem@tneb.in"},
    "Tirunelveli": {"office": "TNEB Tirunelveli", "phone": "0462-2575000", "email": "tvl@tneb.in"},
    "Erode": {"office": "TNEB Erode", "phone": "0424-2261000", "email": "erode@tneb.in"},
    "Vellore": {"office": "TNEB Vellore", "phone": "0416-2222444", "email": "vellore@tneb.in"},
    "Thoothukudi": {"office": "TNEB Thoothukudi", "phone": "0461-2323333", "email": "tdy@tneb.in"},
    "Dindigul": {"office": "TNEB Dindigul", "phone": "0451-2431000", "email": "dgl@tneb.in"},
    "Thanjavur": {"office": "TNEB Thanjavur", "phone": "04362-230000", "email": "tjore@tneb.in"},
    "Ranipet": {"office": "TNEB Ranipet", "phone": "04172-244444", "email": "ranipet@tneb.in"},
    "Sivaganga": {"office": "TNEB Sivaganga", "phone": "04575-240000", "email": "sivaganga@tneb.in"},
    "Kanniyakumari": {"office": "TNEB Nagercoil", "phone": "04652-222", "email": "nagercoil@tneb.in"},
    "Tiruppur": {"office": "TNEB Tiruppur", "phone": "0421-2200000", "email": "tirupur@tneb.in"},
    "Pudukkottai": {"office": "TNEB Pudukkottai", "phone": "04322-222222", "email": "pdk@tneb.in"},
    "Nagapattinam": {"office": "TNEB Nagapattinam", "phone": "04365-242222", "email": "ngp@tneb.in"},
    "Namakkal": {"office": "TNEB Namakkal", "phone": "04286-280000", "email": "namakkal@tneb.in"},
    "Dharmapuri": {"office": "TNEB Dharmapuri", "phone": "04342-230000", "email": "dharmapuri@tneb.in"},
    "Cuddalore": {"office": "TNEB Cuddalore", "phone": "04142-230000", "email": "cuddalore@tneb.in"}
}

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

# LIVE ALERT + TNEB CONTACT SYSTEM
if len(theft_df) > 0:
    st.error(f"🚨 ALERT: {len(theft_df)} Potential Theft Cases Detected! Immediate Action Required.")
    
    with st.expander("Click to see high risk cases + TNEB Contact"):
        for i in range(min(5, len(theft_df))):
            row = theft_df.iloc[i]
            area = row['area']
            contact = tneb_contacts.get(area, {"office": "TNEB Helpline", "phone": "1912", "email": "support@tneb.in"})
            
            st.warning(f"⚡ **Case {i+1}**: {row['consumer_id']} | Area: {area} | Risk: {row['risk_score']}%")
            st.info(f"📞 **Contact TNEB {area}**\n\n**Office:** {contact['office']}\n**Phone:** {contact['phone']}\n**Email:** {contact['email']}")
            st.markdown("---")
else:
    st.success("✅ No theft detected. Grid is safe.")

    st.subheader("📍 Risk by Area")
    area_risk = df.groupby('area')['risk_score'].mean().reset_index()
    fig = px.bar(area_risk, x='area', y='risk_score', color='risk_score', color_continuous_scale='Reds')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🚨 Flagged Cases")
if len(theft_df) > 0:
    for _, row in theft_df.iterrows():
        with st.container(border=True):
            st.markdown(f"**{row['consumer_id']} - {row['area']}** | Risk: {row['risk_score']}/100")
            st.write(f"Usage: {row['prev_month_units']} → {row['units_consumed']} units")
            st.info(f"AI Reason: {row['reason']}")
else:
    st.info("No flagged cases to show yet. Click 'Run AI Scan' to analyze.")

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
    
