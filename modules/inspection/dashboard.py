import streamlit as st
import plotly.graph_objects as go
from modules.inspection.mechanical import MechanicalInspector

# --- HELPER FUNCTION UNTUK WARNA TABEL (PASTEL) ---
def highlight_row(row):
    if "ZONE D" in row['Remark']: 
        return ['background-color: #ffebee; color: #b71c1c']*len(row) # Merah Pucat
    elif "ZONE C" in row['Remark']: 
        return ['background-color: #fffde7; color: #f57f17']*len(row) # Kuning Pucat
    elif "ZONE A" in row['Remark']: 
        return ['background-color: #e8f5e9; color: #1b5e20; font-weight: bold']*len(row) # Hijau Pucat
    else: 
        return ['background-color: #ffffff; color: #212529']*len(row) # Putih

def run():
    # --- INSTANTIATE LOGIC ---
    # Limit Vibrasi 4.5 mm/s (Default ISO Class II)
    # Limit Suhu 85 Celcius (Default Alarm Bearing)
    inspector = MechanicalInspector(vib_limit_warn=4.5, temp_limit_warn=85.0)

    st.header("⚙️ MECHANICAL INSPECTION")
    st.caption("Standards: ISO 20816-3 (Vibration), API 610 (Temp & Pump)")

    # --- INPUT SECTION (FORM) ---
    with st.form("mech_input_form"):
        c1, c2 = st.columns(2)
        
        # 1. DRIVER (MOTOR)
        with c1:
            st.subheader("1. Driver (Motor)")
            c1a, c1b = st.columns(2)
            with c1a:
                st.caption("Drive End (DE)")
                m_de_h = st.number_input("M-DE Horiz (mm/s)", 0.8)
                m_de_v = st.number_input("M-DE Vert (mm/s)", 0.2)
                m_de_a = st.number_input("M-DE Axial (mm/s)", 0.5)
                t_m_de = st.number_input("Temp M-DE (°C)", 45.0)
            with c1b:
                st.caption("Non-Drive End (NDE)")
                m_nde_h = st.number_input("M-NDE Horiz (mm/s)", 0.9)
                m_nde_v = st.number_input("M-NDE Vert (mm/s)", 0.3)
                m_nde_a = st.number_input("M-NDE Axial (mm/s)", 0.4)
                t_m_nde = st.number_input("Temp M-NDE (°C)", 42.0)

        # 2. DRIVEN (PUMP)
        with c2:
            st.subheader("2. Driven (Pump)")
            c2a, c2b = st.columns(2)
            with c2a:
                st.caption("Drive End (DE)")
                p_de_h = st.number_input("P-DE Horiz (mm/s)", 1.2)
                p_de_v = st.number_input("P-DE Vert (mm/s)", 0.8)
                p_de_a = st.number_input("P-DE Axial (mm/s)", 0.6)
                t_p_de = st.number_input("Temp P-DE (°C)", 40.0)
            with c2b:
                st.caption("Non-Drive End (NDE)")
                p_nde_h = st.number_input("P-NDE Horiz (mm/s)", 0.7)
                p_nde_v = st.number_input("P-NDE Vert (mm/s)", 0.4)
                p_nde_a = st.number_input("P-NDE Axial (mm/s)", 0.3)
                t_p_nde = st.number_input("Temp P-NDE (°C)", 38.0)
        
        submit_btn = st.form_submit_button("🔍 RUN MECHANICAL ANALYSIS")

    # --- OUTPUT SECTION ---
    if submit_btn:
        # A. PROSES VIBRASI
        inputs_vib = {
            'm_de_h': m_de_h, 'm_de_v': m_de_v, 'm_de_a': m_de_a,
            'm_nde_h': m_nde_h, 'm_nde_v': m_nde_v, 'm_nde_a': m_nde_a,
            'p_de_h': p_de_h, 'p_de_v': p_de_v, 'p_de_a': p_de_a,
            'p_nde_h': p_nde_h, 'p_nde_v': p_nde_v, 'p_nde_a': p_nde_a
        }
        df_report, vib_causes, max_vib = inspector.analyze_vibration(inputs_vib)

        # B. PROSES TEMPERATUR
        inputs_temp = {
            'Motor DE': t_m_de, 'Motor NDE': t_m_nde,
            'Pump DE': t_p_de, 'Pump NDE': t_p_nde
        }
        temp_status, temp_issues, max_temp = inspector.analyze_temperature(inputs_temp)

        st.divider()
        st.subheader("📋 HASIL ANALISA MEKANIKAL")

        # Layout Hasil: Kiri Tabel, Kanan Gauge & Kesimpulan
        col_res1, col_res2 = st.columns([2, 1])

        with col_res1:
            st.markdown("##### 1. Tabel Laporan Vibrasi (ISO 20816)")
            # Tampilkan Tabel dengan Warna Pastel
            st.dataframe(
                df_report.style.apply(highlight_row, axis=1)
                .format({"DE": "{:.2f}", "NDE": "{:.2f}", "Avr": "{:.2f}", "Limit": "{:.2f}"}),
                use_container_width=True,
                hide_index=True
            )
            
            if vib_causes:
                st.error("**⚠️ Diagnosa Vibrasi:**")
                for cause in vib_causes:
                    st.markdown(f"- {cause}")
            else:
                st.success("✅ Pola Vibrasi Normal (Tidak ada indikasi Misalignment/Unbalance).")

        with col_res2:
            st.markdown("##### 2. Indikator Utama")
            
            # Gauge Vibrasi
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = max_vib,
                title = {'text': "Max Vib (mm/s)"},
                gauge = {
                    'axis': {'range': [0, 10]},
                    'bar': {'color': "black"},
                    'steps': [
                        {'range': [0, 2.3], 'color': "#e8f5e9"}, # A
                        {'range': [2.3, 4.5], 'color': "#ffffff"}, # B
                        {'range': [4.5, 7.1], 'color': "#fffde7"}, # C
                        {'range': [7.1, 10], 'color': "#ffebee"}   # D
                    ]
                }
            ))
            fig.update_layout(height=180, margin=dict(t=30,b=20,l=20,r=20))
            st.plotly_chart(fig, use_container_width=True)

            # Kotak Temperatur
            st.markdown("##### 3. Analisa Suhu")
            if temp_status == "NORMAL":
                st.success(f"🌡️ **Suhu Normal** (Max {max_temp}°C)")
                st.caption("Semua bearing dibawah limit 85°C.")
            else:
                st.error(f"🔥 **{temp_status}** (Max {max_temp}°C)")
                for issue in temp_issues:
                    st.write(f"- {issue}")
