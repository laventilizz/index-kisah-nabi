import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Indeks Tematik Kisah 25 Nabi", layout="wide")

DEFAULT_INDEX_PATH = "Indeks_Kisah_25_Nabi.xlsx"
DEFAULT_EVAL_PATH = "indeks_kisah_nabi_cluster_klasifikasi.xlsx"

st.sidebar.title("Indeks Kisah 25 Nabi")
#uploaded_index = st.sidebar.file_uploader("Unggah file indeks final (.xlsx)", type=["xlsx"])
#uploaded_eval = st.sidebar.file_uploader("Unggah file evaluasi model (.xlsx, opsional)", type=["xlsx"])

@st.cache_data
def load_index(source):
    detail = pd.read_excel(source, sheet_name="Indeks_Lengkap")
    summary = pd.read_excel(source, sheet_name="Ringkasan_Per_Nabi")
    return detail, summary

@st.cache_data
def load_eval(source):
    sheets = pd.read_excel(source, sheet_name=None)
    return sheets

# Pemuatan file langsung (tanpa uploader sidebar)
try:
    detail_df, summary_df = load_index(DEFAULT_INDEX_PATH)
except FileNotFoundError:
    st.error(f"File {DEFAULT_INDEX_PATH} tidak ditemukan di direktori kerja.")
    st.stop()

try:
    eval_sheets = load_eval(DEFAULT_EVAL_PATH)
except FileNotFoundError:
    eval_sheets = None

TEXT_COL_CANDIDATES = ["Teks_Ayat", "Teks_Konteks"]

def resolve_text_column(df):
    for col in TEXT_COL_CANDIDATES:
        if col in df.columns:
            return col
    return None

def render_wrapped_table(df, max_height=600):
    st.markdown(
        """
        <style>
        .wrapped-table-container {
            max-height: MAXHEIGHTpx;
            overflow-y: auto;
            border: 1px solid rgba(128,128,128,0.3);
            border-radius: 8px;
        }
        .wrapped-table-container table { width: 100%; border-collapse: collapse; }
        .wrapped-table-container th, .wrapped-table-container td {
            white-space: normal;
            word-wrap: break-word;
            vertical-align: top;
            padding: 8px 10px;
            border-bottom: 1px solid rgba(128,128,128,0.2);
            text-align: left;
            font-size: 0.9rem;
        }
        .wrapped-table-container th {
            position: sticky;
            top: 0;
            background-color: rgba(30,30,30,0.97);
        }
        </style>
        """.replace("MAXHEIGHT", str(max_height)),
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="wrapped-table-container">{df.to_html(index=False, escape=True)}</div>',
        unsafe_allow_html=True,
    )

#index_source = resolve_source(uploaded_index, DEFAULT_INDEX_PATH)
#eval_source = resolve_source(uploaded_eval, DEFAULT_EVAL_PATH)

#if index_source is None:
#    st.warning("Unggah file indeks final (.xlsx) di sidebar untuk memulai.")
#    st.stop()

#detail_df, summary_df = load_index(index_source)
#eval_sheets = load_eval(eval_source) if eval_source is not None else None

st.sidebar.markdown("---")
nabi_options = summary_df.sort_values("Jumlah_Blok_Ayat", ascending=False)["Bab_Utama (Nabi)"].tolist()
selected_nabi = st.sidebar.multiselect("Bab Utama (Nabi)", nabi_options, default=nabi_options)

surah_options = sorted(detail_df["Surah"].unique())
selected_surah = st.sidebar.multiselect("Surah", surah_options, default=surah_options)

prob_min = float(detail_df["Probabilitas_Fuzzy (%)"].min())
prob_max = float(detail_df["Probabilitas_Fuzzy (%)"].max())
prob_range = st.sidebar.slider("Rentang probabilitas fuzzy (%)", 0.0, 100.0, (prob_min, prob_max))

search_query = st.sidebar.text_input("Cari kata dalam teks ayat")

filtered = detail_df[
    detail_df["Bab_Utama (Nabi)"].isin(selected_nabi)
    & detail_df["Surah"].isin(selected_surah)
]
if search_query:
    filtered = filtered[filtered["Teks_Ayat"].str.contains(search_query, case=False, na=False)]

