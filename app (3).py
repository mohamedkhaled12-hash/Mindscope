import streamlit as st
import pandas as pd
import joblib
import numpy as np
import plotly.express as px
import warnings
import google.generativeai as genai
from PIL import Image
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

warnings.filterwarnings('ignore')

# 1. Page Config
st.set_page_config(page_title="Vision Analytics AI", page_icon="✨", layout="wide")

# ==========================================
# 📊 إعداد الاتصال بقاعدة بيانات Google Sheets
# ==========================================
@st.cache_resource
def get_gspread_client():
    try:
        creds_json = st.secrets["GOOGLE_CREDENTIALS"]
        if isinstance(creds_json, str):
            creds_dict = json.loads(creds_json)
        else:
            creds_dict = creds_json
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        return None

db_client = get_gspread_client()

def log_data(sheet_tab, row_data):
    if db_client:
        try:
            sheet = db_client.open("Vision_Analytics_DB").worksheet(sheet_tab)
            sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + row_data)
        except Exception:
            pass  

if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = ""

# ==========================================
# 🎨 Premium UI/UX: Animations & Refined Glassmorphism
# ==========================================
st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #020617 100%) !important;
        background-attachment: fixed;
    }
    [data-testid="stHeader"] { background-color: transparent !important; }
    [data-testid="stHeader"] * { color: #F8FAFC !important; }

    h1, h2, h3, h4, label, p, li {
        color: #F8FAFC !important;
        font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
        font-weight: 600 !important;
        letter-spacing: 0.2px;
    }

    .gradient-text {
        background: linear-gradient(135deg, #A855F7 0%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        font-size: 3.2rem;
        text-align: center;
        margin-top: -20px;
        letter-spacing: -1px;
        text-shadow: 0px 4px 20px rgba(168, 85, 247, 0.3); 
    }

    @keyframes fadeInUp {
        0% { opacity: 0; transform: translateY(30px); }
        100% { opacity: 1; transform: translateY(0); }
    }

    @keyframes pulseGlow {
        0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.5); }
        70% { box-shadow: 0 0 0 12px rgba(59, 130, 246, 0); }
        100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
    }

    [data-testid="stForm"], .metric-card {
        background: rgba(15, 23, 42, 0.45) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.08);
        transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.4s ease;
        animation: fadeInUp 0.8s ease-out forwards;
    }
    
    [data-testid="stForm"]:hover, .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.15);
    }

    div[data-baseweb="select"] > div, div[data-baseweb="base-input"] > input {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        border-radius: 10px !important;
        border: 2px solid transparent !important;
        -webkit-text-fill-color: #0F172A !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    div[data-baseweb="select"] *, div[data-baseweb="base-input"] * {
        color: #0F172A !important;
    }

    div[data-baseweb="select"] > div:hover, div[data-baseweb="base-input"] > input:hover {
        border: 2px solid rgba(56, 189, 248, 0.5) !important;
        transform: scale(1.01);
    }

    ul[data-baseweb="menu"], div[data-baseweb="popover"] {
        background-color: #F8FAFC !important;
        border-radius: 10px !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.3) !important;
    }
    ul[data-baseweb="menu"] li, ul[data-baseweb="menu"] li *, div[data-baseweb="popover"] * {
        color: #0F172A !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        -webkit-text-fill-color: #0F172A !important;
    }
    ul[data-baseweb="menu"] li { padding: 10px 15px !important; }

    div[role="radiogroup"] {
        display: flex;
        flex-direction: row;
        justify-content: center !important;
        gap: 8px;
        background: rgba(15, 23, 42, 0.6);
        padding: 6px;
        border-radius: 100px;
        width: fit-content;
        margin: 0 auto 35px auto;
        border: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        animation: fadeInUp 0.5s ease-out forwards;
    }
    .stRadio [role="radio"] { display: none !important; }
    .stRadio label {
        background: transparent !important;
        padding: 10px 30px !important;
        border-radius: 100px !important;
        cursor: pointer;
        transition: all 0.3s ease;
        margin: 0 !important;
        border: none !important;
    }
    .stRadio label:hover { background: rgba(255, 255, 255, 0.05) !important; }
    .stRadio label:has(input:checked) {
        background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%) !important;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.5);
    }
    .stRadio label:has(input:checked) div {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        letter-spacing: 0.3px;
    }

    div[data-testid="stFormSubmitButton"] > button, [data-testid="baseButton-secondary"] {
        background: linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%) !important;
        border: none !important;
        padding: 16px 24px !important;
        border-radius: 12px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        animation: pulseGlow 2.5s infinite;
    }
    div[data-testid="stFormSubmitButton"] > button *, [data-testid="baseButton-secondary"] * {
        color: #0F172A !important; 
        -webkit-text-fill-color: #0F172A !important;
        font-weight: 900 !important; 
        font-size: 16px !important;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    div[data-testid="stFormSubmitButton"] > button:hover, [data-testid="baseButton-secondary"]:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 15px 30px -5px rgba(59, 130, 246, 0.6) !important;
        animation: none;
    }

    [data-testid="stExpander"] {
        background: rgba(15, 23, 42, 0.45) !important;
        backdrop-filter: blur(20px);
        border-radius: 15px !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        margin-bottom: 20px;
        animation: fadeInUp 0.7s ease-out forwards;
    }
    [data-testid="stExpander"] summary p {
        color: #38BDF8 !important;
        font-weight: 800 !important;
        font-size: 16px;
    }
    [data-testid="stExpanderDetails"] { background: transparent !important; }
    
    .script-text { line-height: 1.8; font-size: 15px; margin-bottom: 15px; }
    .script-title { font-size: 24px; font-weight: 900; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px; text-shadow: 0 2px 4px rgba(0,0,0,0.3);}
    .section-box { background: rgba(255,255,255,0.03); padding: 18px; border-radius: 10px; margin-bottom: 15px; box-shadow: inset 0 2px 10px rgba(0,0,0,0.1);}
    .section-box ul { margin-top: 10px; padding-right: 20px; }
    .section-box li { margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

# 2. Load Models (Updated to include new app model and encoder)
@st.cache_resource
def load_assets():
    risk_model = joblib.load('risk_model_pipeline.pkl')
    app_model = joblib.load('app_behavior_model_xgb (1).pkl') # Updated
    encoder = joblib.load('label_encoder.pkl')
    app_encoder = joblib.load('label_encoder (1).pkl') # Added
    return risk_model, app_model, encoder, app_encoder

try:
    risk_model, app_model, encoder, app_encoder = load_assets()
except Exception as e:
    st.error(f"⚠️ Failed to load models. Error: {e}")
    st.stop()

# ==========================================
# 🚀 Navigation Header
# ==========================================
st.markdown("<div class='gradient-text'>Vision Analytics</div>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94A3B8 !important; margin-bottom: 25px; font-size: 1.1rem; animation: fadeInUp 0.4s ease-out forwards;'>Empowered by Advanced Machine Learning</p>", unsafe_allow_html=True)

page = st.radio("", ["App Behavior Analysis", "Student Risk Analysis", "AI Assistant 🤖"], horizontal=True, label_visibility="collapsed")

# ------------------------------------------------------------------
# Page 1: App Behavior Analysis (10 Results Update)
# ------------------------------------------------------------------
if page == "App Behavior Analysis":
    st.markdown("<h3 style='color: #67E8F9 !important;'>📱 App Behavior Tech-Metrics</h3>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("💡 Guide: How to find these metrics on your phone?"):
        col_android, col_ios = st.columns(2)
        with col_android:
            st.markdown("<h4 style='color:#34D399; margin-bottom:5px;'>🤖 Android Devices</h4>", unsafe_allow_html=True)
            st.markdown("""
            * **Screen On Time & Usage Time:** Go to **Settings > Digital Wellbeing & parental controls**.
            * **Battery Drain:** Go to **Settings > Battery > Battery usage**.
            * **Data Usage:** Go to **Settings > Network & internet > Internet > App data usage**.
            """)
        with col_ios:
            st.markdown("<h4 style='color:#F87171; margin-bottom:5px;'>🍏 iOS (iPhone)</h4>", unsafe_allow_html=True)
            st.markdown("""
            * **Screen On Time & Usage Time:** Go to **Settings > Screen Time > See All Activity**.
            * **Battery Drain:** Go to **Settings > Battery**.
            * **Data Usage:** Go to **Settings > Cellular**.
            """)
        st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 15px 0;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#A855F7; margin-bottom:5px;'>🔋 How to calculate Battery Drain (mAh)?</h4>", unsafe_allow_html=True)
        st.markdown("""
        > **` (Percentage Used ÷ 100) × Total Battery Capacity (mAh) `**<br>
        *Example:* If you used 40% of a 5000 mAh battery: `(40 ÷ 100) × 5000 = 2000 mAh`.
        """, unsafe_allow_html=True)

    with st.form("app_behavior_form"):
        st.subheader("⚙️ Technical Telemetry")
        st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 10px 0 25px 0;'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2, gap="large")
        with col1:
            age = st.number_input("Age:", 10, 100, 20)
            gender = st.selectbox("Gender:", ["Male", "Female"])
            num_apps = st.number_input("Apps Installed:", 0, 500, 50)
        with col2:
            screen_time = st.number_input("Screen Time (hours):", 0.0, 24.0, 5.0)
            battery = st.number_input("Battery Drain (mAh):", 0, 10000, 2000)
            data_usage = st.number_input("Data (MB):", 0, 50000, 1000)
            app_usage = st.number_input("Usage Time (min):", 0, 1440, 300)
        submit_app = st.form_submit_button("ANALYZE USER BEHAVIOR", use_container_width=True)

    if submit_app:
        with st.spinner("Analyzing..."):
            raw_data = {
                'App Usage Time (min/day)': [float(app_usage)],
                'Screen On Time (hours/day)': [float(screen_time)],
                'Battery Drain (mAh/day)': [float(battery)],
                'Number of Apps Installed': [float(num_apps)],
                'Data Usage (MB/day)': [float(data_usage)],
                'Age': [float(age)],
                'Gender': [gender]
            }
            df_app = pd.DataFrame(raw_data)
            
            if hasattr(app_model, 'feature_names_in_'):
                expected_cols = list(app_model.feature_names_in_)
                if 'Gender_Male' in expected_cols:
                    df_app['Gender_Male'] = 1.0 if gender == "Male" else 0.0
                    df_app['Gender_Female'] = 1.0 if gender == "Female" else 0.0
                    if 'Gender' in df_app.columns:
                        df_app = df_app.drop(columns=['Gender'])
                df_app = df_app.reindex(columns=expected_cols, fill_value=0.0)

            try:
                pred_raw = app_model.predict(df_app)[0]
                success = True
            except Exception as e1:
                try:
                    df_app['Gender'] = 1.0 if gender == "Male" else 0.0
                    df_app = df_app.astype(float)
                    pred_raw = app_model.predict(df_app)[0]
                    success = True
                except Exception as e2:
                    success = False
                    st.error(f"⚠️ خطأ في توافق البيانات: {e2}")
            
            if success:
                # 🛠️ استخدام الـ Encoder الجديد لفك التشفير وتنظيف النص فوراً من أي مسافات مخفية
                pred_class_name = app_encoder.inverse_transform([int(pred_raw)])[0]
                clean_pred_class = str(pred_class_name).replace('\r', '').replace('\n', '').strip()

                st.session_state['last_analysis_context'] = f"قام المستخدم للتو بتحليل (App Behavior Analysis). النتيجة هي: {clean_pred_class}."
                log_data("Apps", [age, gender, num_apps, screen_time, battery, data_usage, app_usage, clean_pred_class])

                st.markdown(f"""
                    <div class="metric-card" style="text-align: center; margin-top:25px;">
                        <h3 style='color:#CBD5E1 !important;'>Predicted Classification</h3>
                        <h1 style='color:#22D3EE !important; font-size:3.5rem; font-weight:900;'>{clean_pred_class}</h1>
                    </div>
                """, unsafe_allow_html=True)

                # ==========================================
                # 📝 توزيع الإسكريبت على الـ 10 نتائج (Low Part & High Part)
                # ==========================================
                app_scripts = {
                    "1 - Low Part": """<div dir="rtl" style="text-align: right;" class="script-text">
<div class="script-title" style="color:#34D399;">الفئة 1: الخطر الأدنى | Class 1: Minimal Risk (Low Part)</div>
<div class="section-box" style="border-right: 4px solid #34D399;">
<p style="color:#6EE7B7; font-size: 18px; margin-bottom: 5px;"><b>التحليل السلوكي (المنفعة الوظيفية):</b></p>
<p>في هذا الجزء المنخفض من الفئة الأولى، تُظهر علاقة واعية ومقصودة جداً مع جهازك، حيث تستخدمه بشكل أساسي للتواصل الضروري، والتعلم، والأدوات المهمة. في هذه المرحلة، تكاد تكون "نسبة تعفن الدماغ" (Brainrot Percentage) معدومة، وتتراوح بشكل مريح بين 0% و 5%. وقت استخدامك للتطبيقات منخفض، واستهلاك البطارية يعكس تفاعلاً ضئيلاً مع خوارزميات وسائل التواصل الاجتماعي المستنزفة. أنت تنظر إلى التكنولوجيا كمساعد مفيد وليس كفخ. ولأن مسارات الدوبامين لديك لا يتم التلاعب بها باستمرار بواسطة مقاطع الفيديو القصيرة، فإن مدى انتباهك يظل حاداً للغاية، ولا يوجد أي إرهاق رقمي. يمثل هذا المعيار الذهبي للرفاهية الرقمية، مما يعني أن لديك سيطرة ممتازة على بيئتك، مما يتيح لك الانخراط بسهولة في العمل العميق والحفاظ على علاقات قوية في العالم الحقيقي (خارج الشاشة).</p>
</div>
<div class="section-box" style="border-right: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>التوصيات العملية:</b></p>
<ul>
<li><b>الحفاظ على مناطق خالية من التكنولوجيا:</b> اجعل غرفة نومك خالية تماماً من الشاشات لحماية جودة نومك العالية. تضمن هذه العادة البسيطة عدم انزلاقك عن طريق الخطأ إلى سلوكيات التمرير في وقت متأخر من الليل.</li>
<li><b>فحص الجهاز المجدول:</b> استمر في التحقق من تطبيقاتك في أوقات محددة بدلاً من الاستجابة لكل إشعار. هذا يساعد في الحفاظ على تركيزك الممتاز ويمنع التلاعب الخوارزمي.</li>
<li><b>تبني الهوايات التناظرية (التقليدية):</b> خصص وقتاً لقراءة الكتب الورقية أو ممارسة الرياضات الخارجية. تعزز الأنشطة غير المتصلة بالإنترنت بطبيعتها مدى انتباهك القوي وتحافظ على صحة دماغك.</li>
</ul>
</div>
</div>
<div dir="ltr" style="text-align: left; margin-top:25px; border-top: 1px dashed rgba(255,255,255,0.2); padding-top:20px;" class="script-text">
<div class="section-box" style="border-left: 4px solid #34D399;">
<p style="color:#6EE7B7; font-size: 18px; margin-bottom: 5px;"><b>Analysis (Functional Utility):</b></p>
<p>In this Low Part of Class 1, you exhibit a highly intentional relationship with your device, primarily utilizing it for essential communication, learning, and necessary tools. At this stage, your estimated "Brainrot Percentage" is virtually non-existent, lingering comfortably between 0% and 5%. Your app usage time is low, and your battery drain reflects minimal engagement with heavy social media algorithms. You view technology as a helpful assistant rather than a trap. Because your dopamine pathways aren't constantly hijacked by short-form videos, your attention span remains incredibly sharp, and digital fatigue is absent. This represents the gold standard of digital well-being, meaning you have excellent control over your environment, allowing you to easily engage in deep work and maintain strong offline connections.</p>
</div>
<div class="section-box" style="border-left: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>Recommendations:</b></p>
<ul>
<li><b>Maintain Tech-Free Zones:</b> Keep your bedroom entirely screen-free to protect your high-quality sleep. This simple habit ensures that you don't accidentally slip into late-night scrolling behaviors.</li>
<li><b>Scheduled Device Checks:</b> Continue checking your apps at designated times rather than responding to every notification. This helps preserve your excellent focus and prevents algorithmic manipulation.</li>
<li><b>Embrace Analog Hobbies:</b> Dedicate time to reading physical books or engaging in outdoor sports. Offline activities naturally reinforce your strong attention span and keep your brain healthy.</li>
</ul>
</div>
</div>""",

                    "1 - High Part": """<div dir="rtl" style="text-align: right;" class="script-text">
<div class="script-title" style="color:#34D399;">الفئة 1: الخطر الأدنى | Class 1: Minimal Risk (High Part)</div>
<div class="section-box" style="border-right: 4px solid #10B981;">
<p style="color:#34D399; font-size: 18px; margin-bottom: 5px;"><b>التحليل السلوكي (الترفيه العرضي):</b></p>
<p>في الجزء المرتفع من الفئة الأولى، لا تزال تحتفظ بسيطرة ممتازة، لكنك تنغمس أحياناً في فترات قصيرة من الترفيه الرقمي. تتراوح نسبة "تعفن الدماغ" لديك بين 6% و 15%. قد تقضي وقتاً أطول قليلاً على هاتفك، ربما في تصفح وسائل التواصل الاجتماعي أو مشاهدة بعض مقاطع الفيديو القصيرة خلال فترات الراحة. ومع ذلك، نادراً ما تفقد الإحساس بالوقت. يُظهر هذا المستوى أنه يمكنك الاستمتاع بأمان بالعالم الرقمي دون السماح له بالتدخل في مسؤولياتك اليومية أو عبء العمل الأكاديمي. على الرغم من أنك تواجه زيادات طفيفة في وقت الشاشة واستخدام البيانات، إلا أن وظائفك الإدراكية وتنظيمك العاطفي تظل سليمة تماماً. أنت توازن بنجاح بين الاتصال الحديث ونمط الحياة الصحي، متجنباً الضباب العقلي الذي يصاحب التمرير اللانهائي.</p>
</div>
<div class="section-box" style="border-right: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>التوصيات العملية:</b></p>
<ul>
<li><b>الحفاظ على مناطق خالية من التكنولوجيا:</b> اجعل غرفة نومك خالية تماماً من الشاشات لحماية جودة نومك العالية. تضمن هذه العادة البسيطة عدم انزلاقك عن طريق الخطأ إلى سلوكيات التمرير في وقت متأخر من الليل.</li>
<li><b>فحص الجهاز المجدول:</b> استمر في التحقق من تطبيقاتك في أوقات محددة بدلاً من الاستجابة لكل إشعار. هذا يساعد في الحفاظ على تركيزك الممتاز ويمنع التلاعب الخوارزمي.</li>
<li><b>تبني الهوايات التناظرية (التقليدية):</b> خصص وقتاً لقراءة الكتب الورقية أو ممارسة الرياضات الخارجية. تعزز الأنشطة غير المتصلة بالإنترنت بطبيعتها مدى انتباهك القوي وتحافظ على صحة دماغك.</li>
</ul>
</div>
</div>
<div dir="ltr" style="text-align: left; margin-top:25px; border-top: 1px dashed rgba(255,255,255,0.2); padding-top:20px;" class="script-text">
<div class="section-box" style="border-left: 4px solid #10B981;">
<p style="color:#34D399; font-size: 18px; margin-bottom: 5px;"><b>Analysis (Casual Entertainment):</b></p>
<p>In the High Part of Class 1, you still maintain excellent control, but you occasionally indulge in short bursts of digital entertainment. Your Brainrot Percentage hovers around 6% to 15%. You might spend a bit more time on your phone, perhaps checking social media or watching a few short-form videos during your breaks. However, you rarely lose track of time. This tier shows that you can safely enjoy the digital world without letting it interfere with your daily responsibilities or academic workload. While you experience slight increases in screen time and data usage, your cognitive functions and emotional regulation remain completely intact. You are successfully balancing modern connectivity with a healthy lifestyle, avoiding the mental fog that accompanies endless scrolling.</p>
</div>
<div class="section-box" style="border-left: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>Recommendations:</b></p>
<ul>
<li><b>Maintain Tech-Free Zones:</b> Keep your bedroom entirely screen-free to protect your high-quality sleep. This simple habit ensures that you don't accidentally slip into late-night scrolling behaviors.</li>
<li><b>Scheduled Device Checks:</b> Continue checking your apps at designated times rather than responding to every notification. This helps preserve your excellent focus and prevents algorithmic manipulation.</li>
<li><b>Embrace Analog Hobbies:</b> Dedicate time to reading physical books or engaging in outdoor sports. Offline activities naturally reinforce your strong attention span and keep your brain healthy.</li>
</ul>
</div>
</div>""",

                    "2 - Low Part": """<div dir="rtl" style="text-align: right;" class="script-text">
<div class="script-title" style="color:#6EE7B7;">الفئة 2: عادة ناشئة | Class 2: Emerging Habit (Low Part)</div>
<div class="section-box" style="border-right: 4px solid #6EE7B7;">
<p style="color:#34D399; font-size: 18px; margin-bottom: 5px;"><b>التحليل السلوكي (وقت الفراغ السلبي):</b></p>
<p>في الجزء المنخفض من الفئة الثانية، تعكس عاداتك الرقمية وقت فراغ سلبي وعرضي. تبلغ نسبة "تعفن الدماغ" لديك حوالي 16% إلى 25%. في هذا المستوى، تستخدم التطبيقات بشكل متكرر للاسترخاء بعد يوم طويل، وتسمح للخوارزميات بتوجيهك لفترات قصيرة. وقت الشاشة واستخدام البيانات مرتفعان بشكل معتدل، ولكن ليس لدرجة مقلقة بعد. في حين أن هذا السلوك يبدو كطريقة غير ضارة للاسترخاء، فإن دماغك يتلقى في الواقع تحفيزاً مستمراً ومنخفض المستوى. قد تلاحظ أحياناً ممانعة طفيفة لترك الهاتف، على الرغم من أنك تستطيع ذلك في النهاية. إنها مرحلة انتقالية تتشكل فيها العادات الرقمية، لكنها لم تتسبب بعد في تشتت ملحوظ في الانتباه أو تعطيل أنماط نومك الأساسية وإنتاجيتك اليومية.</p>
</div>
<div class="section-box" style="border-right: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>التوصيات العملية:</b></p>
<ul>
<li><b>قاعدة الـ 30 دقيقة:</b> قصر جلسات التمرير على 30 دقيقة يومياً. تظهر الدراسات أن تقييد وسائل التواصل الاجتماعي بنصف ساعة يحسن الحالة المزاجية بشكل كبير ويقلل من مستويات القلق.</li>
<li><b>إيقاف الإشعارات غير الضرورية:</b> قم بتعطيل التنبيهات لتطبيقات التواصل الاجتماعي. من خلال إيقاف الانقطاعات المستمرة، تستعيد السيطرة على انتباهك بدلاً من ترك الجهاز يملي عليك تركيزك.</li>
<li><b>الاستخدام المقصود للتطبيقات:</b> قبل فتح أي تطبيق، اذكر بصوت عالٍ الغرض من ذلك. إذا لم تتمكن من تحديد سبب فتحه، فضع الهاتف جانباً. هذا يكسر رد الفعل المتمثل في التحقق الطائش.</li>
</ul>
</div>
</div>
<div dir="ltr" style="text-align: left; margin-top:25px; border-top: 1px dashed rgba(255,255,255,0.2); padding-top:20px;" class="script-text">
<div class="section-box" style="border-left: 4px solid #6EE7B7;">
<p style="color:#34D399; font-size: 18px; margin-bottom: 5px;"><b>Analysis (Passive Leisure):</b></p>
<p>In the Low Part of Class 2, your digital habits reflect casual, passive leisure. Your Brainrot Percentage sits around 16% to 25%. At this level, you frequently use apps for relaxation after a long day, letting algorithms guide you for short periods. Your screen time and data usage are moderately elevated, but not yet alarming. While this behavior feels like harmless unwinding, your brain is actually receiving constant, low-level stimulation. You might occasionally notice a slight reluctance to put the phone down, though you ultimately can. It is a transitional phase where digital habits are forming, but they have not yet caused noticeable attention fragmentation or disrupted your primary sleep patterns and daily productivity.</p>
</div>
<div class="section-box" style="border-left: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>Recommendations:</b></p>
<ul>
<li><b>The 30-Minute Rule:</b> Limit your scrolling sessions to 30 minutes daily. Studies show that restricting social media to half an hour significantly improves mood and reduces anxiety levels.</li>
<li><b>Turn Off Non-Essential Notifications:</b> Disable push alerts for social media apps. By stopping constant interruptions, you regain control over your attention rather than letting the device dictate your focus.</li>
<li><b>Intentional App Usage:</b> Before opening an app, verbally state your purpose. If you cannot define why you are opening it, put the phone down. This breaks the reflex of mindless checking.</li>
</ul>
</div>
</div>""",

                    "2 - High Part": """<div dir="rtl" style="text-align: right;" class="script-text">
<div class="script-title" style="color:#6EE7B7;">الفئة 2: عادة ناشئة | Class 2: Emerging Habit (High Part)</div>
<div class="section-box" style="border-right: 4px solid #34D399;">
<p style="color:#10B981; font-size: 18px; margin-bottom: 5px;"><b>التحليل السلوكي (التمرير المشتت):</b></p>
<p>يقدم الجزء المرتفع من الفئة الثانية العلامات الحقيقية الأولى للتشتت الرقمي، مع نسبة "تعفن الدماغ" تتراوح بين 26% و 35%. من المحتمل أن تظهر بيانات القياس عن بُعد (Telemetry) الخاصة بك زيادة في استهلاك البطارية والتبديل المتكرر بين التطبيقات. غالباً ما تلتقط هاتفك لسبب معين، لتجد نفسك تقوم بالتمرير بلا هدف بعد عشر دقائق. يشير هذا المستوى إلى أن خوارزميات وسائل التواصل الاجتماعي بدأت في التقاط انتباهك والاحتفاظ به بنجاح. قد تعاني من إرهاق عقلي خفيف أو تأخير طفيف في إكمال المهام بسبب الانقطاعات الرقمية. على الرغم من أنك لا تعاني من احتراق كامل، إلا أن الحداثة المستمرة من شاشتك تكيف دماغك ببطء لاشتهاء جرعات متكررة من الدوبامين، مما يجعل التركيز المستمر أكثر صعوبة قليلاً.</p>
</div>
<div class="section-box" style="border-right: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>التوصيات العملية:</b></p>
<ul>
<li><b>قاعدة الـ 30 دقيقة:</b> قصر جلسات التمرير على 30 دقيقة يومياً. تظهر الدراسات أن تقييد وسائل التواصل الاجتماعي بنصف ساعة يحسن الحالة المزاجية بشكل كبير ويقلل من مستويات القلق.</li>
<li><b>إيقاف الإشعارات غير الضرورية:</b> قم بتعطيل التنبيهات لتطبيقات التواصل الاجتماعي. من خلال إيقاف الانقطاعات المستمرة، تستعيد السيطرة على انتباهك بدلاً من ترك الجهاز يملي عليك تركيزك.</li>
<li><b>الاستخدام المقصود للتطبيقات:</b> قبل فتح أي تطبيق، اذكر بصوت عالٍ الغرض من ذلك. إذا لم تتمكن من تحديد سبب فتحه، فضع الهاتف جانباً. هذا يكسر رد الفعل المتمثل في التحقق الطائش.</li>
</ul>
</div>
</div>
<div dir="ltr" style="text-align: left; margin-top:25px; border-top: 1px dashed rgba(255,255,255,0.2); padding-top:20px;" class="script-text">
<div class="section-box" style="border-left: 4px solid #34D399;">
<p style="color:#10B981; font-size: 18px; margin-bottom: 5px;"><b>Analysis (Distracted Scrolling):</b></p>
<p>The High Part of Class 2 introduces the first real signs of digital distraction, with a Brainrot Percentage ranging from 26% to 35%. Your telemetry data likely shows increased battery drain and frequent app switching. You often pick up your phone for a specific reason, only to find yourself scrolling aimlessly ten minutes later. This level indicates that social media algorithms are beginning to successfully capture and hold your attention. You might experience mild mental fatigue or a slight delay in completing tasks due to digital interruptions. While you arent experiencing full burnout, the constant novelty from your screen is slowly conditioning your brain to crave frequent dopamine hits, making sustained focus slightly more difficult.</p>
</div>
<div class="section-box" style="border-left: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>Recommendations:</b></p>
<ul>
<li><b>The 30-Minute Rule:</b> Limit your scrolling sessions to 30 minutes daily. Studies show that restricting social media to half an hour significantly improves mood and reduces anxiety levels.</li>
<li><b>Turn Off Non-Essential Notifications:</b> Disable push alerts for social media apps. By stopping constant interruptions, you regain control over your attention rather than letting the device dictate your focus.</li>
<li><b>Intentional App Usage:</b> Before opening an app, verbally state your purpose. If you cannot define why you are opening it, put the phone down. This breaks the reflex of mindless checking.</li>
</ul>
</div>
</div>""",

                    "3 - Low Part": """<div dir="rtl" style="text-align: right;" class="script-text">
<div class="script-title" style="color:#FBBF24;">الفئة 3: خطر متوسط | Class 3: Moderate Risk (Low Part)</div>
<div class="section-box" style="border-right: 4px solid #FCD34D;">
<p style="color:#FBBF24; font-size: 18px; margin-bottom: 5px;"><b>التحليل السلوكي (الاستهلاك الروتيني):</b></p>
<p>عند دخولك الجزء المنخفض من الفئة الثالثة، يتحول تفاعلك الرقمي إلى استهلاك روتيني، مما يضع نسبة "تعفن الدماغ" لديك بين 36% و 45%. وقت الشاشة لديك مرتفع بشكل ملحوظ، وأصبح التمرير اللانهائي عادة يومية وليس متعة عرضية. من المحتمل أنك تعتمد على المحتوى سريع الوتيرة لتهدئة نفسك أو الهروب من الملل. يعني هذا النمط السلوكي أن دماغك يبقى باستمرار في حالة تأهب، مما يمنع التعافي العقلي الحقيقي. قد تبدأ في ملاحظة أن المهام الأطول، مثل القراءة أو الدراسة، تبدو محبطة أو مملة بشكل غير عادي. يمثل هذا بداية مرحلة "تشتت الانتباه"، حيث تنخفض قدرتك المعرفية، وتبدأ في التوق إلى الإشباع الفوري الذي توفره مقاطع الفيديو القصيرة.</p>
</div>
<div class="section-box" style="border-right: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>التوصيات العملية:</b></p>
<ul>
<li><b>تنفيذ 'فترات راحة للتمرير':</b> بدلاً من محاولة الإقلاع فجأة، قم بجدولة فترات راحة للتمرير مدتها 10 دقائق أثناء جلسات الدراسة أو العمل. بمجرد أن يرن المنبه، يجب عليك العودة إلى مهمتك على الفور.</li>
<li><b>تنظيم المحتوى الخاص بك:</b> قم بإلغاء متابعة الحسابات التي تقدم ترفيهاً طائشاً بحتاً. استبدلها بصناع محتوى تعليميين أو ملهمين بحيث تكتسب قيمة عندما تقوم بالتمرير، وليس مجرد دوبامين سريع.</li>
<li><b>ممارسة تقنية بومودورو (Pomodoro):</b> اعمل في فترات تركيز مكثفة مدتها 25 دقيقة تليها استراحة خالية من التكنولوجيا لمدة 5 دقائق. تعيد هذه الطريقة المدروسة جيداً بناء قدرة دماغك على الانتباه المستمر ببطء.</li>
<li><b>التخلص من السموم الرقمية الصباحية:</b> تجنب النظر إلى هاتفك في الساعة الأولى بعد الاستيقاظ. هذا يمنع الارتفاع الفوري للدوبامين ويحدد نغمة أكثر هدوءاً وتركيزاً لبقية يومك.</li>
</ul>
</div>
</div>
<div dir="ltr" style="text-align: left; margin-top:25px; border-top: 1px dashed rgba(255,255,255,0.2); padding-top:20px;" class="script-text">
<div class="section-box" style="border-left: 4px solid #FCD34D;">
<p style="color:#FBBF24; font-size: 18px; margin-bottom: 5px;"><b>Analysis (Routine Consumption):</b></p>
<p>Entering the Low Part of Class 3, your digital engagement shifts into routine consumption, placing your Brainrot Percentage around 36% to 45%. Your screen time is noticeably high, and endless scrolling has become a daily habit rather than an occasional treat. You likely rely on fast-paced content to self-soothe or escape boredom. This behavioral pattern means your brain is constantly kept in an alert state, preventing true mental recovery. You may start noticing that longer tasks, like reading or studying, feel unusually frustrating or boring. This marks the beginning of the "attention fragmentation" phase, where your cognitive stamina drops, and you begin to crave the instant gratification provided by short-form videos.</p>
</div>
<div class="section-box" style="border-left: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>Recommendations:</b></p>
<ul>
<li><b>Implement 'Scroll Breaks':</b> Instead of trying to quit cold turkey, schedule 10-minute scroll breaks during your study or work sessions. Once the timer rings, you must return to your task immediately.</li>
<li><b>Curate Your Feeds:</b> Unfollow accounts that provide purely mindless entertainment. Replace them with educational or inspiring creators so that when you do scroll, you are gaining value rather than just quick dopamine.</li>
<li><b>Practice the Pomodoro Technique:</b> Work in 25-minute intervals of intense focus followed by a 5-minute tech-free break. This heavily researched method slowly rebuilds your brain’s capacity for sustained attention.</li>
<li><b>Morning Digital Detox:</b> Avoid looking at your phone for the first hour after waking up. This prevents immediate dopamine spikes and sets a calmer, more focused tone for the rest of your day.</li>
</ul>
</div>
</div>""",

                    "3 - High Part": """<div dir="rtl" style="text-align: right;" class="script-text">
<div class="script-title" style="color:#FBBF24;">الفئة 3: خطر متوسط | Class 3: Moderate Risk (High Part)</div>
<div class="section-box" style="border-right: 4px solid #F59E0B;">
<p style="color:#D97706; font-size: 18px; margin-bottom: 5px;"><b>التحليل السلوكي (تشتت الانتباه):</b></p>
<p>في الجزء المرتفع من الفئة الثالثة، يصبح العبء الرقمي الزائد واضحاً جداً. تقفز نسبة "تعفن الدماغ" إلى ما بين 46% و 60%. وقت استخدامك للتطبيقات واستهلاك البيانات مرتفعان للغاية، مما يعكس انجذاباً قوياً نحو "التمرير الكارثي" (Doomscrolling). أنت تقوم بمهام متعددة بشكل متكرر، وتتنقل بسرعة بين المنصات الاجتماعية المختلفة. في هذه المرحلة، من المحتمل أنك تعاني من "الضباب العقلي" الذي يشار إليه عادة باسم "تعفن الدماغ" (Brainrot). إن الوابل المستمر من المعلومات المجزأة يثقل كاهل ذاكرتك العاملة، مما يؤدي إلى انخفاض التفكير النقدي والإرهاق الرقمي الخفيف. قد تجد صعوبة في الجلوس في صمت دون الوصول إلى جهاز. لقد انخفض مدى انتباهك بشكل واضح، مما يجعل العمل الأكاديمي أو المهني العميق والمركز يبدو وكأنه صراع هائل.</p>
</div>
<div class="section-box" style="border-right: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>التوصيات العملية:</b></p>
<ul>
<li><b>تنفيذ 'فترات راحة للتمرير':</b> بدلاً من محاولة الإقلاع فجأة، قم بجدولة فترات راحة للتمرير مدتها 10 دقائق أثناء جلسات الدراسة أو العمل. بمجرد أن يرن المنبه، يجب عليك العودة إلى مهمتك على الفور.</li>
<li><b>تنظيم المحتوى الخاص بك:</b> قم بإلغاء متابعة الحسابات التي تقدم ترفيهاً طائشاً بحتاً. استبدلها بصناع محتوى تعليميين أو ملهمين بحيث تكتسب قيمة عندما تقوم بالتمرير، وليس مجرد دوبامين سريع.</li>
<li><b>ممارسة تقنية بومودورو (Pomodoro):</b> اعمل في فترات تركيز مكثفة مدتها 25 دقيقة تليها استراحة خالية من التكنولوجيا لمدة 5 دقائق. تعيد هذه الطريقة المدروسة جيداً بناء قدرة دماغك على الانتباه المستمر ببطء.</li>
<li><b>التخلص من السموم الرقمية الصباحية:</b> تجنب النظر إلى هاتفك في الساعة الأولى بعد الاستيقاظ. هذا يمنع الارتفاع الفوري للدوبامين ويحدد نغمة أكثر هدوءاً وتركيزاً لبقية يومك.</li>
</ul>
</div>
</div>
<div dir="ltr" style="text-align: left; margin-top:25px; border-top: 1px dashed rgba(255,255,255,0.2); padding-top:20px;" class="script-text">
<div class="section-box" style="border-left: 4px solid #F59E0B;">
<p style="color:#D97706; font-size: 18px; margin-bottom: 5px;"><b>Analysis (Attention Fragmentation):</b></p>
<p>In the High Part of Class 3, digital overload becomes quite apparent. Your Brainrot Percentage jumps to between 46% and 60%. Your app usage time and data consumption are very high, reflecting a strong pull toward doomscrolling. You frequently multitask, switching rapidly between different social platforms. At this stage, you are likely experiencing the "mental fog" commonly referred to as brain rot. The constant barrage of bite-sized information overloads your working memory, leading to decreased critical thinking and mild digital fatigue. You might struggle to sit in silence without reaching for a device. Your attention span has visibly declined, making deep, focused academic or professional work feel like a monumental struggle.</p>
</div>
<div class="section-box" style="border-left: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>Recommendations:</b></p>
<ul>
<li><b>Implement 'Scroll Breaks':</b> Instead of trying to quit cold turkey, schedule 10-minute scroll breaks during your study or work sessions. Once the timer rings, you must return to your task immediately.</li>
<li><b>Curate Your Feeds:</b> Unfollow accounts that provide purely mindless entertainment. Replace them with educational or inspiring creators so that when you do scroll, you are gaining value rather than just quick dopamine.</li>
<li><b>Practice the Pomodoro Technique:</b> Work in 25-minute intervals of intense focus followed by a 5-minute tech-free break. This heavily researched method slowly rebuilds your brain’s capacity for sustained attention.</li>
<li><b>Morning Digital Detox:</b> Avoid looking at your phone for the first hour after waking up. This prevents immediate dopamine spikes and sets a calmer, more focused tone for the rest of your day.</li>
</ul>
</div>
</div>""",

                    "4 - Low Part": """<div dir="rtl" style="text-align: right;" class="script-text">
<div class="script-title" style="color:#F87171;">الفئة 4: خطر مرتفع | Class 4: High Risk (Low Part)</div>
<div class="section-box" style="border-right: 4px solid #FB7185;">
<p style="color:#F43F5E; font-size: 18px; margin-bottom: 5px;"><b>التحليل السلوكي (التمرير الكارثي القهري):</b></p>
<p>يدل الجزء المنخفض من الفئة الرابعة على التحول من العادة إلى السلوك القهري. نسبة "تعفن الدماغ" لديك مرتفعة بشكل مثير للقلق، وتتراوح من 61% إلى 75%. تظهر مقاييس جهازك وقتاً طويلاً جداً للشاشة واستنزافاً كبيراً للبطارية، ويمتد غالباً إلى وقت متأخر من الليل. أنت تقوم بالتمرير ليس لأنك تريد ذلك، ولكن لأنك تشعر أنك مضطر لذلك. يؤثر هذا المستوى بشدة على جودة نومك. التعرض للمحتوى اللانهائي في وقت متأخر من الليل يؤخر إفراز الميلاتونين ويبقي دماغك محفزاً بشدة، مما يقطع نومك العميق. من المحتمل أن تستيقظ وأنت تشعر بالإرهاق العقلي على الرغم من قضاء ساعات في السرير. الضجيج الرقمي المستمر يؤدي إلى تآكل تنظيمك العاطفي بشدة، مما يجعلك أكثر عرضة للتهيج والتوتر ومشاعر عدم الكفاءة.</p>
</div>
<div class="section-box" style="border-right: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>التوصيات العملية:</b></p>
<ul>
<li><b>وضع حدود صارمة للتطبيقات:</b> استخدم أدوات الرفاهية الرقمية المدمجة في هاتفك لقفل التطبيقات المشتتة للانتباه بعد فترة زمنية محددة. يعد فرض حاجز مادي أمراً ضرورياً عندما لا تعود قوة الإرادة وحدها فعالة.</li>
<li><b>صيام الدوبامين:</b> خصص يوماً كاملاً في الأسبوع لتكون خاليًا تماماً من الشاشات. تساعد هذه الممارسة الصارمة في إعادة ضبط نظام المكافأة في دماغك، مما يقلل من الرغبة الشديدة في الحداثة الرقمية.</li>
<li><b>الوضع الرمادي (Grayscale Mode):</b> قم بتغيير إعدادات عرض هاتفك إلى الأبيض والأسود. إزالة الألوان النابضة بالحياة والمحفزة تجعل الشاشة أقل جاذبية بكثير، مما يقلل بشكل طبيعي من الرغبة القهرية في التمرير الكارثي.</li>
<li><b>إعادة تقديم الوسائط الطويلة:</b> أجبر نفسك على مشاهدة مقاطع فيديو أطول، أو الاستماع إلى البودكاست، أو قراءة المقالات دون القيام بمهام متعددة. إعادة تدريب دماغك لقبول الإشباع المؤجل أمر حيوي لإصلاح الانتباه.</li>
</ul>
</div>
</div>
<div dir="ltr" style="text-align: left; margin-top:25px; border-top: 1px dashed rgba(255,255,255,0.2); padding-top:20px;" class="script-text">
<div class="section-box" style="border-left: 4px solid #FB7185;">
<p style="color:#F43F5E; font-size: 18px; margin-bottom: 5px;"><b>Analysis (Compulsive Doomscrolling):</b></p>
<p>The Low Part of Class 4 signifies a shift from habit to compulsion. Your Brainrot Percentage is alarmingly high, ranging from 61% to 75%. Your device metrics show extensive screen-on time and significant battery drainage, often extending late into the night. You scroll not because you want to, but because you feel you have to. This level severely impacts your sleep quality. Late-night exposure to endless content delays melatonin release and keeps your brain heavily stimulated, fragmenting your deep sleep. You likely wake up feeling mentally exhausted despite spending hours in bed. The constant digital noise is aggressively eroding your emotional regulation, making you more prone to irritability, stress, and feelings of inadequacy.</p>
</div>
<div class="section-box" style="border-left: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>Recommendations:</b></p>
<ul>
<li><b>Set Hard App Limits:</b> Use your phone's built-in digital wellbeing tools to lock distracting apps after a specific time limit. Forcing a physical barrier is necessary when willpower alone is no longer effective.</li>
<li><b>Dopamine Fasting:</b> Dedicate one entire day a week to being completely screen-free. This rigorous practice helps reset your brain's reward system, reducing the intense cravings for digital novelty.</li>
<li><b>Grayscale Mode:</b> Change your phone's display settings to black and white. Removing the vibrant, stimulating colors makes the screen significantly less appealing, naturally reducing the compulsive urge to doomscroll.</li>
<li><b>Reintroduce Long-Form Media:</b> Force yourself to watch longer videos, listen to podcasts, or read articles without multitasking. Re-training your brain to accept delayed gratification is vital for repairing attention.</li>
</ul>
</div>
</div>""",

                    "4 - High Part": """<div dir="rtl" style="text-align: right;" class="script-text">
<div class="script-title" style="color:#F87171;">الفئة 4: خطر مرتفع | Class 4: High Risk (High Part)</div>
<div class="section-box" style="border-right: 4px solid #E11D48;">
<p style="color:#BE123C; font-size: 18px; margin-bottom: 5px;"><b>التحليل السلوكي (الإرهاق المعرفي):</b></p>
<p>في الجزء المرتفع من الفئة الرابعة، أنت تعاني من إرهاق معرفي شديد، حيث تستقر نسبة "تعفن الدماغ" بين 76% و 85%. أنت تستهلك كميات هائلة من البيانات يومياً، ويشير استخدامك للتطبيق إلى اعتماد شبه كلي على التحفيز الرقمي. لقد أدى المحتوى القصير إلى إعادة برمجة مسارات المكافأة لديك بشدة. أنت تتعامل الآن مع انخفاض كبير في مدى الانتباه. تبدو أساليب التعلم التقليدية والقراءة المطولة مستحيلة تقريباً. يؤدي هذا التحفيز المفرط المستمر إلى حالة مزمنة من التشتت وزيادة القلق. العالم الرقمي يستنزف طاقتك العقلية، مما يتسبب في انسحابك من الهوايات غير المتصلة بالإنترنت. أنت تقف على حافة الاحتراق الرقمي الكامل، وتحتاج بشكل عاجل إلى التدخل.</p>
</div>
<div class="section-box" style="border-right: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>التوصيات العملية:</b></p>
<ul>
<li><b>وضع حدود صارمة للتطبيقات:</b> استخدم أدوات الرفاهية الرقمية المدمجة في هاتفك لقفل التطبيقات المشتتة للانتباه بعد فترة زمنية محددة. يعد فرض حاجز مادي أمراً ضرورياً عندما لا تعود قوة الإرادة وحدها فعالة.</li>
<li><b>صيام الدوبامين:</b> خصص يوماً كاملاً في الأسبوع لتكون خاليًا تماماً من الشاشات. تساعد هذه الممارسة الصارمة في إعادة ضبط نظام المكافأة في دماغك، مما يقلل من الرغبة الشديدة في الحداثة الرقمية.</li>
<li><b>الوضع الرمادي (Grayscale Mode):</b> قم بتغيير إعدادات عرض هاتفك إلى الأبيض والأسود. إزالة الألوان النابضة بالحياة والمحفزة تجعل الشاشة أقل جاذبية بكثير، مما يقلل بشكل طبيعي من الرغبة القهرية في التمرير الكارثي.</li>
<li><b>إعادة تقديم الوسائط الطويلة:</b> أجبر نفسك على مشاهد مقاطع فيديو أطول، أو الاستماع إلى البودكاست، أو قراءة المقالات دون القيام بمهام متعددة. إعادة تدريب دماغك لقبول الإشباع المؤجل أمر حيوي لإصلاح الانتباه.</li>
</ul>
</div>
</div>
<div dir="ltr" style="text-align: left; margin-top:25px; border-top: 1px dashed rgba(255,255,255,0.2); padding-top:20px;" class="script-text">
<div class="section-box" style="border-left: 4px solid #E11D48;">
<p style="color:#BE123C; font-size: 18px; margin-bottom: 5px;"><b>Analysis (Cognitive Fatigue):</b></p>
<p>In the High Part of Class 4, you are experiencing intense cognitive fatigue, with your Brainrot Percentage resting between 76% and 85%. You consume massive amounts of data daily, and your app usage indicates an almost total reliance on digital stimulation. Short-form content has severely rewired your reward pathways. You are now dealing with significant attention span decline. Traditional learning methods and long-form reading feel nearly impossible to endure. This persistent overstimulation leads to a chronic state of distraction and increased anxiety. The digital world is draining your mental energy, causing you to withdraw from offline hobbies. You are standing right on the edge of complete digital burnout, urgently needing intervention.</p>
</div>
<div class="section-box" style="border-left: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>Recommendations:</b></p>
<ul>
<li><b>Set Hard App Limits:</b> Use your phone's built-in digital wellbeing tools to lock distracting apps after a specific time limit. Forcing a physical barrier is necessary when willpower alone is no longer effective.</li>
<li><b>Dopamine Fasting:</b> Dedicate one entire day a week to being completely screen-free. This rigorous practice helps reset your brain's reward system, reducing the intense cravings for digital novelty.</li>
<li><b>Grayscale Mode:</b> Change your phone's display settings to black and white. Removing the vibrant, stimulating colors makes the screen significantly less appealing, naturally reducing the compulsive urge to doomscroll.</li>
<li><b>Reintroduce Long-Form Media:</b> Force yourself to watch longer videos, listen to podcasts, or read articles without multitasking. Re-training your brain to accept delayed gratification is vital for repairing attention.</li>
</ul>
</div>
</div>""",

                    "5 - Low Part": """<div dir="rtl" style="text-align: right;" class="script-text">
<div class="script-title" style="color:#EF4444;">الفئة 5: خطر شديد | Class 5: Severe Risk (Low Part)</div>
<div class="section-box" style="border-right: 4px solid #EF4444;">
<p style="color:#DC2626; font-size: 18px; margin-bottom: 5px;"><b>التحليل السلوكي (الاحتراق الرقمي):</b></p>
<p>عند دخولك الجزء المنخفض من الفئة الخامسة، تكون قد وصلت إلى الاحتراق الرقمي الفعلي. تتراوح نسبة "تعفن الدماغ" لديك من 86% إلى 95%. تُظهر بيانات الاستخدام الخاصة بك إفراطاً شديداً في جميع المجالات. أنت متصل بالإنترنت بشكل مزمن، وتستخدم الوسائط الرقمية كآلية تكيف لا هوادة فيها للتعامل مع التوتر، على الرغم من أنها تجعلك تشعر بأسوأ. في هذه المرحلة الحرجة، أدى التبديل المستمر بين المهام ومقاطع الفيديو إلى إضعاف وظائفك التنفيذية بشدة. من المحتمل أنك تعاني من ضباب عقلي مزمن، وخمول شديد، وشعور بالخدر العاطفي. أنت مرهق جسدياً ولكنك مستنفر عقلياً. قد تبدو تفاعلات الحياة الواقعية مملة للغاية مقارنة بالبيئة شديدة التحفيز لهاتفك، مما يؤدي إلى عزلة اجتماعية عميقة ونقص سائد في الدافع.</p>
</div>
<div class="section-box" style="border-right: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>التوصيات العملية:</b></p>
<ul>
<li><b>طلب الدعم المهني:</b> فكر في استشارة مستشار أو معالج متخصص في الإدمان الرقمي. عندما يصل الاحتراق إلى هذا المستوى، غالباً ما يكون التوجيه المهني ضرورياً لعلاج الأسباب الكامنة وراء التجنب القهري.</li>
<li><b>حذف التطبيقات عالية الخطورة:</b> قم بإزالة التطبيقات المحددة التي تسبب حلقات التمرير اللانهائي تماماً. ضع عقبات من خلال إجبار نفسك على تسجيل الدخول عبر متصفح الويب إذا كان لا بد من التحقق منها.</li>
<li><b>أمسيات إلزامية خالية من الشاشات:</b> افرض قاعدة صارمة تمنع استخدام الشاشات قبل ساعتين من موعد النوم. استبدل هذا الوقت بتمارين التمدد اللطيفة أو تدوين اليوميات للسماح لجهازك العصبي المفرط التحفيز بالاسترخاء.</li>
<li><b>إعادة بناء روابط العالم الحقيقي:</b> قم بجدولة لقاءات وجهاً لوجه مع الأصدقاء أو العائلة بنشاط. إن إجبار نفسك على الانخراط في تفاعلات اجتماعية جسدية وحاضرة أمر بالغ الأهمية لعكس العزلة العميقة الناجمة عن الاحتراق الرقمي الشديد.</li>
<li><b>التدخل بالنشاط البدني:</b> التزم بـ 30 دقيقة من التمارين المعتدلة يومياً. الحركة الجسدية تزيد من تدفق الدم إلى الدماغ، وهو أمر تشتد الحاجة إليه لإزالة الضباب العقلي الشديد وإصلاح الوظائف الإدراكية.</li>
</ul>
</div>
</div>
<div dir="ltr" style="text-align: left; margin-top:25px; border-top: 1px dashed rgba(255,255,255,0.2); padding-top:20px;" class="script-text">
<div class="section-box" style="border-left: 4px solid #EF4444;">
<p style="color:#DC2626; font-size: 18px; margin-bottom: 5px;"><b>Analysis (Digital Burnout):</b></p>
<p>Entering the Low Part of Class 5, you have hit actual digital burnout. Your Brainrot Percentage spans from 86% to 95%. Your telemetry shows extreme usage across the board. You are chronically online, using digital media as a relentless coping mechanism for stress, even though it actively makes you feel worse. At this critical stage, the constant switching between tasks and videos has severely impaired your executive functioning. You likely suffer from chronic brain fog, extreme lethargy, and a feeling of emotional numbness. You are physically exhausted but mentally wired. Real-life interactions may feel incredibly dull compared to the hyper-stimulating environment of your phone, leading to deep social isolation and a pervasive lack of motivation.</p>
</div>
<div class="section-box" style="border-left: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>Recommendations:</b></p>
<ul>
<li><b>Seek Professional Support:</b> Consider consulting a counselor or therapist specializing in digital addiction. When burnout reaches this level, professional guidance is often necessary to treat the underlying causes of compulsive avoidance.</li>
<li><b>Delete High-Risk Apps:</b> Completely remove the specific apps that cause your endless scrolling loops. Introduce friction by forcing yourself to log in via a web browser if you absolutely must check them.</li>
<li><b>Mandatory Screen-Free Evenings:</b> Enforce a strict rule of no screens two hours before bedtime. Replace this time with gentle stretching or journaling to allow your highly overstimulated nervous system to decompress.</li>
<li><b>Rebuild Real-World Connections:</b> Actively schedule face-to-face meetups with friends or family. Forcing yourself to engage in present, physical social interactions is crucial for reversing the deep isolation caused by severe digital burnout.</li>
<li><b>Physical Activity Intervention:</b> Commit to 30 minutes of moderate exercise daily. Physical movement increases blood flow to the brain, which is desperately needed to clear severe brain fog and repair cognitive functioning.</li>
</ul>
</div>
</div>""",

                    "5 - High Part": """<div dir="rtl" style="text-align: right;" class="script-text">
<div class="script-title" style="color:#EF4444;">الفئة 5: خطر شديد | Class 5: Severe Risk (High Part)</div>
<div class="section-box" style="border-right: 4px solid #B91C1C;">
<p style="color:#991B1B; font-size: 18px; margin-bottom: 5px;"><b>التحليل السلوكي (التبلد الحسي الكامل):</b></p>
<p>الجزء المرتفع من الفئة الخامسة هو أشد مستويات العبء الرقمي الزائد، حيث تصل نسبة "تعفن الدماغ" إلى 96% - 100%. تعكس مقاييس جهازك إدماناً رقمياً يستهلك كل شيء. أنت تقضي تقريباً جميع ساعات استيقاظك متصلاً، مما يؤدي إلى حمل إدراكي زائد كامل وتبلد حسي عميق تجاه الحياة اليومية. تسبب هذه الحالة القصوى تغييرات هيكلية في كيفية معالجة دماغك للمعلومات والمتعة. انتباهك المستمر محطم تماماً، ومن المحتمل أن حياتك الأكاديمية أو المهنية تعاني بشكل كبير. قد تعاني من أعراض جسدية مثل إجهاد العين، والأرق، وتقلبات مزاجية حادة. هذه حالة من الإرهاق الرقمي الكلي، تتطلب تغييرات جذرية وفورية في نمط الحياة لاستعادة صحتك العقلية وقدراتك المعرفية.</p>
</div>
<div class="section-box" style="border-right: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>التوصيات العملية:</b></p>
<ul>
<li><b>طلب الدعم المهني:</b> فكر في استشارة مستشار أو معالج متخصص في الإدمان الرقمي. عندما يصل الاحتراق إلى هذا المستوى، غالباً ما يكون التوجيه المهني ضرورياً لعلاج الأسباب الكامنة وراء التجنب القهري.</li>
<li><b>حذف التطبيقات عالية الخطورة:</b> قم بإزالة التطبيقات المحددة التي تسبب حلقات التمرير اللانهائي تماماً. ضع عقبات من خلال إجبار نفسك على تسجيل الدخول عبر متصفح الويب إذا كان لا بد من التحقق منها.</li>
<li><b>أمسيات إلزامية خالية من الشاشات:</b> افرض قاعدة صارمة تمنع استخدام الشاشات قبل ساعتين من موعد النوم. استبدل هذا الوقت بتمارين التمدد اللطيفة أو تدوين اليوميات للسماح لجهازك العصبي المفرط التحفيز بالاسترخاء.</li>
<li><b>إعادة بناء روابط العالم الحقيقي:</b> قم بجدولة لقاءات وجهاً لوجه مع الأصدقاء أو العائلة بنشاط. إن إجبار نفسك على الانخراط في تفاعلات اجتماعية جسدية وحاضرة أمر بالغ الأهمية لعكس العزلة العميقة الناجمة عن الاحتراق الرقمي الشديد.</li>
<li><b>التدخل بالنشاط البدني:</b> التزم بـ 30 دقيقة من التمارين المعتدلة يومياً. الحركة الجسدية تزيد من تدفق الدم إلى الدماغ، وهو أمر تشتد الحاجة إليه لإزالة الضباب العقلي الشديد وإصلاح الوظائف الإدراكية.</li>
</ul>
</div>
</div>
<div dir="ltr" style="text-align: left; margin-top:25px; border-top: 1px dashed rgba(255,255,255,0.2); padding-top:20px;" class="script-text">
<div class="section-box" style="border-left: 4px solid #B91C1C;">
<p style="color:#991B1B; font-size: 18px; margin-bottom: 5px;"><b>Analysis (Complete Desensitization):</b></p>
<p>The High Part of Class 5 is the most severe level of digital overload, with a Brainrot Percentage hitting 96% to 100%. Your device metrics reflect an all-consuming digital addiction. You spend nearly all your waking hours plugged in, resulting in complete cognitive overload and profound desensitization to everyday life. This extreme state causes structural changes to how your brain processes information and pleasure. Your sustained attention is entirely shattered, and your academic or professional life is likely suffering greatly. You may experience physical symptoms like eye strain, insomnia, and severe mood swings. This is a state of total digital exhaustion, requiring immediate, drastic lifestyle changes to reclaim your mental health and cognitive abilities.</p>
</div>
<div class="section-box" style="border-left: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>Recommendations:</b></p>
<ul>
<li><b>Seek Professional Support:</b> Consider consulting a counselor or therapist specializing in digital addiction. When burnout reaches this level, professional guidance is often necessary to treat the underlying causes of compulsive avoidance.</li>
<li><b>Delete High-Risk Apps:</b> Completely remove the specific apps that cause your endless scrolling loops. Introduce friction by forcing yourself to log in via a web browser if you absolutely must check them.</li>
<li><b>Mandatory Screen-Free Evenings:</b> Enforce a strict rule of no screens two hours before bedtime. Replace this time with gentle stretching or journaling to allow your highly overstimulated nervous system to decompress.</li>
<li><b>Rebuild Real-World Connections:</b> Actively schedule face-to-face meetups with friends or family. Forcing yourself to engage in present, physical social interactions is crucial for reversing the deep isolation caused by severe digital burnout.</li>
<li><b>Physical Activity Intervention:</b> Commit to 30 minutes of moderate exercise daily. Physical movement increases blood flow to the brain, which is desperately needed to clear severe brain fog and repair cognitive functioning.</li>
</ul>
</div>
</div>"""
                }

                st.markdown(f'''<div class="metric-card" style="margin-top: 15px;">\n{app_scripts.get(clean_pred_class, "<h3 style='color:red;'>تعذر جلب التحليل الخاص بهذه الفئة. يُرجى مراجعة التوصيات العامة.</h3>")}\n</div>''', unsafe_allow_html=True)

# ------------------------------------------------------------------
# Page 2: Student Risk Analysis (Swapped)
# ------------------------------------------------------------------
elif page == "Student Risk Analysis":
    st.markdown("<h3 style='color: #E9D5FF !important; font-weight: 700; display:flex; align-items:center; gap:10px; animation: fadeInUp 0.6s ease-out forwards;'>🧠 Student Risk Intelligence</h3>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    stress_map = {"Very Calm": 1.0, "Normal Stress": 4.0, "Highly Stressed": 7.0, "Extremely Stressed": 10.0}
    anxiety_map = {"Stable": 1.0, "Mild Anxiety": 3.5, "Constant Tension": 7.0, "Severe Panic": 10.0}
    support_map = {"Completely Isolated": 1.0, "Limited Support": 4.0, "Good Support": 7.5, "Strong Support": 10.0}
    dep_map = {"Optimistic & Energetic": 1.0, "Occasional Sadness": 4.5, "Frequent Low Mood": 7.5, "Severe Despair": 10.0}
    sleep_map = {"< 4 hours (Severely Deprived)": 3.0, "4-6 hours (Insufficient)": 5.0, "7-9 hours (Healthy)": 8.0, "> 9 hours (Oversleeping)": 10.0}
    exam_map = {"No Immediate Exams": 1.0, "Manageable Workload": 4.0, "High Academic Stress": 7.5, "Overwhelming Pressure": 10.0}

    with st.form("risk_form"):
        st.subheader("📋 Behavioral Assessment")
        st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 10px 0 25px 0;'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown("<b style='color:#38BDF8 !important; font-size: 18px;'>🧬 Psychological Factors</b>", unsafe_allow_html=True)
            stress = st.selectbox("Stress Level:", list(stress_map.keys()))
            anxiety = st.selectbox("Anxiety Level:", list(anxiety_map.keys()))
            depression = st.selectbox("Mood & Energy:", list(dep_map.keys()))
        with col2:
            st.markdown("<b style='color:#38BDF8 !important; font-size: 18px;'>🌍 Environmental Factors</b>", unsafe_allow_html=True)
            support = st.selectbox("Social Support:", list(support_map.keys()))
            sleep = st.selectbox("Daily Sleep:", list(sleep_map.keys()))
            exams = st.selectbox("Academic Workload:", list(exam_map.keys()))
        submit_risk = st.form_submit_button("Initiate AI Analysis", use_container_width=True)

    if submit_risk:
        features = pd.DataFrame([{
            'stress_level': float(stress_map[stress]), 'anxiety_score': float(anxiety_map[anxiety]),
            'depression_score': float(dep_map[depression]), 'social_support': float(support_map[support]),
            'sleep_hours': float(sleep_map[sleep]), 'exam_pressure': float(exam_map[exams])
        }])

        with st.spinner("Processing..."):
            probs = risk_model.predict_proba(features)[0]
            clean_classes = [str(c).strip().title() for c in encoder.classes_]
            prob_dict = {c: p for c, p in zip(clean_classes, probs)}
            
            if prob_dict.get('High', 0.0) >= 0.25: final_label = 'High'
            elif prob_dict.get('Medium', 0.0) >= 0.35: final_label = 'Medium'
            else: final_label = clean_classes[np.argmax(probs)]

            st.session_state['last_analysis_context'] = f"قام المستخدم للتو بتحليل (Student Risk Analysis). النتيجة هي: مستوى خطر {final_label}."
            log_data("Students", [stress, anxiety, depression, support, sleep, exams, final_label])

        res_col1, res_col2 = st.columns([1, 1.5])
        with res_col1:
            st.markdown('<div class="metric-card" style="text-align: center;">', unsafe_allow_html=True)
            if 'High' in final_label: st.markdown("<h2 style='color:#F43F5E; font-size: 30px; font-weight: 900;'>🚨 HIGH RISK</h2>", unsafe_allow_html=True)
            elif 'Medium' in final_label: st.markdown("<h2 style='color:#FBBF24; font-size: 30px; font-weight: 900;'>🟡 MEDIUM RISK</h2>", unsafe_allow_html=True)
            else: st.markdown("<h2 style='color:#34D399; font-size: 30px; font-weight: 900;'>✅ LOW RISK</h2>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with res_col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            fig = px.bar(x=probs*100, y=clean_classes, orientation='h', color=clean_classes, color_discrete_map={'High':'#F43F5E', 'Medium':'#FBBF24', 'Low':'#34D399'})
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#F8FAFC'), height=200, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ==========================================
        # 📝 إسكريبت تقييم الطلاب
        # ==========================================
        student_scripts = {
            'Low': """<div dir="rtl" style="text-align: right;" class="script-text">
<div class="script-title" style="color:#34D399;">✅ مستوى الخطر المنخفض | Low Risk Level</div>
<div class="section-box" style="border-right: 4px solid #34D399;">
<p style="color:#6EE7B7; font-size: 18px; margin-bottom: 5px;"><b>التحليل المباشر:</b></p>
<p>يشير مستوى الخطر المنخفض إلى أنك تتنقل في بيئتك الأكاديمية بنجاح مع توازن عقلي وعاطفي ممتاز. من المحتمل أنك تبلغ عن أنماط نوم صحية، وعبء عمل أكاديمي يمكن إدارته، ومزاج متفائل بشكل عام. نظراً لأن مستويات التوتر والقلق لديك مستقرة، تظل وظائفك المعرفية حادة، مما يسمح بأداء أكاديمي عالٍ. أنت تستفيد بشكل كبير من أنظمة الدعم الاجتماعي القوية وآليات التكيف الصحية، مما يضمن عدم تحول الضغوط العرضية إلى احتراق. أنت تنظر إلى دراستك كتمثيل لتحدٍ إيجابي وليس كعبء ساحق. تحميك هذه الحالة المرنة بقوة ضد الاحتراق الرقمي، مما يعني أنه يمكنك استخدام التكنولوجيا للتعلم دون الوقوع في فخ التمرير اللانهائي أو استخدام وسائل التواصل الاجتماعي للهروب من الواقع الأكاديمي.</p>
</div>
<div class="section-box" style="border-right: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>التوصيات العملية:</b></p>
<ul>
<li><b>الحفاظ على عادات نوم صحية ومتسقة:</b> استمر في إعطاء الأولوية للنوم من 7 إلى 9 ساعات. الراحة عالية الجودة هي الركيزة الأساسية لنجاحك الأكاديمي الحالي وتنظيمك العاطفي الممتاز.</li>
<li><b>التوجيه ودعم الأقران:</b> نظراً لأن لديك دعماً اجتماعياً قوياً، فكر في توجيه الآخرين. إن تعليم الأقران لا يعزز معرفتك فحسب، بل يعمق أيضاً روابطك الاجتماعية القيمة.</li>
<li><b>إدارة الوقت الاستباقية:</b> استمر في استخدام المخططات أو التقويمات الرقمية لجدولة مهامك مسبقاً. البقاء متقدماً على المواعيد النهائية يضمن بقاء عبء العمل قابلاً للإدارة وبقاء التوتر منخفضاً بشكل ملحوظ.</li>
</ul>
</div>
</div>
<div dir="ltr" style="text-align: left; margin-top:25px; border-top: 1px dashed rgba(255,255,255,0.2); padding-top:20px;" class="script-text">
<div class="section-box" style="border-left: 4px solid #34D399;">
<p style="color:#6EE7B7; font-size: 18px; margin-bottom: 5px;"><b>Analysis:</b></p>
<p>A Low Risk Level indicates that you are successfully navigating your academic environment with excellent mental and emotional balance. You likely report healthy sleep patterns, a manageable academic workload, and a generally optimistic mood. Because your stress and anxiety levels are stable, your cognitive functions remain sharp, allowing for high academic performance. You benefit greatly from strong social support systems and healthy coping mechanisms, ensuring that occasional pressures do not escalate into burnout. You view your studies as a positive challenge rather than an overwhelming burden. This resilient state strongly protects you against digital burnout, meaning you can utilize technology for learning without falling into the trap of endless scrolling or using social media to escape academic reality.</p>
</div>
<div class="section-box" style="border-left: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>Recommendations:</b></p>
<ul>
<li><b>Maintain Consistent Sleep Hygiene:</b> Continue prioritizing your 7 to 9 hours of sleep. High-quality rest is the foundational pillar of your current academic success and excellent emotional regulation.</li>
<li><b>Mentorship and Peer Support:</b> Since you have strong social support, consider mentoring others. Teaching peers not only reinforces your own knowledge but also deepens your valuable social connections.</li>
<li><b>Proactive Time Management:</b> Keep using planners or digital calendars to schedule your tasks in advance. Staying ahead of deadlines ensures your workload remains manageable and your stress stays remarkably low.</li>
</ul>
</div>
</div>""",

            'Medium': """<div dir="rtl" style="text-align: right;" class="script-text">
<div class="script-title" style="color:#FBBF24;">🟡 مستوى الخطر المتوسط | Medium Risk Level</div>
<div class="section-box" style="border-right: 4px solid #FBBF24;">
<p style="color:#FCD34D; font-size: 18px; margin-bottom: 5px;"><b>التحليل المباشر:</b></p>
<p>يشير مستوى الخطر المتوسط إلى أنك تتأرجح على حافة الإرهاق الأكاديمي. أنت تعاني من ارتفاع التوتر، والحزن العرضي، والقلق الخفيف. قد يكون نومك غير كافٍ، حيث يتقلب بين 4 إلى 6 ساعات، مما يعيق بشكل مباشر قدرة دماغك على التعافي. يتزايد الضغط الأكاديمي، مما يجعل الشعور بعبء العمل أكثر صعوبة في الإدارة. في هذه المرحلة، أنت معرض بشدة لاستخدام الوسائط الرقمية كآلية للتكيف. قد تجد نفسك تقوم بالتمرير بشكل سلبي لتجنب التفكير في الاختبارات القادمة، مبدلاً دون قصد الراحة المجددة للنشاط بالتشتت الرقمي. يخلق هذا حلقة مفرغة خطيرة حيث يؤدي ضعف النوم والاحتراق الخفيف إلى مزيد من وقت الشاشة، والذي بدوره يقلل من دافعك العام وتركيزك اليومي.</p>
</div>
<div class="section-box" style="border-right: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>التوصيات العملية:</b></p>
<ul>
<li><b>إنشاء روتين للاسترخاء:</b> استبدل الدراسة أو التمرير في وقت متأخر من الليل بروتين مهدئ قبل النوم. قراءة كتاب أو ممارسة التنفس العميق يساعد على نقل دماغك من الضغط الأكاديمي العالي إلى النوم المجدد للنشاط.</li>
<li><b>تقسيم المهام إلى خطوات صغيرة:</b> تؤدي أعباء العمل المرهقة إلى سلوكيات التجنب مثل التمرير الكارثي. قم بتقسيم مهامك إلى مهام صغيرة مدتها 15 دقيقة لبناء الزخم وتقليل القلق المرتبط بالمشاريع الكبيرة.</li>
<li><b>جدولة "وقت للقلق":</b> خصص 20 دقيقة يومياً تحديداً لتدوين مخاوفك الأكاديمية. احتواء توترك في نافذة زمنية محددة يمنعه من التسرب إلى وقت استرخائك ونومك.</li>
<li><b>الاستفادة من موارد الحرم الجامعي:</b> لا تنتظر حتى يتم إرهاقك تماماً. شكل مجموعة دراسية أو قم بزيارة مركز الدعم الأكاديمي بجامعتك لتوزيع الضغط بشكل خفيف وتحسين شبكة الدعم الاجتماعي الخاصة بك.</li>
</ul>
</div>
</div>
<div dir="ltr" style="text-align: left; margin-top:25px; border-top: 1px dashed rgba(255,255,255,0.2); padding-top:20px;" class="script-text">
<div class="section-box" style="border-left: 4px solid #FBBF24;">
<p style="color:#FCD34D; font-size: 18px; margin-bottom: 5px;"><b>Analysis:</b></p>
<p>A Medium Risk Level suggests you are balancing on the edge of academic fatigue. You are experiencing elevated stress, occasional sadness, and mild anxiety. Your sleep might be insufficient, fluctuating between 4 to 6 hours, which directly hampers your brain's ability to recover. The academic pressure is building, making your workload feel increasingly difficult to manage. At this stage, you are highly vulnerable to using digital media as a coping mechanism. You might find yourself passively scrolling to avoid thinking about upcoming exams, unintentionally trading restorative rest for digital distraction. This creates a dangerous feedback loop where poor sleep and mild burnout lead to more screen time, which in turn further decreases your overall motivation and daily focus.</p>
</div>
<div class="section-box" style="border-left: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>Recommendations:</b></p>
<ul>
<li><b>Establish a Wind-Down Routine:</b> Swap late-night studying or scrolling for a calming pre-sleep routine. Reading a book or practicing deep breathing helps transition your brain from high academic stress to restorative sleep.</li>
<li><b>Break Tasks into Micro-Steps:</b> Overwhelming workloads trigger avoidance behaviors like doomscrolling. Break your assignments into tiny, 15-minute tasks to build momentum and reduce the anxiety associated with large projects.</li>
<li><b>Schedule "Worry Time":</b> Allocate 20 minutes a day specifically to write down your academic anxieties. Containing your stress to a specific window prevents it from bleeding into your relaxation and sleep time.</li>
<li><b>Leverage Campus Resources:</b> Don't wait until you are fully overwhelmed. Form a study group or visit your university's academic support center to lightly distribute the pressure and improve your social support network.</li>
</ul>
</div>
</div>""",

            'High': """<div dir="rtl" style="text-align: right;" class="script-text">
<div class="script-title" style="color:#F43F5E;">🚨 مستوى الخطر المرتفع | High Risk Level</div>
<div class="section-box" style="border-right: 4px solid #F43F5E;">
<p style="color:#FB7185; font-size: 18px; margin-bottom: 5px;"><b>التحليل المباشر:</b></p>
<p>مستوى الخطر المرتفع هو علامة تحذير حاسمة من الاحتراق الأكاديمي والرقمي الشديد. من المحتمل أنك تعاني من ضغط شديد، وحالات مزاجية منخفضة متكررة، وقلق حاد. نومك إما محروم بشدة أو مفرط كاستجابة للإرهاق. مع الضغط الأكاديمي الساحق والدعم الاجتماعي المحدود، أنت تعمل بالكامل في وضع "البقاء على قيد الحياة". في هذا المستوى، يكون احتمال الاستخدام الإشكالي لوسائل التواصل الاجتماعي مرتفعاً بشكل لا يصدق. قد تستخدم المحتوى اللانهائي للانفصال تماماً عن الضغط الشديد لحياتك اليومية. يضعف هذا الإرهاق الشديد ذاكرتك، ويسحق وظائفك التنفيذية، ويدمر أداءك الأكاديمي. دماغك مثقل بشكل كبير، ويتطلب تدخلاً فورياً ورحيماً لاستعادة رفاهيتك الجسدية والعقلية.</p>
</div>
<div class="section-box" style="border-right: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>التوصيات العملية (تدخل فوري):</b></p>
<ul>
<li><b>إعطاء الأولوية للراحة فوق كل شيء:</b> النجاح الأكاديمي مستحيل دون الأداء المعرفي. يجب عليك على الفور إعطاء الأولوية للحصول على ما لا يقل عن 7 ساعات من النوم، حتى لو كان ذلك يعني طلب تمديد لمهامك الحالية.</li>
<li><b>طلب الاستشارة المهنية:</b> يتطلب الاحتراق عالي المستوى تدخلاً مهنياً. تواصل مع خدمات الصحة النفسية في جامعتك على الفور لوضع خطة منظمة وواقعية لإدارة قلقك الشديد.</li>
<li><b>التواصل مع الأساتذة:</b> لا تخفِ معاناتك. تواصل بصراحة حول إرهاقك مع أساتذتك أو مرشديك الأكاديميين. يميل معظم أعضاء هيئة التدريس إلى تقديم تسهيلات عندما يدركون أنك في أزمة.</li>
<li><b>الانفصال الرقمي الجذري:</b> نظراً لأن الشاشات من المحتمل أن تغذي انفصالك عن الواقع، قم بتنفيذ التخلص من السموم الرقمية بصرامة. استخدم أدوات حظر مواقع الويب على الكمبيوتر المحمول الخاص بك لتقييد وصولك إلى الإنترنت بشكل صارم على البوابات الأكاديمية الأساسية فقط.</li>
</ul>
</div>
</div>
<div dir="ltr" style="text-align: left; margin-top:25px; border-top: 1px dashed rgba(255,255,255,0.2); padding-top:20px;" class="script-text">
<div class="section-box" style="border-left: 4px solid #F43F5E;">
<p style="color:#FB7185; font-size: 18px; margin-bottom: 5px;"><b>Analysis:</b></p>
<p>A High Risk Level is a critical warning sign of severe academic and digital burnout. You are likely enduring extreme stress, frequent low moods, and severe anxiety. Your sleep is either severely deprived or excessive as an exhaustion response. With overwhelming academic pressure and limited social support, you are functioning entirely in survival mode. In this tier, the likelihood of problematic social media use is incredibly high. You may be using endless content to completely dissociate from the intense pressure of your daily life. This severe exhaustion impairs your memory, crushes your executive functioning, and ruins your academic performance. Your brain is drastically overloaded, requiring an immediate and compassionate intervention to restore your physical and mental well-being.</p>
</div>
<div class="section-box" style="border-left: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>Recommendations:</b></p>
<ul>
<li><b>Prioritize Rest Above All:</b> Academic success is impossible without cognitive functioning. You must immediately prioritize getting at least 7 hours of sleep, even if it means requesting extensions on your current assignments.</li>
<li><b>Seek Professional Counseling:</b> High-level burnout requires professional intervention. Reach out to your university's mental health services immediately to develop a structured, realistic plan for managing your severe anxiety.</li>
<li><b>Communicate with Professors:</b> Do not hide your struggle. Openly communicate your burnout to your professors or academic advisors. Most faculty members are willing to offer accommodations when they understand you are in crisis.</li>
<li><b>Radical Digital Disconnect:</b> Since screens are likely fueling your dissociation, implement a strict digital detox. Use website blockers on your laptop to strictly limit your internet access to only essential academic portals.</li>
</ul>
</div>
</div>"""
        }

        risk_key = 'High' if 'High' in final_label else 'Medium' if 'Medium' in final_label else 'Low'
        st.markdown(f'''<div class="metric-card" style="margin-top: 25px;">\n{student_scripts.get(risk_key, "")}\n</div>''', unsafe_allow_html=True)

# ------------------------------------------------------------------
# Page 3: AI Assistant 🤖
# ------------------------------------------------------------------
elif page == "AI Assistant 🤖":
    st.markdown("<h3 style='color: #A855F7 !important; font-weight: 700; animation: fadeInUp 0.6s ease-out forwards;'>🤖 Smart AI Assistant</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8 !important;'>اسألني عن النتائج، أو ارفع صورة للمخطط البياني وسأقوم بتحليله لك استناداً إلى أحدث تقنيات Gemini.</p>", unsafe_allow_html=True)

    try:
        dev_api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        dev_api_key = ""

    if "user_api_key" not in st.session_state:
        st.session_state.user_api_key = ""

    with st.expander("⚙️ الخادم مشغول؟ (أدخل مفتاحك الخاص لتجاوز الزحام)", expanded=False):
        st.markdown("""
        <p style='color:#CBD5E1; font-size:14px; line-height: 1.6;'>
        هذا التطبيق يوفر شات مجاني تماماً. ولكن في حال ظهور رسالة خطأ تخبرك بأن <b>الحد اليومي المسموح به قد انتهى</b> بسبب الضغط العالي، يمكنك وضع مفتاح Gemini API الخاص بك هنا لاستكمال محادثتك فوراً من خلال حسابك الخاص. <br>
        <a href='https://aistudio.google.com/app/apikey' target='_blank' style='color:#38BDF8;'>اضغط هنا للحصول على مفتاح مجاني في ثوانٍ.</a>
        </p>
        """, unsafe_allow_html=True)
        
        user_input_key = st.text_input("مفتاح API الاحتياطي (اختياري):", value=st.session_state.user_api_key, type="password")
        if user_input_key:
            st.session_state.user_api_key = user_input_key
            st.success("✅ تم تفعيل مفتاحك الخاص بنجاح! يمكنك الآن استخدام الشات.")

    active_api_key = st.session_state.user_api_key if st.session_state.user_api_key else dev_api_key

    if not active_api_key:
        st.error("⚠️ لم يتم العثور على أي مفتاح API صالح. يرجى إعداد الـ Secrets أو إدخال مفتاحك الخاص ليعمل الشات.")
        st.stop()
    else:
        genai.configure(api_key=active_api_key)

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        with st.expander("📷 إرفاق صورة للتحليل (اختياري)"):
            uploaded_file = st.file_uploader("اختر صورة (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])
            if uploaded_file is not None:
                st.image(uploaded_file, caption="الصورة المرفوعة", width=250)

        if prompt := st.chat_input("اكتب سؤالك هنا... (مثال: اشرح لي نتيجتي الأخيرة)"):
            
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            sys_instruct = """أنت مهندس بيانات ومساعد ذكي مدمج في منصة 'Vision Analytics'. وظيفتك تحليل البيانات والرد على استفسارات المستخدمين باحترافية وتقديم رؤى واضحة.
            يجب أن تفهم جيداً أن هذه المنصة تحتوي على نظامين منفصلين للذكاء الاصطناعي:
            1. نظام (Student Risk Analysis): مخصص للطلاب فقط. يتوقع احتمالية تعرض الطالب للخطر بناءً على عوامل نفسية وبيئية.
            2. نظام (App Behavior Analysis): يحلل السلوك التقني لمستخدمي الهواتف الذكية. ركز على نصائح "الديتوكس الرقمي" والصحة.
            بناءً على هذا الفهم، قم بالإجابة بدقة عالية وقدم نصائح عملية ومباشرة."""
            
            if 'last_analysis_context' in st.session_state:
                sys_instruct += f"\n\n[سياق مخفي هام جداً للإجابة]: أحدث نتيجة تحليل قام بها المستخدم للتو هي: {st.session_state['last_analysis_context']}"

            model = genai.GenerativeModel(
                model_name='gemini-flash-latest',
                system_instruction=sys_instruct
            )

            with st.chat_message("assistant"):
                with st.spinner("جاري التحليل... 🧠"):
                    try:
                        if uploaded_file is not None:
                            img = Image.open(uploaded_file)
                            response = model.generate_content([prompt, img])
                        else:
                            response = model.generate_content(prompt)
                        
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
                    except Exception as e:
                        if "429" in str(e) or "Quota" in str(e):
                            st.error("⚠️ يبدو أن الضغط عالٍ جداً على خوادمنا المجانية في الوقت الحالي! لضمان استمرار خدمتك، يرجى فتح القائمة العلوية ⚙️ وإدخال مفتاح API الخاص بك لتتجاوز الزحام.")
                        else:
                            st.error(f"حدث خطأ أثناء معالجة الطلب. (الخطأ: {e})")
