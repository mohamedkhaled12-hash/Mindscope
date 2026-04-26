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

    /* إصلاح مربعات الإدخال والقوائم لتتكيف مع الـ Light/Dark Mode */
    div[data-baseweb="select"] > div, div[data-baseweb="base-input"] > input {
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        -webkit-text-fill-color: var(--text-color) !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        border-radius: 10px !important;
        border: 2px solid transparent !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    div[data-baseweb="select"] > div *, div[data-baseweb="base-input"] > input * {
        color: var(--text-color) !important;
        -webkit-text-fill-color: var(--text-color) !important;
    }

    [data-baseweb="popover"] { background-color: transparent !important; }
    [role="listbox"], ul[data-baseweb="menu"], div[data-baseweb="popover"] > div {
        background-color: var(--background-color) !important; 
        border-radius: 12px !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3) !important;
        border: 1px solid var(--secondary-background-color) !important;
        padding: 4px !important;
    }
    [role="option"], ul[data-baseweb="menu"] li {
        color: var(--text-color) !important;
        -webkit-text-fill-color: var(--text-color) !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        background-color: transparent !important;
        padding: 10px 15px !important;
        border-radius: 8px !important;
    }

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
    .stRadio label:has(input:checked) {
        background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%) !important;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.5);
    }

    div[data-testid="stFormSubmitButton"] > button, [data-testid="baseButton-secondary"] {
        background: linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%) !important;
        border: none !important;
        padding: 16px 24px !important;
        border-radius: 12px !important;
        animation: pulseGlow 2.5s infinite;
    }
    div[data-testid="stFormSubmitButton"] > button *, [data-testid="baseButton-secondary"] * {
        color: #0F172A !important; 
        -webkit-text-fill-color: #0F172A !important;
        font-weight: 900 !important; 
    }

    .script-text { line-height: 1.8; font-size: 15px; margin-bottom: 15px; }
    .script-title { font-size: 24px; font-weight: 900; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px; }
    .section-box { background: rgba(255,255,255,0.03); padding: 18px; border-radius: 10px; margin-bottom: 15px; box-shadow: inset 0 2px 10px rgba(0,0,0,0.1);}
</style>
""", unsafe_allow_html=True)

# 2. Load Assets (Updated filenames)
@st.cache_resource
def load_assets():
    risk_model = joblib.load('risk_model_pipeline.pkl')
    app_model = joblib.load('app_behavior_model_xgb (1).pkl')
    app_encoder = joblib.load('label_encoder (1).pkl')
    original_encoder = joblib.load('label_encoder.pkl') 
    return risk_model, app_model, app_encoder, original_encoder

try:
    risk_model, app_model, app_encoder, original_encoder = load_assets()
except Exception as e:
    st.error(f"⚠️ Failed to load models. Error: {e}")
    st.stop()

# ==========================================
# 🚀 Navigation Header
# ==========================================
st.markdown("<div class='gradient-text'>Vision Analytics</div>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94A3B8 !important; margin-bottom: 25px; font-size: 1.1rem;'>Empowered by Advanced Machine Learning</p>", unsafe_allow_html=True)

page = st.radio("", ["Student Risk Analysis", "App Behavior Analysis", "AI Assistant 🤖"], horizontal=True, label_visibility="collapsed")

# ------------------------------------------------------------------
# Page 1: Student Risk Analysis
# ------------------------------------------------------------------
if page == "Student Risk Analysis":
    st.markdown("<h3 style='color: #E9D5FF !important;'>🧠 Student Risk Intelligence</h3>", unsafe_allow_html=True)
    
    stress_map = {"Very Calm": 1.0, "Normal Stress": 4.0, "Highly Stressed": 7.0, "Extremely Stressed": 10.0}
    anxiety_map = {"Stable": 1.0, "Mild Anxiety": 3.5, "Constant Tension": 7.0, "Severe Panic": 10.0}
    support_map = {"Completely Isolated": 1.0, "Limited Support": 4.0, "Good Support": 7.5, "Strong Support": 10.0}
    dep_map = {"Optimistic & Energetic": 1.0, "Occasional Sadness": 4.5, "Frequent Low Mood": 7.5, "Severe Despair": 10.0}
    sleep_map = {"< 4 hours (Severely Deprived)": 3.0, "4-6 hours (Insufficient)": 5.0, "7-9 hours (Healthy)": 8.0, "> 9 hours (Oversleeping)": 10.0}
    exam_map = {"No Immediate Exams": 1.0, "Manageable Workload": 4.0, "High Academic Stress": 7.5, "Overwhelming Pressure": 10.0}

    with st.form("risk_form"):
        st.subheader("📋 Behavioral Assessment")
        col1, col2 = st.columns(2, gap="large")
        with col1:
            stress = st.selectbox("Stress Level:", list(stress_map.keys()))
            anxiety = st.selectbox("Anxiety Level:", list(anxiety_map.keys()))
            depression = st.selectbox("Mood & Energy:", list(dep_map.keys()))
        with col2:
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
            clean_classes = [str(c).strip().title() for c in original_encoder.classes_]
            prob_dict = {c: p for c, p in zip(clean_classes, probs)}
            
            if prob_dict.get('High', 0.0) >= 0.25: final_label = 'High'
            elif prob_dict.get('Medium', 0.0) >= 0.35: final_label = 'Medium'
            else: final_label = clean_classes[np.argmax(probs)]
            
            st.session_state['last_analysis_context'] = f"Student Risk Analysis: {final_label}"
            log_data("Students", [stress, anxiety, depression, support, sleep, exams, final_label])

        res_col1, res_col2 = st.columns([1, 1.5])
        with res_col1:
            st.markdown('<div class="metric-card" style="text-align: center;">', unsafe_allow_html=True)
            color = "#F43F5E" if 'High' in final_label else "#FBBF24" if 'Medium' in final_label else "#34D399"
            st.markdown(f"<h2 style='color:{color}; font-size: 30px;'>{final_label.upper()} RISK</h2>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with res_col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            fig = px.bar(x=probs*100, y=clean_classes, orientation='h', color=clean_classes, color_discrete_map={'High':'#F43F5E', 'Medium':'#FBBF24', 'Low':'#34D399'})
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#F8FAFC'), height=200, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        student_scripts = {
            'Low': """<div dir="rtl" style="text-align: right;" class="script-text">