st.title("Dashboard Indeks Tematik Kisah 25 Nabi")
st.caption("Hasil hybrid rule-based, clustering (BERTopic), klasifikasi, dan fuzzy multi-label untuk validasi pakar tafsir.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total baris (ayat-nabi)", len(filtered))
col2.metric("Jumlah ayat unik", filtered[["Surah", "Ayat"]].drop_duplicates().shape[0])
col3.metric("Jumlah nabi", filtered["Bab_Utama (Nabi)"].nunique())
col4.metric("Jumlah sub-kisah", filtered["Sub_Kisah (Klaster Mesin)"].nunique())

tab_names = ["Ringkasan", "Jelajah Ayat", "Detail per Ayat"]
if eval_sheets is not None:
    tab_names.append("Evaluasi Model")
tabs = st.tabs(tab_names)

with tabs[0]:
    st.subheader("Jumlah Blok Ayat per Nabi")
    count_per_nabi = filtered.groupby("Bab_Utama (Nabi)").size().reset_index(name="jumlah_ayat")
    fig_bar_nabi = px.bar(
        count_per_nabi.sort_values("jumlah_ayat", ascending=True),
        x="jumlah_ayat", y="Bab_Utama (Nabi)", orientation="h",
    )
    st.plotly_chart(fig_bar_nabi, use_container_width=True)

    st.subheader("Sub-Kisah Terbanyak")
    count_per_sub = filtered.groupby("Sub_Kisah (Klaster Mesin)").size().reset_index(name="jumlah_ayat")
    count_per_sub = count_per_sub.sort_values("jumlah_ayat", ascending=True).tail(15)
    fig_bar_sub = px.bar(count_per_sub, x="jumlah_ayat", y="Sub_Kisah (Klaster Mesin)", orientation="h")
    st.plotly_chart(fig_bar_sub, use_container_width=True)

    st.subheader("Distribusi Probabilitas Fuzzy")
    fig_hist = px.histogram(filtered, x="Probabilitas_Fuzzy (%)", nbins=30, color="Bab_Utama (Nabi)")
    st.plotly_chart(fig_hist, use_container_width=True)

with tabs[1]:
    st.subheader("Tabel Ayat (dapat difilter dan diunduh)")
    
    # 1. Tambahkan kotak pencarian interaktif di atas tabel
    keyword_tabel = st.text_input("🔍 Cari kata atau teks spesifik dalam tabel", "", key="search_tabel_ayat")
    
    display_cols = [
        "Surah", "Ayat", "Bab_Utama (Nabi)", "Sub_Kisah (Klaster Mesin)",
        "Probabilitas_Fuzzy (%)", "Teks_Ayat", "Teks_Konteks",
    ]
    
    # 2. Filter data berdasarkan kotak pencarian tabel
    df_tabel = filtered[display_cols].copy()
    if keyword_tabel:
        def norm(s):
            import re
            return re.sub(r'[\W_]+', '', str(s)).lower()
        
        q_norm = norm(keyword_tabel)
        mask = (
            df_tabel["Surah"].apply(norm).str.contains(q_norm, na=False) |
            df_tabel["Bab_Utama (Nabi)"].apply(norm).str.contains(q_norm, na=False) |
            df_tabel["Sub_Kisah (Klaster Mesin)"].apply(norm).str.contains(q_norm, na=False) |
            df_tabel["Teks_Ayat"].apply(norm).str.contains(q_norm, na=False) |
            df_tabel["Teks_Konteks"].apply(norm).str.contains(q_norm, na=False)
        )
        df_tabel = df_tabel[mask]

    df_sorted = df_tabel.sort_values(
        ["Surah", "Ayat", "Probabilitas_Fuzzy (%)"], ascending=[True, True, False]
    )
    
    # 3. Tampilkan menggunakan render_wrapped_table agar wrap text sempurna ala Excel
    render_wrapped_table(df_sorted, max_height=600)
    
    # 4. Tombol unduh CSV
    csv_data = df_sorted.to_csv(index=False).encode("utf-8")
    st.download_button("Unduh hasil filter (CSV)", data=csv_data, file_name="hasil_filter_indeks_nabi.csv", mime="text/csv")

