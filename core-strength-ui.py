import tempfile
import pandas as pd
from fpdf import FPDF
import streamlit as st
from datetime import datetime
from pymongo import MongoClient

# ---------- MongoDB Setup ----------
mongo_uri = "mongodb://localhost:27017"
client = MongoClient(mongo_uri)
db = client["concrete_app"]
feedback_col = db["feedbacks"]
recipient_col = db["recipient_emails"]

# ---------- Session State Defaults ----------
if "show_share_form" not in st.session_state:
    st.session_state["show_share_form"] = False
if "show_feedback_form" not in st.session_state:
    st.session_state["show_feedback_form"] = False

# ---------- Styling (Dark/Light Mode Friendly) ----------
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
    }
    .stButton>button {
        background-color: #336699;
        color: white;
        padding: 8px 20px;
        border-radius: 5px;
        font-size: 16px;
        transition: background-color 0.3s ease;
        border: none;
    }
    .stButton>button:hover {
        background-color: #25476a;
    }
    h1, h2, h3 {
        color: inherit !important;
    }
    .stForm {
        border: 1px solid rgba(128, 128, 128, 0.3);
        padding: 20px;
        border-radius: 8px;
        background-color: rgba(255, 255, 255, 0.05);
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Sidebar Forms ----------
st.sidebar.markdown("## Share This App")
if st.sidebar.button("Open Share Form"):
    st.session_state["show_share_form"] = not st.session_state["show_share_form"]

if st.session_state["show_share_form"]:
    with st.sidebar.form("share_form"):
        share_email = st.text_input("Recipient Email(s)")
        share_submit = st.form_submit_button("Send")
        if share_submit:
            if share_email.strip():
                try:
                    recipient_col.insert_one({
                        "recipient": share_email.strip(),
                        "shared_at": datetime.utcnow()
                    })
                    st.success(f"✅ App link shared to {share_email} (simulated and saved).")
                except Exception:
                    st.error("❌ Failed to save recipient email.")
            else:
                st.warning("⚠️ Please enter a valid email.")

st.sidebar.markdown("---")
st.sidebar.markdown("## Leave Feedback")
if st.sidebar.button("Open Feedback Form"):
    st.session_state["show_feedback_form"] = not st.session_state["show_feedback_form"]

if st.session_state["show_feedback_form"]:
    with st.sidebar.form("feedback_form"):
        user = st.text_input("Your Name or Email")
        comment = st.text_area("Your Feedback")
        fb_submit = st.form_submit_button("Submit")
        if fb_submit:
            if user.strip() and comment.strip():
                try:
                    feedback_col.insert_one({
                        "user": user.strip(),
                        "comment": comment.strip(),
                        "submitted_at": datetime.utcnow()
                    })
                    st.success("✅ Thank you for your feedback!")
                except:
                    st.error("❌ Failed to submit feedback.")
            else:
                st.warning("⚠️ Please complete all fields.")

# ---------- Header ----------
st.markdown("<h1 style='text-align: center;'>Concrete Core Compression Strength</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size:16px;'>IS 516-compliant evaluation tool</p>", unsafe_allow_html=True)
st.markdown("---")

# ---------- Input Form ----------
with st.form("core_input_form"):
    st.markdown("### Enter Core Test Values")
    col1, col2 = st.columns(2)

    with col1:
        core_diameter = st.number_input("Core Diameter (in mm)", min_value=1.0, value=68.0,
                                        help="Measured diameter of the concrete core sample")
        load_kn = st.number_input("Load Applied (in kN)", min_value=0.1, value=175.0,
                                  help="Compressive load at failure")

    with col2:
        core_length = st.number_input("Core Length (in mm)", min_value=1.0, value=132.0,
                                      help="Measured length of the core")
        grade_mpa = st.number_input("Concrete Grade (in MPa)", min_value=1.0, value=50.0,
                                    help="Target concrete strength")

    submit_button = st.form_submit_button("🚀 Evaluate Strength")

# ---------- Evaluation Logic ----------
if submit_button:
    pi = 3.14
    area_mm2 = round((pi / 4) * core_diameter ** 2, 2)
    load_n = load_kn * 1000
    raw_strength = round(load_n / area_mm2, 2)
    ld_ratio = core_length / core_diameter

    dia_correction_factor = 1.06 if core_diameter < 70 else 1.03 if core_diameter <= 80 else 1.00
    corrected_strength = round(raw_strength * dia_correction_factor, 2)
    graph_correction_factor = round(0.11 * ld_ratio + 0.78, 2)
    graph_corrected_strength = round(corrected_strength * graph_correction_factor, 2)
    cube_equivalent_strength = round(graph_corrected_strength * 1.25, 2)
    percent_strength = round((cube_equivalent_strength / grade_mpa) * 100, 2)
    required_strength = round(0.75 * grade_mpa, 2)
    status = "✅ PASS" if corrected_strength >= required_strength else "❌ FAIL"
    status_color = "#d4edda" if "PASS" in status else "#f8d7da"
    status_text_color = "#155724" if "PASS" in status else "#721c24"

    # ---------- Summary ----------
    st.markdown("---")
    st.markdown("<h3>Evaluation Summary</h3>", unsafe_allow_html=True)
    st.markdown(
        f"<p>L/D Ratio: <strong>{ld_ratio:.2f}</strong> | Diameter Correction: <strong>{dia_correction_factor}</strong> | Graph Factor: <strong>{graph_correction_factor}</strong></p>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Raw Strength", f"{raw_strength:.2f} MPa")
    col2.metric("Dia Corrected", f"{corrected_strength:.2f} MPa")
    col3.metric("Graph Corrected", f"{graph_corrected_strength:.2f} MPa")

    col4, col5 = st.columns(2)
    col4.metric("Cube Equivalent", f"{cube_equivalent_strength:.2f} MPa")
    col5.metric("Strength %", f"{percent_strength:.2f} %")

    st.markdown(f"""
        <div style="padding: 12px; border-radius: 8px; background-color: {status_color}; color: {status_text_color}; text-align: center;">
            <strong>{status}</strong>
        </div>
    """, unsafe_allow_html=True)

    # ---------- Detailed Breakdown ----------
    with st.expander("See Detailed Calculation"):
        st.write({
            "Core Diameter (mm)": core_diameter,
            "Core Length (mm)": core_length,
            "Load (kN)": load_kn,
            "Load (N)": load_n,
            "Area (mm²)": area_mm2,
            "L/D Ratio": round(ld_ratio, 2),
            "Dia Correction Factor": dia_correction_factor,
            "Raw Strength (MPa)": raw_strength,
            "Corrected Strength (MPa)": corrected_strength,
            "Graph Correction Factor": graph_correction_factor,
            "Graph Corrected Strength (MPa)": graph_corrected_strength,
            "Cube Equivalent Strength (MPa)": cube_equivalent_strength,
            "Percent Strength vs Grade (%)": percent_strength,
            "Required Strength (75% of Grade)": required_strength,
            "Status": status
        })

    # ---------- Export Section ----------
    export_data = {
        "Core Diameter (mm)": core_diameter,
        "Core Length (mm)": core_length,
        "Load (kN)": load_kn,
        "Load (N)": load_n,
        "Area (mm²)": area_mm2,
        "L/D Ratio": round(ld_ratio, 2),
        "Dia Correction Factor": dia_correction_factor,
        "Raw Strength (MPa)": raw_strength,
        "Corrected Strength (MPa)": corrected_strength,
        "Graph Correction Factor": graph_correction_factor,
        "Graph Corrected Strength (MPa)": graph_corrected_strength,
        "Cube Equivalent Strength (MPa)": cube_equivalent_strength,
        "Percent Strength vs Grade (%)": percent_strength,
        "Required Strength (75% of Grade)": required_strength,
        "Status": status.replace("✅", "").replace("❌", "")
    }

    df = pd.DataFrame([export_data])
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", csv, "core_strength_report.csv", "text/csv")

    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 12)
            self.cell(0, 10, "Concrete Core Strength Report", ln=True, align="C")
            self.ln(5)

        def body(self, data):
            self.set_font("Arial", "", 10)
            for k, v in data.items():
                self.cell(80, 10, f"{k}", border=1)
                self.cell(0, 10, f"{v}", border=1, ln=True)

    pdf = PDF()
    pdf.add_page()
    pdf.body(export_data)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        pdf.output(tmp_file.name)
        tmp_file.seek(0)
        st.download_button("⬇️ Download PDF", tmp_file.read(), "core_strength_report.pdf", "application/pdf")