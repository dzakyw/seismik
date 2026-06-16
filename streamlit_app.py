import streamlit as st
import segyio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# Konfigurasi halaman
st.set_page_config(layout="wide", page_title="Penampil Data SEG-Y 2D")
st.title("📈 Penampil Data SEG-Y 2D")
st.markdown("Unggah berkas SEG-Y untuk melihat header lengkap, plot lintasan, tampilan trace, dan visualisasi 3D.")

# --- Unggah Berkas ---
uploaded_file = st.file_uploader("Pilih berkas SEG-Y", type=["sgy", "segy"])

if uploaded_file is not None:
    # Simpan file yang diunggah sebagai file sementara agar bisa dibaca segyio
    with open("temp_segy_file.sgy", "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        # --- Membuka file dengan segyio ---
        with segyio.open("temp_segy_file.sgy", "r", ignore_geometry=True) as segyfile:
            st.success("✅ Berkas berhasil dimuat!")

            # Ambil informasi dasar
            trace_count = segyfile.tracecount
            samples_per_trace = segyfile.samples.size
            sample_interval = segyfile.bin[segyio.BinField.Interval] / 1000000.0  # Mikrosekon ke detik

            # Sidebar Informasi File
            st.sidebar.header("📊 Informasi Berkas")
            st.sidebar.write(f"**Jumlah Trace:** {trace_count}")
            st.sidebar.write(f"**Sampel per Trace:** {samples_per_trace}")
            st.sidebar.write(f"**Interval Sampel:** {sample_interval:.3f} detik")

            # --- 1. Tampilkan Header Teks ---
            with st.expander("📄 Header Teks", expanded=False):
                text_header = segyio.tools.wrap(segyfile.text[0], 80)
                st.text(text_header)

            # --- 2. Tampilkan Header Biner ---
            with st.expander("⚙️ Header Biner", expanded=False):
                bin_header_keys = {
                    segyio.BinField.Samples: "Jumlah Sampel",
                    segyio.BinField.Interval: "Interval Sampel (mikrosekon)",
                    segyio.BinField.Format: "Format Data",
                    segyio.BinField.MeasurementSystem: "Sistem Pengukuran",
                    segyio.BinField.Traces: "Jumlah Trace",
                    segyio.BinField.ExtendedHeaders: "Jumlah Header Ekstensi",
                }
                bin_data = {}
                for key, desc in bin_header_keys.items():
                    try:
                        bin_data[desc] = segyfile.bin[key]
                    except:
                        bin_data[desc] = "Tidak tersedia"
                st.json(bin_data)

            # --- 3. Tampilkan Header Trace ---
            with st.expander("📋 Header Trace (Lintasan)", expanded=False):
                # Pilih field header yang akan ditampilkan
                header_fields = {
                    segyio.TraceField.TRACE_SEQUENCE_LINE: "Urutan Trace (Line)",
                    segyio.TraceField.TRACE_SEQUENCE_FILE: "Urutan Trace (File)",
                    segyio.TraceField.FieldRecord: "Nomor Rekaman Lapangan",
                    segyio.TraceField.TraceNumber: "Nomor Trace",
                    segyio.TraceField.SourcePoint: "Titik Sumber",
                    segyio.TraceField.CDP: "CDP",
                    segyio.TraceField.CDP_X: "Koordinat X CDP",
                    segyio.TraceField.CDP_Y: "Koordinat Y CDP",
                    segyio.TraceField.INLINE_3D: "Inline (3D)",
                    segyio.TraceField.CROSSLINE_3D: "Crossline (3D)",
                    segyio.TraceField.ShotPoint: "Titik Tembak",
                    segyio.TraceField.ShotPointX: "Koordinat X Sumber",
                    segyio.TraceField.ShotPointY: "Koordinat Y Sumber",
                    segyio.TraceField.ReceiverGroupElevation: "Elevasi Penerima",
                    segyio.TraceField.SourceDepth: "Kedalaman Sumber",
                }

                # Baca semua header trace (dibatasi 1000 trace pertama agar tidak ngelag)
                header_data = []
                for trace_idx in range(min(trace_count, 1000)):
                    row = {"Indeks Trace": trace_idx}
                    for key, desc in header_fields.items():
                        try:
                            row[desc] = segyfile.header[trace_idx][key]
                        except:
                            row[desc] = "Tidak tersedia"
                    header_data.append(row)

                df_headers = pd.DataFrame(header_data)
                st.dataframe(df_headers, use_container_width=True)

            # --- 4. Plot Lintasan (Line Plot) ---
            st.subheader("🗺️ Plot Lintasan")
            col1, col2 = st.columns(2)

            with col1:
                # Coba ambil koordinat CDP X/Y
                try:
                    cdp_x = [segyfile.header[i][segyio.TraceField.CDP_X] for i in range(trace_count)]
                    cdp_y = [segyfile.header[i][segyio.TraceField.CDP_Y] for i in range(trace_count)]
                    has_coords = True
                except:
                    has_coords = False
                    st.warning("Tidak ditemukan koordinat CDP X/Y, menggunakan indeks trace sebagai posisi.")

                fig_line, ax_line = plt.subplots(figsize=(8, 6))

                if has_coords:
                    # Gambar menggunakan koordinat sebenarnya
                    ax_line.plot(cdp_x, cdp_y, 'b-', linewidth=2)
                    ax_line.scatter(cdp_x, cdp_y, c='red', s=10)
                    ax_line.set_xlabel("Koordinat X CDP")
                    ax_line.set_ylabel("Koordinat Y CDP")
                    ax_line.set_title("Plot Lintasan (Koordinat CDP)")
                    ax_line.axis('equal')
                else:
                    # Tanpa koordinat, gunakan indeks
                    ax_line.plot(range(trace_count), np.zeros(trace_count), 'b-', linewidth=2)
                    ax_line.scatter(range(trace_count), np.zeros(trace_count), c='red', s=10)
                    ax_line.set_xlabel("Indeks Trace")
                    ax_line.set_ylabel("Posisi (tanpa koordinat)")
                    ax_line.set_title("Plot Lintasan (Berdasarkan Indeks)")

                st.pyplot(fig_line)

            with col2:
                st.info("""
                **Keterangan Plot Lintasan**
                - Garis biru : jalur lintasan
                - Titik merah : posisi setiap trace
                - Jika SEG-Y memiliki koordinat CDP, maka akan tampil peta koordinat sebenarnya
                """)

            # --- 5. Tampilan Trace Seismik ---
            st.subheader("📊 Tampilan Trace Seismik")
            
            # Pilih mode tampilan
            view_mode = st.radio("Pilih mode tampilan:", ["Densitas Variabel (Wiggle + Warna)", "Wiggle (Gelombang)", "Variable Area (Area Variabel)"], horizontal=True)

            # Pilih rentang trace
            trace_start, trace_end = st.slider(
                "Pilih rentang trace:",
                min_value=0,
                max_value=trace_count - 1,
                value=(0, min(trace_count - 1, 50))
            )

            # Baca data trace terpilih
            traces_data = []
            for i in range(trace_start, trace_end + 1):
                traces_data.append(segyfile.trace[i])

            traces_array = np.array(traces_data).T  # Transpose menjadi (sampel, jumlah trace)
            time_axis = np.arange(samples_per_trace) * sample_interval

            # Buat plot
            fig_trace, ax_trace = plt.subplots(figsize=(12, 8))

            if view_mode == "Densitas Variabel (Wiggle + Warna)":
                # Plot densitas (warna)
                extent = [trace_start, trace_end, time_axis[-1], time_axis[0]]
                im = ax_trace.imshow(traces_array, aspect='auto', cmap='seismic', extent=extent)
                plt.colorbar(im, ax=ax_trace, label='Amplitudo')
                ax_trace.set_xlabel("Indeks Trace")
                ax_trace.set_ylabel("Waktu (detik)")
                ax_trace.set_title("Densitas Variabel + Wiggle")
                # Overlay wiggle
                for i in range(traces_array.shape[1]):
                    trace_idx = trace_start + i
                    trace = traces_array[:, i]
                    if np.max(np.abs(trace)) > 0:
                        trace_norm = trace / np.max(np.abs(trace)) * 0.8
                    else:
                        trace_norm = trace
                    ax_trace.plot(trace_idx + trace_norm, time_axis, 'k-', linewidth=0.5, alpha=0.6)

            elif view_mode == "Wiggle (Gelombang)":
                for i in range(traces_array.shape[1]):
                    trace_idx = trace_start + i
                    trace = traces_array[:, i]
                    if np.max(np.abs(trace)) > 0:
                        trace_norm = trace / np.max(np.abs(trace)) * 0.8
                    else:
                        trace_norm = trace
                    ax_trace.plot(trace_idx + trace_norm, time_axis, 'k-', linewidth=0.8)
                    # Arsir bagian positif
                    ax_trace.fill_betweenx(time_axis, trace_idx, trace_idx + trace_norm,
                                           where=(trace_norm > 0), color='black', alpha=0.3)

                ax_trace.set_xlabel("Indeks Trace")
                ax_trace.set_ylabel("Waktu (detik)")
                ax_trace.set_title("Wiggle (Gelombang)")
                ax_trace.invert_yaxis()

            else:  # Variable Area
                for i in range(traces_array.shape[1]):
                    trace_idx = trace_start + i
                    trace = traces_array[:, i]
                    if np.max(np.abs(trace)) > 0:
                        trace_norm = trace / np.max(np.abs(trace)) * 0.8
                    else:
                        trace_norm = trace
                    ax_trace.plot(trace_idx + trace_norm, time_axis, 'k-', linewidth=0.8)
                    # Arsir area positif
                    ax_trace.fill_betweenx(time_axis, trace_idx, trace_idx + trace_norm,
                                           where=(trace_norm > 0), color='black', alpha=0.5)

                ax_trace.set_xlabel("Indeks Trace")
                ax_trace.set_ylabel("Waktu (detik)")
                ax_trace.set_title("Variable Area (Area Variabel)")
                ax_trace.invert_yaxis()

            st.pyplot(fig_trace)

            # --- 6. Lihat Trace Tunggal ---
            st.subheader("🔍 Lihat Trace Tunggal")

            trace_idx_single = st.slider("Pilih trace yang ingin dilihat:", 0, trace_count - 1, 0)

            fig_single, ax_single = plt.subplots(figsize=(10, 6))
            single_trace = segyfile.trace[trace_idx_single]
            time_axis_single = np.arange(len(single_trace)) * sample_interval

            ax_single.plot(single_trace, time_axis_single, 'b-', linewidth=1.5)
            ax_single.fill_betweenx(time_axis_single, 0, single_trace,
                                    where=(single_trace > 0), color='blue', alpha=0.3)
            ax_single.fill_betweenx(time_axis_single, 0, single_trace,
                                    where=(single_trace < 0), color='red', alpha=0.3)
            ax_single.set_xlabel("Amplitudo")
            ax_single.set_ylabel("Waktu (detik)")
            ax_single.set_title(f"Bentuk Gelombang Trace ke-{trace_idx_single}")
            ax_single.invert_yaxis()
            ax_single.grid(True, alpha=0.3)
            st.pyplot(fig_single)

            # --- 7. Visualisasi 3D Interaktif ---
            st.subheader("🌐 Visualisasi 3D (Plotly)")

            # Pilih rentang trace untuk 3D
            trace_start_3d, trace_end_3d = st.slider(
                "Pilih rentang trace untuk 3D:",
                min_value=0,
                max_value=trace_count - 1,
                value=(0, min(trace_count - 1, 100)),
                key="3d_slider"
            )

            # Baca data
            traces_3d = []
            for i in range(trace_start_3d, trace_end_3d + 1):
                traces_3d.append(segyfile.trace[i])
            traces_3d_array = np.array(traces_3d).T

            # Buat grid
            trace_indices_3d = np.arange(trace_start_3d, trace_end_3d + 1)
            time_indices_3d = np.arange(samples_per_trace) * sample_interval

            # Plot 3D dengan Plotly
            fig_3d = go.Figure(data=[go.Surface(
                z=traces_3d_array,
                x=trace_indices_3d,
                y=time_indices_3d,
                colorscale='RdBu',
                showscale=True,
                colorbar=dict(title="Amplitudo")
            )])

            fig_3d.update_layout(
                title="Tampilan 3D Data Seismik",
                scene=dict(
                    xaxis_title="Indeks Trace",
                    yaxis_title="Waktu (detik)",
                    zaxis_title="Amplitudo",
                    camera=dict(
                        eye=dict(x=1.5, y=1.5, z=0.8)
                    )
                ),
                width=900,
                height=600
            )

            st.plotly_chart(fig_3d, use_container_width=True)

            st.info("💡 **Tips**: Pada tampilan 3D, Anda bisa menggeser, memutar, dan memperbesar/zoom menggunakan mouse.")

            # --- 8. Ekspor Data ---
            st.subheader("💾 Ekspor Data")
            export_format = st.selectbox("Pilih format ekspor:", ["CSV (Header Trace)", "NumPy (Data Seismik)"])

            if export_format == "CSV (Header Trace)":
                # Ekspor semua header trace ke CSV
                all_headers = []
                for trace_idx in range(trace_count):
                    row = {"Indeks Trace": trace_idx}
                    for key, desc in header_fields.items():
                        try:
                            row[desc] = segyfile.header[trace_idx][key]
                        except:
                            row[desc] = "Tidak tersedia"
                    all_headers.append(row)
                df_export = pd.DataFrame(all_headers)

                csv = df_export.to_csv(index=False)
                st.download_button(
                    label="📥 Unduh Header CSV",
                    data=csv,
                    file_name="segy_headers.csv",
                    mime="text/csv"
                )
            else:
                # Ekspor semua data seismik ke NumPy
                all_traces = []
                for i in range(trace_count):
                    all_traces.append(segyfile.trace[i])
                data_array = np.array(all_traces)

                buffer = io.BytesIO()
                np.save(buffer, data_array)
                buffer.seek(0)

                st.download_button(
                    label="📥 Unduh Data Seismik (.npy)",
                    data=buffer,
                    file_name="seismic_data.npy",
                    mime="application/octet-stream"
                )

    except Exception as e:
        st.error(f"❌ Gagal memuat berkas SEG-Y: {e}")
        st.info("Pastikan file yang diunggah adalah format SEG-Y yang valid.")

else:
    st.info("👆 Silakan unggah berkas SEG-Y untuk memulai.")
    st.markdown("""
    ### Fitur yang tersedia
    - ✅ Menampilkan Header Teks dan Header Biner secara lengkap
    - ✅ Menampilkan Header Trace (CDP, koordinat, inline, dll.)
    - ✅ Plot Lintasan (mendukung koordinat CDP)
    - ✅ Tampilan Trace Seismik (Densitas Variabel, Wiggle, Variable Area)
    - ✅ Lihat Trace Tunggal
    - ✅ Visualisasi 3D interaktif (bisa diputar-putar)
    - ✅ Ekspor data ke CSV atau NumPy
    """)