with tabs[2]:
    st.subheader("Lihat Semua Bab Nabi untuk Satu Ayat")
    
    # Fitur search ayat di atas dropdown
    search_ayat_box = st.text_input("Cari ayat (ketik nama surah, nomor ayat, atau kata kunci dalam teks)", "", key="search_ayat_detail")
    
    # 1. Sertakan "Teks_Konteks" di sini
    ayat_keys = filtered[["Surah", "Ayat", "Teks_Ayat", "Teks_Konteks"]].drop_duplicates().copy()
    ayat_keys["label"] = ayat_keys["Surah"] + " : Ayat " + ayat_keys["Ayat"].astype(str) + " (" + ayat_keys["Teks_Ayat"].str[:60] + "...)"
    
    if search_ayat_box:
        # Menggunakan pencarian yang aman dan natural (tanpa menghapus spasi)
        mask = (
            ayat_keys["Surah"].astype(str).str.contains(search_ayat_box, case=False, na=False) |
            ayat_keys["Ayat"].astype(str).str.contains(search_ayat_box, case=False, na=False) |
            ayat_keys["Teks_Ayat"].astype(str).str.contains(search_ayat_box, case=False, na=False) |
            ayat_keys["Teks_Konteks"].astype(str).str.contains(search_ayat_box, case=False, na=False)
        )
        ayat_keys_filtered = ayat_keys[mask]
    else:
        ayat_keys_filtered = ayat_keys
        
    if len(ayat_keys_filtered) == 0:
        st.warning("Tidak ada ayat yang cocok dengan kata kunci pencarian.")
        selected_label = None
    else:
        selected_label = st.selectbox("Pilih ayat", ayat_keys_filtered.sort_values(["Surah", "Ayat"])["label"])
        
    if selected_label:
        parts = selected_label.split(" : Ayat ")
        selected_surah_val = parts[0]
        selected_ayat_val = int(parts[1].split(" (")[0])

        ayat_detail = detail_df[
            (detail_df["Surah"] == selected_surah_val) & (detail_df["Ayat"] == selected_ayat_val)
        ].sort_values("Probabilitas_Fuzzy (%)", ascending=False)

        # 2. Tampilkan Teks Ayat dan Teks Konteks secara berurutan di bawah
        st.markdown(f"**Teks Ayat:** {ayat_detail.iloc[0]['Teks_Ayat']}")
        
        # Menampilkan teks konteks dengan sedikit gaya agar lebih rapi
        st.markdown(f"**Teks Konteks (Blok Ayat):** {ayat_detail.iloc[0]['Teks_Konteks']}")
        
        st.markdown("---")

        fig_donut = px.pie(ayat_detail, values="Probabilitas_Fuzzy (%)", names="Sub_Kisah (Klaster Mesin)", hole=0.45)
        st.plotly_chart(fig_donut, use_container_width=True)

        st.table(
            ayat_detail[["Bab_Utama (Nabi)", "Sub_Kisah (Klaster Mesin)", "Probabilitas_Fuzzy (%)"]].rename(
                columns={"Probabilitas_Fuzzy (%)": "Probabilitas (%)"}
            )
        )

if eval_sheets is not None:
    with tabs[3]:
        st.subheader("Evaluasi Clustering")
        if "Evaluasi_Klaster" in eval_sheets:
            cluster_eval = eval_sheets["Evaluasi_Klaster"].iloc[0]
            ecol1, ecol2, ecol3 = st.columns(3)
            ecol1.metric("Jumlah Topik", int(cluster_eval["jumlah_topik"]))
            ecol2.metric("Proporsi Outlier", f"{cluster_eval['proporsi_outlier'] * 100:.2f}%")
            ecol3.metric("Silhouette Score", f"{cluster_eval['silhouette_score']:.4f}")

        st.subheader("Evaluasi Klasifikasi (Ringkasan)")
        if "Evaluasi_Ringkasan" in eval_sheets:
            st.dataframe(eval_sheets["Evaluasi_Ringkasan"], use_container_width=True)

        st.subheader("Precision / Recall / F1 per Nabi")
        if "Evaluasi_Per_Nabi" in eval_sheets:
            per_nabi = eval_sheets["Evaluasi_Per_Nabi"].sort_values("f1_score", ascending=True)
            fig_f1 = px.bar(per_nabi, x="f1_score", y="nabi", orientation="h", title="F1-Score per Nabi")
            st.plotly_chart(fig_f1, use_container_width=True)
            st.dataframe(eval_sheets["Evaluasi_Per_Nabi"], use_container_width=True)

        st.subheader("Confusion Matrix per Nabi")
        if "Confusion_Per_Nabi" in eval_sheets:
            st.dataframe(eval_sheets["Confusion_Per_Nabi"], use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption("Sumber: hasil hybrid rule-based, BERTopic, klasifikasi, dan Fuzzy C-Means")