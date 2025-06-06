import streamlit as st
from fpdf import FPDF
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import tempfile

# ---------- MongoDB Setup ----------
mongo_uri = "mongodb://localhost:27017"  # Replace with your URI if needed
client = MongoClient(mongo_uri)
db = client["concrete_app"]
feedback_col = db["feedbacks"]

# ---------- Session State Defaults ----------
if "show_share_form" not in st.session_state:
    st.session_state["show_share_form"] = False
if "show_feedback_form" not in st.session_state:
    st.session_state["show_feedback_form"] = False

# ---------- Page Styling ----------
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
        background-color: #f9f9f9;
        color: #2c3e50;
    }
    .stButton>button {
        background-color: #2c3e50;
        color: white;
        padding: 8px 20px;
        border-radius: 5px;
        font-size: 16px;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #1a242f;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #1f77b4;
    }
    .stForm {
        border: 1px solid #ddd;
        padding: 20px;
        border-radius: 8px;
        background-color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Sidebar: Share + Feedback ----------
st.sidebar.markdown("## 📤 Share This App")
if st.sidebar.button("Open Share Form"):
    st.session_state["show_share_form"] = not st.session_state["show_share_form"]

if st.session_state["show_share_form"]:
    with st.sidebar.form("share_form"):
        share_email = st.text_input("Recipient Email(s)")
        share_submit = st.form_submit_button("Send")
        if share_submit:
            if share_email.strip():
                st.success(f"✅ App link shared to {share_email} (simulation).")
            else:
                st.warning("⚠️ Please enter a valid email.")

st.sidebar.markdown("---")
st.sidebar.markdown("## 💬 Leave Feedback")
if st.sidebar.button("Open Feedback Form"):
    st.session_state["show_feedback_form"] = not st.session_state["show_feedback_form"]

if st.session_state["show_feedback_form"]:
    with st.sidebar.form("feedback_form"):
        user = st.text_input("Your Name or Email")
        comment = st.text_area("Your Feedback")
        fb_submit = st.form_submit_button("Submit")
        if fb_submit:
            if user.strip() and comment.strip():
                if feedback_col is not None:
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
                    st.warning("⚠️ MongoDB not connected. Feedback not saved.")
            else:
                st.warning("⚠️ Please complete all fields.")

# ---------- Header ----------
st.markdown("<h1 style='text-align: center;'>Concrete Core Strength Evaluator</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size:16px; color: #555;'>IS 516-compliant evaluation tool</p>", unsafe_allow_html=True)
st.markdown("---")

# ---------- Input Form ----------
with st.form("core_input_form"):
    col1, col2 = st.columns(2)

    with col1:
        core_diameter = st.number_input("Core Diameter (mm) – e.g., 68.00", min_value=1.0, value=68.0)
        load_kn = st.number_input("Load Applied (kN) – e.g., 175.00", min_value=0.1, value=175.0)

    with col2:
        core_length = st.number_input("Core Length (mm) – e.g., 132.00", min_value=1.0, value=132.0)
        grade_mpa = st.number_input("Concrete Grade (MPa) – e.g., 50.00", min_value=1.0, value=50.0)

    submit_button = st.form_submit_button("Evaluate Strength")

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
    status_color = "#dff0d8" if "PASS" in status else "#f2dede"
    status_text_color = "#3c763d" if "PASS" in status else "#a94442"

    # ---------- Summary ----------
    st.markdown("---")
    st.markdown("<h3 style='color:#1f77b4;'>Evaluation Summary</h3>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='font-size:15px; color:#333;'>L/D Ratio: <strong>{ld_ratio:.2f}</strong> | Diameter Correction Factor: <strong>{dia_correction_factor}</strong> | Graph Factor: <strong>{graph_correction_factor}</strong></p>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Raw Strength", f"{raw_strength:.2f} MPa")
    col2.metric("After Dia Correction", f"{corrected_strength:.2f} MPa")
    col3.metric("After Graph Correction", f"{graph_corrected_strength:.2f} MPa")

    col4, col5 = st.columns(2)
    col4.metric("Cube Equivalent", f"{cube_equivalent_strength:.2f} MPa")
    col5.metric("% Strength vs Grade", f"{percent_strength:.2f} %")

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
                self.cell(0, 10, f"{k}: {v}", ln=True)

    pdf = PDF()
    pdf.add_page()
    pdf.body(export_data)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        pdf.output(tmp_file.name)
        tmp_file.seek(0)
        st.download_button("⬇️ Download PDF", tmp_file.read(), "core_strength_report.pdf", "application/pdf")