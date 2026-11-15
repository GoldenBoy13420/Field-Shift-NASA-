import streamlit as st
import pandas as pd
import requests
import folium
from folium.plugins import LocateControl
from datetime import datetime, timedelta
from streamlit_folium import st_folium

from core.controller import FieldShiftController

# --- 1. Page Configuration & High-Contrast Theme ---
st.set_page_config(page_title="Field Shift | Smart Agriculture", page_icon="🌱", layout="wide", initial_sidebar_state="expanded")

# --- Orbital telemetry visual system ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Orbitron:wght@500;600;700;800&display=swap');
    :root {
        --space: #050811;
        --surface: rgba(11, 18, 33, .78);
        --line: rgba(0, 240, 255, .22);
        --cyan: #00F0FF;
        --green: #10B981;
        --red: #FC3D21;
        --amber: #F59E0B;
        --muted: #91A4B8;
        --text: #E8F2FA;
    }
    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        color: var(--text);
        background-color: var(--space);
        position: relative;
        isolation: isolate;
        background-image: radial-gradient(ellipse at 18% 0%, rgba(0, 240, 255, .09), transparent 34%),
            radial-gradient(ellipse at 85% 22%, rgba(16, 185, 129, .06), transparent 30%),
            radial-gradient(rgba(185, 220, 255, .26) .7px, transparent .9px);
        background-size: auto, auto, 90px 90px;
        background-position: center, center, 18px 22px;
    }
    .stApp::before {
        content: '';
        position: fixed;
        inset: 0;
        z-index: 0;
        pointer-events: none;
        opacity: .05;
        mix-blend-mode: screen;
        background-image: url('/app/static/space-pattern-bg.jpg');
        background-repeat: repeat;
        background-size: 720px 720px;
        background-position: center top;
    }
    .stApp > header, .stApp [data-testid="stAppViewContainer"] { position: relative; z-index: 1; }
    [data-testid="stHeader"] { background: rgba(5, 8, 17, .72); }
    [data-testid="stSidebar"] { background: #080E19; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] * { color: var(--text); }
    h1, h2, h3, h4, h5, h6 { color: var(--text) !important; }
    h1, h2, h3 { font-family: 'Orbitron', 'Inter', sans-serif !important; }
    .mission-title { font-size: 30px; }
    p, label, .stCaption { color: #B5C4D3; }
    code, [data-testid="stMetricValue"], .telemetry-mono { font-family: 'JetBrains Mono', monospace !important; }
    .stMarkdown p { font-size: 1rem; }
    div.stButton > button:first-child {
        color: #031116 !important; background: var(--cyan); border: 1px solid var(--cyan);
        border-radius: 4px; font-weight: 800; transition: all .2s ease;
        box-shadow: 0 0 16px rgba(0, 240, 255, .14);
    }
    div.stButton > button:first-child:hover {
        color: var(--cyan) !important; background: rgba(0, 240, 255, .08);
        box-shadow: 0 0 24px rgba(0, 240, 255, .35); transform: translateY(-1px);
    }
    [data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] { background: var(--cyan); }
    [data-testid="stMetric"] { background: transparent; }
    [data-testid="stMetricValue"] { color: var(--cyan) !important; font-size: 1.7rem !important; }
    [data-testid="stMetricLabel"] { color: var(--muted) !important; }
    [data-testid="stAlert"] { border-radius: 3px; }
    [data-testid="stVerticalBlock"] iframe { max-width: 100%; }
    iframe[title*="st_folium"] { border: 1px solid var(--line); box-shadow: 0 0 22px rgba(0, 240, 255, .1); }
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #080E19; }
    ::-webkit-scrollbar-thumb { background: #1A3846; border: 1px solid #254C59; border-radius: 8px; }
    .mission-hero {
        min-height: 250px; padding: 28px 34px; margin: 4px 0 20px; position: relative; overflow: hidden;
        display: flex; flex-direction: column; justify-content: center; gap: 14px;
        border: 1px solid var(--line); border-left: 3px solid var(--cyan); border-radius: 4px;
        background-image: linear-gradient(90deg, #050811 40%, rgba(5, 8, 17, .55) 100%),
            url('/app/static/nasa-astronaut-hero.jpg');
        background-color: #07111D; background-position: center, 54% 42%; background-size: cover;
        box-shadow: inset 0 0 45px rgba(0, 240, 255, .05);
    }
    .mission-brand { display: flex; align-items: center; gap: 14px; }
    .nasa-mark { width: 56px; height: 56px; object-fit: contain; filter: drop-shadow(0 0 9px rgba(0, 240, 255, .22)); }
    .mission-kicker { color: var(--cyan); font: 700 11px 'JetBrains Mono', monospace; letter-spacing: 1.5px; }
    .mission-title { color: white; font: 700 30px 'Orbitron', sans-serif; margin: 0; }
    .mission-subtitle { color: #C0CFDD; margin: 0; max-width: 660px; font-size: 14px; }
    .link-pill { width: fit-content; padding: 9px 12px; border: 1px solid rgba(16, 185, 129, .44); border-radius: 3px;
        background: rgba(7, 18, 25, .78); color: #B8F7DE; font: 600 11px 'JetBrains Mono', monospace; }
    .link-dot { color: var(--green); animation: beacon 1.8s ease-in-out infinite; }
    @keyframes beacon { 50% { opacity: .35; text-shadow: 0 0 12px var(--green); } }
    .source-row { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin: 0 0 18px; }
    .source-chip { min-width: 0; padding: 10px 12px; background: var(--surface); border: 1px solid var(--line);
        border-radius: 3px; color: #D7E5F0; font-size: 11px; }
    .source-chip strong { display: block; color: var(--text); font: 600 11px 'JetBrains Mono', monospace; }
    .source-state { display: block; margin-top: 5px; color: var(--muted); font: 500 9px 'JetBrains Mono', monospace; }
    .state-live { color: var(--green); }
    .hud-panel { background: var(--surface); border: 1px solid var(--line); border-radius: 4px;
        padding: 16px; position: relative; margin-bottom: 16px; box-shadow: 0 10px 32px rgba(0, 0, 0, .18); }
    .hud-panel:before, .hud-panel:after { content: ''; position: absolute; width: 12px; height: 12px; border-color: var(--cyan); opacity: .8; }
    .hud-panel:before { top: -1px; left: -1px; border-top: 2px solid; border-left: 2px solid; }
    .hud-panel:after { bottom: -1px; right: -1px; border-bottom: 2px solid; border-right: 2px solid; }
    .panel-heading { display: flex; justify-content: space-between; gap: 10px; align-items: center; margin-bottom: 12px;
        color: var(--cyan); font: 600 12px 'JetBrains Mono', monospace; text-transform: uppercase; }
    .bridge-svg { width: 100%; height: auto; display: block; }
    .beam { stroke-dasharray: 5 7; animation: telemetry 1.4s linear infinite; }
    @keyframes telemetry { to { stroke-dashoffset: -24; } }
    .pipeline { display: grid; grid-template-columns: 1fr 30px 1fr 30px 1fr; align-items: stretch; gap: 5px; margin: 0 0 20px; }
    .pipeline-node { padding: 13px; background: rgba(11, 18, 33, .72); border: 1px solid rgba(0, 240, 255, .18); border-radius: 3px; }
    .pipeline-node b { color: var(--cyan); font: 600 10px 'JetBrains Mono', monospace; }
    .pipeline-node span { display: block; margin-top: 6px; color: #E0EBF3; font-size: 12px; line-height: 1.45; }
    .pipeline-node small { display: block; margin-top: 5px; color: var(--muted); font: 10px 'JetBrains Mono', monospace; }
    .pipeline-arrow { align-self: center; color: var(--green); text-align: center; font: 18px 'JetBrains Mono', monospace; }
    .coord-readout { padding: 9px 11px; margin: 8px 0 12px; color: var(--cyan); background: rgba(0, 240, 255, .05);
        border: 1px solid rgba(0, 240, 255, .16); font: 11px 'JetBrains Mono', monospace; }
    .telemetry-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin: 12px 0; }
    .gauge { padding: 13px; min-width: 0; background: rgba(11, 18, 33, .8); border: 1px solid var(--line); border-radius: 3px; }
    .gauge-label { color: var(--muted); font: 10px 'JetBrains Mono', monospace; }
    .gauge-value { margin: 7px 0 10px; color: var(--cyan); font: 700 22px 'JetBrains Mono', monospace; }
    .gauge-ground .gauge-value { color: var(--green); }
    .gauge-delta .gauge-value { color: var(--amber); }
    .gauge-track { height: 5px; background: #162535; overflow: hidden; }
    .gauge-fill { height: 100%; background: var(--cyan); box-shadow: 0 0 10px rgba(0, 240, 255, .65); }
    .gauge-ground .gauge-fill { background: var(--green); box-shadow: 0 0 10px rgba(16, 185, 129, .6); }
    .stress-banner { padding: 12px; margin: 12px 0; color: #FFD5CE; background: rgba(252, 61, 33, .12);
        border: 1px solid rgba(252, 61, 33, .75); font: 700 12px 'JetBrains Mono', monospace;
        animation: alert-pulse 1.8s ease-in-out infinite; }
    @keyframes alert-pulse { 50% { box-shadow: 0 0 18px rgba(252, 61, 33, .22); } }
    @media (max-width: 700px) {
        .mission-hero { min-height: 280px; padding: 20px; background-position: center, 62% center; }
        .mission-title { font-size: 24px; }
        .nasa-mark { width: 44px; height: 44px; }
        .source-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .pipeline { grid-template-columns: 1fr; }
        .pipeline-arrow { transform: rotate(90deg); }
        .telemetry-grid { grid-template-columns: 1fr; }
        .link-pill { line-height: 1.6; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. Simplified Bilingual Dictionary (صياغة مبسطة ومفهومة جداً) ---
ui = {
    "title": {"en": "🌱 Field Shift: Your Smart Farm Assistant", "ar": "🌱 فيلد شيفت: مساعدك الزراعي الذكي"},
    "subtitle": {"en": "Check your soil health and get expert crop advice based on NASA data.", "ar": "طابق حالة أرضك مع بيانات ناسا واعرف المحصول الأنسب لإنقاذ زرعتك."},
    "sidebar": {"en": "⚙️ Farm Settings", "ar": "⚙️ إعدادات المزرعة"},
    "sensor_h": {"en": "💧 Current Soil Moisture", "ar": "💧 رطوبة الأرض الحالية"},
    "sensor_p": {"en": "Move the slider to match your farm's actual moisture level:", "ar": "حرك المؤشر لتحديد نسبة الرطوبة الفعلية في أرضك دلوقتي:"},
    "slider": {"en": "Moisture Level", "ar": "مستوى الرطوبة"},
    "sys_ok": {"en": "✅ System is Ready", "ar": "✅ النظام جاهز ومتصل"},
    "step1": {"en": "🌍 Step 1: Pinpoint Your Farm", "ar": "🌍 الخطوة الأولى: حدد مكان أرضك"},
    "step1_cap": {"en": "Click the GPS icon to find you, or tap anywhere on the map.", "ar": "دوس على علامة (GPS 🎯) عشان تروح لمكانك، أو اضغط على الخريطة لتحديد الأرض."},
    "step2": {"en": "🛰️ Step 2: Analyze Soil & Climate", "ar": "🛰️ الخطوة الثانية: فحص التربة والمناخ"},
    "btn": {"en": "🔍 Scan Farm with NASA AI", "ar": "🔍 افحص الأرض بالذكاء الاصطناعي"},
    "loading1": {"en": "Connecting to NASA satellites...", "ar": "جاري سحب حالة الطقس والتربة من الأقمار الصناعية..."},
    "loading2": {"en": "Analyzing data with AI...", "ar": "جاري تحليل حالة أرضك بالذكاء الاصطناعي..."},
    "diag": {"en": "📊 Farm Diagnosis", "ar": "📊 تقرير حالة المزرعة"},
    "ai_base": {"en": "Target Moisture", "ar": "الرطوبة المطلوبة"},
    "iot": {"en": "Actual Moisture", "ar": "رطوبة أرضك الحالية"},
    "def": {"en": "Water Gap", "ar": "نقص / زيادة المياه"},
    "stress": {"en": "CRITICAL: Severe drought detected. Irrigate immediately.", "ar": "خطر: جفاف شديد! الأرض محتاجة تتروي فوراً لإنقاذ الزرع."},
    "over": {"en": "WARNING: Soil is waterlogged. Stop irrigation.", "ar": "تحذير: الأرض غرقانة مياه! وقف الري فوراً عشان الجذور متختنقش."},
    "opt": {"en": "EXCELLENT: Soil moisture is perfect.", "ar": "ممتاز: رطوبة الأرض معتدلة ومثالية جداً."},
    "rep_t": {"en": "💡 Expert Recommendation", "ar": "💡 نصيحة الخبراء"},
    "act": {"en": "**Best Crop for these conditions:**", "ar": "**المحصول الأنسب لحالة أرضك دي:**"},
    "fao": {"en": "**Scientific Reason (FAO):**", "ar": "**التفسير العلمي (منظمة الفاو):**"},
    "wait": {"en": "👈 Please select your farm on the map to begin.", "ar": "👈 لو سمحت، حدد مكان أرضك على الخريطة الأول عشان نبدأ."}
}

# --- 3. Sidebar & Language Selection ---
with st.sidebar:
    lang_choice = st.radio("🌐 Language / اللغة", ["العربية", "English"], horizontal=True)
    lang = "ar" if lang_choice == "العربية" else "en"
    
    # RTL Styling for Arabic
    if lang == "ar":
        st.markdown("<style>p, h1, h2, h3, h4, h5, h6, span, label, .stAlert, .stMarkdown { direction: rtl; text-align: right; } div[data-testid='stMetricValue'], div[data-testid='stMetricDelta'] { text-align: right; }</style>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader(ui["sidebar"][lang])
    st.write(ui["sensor_p"][lang])
    live_sensor_reading = st.slider(ui["slider"][lang], 0.0, 0.8, 0.20, 0.01)
    st.divider()
    st.success(ui["sys_ok"][lang])

# --- 4. System Initialization ---
if "controller" not in st.session_state:
    with st.spinner("Starting AI Engines..." if lang == "en" else "جاري تجهيز النظام..."):
        API_KEY = "AQ.Ab8RN6J6_X0_CimVL9O3xRCD06PhMjGtJhY0kCa0PffO5uCqig"
        st.session_state.controller = FieldShiftController(api_key=API_KEY)

if "lat" not in st.session_state:
    st.session_state.lat = 30.0444
if "lon" not in st.session_state:
    st.session_state.lon = 31.2357

# --- 5. Live Data Fetcher ---
def fetch_live_satellite_data(lat, lon):
    target_date = (datetime.now() - timedelta(days=5)).strftime('%Y%m%d')
    try:
        res = requests.get("https://power.larc.nasa.gov/api/temporal/daily/point", params={"parameters": "T2M,RH2M,PRECTOTCORR", "community": "AG", "longitude": lon, "latitude": lat, "start": target_date, "end": target_date, "format": "JSON"}, timeout=10).json()
        temp = list(res['properties']['parameter']['T2M'].values())[0]
        rh = list(res['properties']['parameter']['RH2M'].values())[0]
        precip = list(res['properties']['parameter']['PRECTOTCORR'].values())[0]
    except: temp, rh, precip = 32.0, 45.0, 0.0

    try:
        soil_res = requests.get(f"https://rest.isric.org/soilgrids/v2.0/properties/query?lon={lon}&lat={lat}&property=sand&property=clay&depth=0-5cm", timeout=10).json()
        sand_pct, clay_pct = 50.0, 20.0 
        for layer in soil_res.get('properties', {}).get('layers', []):
            val = layer['depths'][0]['values']['mean']
            if val:
                if layer['name'] == 'sand': sand_pct = val / 10
                elif layer['name'] == 'clay': clay_pct = val / 10
    except: sand_pct, clay_pct = 50.0, 20.0

    ndvi = 0.55 if clay_pct > 25 else 0.15 
    lst = temp + 3.5 
    now = datetime.now()
    return {
        'Temperature_Avg': temp, 'Relative_Humidity': rh, 'Precipitation': precip,
        'NDVI': ndvi, 'LST_Celsius': lst, 'Soil_Sand_pct': sand_pct, 'Soil_Clay_pct': clay_pct,
        'Crop_Kc': 1.15, 'Month': now.month, 'DayOfYear': now.timetuple().tm_yday, 
        'Rain_3d_sum': precip * 1.5, 'LST_5d_avg': lst - 1.0
    }

# --- 6. Main Dashboard ---
st.markdown(f"""
<section class="mission-hero">
    <div class="mission-brand">
        <img class="nasa-mark" src="https://upload.wikimedia.org/wikipedia/commons/e/e5/NASA_logo.svg"
            alt="NASA insignia" onerror="this.style.display='none'">
        <div>
            <div class="mission-kicker">FIELD SHIFT // ORBITAL TELEMETRY</div>
            <h1 class="mission-title">Field Shift: From Space to Roots</h1>
        </div>
    </div>
    <p class="mission-subtitle">{ui['subtitle'][lang]}</p>
    <div class="link-pill"><span class="link-dot">●</span> ORBITAL LINK ACTIVE &nbsp;•&nbsp; NASA POWER + SMAP + MODIS &nbsp;|&nbsp; CATBOOST RMSE: 0.0648</div>
</section>
<div class="source-row">
    <div class="source-chip"><strong>NASA POWER API</strong><span class="source-state state-live">● LIVE ON SCAN</span></div>
    <div class="source-chip"><strong>NASA SMAP</strong><span class="source-state">○ PROJECT DATA PILLAR</span></div>
    <div class="source-chip"><strong>MODIS (GEE)</strong><span class="source-state">○ PROJECT DATA PILLAR</span></div>
    <div class="source-chip"><strong>ISRIC SoilGrids · 5 cm</strong><span class="source-state state-live">● LIVE ON SCAN</span></div>
</div>
<div class="hud-panel">
    <div class="panel-heading"><span>Space-to-Roots Bridge</span><span class="telemetry-mono">ORBIT → CANOPY → ROOT ZONE</span></div>
    <svg class="bridge-svg" viewBox="0 0 960 190" role="img" aria-label="Satellite telemetry beam travels through the atmosphere to a root-zone soil sensor">
        <defs>
            <linearGradient id="soilLayer" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#12342F"/><stop offset="1" stop-color="#101A21"/></linearGradient>
            <linearGradient id="signalBeam" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#00F0FF" stop-opacity=".85"/><stop offset="1" stop-color="#10B981" stop-opacity=".35"/></linearGradient>
        </defs>
        <path d="M0 119 H960 V190 H0Z" fill="url(#soilLayer)" stroke="#10B981" stroke-opacity=".4"/>
        <path d="M0 143 H960 M0 167 H960" stroke="#10B981" stroke-opacity=".16" stroke-dasharray="3 8"/>
        <path d="M0 54 Q240 39 480 54 T960 54" fill="none" stroke="#00F0FF" stroke-opacity=".18"/>
        <path d="M0 79 Q240 64 480 79 T960 79" fill="none" stroke="#00F0FF" stroke-opacity=".12"/>
        <text x="24" y="48" fill="#91A4B8" font-size="10" font-family="JetBrains Mono">THERMOSPHERE</text>
        <text x="24" y="75" fill="#91A4B8" font-size="10" font-family="JetBrains Mono">ATMOSPHERE</text>
        <text x="24" y="139" fill="#8DE4BF" font-size="10" font-family="JetBrains Mono">ROOT ZONE</text>
        <g transform="translate(580 24)" stroke="#B9F7FF" stroke-width="2" fill="#102839">
            <rect x="-19" y="-9" width="38" height="18" rx="2"/><path d="M-48 -15 H-23 V15 H-48Z M23 -15 H48 V15 H23Z" fill="#0B3441" stroke="#00F0FF"/>
            <path d="M0 -9 V-21 M-7 -21 H7 M-14 0 H14" fill="none"/>
            <circle cx="0" cy="0" r="3" fill="#00F0FF" stroke="none"/>
        </g>
        <path class="beam" d="M580 48 L580 129" fill="none" stroke="url(#signalBeam)" stroke-width="3"/>
        <path d="M570 80 Q580 72 590 80 M564 89 Q580 76 596 89 M558 99 Q580 80 602 99" fill="none" stroke="#00F0FF" stroke-opacity=".72"/>
        <g transform="translate(580 122)" stroke="#B8F7DE" stroke-width="2" fill="none">
            <path d="M0 0 V39 M-8 39 H8 M0 26 L-10 34 M0 30 L11 38"/>
            <circle cx="0" cy="-2" r="5" fill="#10B981" stroke="#B8F7DE"/>
        </g>
        <text x="620" y="31" fill="#B9F7FF" font-size="10" font-family="JetBrains Mono">ORBITAL SENSOR</text>
        <text x="620" y="154" fill="#8DE4BF" font-size="10" font-family="JetBrains Mono">GROUND IoT PROBE</text>
        <circle cx="580" cy="77" r="3" fill="#00F0FF"><animate attributeName="cy" values="50;116;50" dur="2.4s" repeatCount="indefinite"/></circle>
    </svg>
</div>
<div class="pipeline">
    <div class="pipeline-node"><b>LAYER 01 · DECIDE</b><span>Deterministic JSON Rule Engine</span><small>crops_knowledge_base.json</small></div>
    <div class="pipeline-arrow">›</div>
    <div class="pipeline-node"><b>LAYER 02 · RETRIEVE</b><span>FAISS Vector Search · 959 chunks</span><small>FAO-56 knowledge context</small></div>
    <div class="pipeline-arrow">›</div>
    <div class="pipeline-node"><b>LAYER 03 · EXPLAIN</b><span>Context-grounded explanation</span><small>Gemini 3.1-Flash-Lite · fallback enabled</small></div>
</div>
<div class="coord-readout">FIELD FIX &nbsp; / &nbsp; LAT {st.session_state.lat:.4f}° &nbsp; · &nbsp; LON {st.session_state.lon:.4f}° &nbsp; / &nbsp; SENSOR {live_sensor_reading:.0%}</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.2], gap="large")

with col1:
    st.subheader(ui["step1"][lang])
    st.caption(ui["step1_cap"][lang])
    
    m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=7, tiles=None)
    folium.TileLayer(tiles="CartoDB dark_matter", name="Tactical Night", overlay=False, control=True).add_to(m)
    LocateControl(auto_start=False, position='topleft').add_to(m)
    folium.Marker([st.session_state.lat, st.session_state.lon], popup="📍 Farm", icon=folium.Icon(color="green", icon="leaf")).add_to(m)
    
    map_data = st_folium(m, height=400, width=700, returned_objects=["last_clicked"])
    
    if map_data and map_data.get("last_clicked"):
        c_lat, c_lon = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]
        if c_lat != st.session_state.lat or c_lon != st.session_state.lon:
            st.session_state.lat, st.session_state.lon = c_lat, c_lon
            st.rerun()

with col2:
    st.subheader(ui["step2"][lang])
    
    if st.button(ui["btn"][lang], type="primary", use_container_width=True):
        with st.spinner(ui["loading1"][lang]):
            real_live_data = fetch_live_satellite_data(st.session_state.lat, st.session_state.lon)
            
        with st.spinner(ui["loading2"][lang]):
            try:
                result = st.session_state.controller.run_pipeline(
                    raw_input_data=real_live_data, 
                    live_sensor_reading=live_sensor_reading,
                    lang=lang 
                )
                
                st.subheader(ui["diag"][lang])
                ai_percent = result["ai_baseline"] * 100
                sensor_percent = result["sensor_reading"] * 100
                delta_percent = result["deficit"] * 100
                ai_bar = max(0, min(100, ai_percent / 0.8))
                sensor_bar = max(0, min(100, sensor_percent / 0.8))
                st.markdown(f"""
                <div class="hud-panel">
                    <div class="panel-heading"><span>Space vs. Ground Reality</span><span class="telemetry-mono">LIVE FIELD COMPARISON</span></div>
                    <div class="telemetry-grid">
                        <div class="gauge"><div class="gauge-label">AI SPACE BASELINE · CATBOOST</div>
                            <div class="gauge-value">{ai_percent:.1f}%</div><div class="gauge-track"><div class="gauge-fill" style="width:{ai_bar:.1f}%"></div></div></div>
                        <div class="gauge gauge-ground"><div class="gauge-label">GROUND IoT SENSOR</div>
                            <div class="gauge-value">{sensor_percent:.1f}%</div><div class="gauge-track"><div class="gauge-fill" style="width:{sensor_bar:.1f}%"></div></div></div>
                        <div class="gauge gauge-delta"><div class="gauge-label">WATER GAP · BASELINE − SENSOR</div>
                            <div class="gauge-value">{delta_percent:+.1f}%</div><div class="gauge-label">ALERT THRESHOLD: ±10.0%</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if result['status'] == "SEVERE WATER STRESS":
                    st.markdown(f'<div class="stress-banner">▲ &nbsp; SEVERE WATER STRESS DETECTED &nbsp; / &nbsp; {delta_percent:+.1f}% DEFICIT<br><span style="font-weight:500">{ui["stress"][lang]}</span></div>', unsafe_allow_html=True)
                elif result['status'] == "OVER-IRRIGATION":
                    st.warning(f"⚠️ **{ui['over'][lang]}**")
                else:
                    st.success(f"✅ **{ui['opt'][lang]}**")
                    
                st.subheader(ui["rep_t"][lang])
                st.info(f"{ui['act'][lang]} {result['recommended_crop']}")
                st.write(f"{ui['fao'][lang]}\n\n{result['fao_report']}")
                
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.write(ui["wait"][lang])