<div class="script-title" style="color:#34D399;">✅ مستوى الخطر المنخفض</div>
<div class="section-box" style="border-right: 4px solid #34D399;"><p>يشير مستوى الخطر المنخفض إلى أنك تتنقل في بيئتك الأكاديمية بنجاح مع توازن عقلي وعاطفي ممتاز. أنت تستفيد بشكل كبير من أنظمة الدعم الاجتماعي القوية، مما يضمن عدم تحول الضغوط إلى احتراق.</p></div>
<div class="section-box" style="border-right: 4px solid #A855F7;"><p><b>التوصيات:</b> الحفاظ على عادات نوم صحية، إدارة الوقت الاستباقية، والتوجيه ودعم الأقران.</p></div>
</div>""",
            'Medium': """<div dir="rtl" style="text-align: right;" class="script-text">
<div class="script-title" style="color:#FBBF24;">🟡 مستوى الخطر المتوسط</div>
<div class="section-box" style="border-right: 4px solid #FBBF24;"><p>يشير مستوى الخطر المتوسط إلى أنك تتأرجح على حافة الإرهاق الأكاديمي. قد تجد نفسك تقوم بالتمرير بشكل سلبي لتجنب التفكير في الاختبارات القادمة، مما يعيق تعافي دماغك.</p></div>
<div class="section-box" style="border-right: 4px solid #A855F7;"><p><b>التوصيات:</b> إنشاء روتين للاسترخاء قبل النوم، تقسيم المهام الكبيرة لخطوات صغيرة، وجدولة وقت للقلق.</p></div>
</div>""",
            'High': """<div dir="rtl" style="text-align: right;" class="script-text">
