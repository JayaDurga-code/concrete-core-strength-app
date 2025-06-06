import streamlit as st

st.set_page_config(page_title="Core Strength Evaluator", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { background-color: #4CAF50; color: white; }
    .stMetric label { font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #1f77b4;'>🧱 Concrete Core Strength Evaluator</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size:18px;'>IS 516 + Excel-style Calculation for Concrete Core Compression Strength</p>", unsafe_allow_html=True)
st.markdown("---")

with st.form("core_input_form"):
    col1, col2 = st.columns(2)

    with col1:
        core_diameter = st.number_input("🔘 Core Diameter (mm)", min_value=1.0, value=68.0)
        load_kn = st.number_input("📦 Load Applied (kN)", min_value=0.1, value=175.0)

    with col2:
        core_length = st.number_input("📏 Core Length (mm)", min_value=1.0, value=132.0)
        grade_mpa = st.number_input("🏗️ Concrete Grade (MPa)", min_value=1.0, value=50.0)

    submit_button = st.form_submit_button("🚀 Evaluate Strength")

if submit_button:
    # ✅ Excel-style area calculation (do not change)
    pi = 3.14
    area_raw = (pi / 4) * core_diameter ** 2
    area_mm2 = int(area_raw * 100) / 100  # Truncate to 2 decimals

    # Load and raw strength
    load_n = load_kn * 1000
    raw_strength = load_n / area_mm2
    raw_strength = int(raw_strength * 100) / 100

    # L/D ratio
    ld_ratio = core_length / core_diameter

    # ✅ Diameter-based correction
    if core_diameter < 70:
        dia_correction_factor = 1.06
    elif 70 <= core_diameter <= 80:
        dia_correction_factor = 1.03
    else:
        dia_correction_factor = 1.00

    corrected_strength = raw_strength * dia_correction_factor
    corrected_strength = int(corrected_strength * 100) / 100

    # ✅ Graph-based correction on top of diameter-based correction
    graph_correction_factor = round(0.11 * ld_ratio + 0.78, 2)
    graph_corrected_strength = corrected_strength * graph_correction_factor
    graph_corrected_strength = int(graph_corrected_strength * 100) / 100

    # ✅ Cube equivalent and % strength (from graph corrected)
    cube_equivalent_strength = int(graph_corrected_strength * 1.25 * 100) / 100
    percent_strength = int((cube_equivalent_strength / grade_mpa) * 10000) / 100

    # Required strength and pass/fail
    required_strength = 0.75 * grade_mpa
    status = "✅ PASS" if corrected_strength >= required_strength else "❌ FAIL"
    status_color = "green" if "PASS" in status else "red"

    # ✅ Display summary
    st.markdown("---")
    st.markdown(f"<h3 style='color:#4CAF50;'>📊 Evaluation Summary</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:16px;'>L/D Ratio: <strong>{ld_ratio:.2f}</strong> | Dia Correction: ×<strong>{dia_correction_factor}</strong> | Graph Factor: <strong>{graph_correction_factor}</strong></p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Raw Strength", f"{raw_strength:.2f} MPa")
    col2.metric("After Dia Correction", f"{corrected_strength:.2f} MPa")
    col3.metric("After Graph Correction", f"{graph_corrected_strength:.2f} MPa")

    col4, col5 = st.columns(2)
    col4.metric("Cube Equivalent", f"{cube_equivalent_strength:.2f} MPa")
    col5.metric("% Strength vs Grade", f"{percent_strength:.2f} %")

    st.markdown(f"<h2 style='text-align:center; color:{status_color};'>{status}</h2>", unsafe_allow_html=True)

    # 🔍 Detailed Breakdown
    with st.expander("🔍 See Detailed Calculation"):
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