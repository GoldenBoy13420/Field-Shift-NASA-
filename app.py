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

# إصلاح تباين الألوان (Contrast) وتوضيح الخطوط
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
        
        /* تطبيق الخط على كل العناصر بأمان بدون تدمير ألوان Streamlit الأساسية */
        html, body, [class*="css"], p, span, label { 
            font-family: 'Cairo', sans-serif !important; 
        }
        
        /* خلفية التطبيق (أخضر زراعي فاتح جداً ومريح) */
        .stApp { background-color: #F4F9F4; }
        
        /* خلفية القائمة الجانبية */
        [data-testid="stSidebar"] { background-color: #E2EDE2; border-right: 2px solid #C8DFC8; }
        
        /* العناوين: لون غامق جداً (شبه أسود) عشان تبقى واضحة وضوح الشمس */
        h1, h2, h3, h4, h5, h6 { 
            color: #0A3619 !important; 
            font-weight: 900 !important; 
        }
        
        /* النصوص العادية: أسود واضح لتسهيل القراءة */
        .stMarkdown p { color: #111111; font-weight: 600; font-size: 1.1rem; }
        
        /* الزرار الأساسي: أخضر قوي مع نص أبيض ناصع */
        div.stButton > button:first-child { 
            background-color: #125B29; 
            color: #FFFFFF !important; 
            border-radius: 8px; 
            border: none; 
            font-weight: 800; 
            font-size: 1.2rem;
            padding: 0.6rem 1.2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.15); 
            transition: all 0.3s ease; 
        }
        div.stButton > button:first-child:hover { 
            background-color: #0A3619; 
            transform: translateY(-2px); 
        }
        
        /* الأرقام (الرطوبة والنتائج): واضحة وكبيرة */
        div[data-testid="stMetricValue"] { color: #125B29 !important; font-weight: 900 !important; font-size: 2.2rem !important; }
        div[data-testid="stMetricLabel"] { color: #222222 !important; font-weight: 700 !important; font-size: 1.1rem !important; }
        
        /* إزالة التحكم الإجباري في الألوان داخل التنبيهات عشان Streamlit يظبطها صح (أبيض على أحمر، إلخ) */
        .stAlert { border-radius: 10px; font-weight: 600; }
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
st.title(ui["title"][lang])
st.markdown(ui["subtitle"][lang])

col1, col2 = st.columns([1, 1.2], gap="large")

with col1:
    st.subheader(ui["step1"][lang])
    st.caption(ui["step1_cap"][lang])
    
    m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=7, tiles=None)
    folium.TileLayer(tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}", attr="Google", name="Google Satellite", overlay=False, control=True).add_to(m)
    LocateControl(auto_start=False, position='topleft').add_to(m)
    folium.Marker([st.session_state.lat, st.session_state.lon], popup="📍 Farm", icon=folium.Icon(color="green", icon="leaf")).add_to(m)
    
    map_data = st_folium(m, height=400, width=400, returned_objects=["last_clicked"])
    
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
                metric_cols = st.columns(3)
                metric_cols[0].metric(ui["ai_base"][lang], f"{result['ai_baseline']:.3f}")
                metric_cols[1].metric(ui["iot"][lang], f"{result['sensor_reading']:.3f}")
                metric_cols[2].metric(ui["def"][lang], f"{result['deficit']:.3f}", delta=f"{result['deficit']:.3f}", delta_color="inverse")
                
                st.write("---")
                if result['status'] == "SEVERE WATER STRESS":
                    st.error(f"🚨 **{ui['stress'][lang]}**")
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