<div class="script-title" style="color:#F43F5E;">🚨 مستوى الخطر المرتفع</div>
<div class="section-box" style="border-right: 4px solid #F43F5E;"><p>علامة تحذير حاسمة من الاحتراق الأكاديمي والرقمي الشديد. أنت تعمل بوضع "البقاء على قيد الحياة" مما يضعف وظائفك التنفيذية ويدمر أداءك الأكاديمي.</p></div>
<div class="section-box" style="border-right: 4px solid #A855F7;"><p><b>التوصيات:</b> إعطاء الأولوية للراحة، طلب الاستشارة المهنية، التواصل مع الأساتذة، والانفصال الرقمي الجذري.</p></div>
</div>"""
        }
        st.markdown(f'''<div class="metric-card" style="margin-top: 25px;">\n{student_scripts.get(final_label, "")}\n</div>''', unsafe_allow_html=True)

# ------------------------------------------------------------------
# Page 2: App Behavior Analysis (10 Results Update)
# ------------------------------------------------------------------
elif page == "App Behavior Analysis":
    st.markdown("<h3 style='color: #67E8F9 !important;'>📱 App Behavior Tech-Metrics</h3>", unsafe_allow_html=True)

    with st.form("app_behavior_form"):
        st.subheader("⚙️ Technical Telemetry")
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
            
            # التحقق من أسماء الأعمدة المتوقعة من الموديل الجديد
            if hasattr(app_model, 'feature_names_in_'):
                expected_cols = list(app_model.feature_names_in_)
                if 'Gender_Male' in expected_cols:
                    df_app['Gender_Male'] = 1.0 if gender == "Male" else 0.0
                    df_app['Gender_Female'] = 1.0 if gender == "Female" else 0.0
                    if 'Gender' in df_app.columns: df_app = df_app.drop(columns=['Gender'])
                df_app = df_app.reindex(columns=expected_cols, fill_value=0.0)

            # التنبؤ وجلب التسمية من الـ Encoder الجديد
            pred_idx = app_model.predict(df_app)[0]
            raw_label = str(app_encoder.inverse_transform([pred_idx])[0])
            
            # 🛠️ التنظيف الجذري: مسح أي مسافات أو حروف مخفية مثل \r أو \n
            final_app_label = raw_label.replace('\r', '').replace('\n', '').strip()
            
            st.session_state['last_analysis_context'] = f"App Behavior Analysis Result: {final_app_label}"
            log_data("Apps", [age, gender, num_apps, screen_time, battery, data_usage, app_usage, final_app_label])

            st.markdown(f"""
                <div class="metric-card" style="text-align: center; margin-top:25px;">
                    <h3 style='color:#CBD5E1 !important;'>Predicted Classification</h3>
                    <h1 style='color:#22D3EE !important; font-size:2.8rem; font-weight:900;'>{final_app_label}</h1>
                </div>
            """, unsafe_allow_html=True)

            # ==========================================
            # 📝 توزيع الإسكريبت على الـ 10 نتائج (Label Encoder)
            # ==========================================
            
            recs = {
                1: "1. الحفاظ على مناطق خالية من التكنولوجيا. 2. فحص الجهاز المجدول. 3. تبني الهوايات التناظرية.",
                2: "1. قاعدة الـ 30 دقيقة للتمرير. 2. إيقاف الإشعارات غير الضرورية. 3. الاستخدام المقصود للتطبيقات.",
                3: "1. تنفيذ فترات راحة للتمرير. 2. تنظيم المحتوى الخاص بك. 3. ممارسة تقنية بومودورو.",
                4: "1. وضع حدود صارمة للتطبيقات. 2. صيام الدوبامين أسبوعياً. 3. الوضع الرمادي للشاشة.",
                5: "1. طلب الدعم المهني. 2. حذف التطبيقات عالية الخطورة. 3. أمسيات إلزامية خالية من الشاشات."
            }

            analysis_parts = {
                "1 - Low Part": "تُظهر علاقة واعية ومقصودة جداً مع جهازك. نسبة تعفن الدماغ معدومة (0%-5%). وقت استخدامك منخفض واستهلاك البطارية يعكس تفاعلاً ضئيلاً. أنت تنظر للتكنولوجيا كمساعد وليس فخ.",
                "1 - High Part": "لا تزال تحتفظ بسيطرة ممتازة ولكنك تنغمس أحياناً في ترفيه رقمي (6%-15%). نادراً ما تفقد الإحساس بالوقت، وتوازن بنجاح بين الاتصال الحديث ونمط الحياة الصحي.",
                "2 - Low Part": "تعكس عاداتك وقت فراغ سلبي وعرضي (16%-25%). تستخدم التطبيقات للاسترخاء بعد يوم طويل، وهي مرحلة انتقالية تتشكل فيها العادات دون تشتت ملحوظ.",
                "2 - High Part": "تظهر العلامات الأولى للتشتت الرقمي (26%-35%). الخوارزميات بدأت في التقاط انتباهك، وقد تعاني من إرهاق عقلي خفيف أو تأخير في إكمال المهام.",
                "3 - Low Part": "يتحول تفاعلك إلى استهلاك روتيني (36%-45%). أصبح التمرير عادة يومية، ودماغك يبقى في حالة تأهب مما يمنع التعافي العقلي الحقيقي. بداية تشتت الانتباه.",
                "3 - High Part": "العبء الرقمي الزائد واضح (46%-60%). انجذاب قوي نحو 'التمرير الكارثي'. تعاني من ضباب عقلي (Brainrot) ويصعب عليك الجلوس في صمت دون جهاز.",
                "4 - Low Part": "تحول من العادة إلى السلوك القهري (61%-75%). وقت شاشة طويل جداً يمتد لمنتصف الليل، مما يؤثر بشدة على جودة نومك وإفراز الميلاتونين.",
                "4 - High Part": "إرهاق معرفي شديد (76%-85%). اعتماد شبه كلي على التحفيز الرقمي. القراءة المطولة أصبحت مستحيلة، وأنت تقف على حافة الاحتراق الرقمي الكامل.",
                "5 - Low Part": "وصلت إلى الاحتراق الرقمي الفعلي (86%-95%). تواصل مزمن وآلية تكيف مدمرة. تعاني من خمول شديد وخدر عاطفي، وتفاعلات الحياة الواقعية تبدو مملة.",
                "5 - High Part": "أشد مستويات العبء الرقمي (96%-100%). إدمان يستهلك كل شيء وحمل إدراكي زائد كامل. انتباهك محطم تماماً، وتعاني من إجهاد عين وأرق حاد."
            }

            # 🛠️ استخراج رقم الفئة بأمان تام حتى لو في مسافات
            try:
                class_num = int(''.join(filter(str.isdigit, final_app_label.split('-')[0])))
            except:
                class_num = 1 # قيمة افتراضية لتجنب توقف التطبيق
            
            app_script_html = f"""<div dir="rtl" style="text-align: right;" class="script-text">
<div class="script-title" style="color:#22D3EE;">📋 التقرير التحليلي للفئة {class_num}</div>
<div class="section-box" style="border-right: 4px solid #22D3EE;">
<p style="color:#67E8F9; font-size: 18px; margin-bottom: 5px;"><b>التحليل السلوكي للجزء الخاص بك:</b></p>
<p>{analysis_parts.get(final_app_label, "تم التحليل بنجاح، يُرجى مراجعة التوصيات.")}</p>
</div>
<div class="section-box" style="border-right: 4px solid #A855F7;">
<p style="color:#C084FC; font-size: 18px; margin-bottom: 5px;"><b>توصيات الفئة {class_num}:</b></p>
<p>{recs.get(class_num, "")}</p>
</div>
</div>"""

            st.markdown(f'''<div class="metric-card" style="margin-top: 15px;">\n{app_script_html}\n</div>''', unsafe_allow_html=True)

# ------------------------------------------------------------------
# Page 3: AI Assistant 🤖
# ------------------------------------------------------------------
elif page == "AI Assistant 🤖":
    st.markdown("<h3 style='color: #A855F7 !important;'>🤖 Smart AI Assistant</h3>", unsafe_allow_html=True)
    
    try: dev_api_key = st.secrets["GEMINI_API_KEY"]
    except: dev_api_key = ""

    if "messages" not in st.session_state: st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]): st.markdown(message["content"])

    if prompt := st.chat_input("اكتب سؤالك هنا..."):
        with st.chat_message("user"): st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        sys_instruct = "أنت مهندس بيانات ومساعد ذكي في منصة Vision Analytics. حلل البيانات وقدم نصائح صحية ودراسية."
        if 'last_analysis_context' in st.session_state:
            sys_instruct += f"\n\n[Context]: {st.session_state['last_analysis_context']}"

        genai.configure(api_key=dev_api_key)
        model = genai.GenerativeModel('gemini-flash-latest', system_instruction=sys_instruct)

        with st.chat_message("assistant"):
            with st.spinner("🧠..."):
                try:
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"Error: {e}")
