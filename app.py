import io
import math
from pathlib import Path
from typing import List, Tuple
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go


st.set_page_config(page_title="FCT – TKPI + AKG", page_icon="🥗", layout="wide")

# =========================
# ---------- Utils --------
# =========================
def norm(s: str) -> str:
    return str(s).strip().upper()

def grams_from(value: float, unit: str) -> float:
    unit = (unit or "").lower().strip()
    if unit in ["g", "gram", "grams"]:
        return float(value)
    if unit in ["kg", "kilogram", "kilograms"]:
        return float(value) * 1000.0
    return float(value)

def excel_writer(bytes_buffer: io.BytesIO):
    """Prefer xlsxwriter; fallback ke openpyxl jika belum terinstal."""
    try:
        return pd.ExcelWriter(bytes_buffer, engine="xlsxwriter")
    except ModuleNotFoundError:
        return pd.ExcelWriter(bytes_buffer, engine="openpyxl")

@st.cache_data
def load_tkpi_any(file_or_path, sheet_name=None) -> pd.DataFrame:
    """
    Terima UploadedFile/BytesIO atau Path/str.
    Support XLSX (via ExcelFile) dan CSV (via read_csv).
    """
    if hasattr(file_or_path, "read"):  # UploadedFile (BytesIO-like)
        name = getattr(file_or_path, "name", "").lower()
        if name.endswith(".csv"):
            df = pd.read_csv(file_or_path)
        else:
            xls = pd.ExcelFile(file_or_path)
            s = sheet_name or xls.sheet_names[0]
            df = xls.parse(s)
    else:
        path = Path(file_or_path)
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path)
        else:
            xls = pd.ExcelFile(path)
            s = sheet_name or xls.sheet_names[0]
            df = xls.parse(s)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def get_yield(yield_df: pd.DataFrame, method: str) -> float:
    if yield_df.empty: return 1.0
    sub = yield_df[yield_df["Metode"].str.upper()==norm(method)]
    return float(sub["Yield"].iloc[0]) if len(sub) else 1.0

def get_retention(ret_df: pd.DataFrame, method: str, nutrient_key_upper: str) -> float:
    """nutrient_key_upper contoh: PROTEIN, SERAT, VIT_C, VIT A RE, VIT RAE, dst."""
    if ret_df.empty: return 1.0
    m = norm(method)
    nk = nutrient_key_upper
    sub = ret_df[(ret_df["Metode"].str.upper()==m) & (ret_df["Nutrien"].str.upper()==nk)]
    if len(sub): return float(sub["Retensi"].iloc[0])
    sub = ret_df[(ret_df["Metode"].str.upper()==m) & (ret_df["Nutrien"].str.upper()=="ALL")]
    if len(sub): return float(sub["Retensi"].iloc[0])
    return 1.0

def tkpi_value(row: pd.Series, col: str) -> float:
    if col in row.index:
        return float(pd.to_numeric(row[col], errors="coerce"))
    return math.nan

def default_yield_table() -> pd.DataFrame:
    return pd.DataFrame([
        {"Metode":"segar","Yield":1.0},
        {"Metode":"direbus","Yield":1.0},
        {"Metode":"tumis","Yield":0.90},
        {"Metode":"digoreng","Yield":0.85},
        {"Metode":"panggang","Yield":0.85},
    ])

def default_retention_table() -> pd.DataFrame:
    return pd.DataFrame([
        {"Metode":"segar","Nutrien":"ALL","Retensi":1.0},

        {"Metode":"direbus","Nutrien":"PROTEIN","Retensi":0.98},
        {"Metode":"direbus","Nutrien":"SERAT","Retensi":0.95},
        {"Metode":"direbus","Nutrien":"VIT_C","Retensi":0.60},
        {"Metode":"direbus","Nutrien":"VIT A RE","Retensi":0.90},
        {"Metode":"direbus","Nutrien":"VIT RAE","Retensi":0.90},
        {"Metode":"direbus","Nutrien":"KALIUM","Retensi":0.90},
        {"Metode":"direbus","Nutrien":"KALSIUM","Retensi":0.98},
        {"Metode":"direbus","Nutrien":"BESI","Retensi":0.98},
        {"Metode":"direbus","Nutrien":"SENG","Retensi":0.98},

        {"Metode":"tumis","Nutrien":"PROTEIN","Retensi":0.97},
        {"Metode":"tumis","Nutrien":"SERAT","Retensi":0.95},
        {"Metode":"tumis","Nutrien":"VIT_C","Retensi":0.70},
        {"Metode":"tumis","Nutrien":"VIT A RE","Retensi":0.90},
        {"Metode":"tumis","Nutrien":"VIT RAE","Retensi":0.90},
        {"Metode":"tumis","Nutrien":"KALIUM","Retensi":0.95},

        {"Metode":"digoreng","Nutrien":"PROTEIN","Retensi":0.95},
        {"Metode":"digoreng","Nutrien":"SERAT","Retensi":0.90},
        {"Metode":"digoreng","Nutrien":"VIT_C","Retensi":0.65},
        {"Metode":"digoreng","Nutrien":"VIT A RE","Retensi":0.85},
        {"Metode":"digoreng","Nutrien":"VIT RAE","Retensi":0.85},

        {"Metode":"panggang","Nutrien":"PROTEIN","Retensi":0.97},
        {"Metode":"panggang","Nutrien":"SERAT","Retensi":0.95},
        {"Metode":"panggang","Nutrien":"VIT_C","Retensi":0.70},
        {"Metode":"panggang","Nutrien":"VIT A RE","Retensi":0.88},
        {"Metode":"panggang","Nutrien":"VIT RAE","Retensi":0.88},
    ])

# ===== AKG REFERENCE & HELPERS =====
AKG_GROUPS = [
    {"Kelompok": "Anak 7–9 th",           "JK":"NA","Energi":1650,"Protein":40,"Lemak_total":55,"Omega3":0.9,"Omega6":10,"Karbohidrat":250,"Serat":23,"Air":1650},
    {"Kelompok": "Laki-laki 10–12 th",    "JK":"L", "Energi":2000,"Protein":50,"Lemak_total":65,"Omega3":1.2,"Omega6":12,"Karbohidrat":300,"Serat":28,"Air":1850},
    {"Kelompok": "Laki-laki 13–15 th",    "JK":"L", "Energi":2400,"Protein":70,"Lemak_total":80,"Omega3":1.6,"Omega6":16,"Karbohidrat":350,"Serat":34,"Air":2100},
    {"Kelompok": "Laki-laki 16–18 th",    "JK":"L", "Energi":2650,"Protein":75,"Lemak_total":85,"Omega3":1.6,"Omega6":16,"Karbohidrat":400,"Serat":37,"Air":2300},
    {"Kelompok": "Perempuan 10–12 th",    "JK":"P", "Energi":1900,"Protein":55,"Lemak_total":65,"Omega3":1.0,"Omega6":10,"Karbohidrat":280,"Serat":27,"Air":1850},
    {"Kelompok": "Perempuan 13–15 th",    "JK":"P", "Energi":2050,"Protein":65,"Lemak_total":70,"Omega3":1.1,"Omega6":11,"Karbohidrat":300,"Serat":29,"Air":2100},
    {"Kelompok": "Perempuan 16–18 th",    "JK":"P", "Energi":2100,"Protein":65,"Lemak_total":70,"Omega3":1.1,"Omega6":11,"Karbohidrat":300,"Serat":29,"Air":2150},
]
AKG_COLS = ["Energi","Protein","Lemak_total","Omega3","Omega6","Karbohidrat","Serat","Air"]

def akg_ref_df():
    return pd.DataFrame(AKG_GROUPS)

def adequacy_pct(intake: pd.Series, akg_row: pd.Series) -> pd.Series:
    out = {}
    for c in AKG_COLS:
        tgt = float(akg_row[c])
        val = float(intake.get(c, float("nan")))
        out[c] = float("nan") if (pd.isna(val) or tgt==0) else (val/tgt*100.0)
    return pd.Series(out)

def compute_akg_all(intake: pd.Series, ref: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in ref.iterrows():
        pct = adequacy_pct(intake, r)
        rows.append({"Kelompok": r["Kelompok"], **{f"% {k}": v for k, v in pct.items()}})
    return pd.DataFrame(rows)

# =========================
# ---------- Sidebar ------
# =========================
st.sidebar.header("📦 Data TKPI")

tkpi_source = st.sidebar.radio(
    "Sumber TKPI",
    options=["Default (TKPI 2017)", "Upload (versi terbaru)"],
    index=0,
    help="Pilih 'Default' untuk memakai file TKPI 2017 yang ada di folder aplikasi. "
         "Pilih 'Upload' jika ingin memakai file TKPI versi terbaru milik Anda (XLSX/CSV)."
)

default_tkpi_path = Path.cwd() / "TKPI 2017.xlsx"
tkpi_sheet = st.sidebar.text_input("Nama Sheet TKPI (opsional)", value="")

tkpi_upload = None
if tkpi_source == "Upload (versi terbaru)":
    tkpi_upload = st.sidebar.file_uploader(
        "Upload file TKPI (XLSX/CSV)",
        type=["xlsx", "csv"],
        help="Unggah TKPI versi terbaru. Jika CSV, pastikan delimiter sesuai (default koma)."
    )

# Quick open help expander from sidebar
if st.sidebar.button("📘 Petunjuk & Metodologi"):
    st.session_state["show_help"] = True

st.sidebar.header("⚙️ Kolom TKPI (mapping)")
st.sidebar.caption(
    "Isi nama kolom persis seperti header di file TKPI Anda. "
    "Contoh: jika header Anda 'Energi (kkal)', isi kolom ENERGI dengan 'Energi (kkal)'. "
    "Jika 'Karbohidrat (g)', isi KH dengan 'Karbohidrat (g)'."
)
col_map = {
    "PGSPL": st.sidebar.text_input("PGSPL", value="PGSPL"),
    "KODE BARU": st.sidebar.text_input("KODE BARU", value="KODE BARU"),
    "NAMA BAHAN MENTAH": st.sidebar.text_input("NAMA BAHAN MENTAH", value="NAMA BAHAN MENTAH"),
    "SUMBER": st.sidebar.text_input("SUMBER", value="SUMBER"),
    "KELOMPOK": st.sidebar.text_input("KELOMPOK", value="KELOMPOK"),
    "ENERGI": st.sidebar.text_input("ENERGI", value="ENERGI"),
    "PROTEIN": st.sidebar.text_input("PROTEIN", value="PROTEIN"),
    "AIR": st.sidebar.text_input("AIR", value="AIR"),
    "LEMAK": st.sidebar.text_input("LEMAK", value="LEMAK"),
    "KH": st.sidebar.text_input("KH (Karbohidrat)", value="KH"),
    "KALSIUM": st.sidebar.text_input("KALSIUM", value="KALSIUM"),
    "BESI": st.sidebar.text_input("BESI (Zat Besi)", value="BESI"),
    "SENG": st.sidebar.text_input("SENG (Zink)", value="SENG"),
    "VIT_C": st.sidebar.text_input("VIT_C", value="VIT_C"),
    "THIAMIN": st.sidebar.text_input("THIAMIN (B1)", value="THIAMIN"),
    "RIBOFLAVIN": st.sidebar.text_input("RIBOFLAVIN (B2)", value="RIBOFLAVIN"),
    "NIASIN": st.sidebar.text_input("NIASIN (B3)", value="NIASIN"),
    "B6": st.sidebar.text_input("B6", value="B6"),
    "Folat": st.sidebar.text_input("Folat (B9)", value="Folat"),
    "B12": st.sidebar.text_input("B12", value="B12"),
    "Vit A RE": st.sidebar.text_input("Vit A RE", value="Vit A RE"),
    "Vit RAE": st.sidebar.text_input("Vit RAE", value="Vit RAE"),
    "RETINOL (RE)": st.sidebar.text_input("RETINOL (RE)", value="RETINOL (RE)"),
    "B-KAR (mcg)": st.sidebar.text_input("B-KAR (mcg)", value="B-KAR (mcg)"),
    "KARTOTAL (mcg)": st.sidebar.text_input("KARTOTAL (mcg)", value="KARTOTAL (mcg)"),
    "BDD": st.sidebar.text_input("BDD (%)", value="BDD"),
    "KALIUM": st.sidebar.text_input("KALIUM (opsional)", value="KALIUM"),
    "NATRIUM": st.sidebar.text_input("NATRIUM (opsional)", value="NATRIUM"),
}

if "yield_df" not in st.session_state:
    st.session_state.yield_df = default_yield_table()
if "ret_df" not in st.session_state:
    st.session_state.ret_df = default_retention_table()

st.sidebar.caption("Faktor Yield & Retensi (default, dapat diubah dari kode/CSV eksternal).")
st.sidebar.dataframe(st.session_state.yield_df, use_container_width=True)
st.sidebar.dataframe(st.session_state.ret_df.head(12), use_container_width=True)

# =========================
# ------- Load TKPI -------
# =========================
try:
    if tkpi_source == "Default (TKPI 2017)":
        if not default_tkpi_path.exists():
            st.error(f"File default tidak ditemukan: {default_tkpi_path}")
            st.stop()
        tkpi_df = load_tkpi_any(default_tkpi_path, sheet_name=(tkpi_sheet or None))
        st.caption(f"📘 TKPI sumber: Default 2017 → {default_tkpi_path.name}")
    else:
        if tkpi_upload is None:
            st.warning("Unggah TKPI versi terbaru (XLSX/CSV) di sidebar.")
            st.stop()
        tkpi_df = load_tkpi_any(tkpi_upload, sheet_name=(tkpi_sheet or None))
        st.caption(f"📘 TKPI sumber: Upload → {tkpi_upload.name}")
except Exception as e:
    st.error(f"Gagal memuat TKPI: {e}")
    st.stop()

name_col = col_map["NAMA BAHAN MENTAH"]
if name_col not in tkpi_df.columns:
    st.error(f"Kolom '{name_col}' tidak ada di TKPI. Sesuaikan mapping kolom di sidebar.")
    st.dataframe(tkpi_df.head(), use_container_width=True)
    st.stop()

ingredients_list = sorted(tkpi_df[name_col].dropna().astype(str).unique().tolist())

# =========================
# --------- UI Main -------
# =========================
st.title("🥗 Food Composition Tool (FCT) – TKPI 2017 + AKG")
st.caption("Hitung komposisi gizi per bahan & per menu (BDD, yield, retensi) dan evaluasi terhadap AKG.")

# Help expander (with blue background + LaTeX)
with st.expander("📘 Petunjuk & Metodologi (klik untuk lihat)", expanded=st.session_state.get("show_help", False)):
    # Header card (biru lembut)
    st.markdown(
        """
        <div style="
            background-color:#e8f3ff;
            padding:1.2rem 1.5rem;
            border-radius:0.6rem;
            border:1px solid #bcdfff;
            font-size:0.95rem;
            line-height:1.6;
        ">
        <b>Sumber data:</b> Tabel Komposisi Pangan Indonesia (TKPI) 2017.<br>
        Basis perhitungan menggunakan kandungan nutrien per 100 g <b>bagian dapat dimakan (BDD)</b>.
        </div>
        """,
        unsafe_allow_html=True
    )

    # Rumus inti (tetap seperti versi yang kamu suka)
    st.markdown("**Langkah koreksi untuk setiap bahan:**")
    st.markdown("**1️⃣ BDD (Edible Portion)**")
    st.latex(r"w_{\mathrm{edible}} = w_{\mathrm{input}} \times \frac{\mathrm{BDD}\,(\%)}{100}")

    st.markdown("**2️⃣ Yield (Perubahan berat setelah pemasakan)**")
    st.latex(r"w_{\mathrm{final}} = w_{\mathrm{edible}} \times \mathrm{Yield}\!\left(\text{metode}\right)")

    st.markdown("**3️⃣ Retensi Nutrien (Degradasi karena proses pemasakan)**")
    st.latex(r"N_{\mathrm{akhir}} = \left(\frac{N_{100}}{100}\right) \times w_{\mathrm{final}} \times \mathrm{Retensi}_{N}\!\left(\text{metode}\right)")

    st.markdown("**4️⃣ Agregasi per Menu**")
    st.latex(r"N_{\mathrm{menu}} = \sum_{i=1}^{k} N_{\mathrm{akhir},\,i}")

    # Catatan ilmiah
    st.markdown(
        """
        <div style="
            background-color:#f5faff;
            padding:0.8rem 1rem;
            border-left:4px solid #2c80ff;
            margin-top:0.8rem;
        ">
        <b>Catatan ilmiah:</b> Vitamin (Vit C, provitamin A) lebih labil terhadap panas/oksidasi dibanding mineral atau makronutrien.
        Faktor <i>yield</i> dan <i>retensi</i> dapat disesuaikan menurut tabel referensi (USDA Retention Factors, FNDDS Cooking Yields, FAO/INFOODS).
        </div>
        """,
        unsafe_allow_html=True
    )

    # Garis pemisah
    st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:1rem 0;'>", unsafe_allow_html=True)

    # 🧭 Alur pengisian (step-by-step)
    st.markdown(
        """
### 🧭 Alur Pengisian Aplikasi (Step-by-step)
1. **Pilih database TKPI**  
   - Pakai **TKPI 2017** (default), atau unggah file **XLSX/CSV** versi terbaru.  
   - Jika header file berbeda, buka **⚙️ Kolom TKPI (Mapping)** dan samakan nama kolom.
2. **Tambahkan Menu** *(misal: “Capcay”)*.
3. **Tambah Bahan ke Menu**  
   - Cari bahan dari basis TKPI → tentukan **berat** (g atau kg) → pilih **metode masak** (segar/rebus/tumis/goreng/dst).  
   - Sistem menghitung **BDD → Yield → Retensi**, menghasilkan **Per Bahan** & **Per Menu**.
4. **Tinjau Hasil**  
   - Tabel **Per Bahan** untuk jejak perhitungan; **Per Menu** untuk total akhir per porsi/menu.
5. **Analisis AKG**  
   - Pilih **Dari Per Menu** (default: **menjumlah semua menu** kalau tidak dipilih apa pun) atau **Input manual**.  
   - Lihat **% Pencapaian AKG** + grafik **Bar** & **Radar**.
6. **Unduh Excel**  
   - Berisi: input mentah, Per Bahan, Per Menu, faktor yield/retensi, referensi AKG, asupan, dan pencapaian AKG.

**Referensi**: TKPI 2017 (Kemenkes RI); USDA *Table of Nutrient Retention Factors*; USDA FNDDS *Cooking Yields*; FAO/INFOODS guidelines.
        """
    )


# Inisialisasi state
if "menus" not in st.session_state:
    st.session_state.menus = []
if "rows" not in st.session_state:
    st.session_state.rows = []  # list of dict: {Nama Menu, Bahan, Berat Input, Unit, Metode}

# ---------- Reset ----------
st.subheader("0) Reset Data")
if st.button("🧹 Reset semua menu & bahan"):
    st.session_state.menus = []
    st.session_state.rows = []
    st.success("Semua data di-reset.")

# ---------- Menu CRUD ----------
st.subheader("1) Kelola Menu")

left, right = st.columns([2, 2])

# ➕ Tambah menu (tetap terlihat)
with left:
    new_menu = st.text_input("Tambah menu baru", placeholder="mis. Capcay, Korean Wings, dst.", key="add_menu_name")
    if st.button("➕ Tambah Menu", key="btn_add_menu"):
        if new_menu.strip():
            if new_menu.strip() not in st.session_state.menus:
                st.session_state.menus.append(new_menu.strip())
                st.success(f"Menu ditambahkan: {new_menu}")
            else:
                st.warning("Menu sudah ada.")
        else:
            st.warning("Nama menu tidak boleh kosong.")

# ✏️🗑️ Edit/Hapus menu → disembunyikan dalam expander
with right:
    with st.expander("✏️ / 🗑️ Edit & Hapus Menu", expanded=False):
        if st.session_state.menus:
            sel_menu_manage = st.selectbox(
                "Pilih menu untuk Edit/Hapus",
                st.session_state.menus,
                key="sel_menu_manage"
            )
            new_name = st.text_input("Rename menu", value=sel_menu_manage, key="rename_menu_name")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✏️ Simpan Rename", key="btn_save_rename"):
                    old = sel_menu_manage
                    new = new_name.strip()
                    if new and new != old:
                        st.session_state.menus = [new if m == old else m for m in st.session_state.menus]
                        for r in st.session_state.rows:
                            if r["Nama Menu"] == old:
                                r["Nama Menu"] = new
                        st.success(f"Menu '{old}' diubah menjadi '{new}'.")
                    else:
                        st.info("Tidak ada perubahan nama.")
            with c2:
                if st.button("🗑️ Hapus Menu", key="btn_delete_menu"):
                    to_del = sel_menu_manage
                    st.session_state.menus = [m for m in st.session_state.menus if m != to_del]
                    st.session_state.rows = [r for r in st.session_state.rows if r["Nama Menu"] != to_del]
                    st.success(f"Menu '{to_del}' dihapus.")
        else:
            st.info("Belum ada menu. Tambahkan menu baru terlebih dahulu.")

if not st.session_state.menus:
    st.stop()


# ---------- Add Bahan ----------
st.subheader("2) Tambahkan Bahan ke Menu")
c1, c2, c3, c4, c5 = st.columns([2,3,2,2,2])
with c1:
    sel_menu = st.selectbox("Pilih Menu", st.session_state.menus, key="sel_menu_add")
with c2:
    sel_ing = st.selectbox("Pilih Bahan (TKPI)", ingredients_list, key="sel_ing_add")
with c3:
    w_val = st.number_input("Berat", min_value=0.0, value=100.0, step=10.0)
with c4:
    unit = st.selectbox("Unit", ["g","kg"], index=0)
with c5:
    method = st.selectbox("Metode Masak", ["segar","direbus","tumis","digoreng","panggang"], index=0)

if st.button("➕ Tambah Bahan ke Menu"):
    st.session_state.rows.append({
        "Nama Menu": sel_menu,
        "Bahan": sel_ing,
        "Berat Input": w_val,
        "Unit": unit,
        "Metode": method
    })
    st.success(f"Ditambahkan: {sel_ing} ({w_val}{unit}) ke {sel_menu}")

# ---------- Tabel Bahan + Edit/Delete ----------
st.subheader("3) Tabel Bahan per Menu")

if st.session_state.rows:
    df_input = pd.DataFrame(st.session_state.rows)
    st.dataframe(df_input, use_container_width=True)

    # ✏️🗑️ Edit/Hapus baris bahan → expander agar tidak memenuhi layar
    with st.expander("✏️ / 🗑️ Edit & Hapus Baris Bahan", expanded=False):
        # Lebih ramah: pilih baris via selectbox berlabel (idx — menu — bahan)
        options = [f"{i} — {r['Nama Menu']} — {r['Bahan']}" for i, r in df_input.iterrows()]
        sel_label = st.selectbox(
            "Pilih baris untuk Edit/Hapus",
            options,
            key="sel_row_edit"
        )
        sel_idx = int(sel_label.split(" — ")[0])
        row_cur = df_input.iloc[sel_idx]

        ec1, ec2, ec3, ec4, ec5 = st.columns([2, 3, 2, 2, 2])
        with ec1:
            e_menu = st.selectbox(
                "Menu (edit)",
                st.session_state.menus,
                index=st.session_state.menus.index(row_cur["Nama Menu"]),
                key="edit_menu_select"
            )
        with ec2:
            e_ing = st.selectbox(
                "Bahan (edit)",
                ingredients_list,
                index=ingredients_list.index(row_cur["Bahan"]),
                key="edit_ing_select"
            )
        with ec3:
            e_w = st.number_input(
                "Berat (edit)",
                min_value=0.0,
                value=float(row_cur["Berat Input"]),
                step=10.0,
                key="edit_weight_input"
            )
        with ec4:
            e_unit = st.selectbox(
                "Unit (edit)",
                ["g", "kg"],
                index=["g", "kg"].index(row_cur["Unit"]),
                key="edit_unit_select"
            )
        with ec5:
            e_method = st.selectbox(
                "Metode (edit)",
                ["segar", "direbus", "tumis", "digoreng", "panggang"],
                index=["segar", "direbus", "tumis", "digoreng", "panggang"].index(row_cur["Metode"]),
                key="edit_method_select"
            )

        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("💾 Simpan Perubahan", key="btn_save_row"):
                st.session_state.rows[sel_idx] = {
                    "Nama Menu": e_menu,
                    "Bahan": e_ing,
                    "Berat Input": e_w,
                    "Unit": e_unit,
                    "Metode": e_method
                }
                st.success("Baris diperbarui.")
        with cc2:
            if st.button("🗑️ Hapus Baris", key="btn_delete_row"):
                del st.session_state.rows[sel_idx]
                st.success("Baris dihapus.")
else:
    st.info("Belum ada bahan. Tambahkan bahan terlebih dahulu.")
    st.stop()


# ---------- Perhitungan ----------
st.subheader("4) Hitung Komposisi (Per Bahan & Per Menu)")
tkpi_idx = tkpi_df.set_index(name_col)

candidate_keys = [
    "ENERGI","PROTEIN","LEMAK","KH","AIR","VIT_C",
    "KALSIUM","BESI","SENG",
    "THIAMIN","RIBOFLAVIN","NIASIN","B6","Folat","B12",
    "Vit A RE","Vit RAE","RETINOL (RE)","B-KAR (mcg)","KARTOTAL (mcg)",
    "KALIUM","NATRIUM"
]
available_nutrients: List[Tuple[str,str]] = []
for key in candidate_keys:
    col = col_map.get(key)
    if col and col in tkpi_df.columns:
        available_nutrients.append((key, col))

calc_rows = []
yield_df = st.session_state.yield_df
ret_df = st.session_state.ret_df

for r in st.session_state.rows:
    menu  = r["Nama Menu"]
    bahan = r["Bahan"]
    unit  = r["Unit"]
    w_in  = grams_from(r["Berat Input"], unit)
    method = r["Metode"]

    if bahan in tkpi_idx.index:
        tk = tkpi_idx.loc[bahan]
    else:
        st.warning(f"Bahan tidak ditemukan di TKPI: {bahan}")
        continue

    bdd_col = col_map["BDD"]
    bdd_val = tkpi_value(tk, bdd_col) if bdd_col in tkpi_df.columns else 100.0
    if math.isnan(bdd_val): bdd_val = 100.0

    w_edible = w_in * (bdd_val/100.0)
    y = get_yield(yield_df, method)
    w_final = w_edible * y

    out = {
        "Nama Menu": menu, "Bahan": bahan, "Metode": method,
        "Berat Input (g)": w_in, "BDD (%)": bdd_val, "Berat Edible (g)": w_edible,
        "Yield": y, "Berat Akhir (g)": w_final
    }
    for key, col in available_nutrients:
        per100 = tkpi_value(tk, col)
        if math.isnan(per100):
            out[key] = math.nan
            continue
        base = (per100/100.0) * w_final
        rf = get_retention(ret_df, method, norm(key))
        out[key] = base * rf
    calc_rows.append(out)

df_per_bahan = pd.DataFrame(calc_rows)
if df_per_bahan.empty:
    st.warning("Tidak ada hasil perhitungan. Pastikan bahan cocok dan mapping kolom TKPI benar.")
    st.stop()

nutr_cols_present = [c for c in df_per_bahan.columns if c not in
                     ["Nama Menu","Bahan","Metode","Berat Input (g)","BDD (%)","Berat Edible (g)","Yield","Berat Akhir (g)"]]
df_per_menu = df_per_bahan.groupby("Nama Menu")[nutr_cols_present].sum(numeric_only=True).reset_index()

st.success("✅ Perhitungan selesai.")
st.write("**Per Bahan**")
st.dataframe(df_per_bahan, use_container_width=True)
st.write("**Per Menu**")
st.dataframe(df_per_menu, use_container_width=True)

# ---------- Analisis AKG ----------
st.subheader("5) Analisis AKG (Angka Kecukupan Gizi)")

ref_akg = akg_ref_df()

mode_akg = st.radio("Sumber asupan harian", ["Dari Per Menu", "Input manual"], horizontal=True)

# asupan default
asupan = {"Energi":2000,"Protein":65,"Lemak_total":70,"Omega3":1.2,"Omega6":12,"Karbohidrat":300,"Serat":28,"Air":1800}

if mode_akg == "Dari Per Menu":
    if df_per_menu.empty:
        st.info("Per Menu kosong. Gunakan 'Input manual' atau tambahkan bahan dulu.")
    else:
        st.caption("Pilih satu atau beberapa menu untuk dijumlahkan sebagai asupan harian.")
        selected = st.multiselect("Pilih menu", df_per_menu["Nama Menu"].tolist())

        # === pilih dataframe sumber ===
        if selected:
            sel_df = df_per_menu[df_per_menu["Nama Menu"].isin(selected)].copy()
        else:
            sel_df = df_per_menu.copy()
            st.info("Belum ada menu dipilih → menggunakan **SEMUA menu** sebagai asupan harian.")

        # --- Normalisasi kolom (case-insensitive)
        lower_map = {c.lower(): c for c in sel_df.columns}

        # --- alias kolom utk pemetaan FCT -> variabel AKG
        aliases = {
            "Energi":      ["energi", "energi (kkal)", "energy", "kcal", "energi_total", "energi total", "energi (kcal)"],
            "Protein":     ["protein", "protein (g)", "protein_total", "protein total"],
            "Lemak_total": ["lemak_total", "lemak", "lemak (g)", "fat", "total fat"],
            "Omega3":      ["omega3", "omega 3", "n-3", "omega-3"],
            "Omega6":      ["omega6", "omega 6", "n-6", "omega-6"],
            "Karbohidrat": ["karbohidrat", "kh", "karbohidrat (g)", "carb", "carbohydrate"],
            "Serat":       ["serat", "serat (g)", "fiber", "dietary fiber", "fibre"],
            "Air":         ["air", "air (ml)", "air (g)", "water", "water (ml)", "water (g)"],
        }
        # alias spesifik versi huruf besar di tabelmu
        aliases["Energi"] += ["energi"]
        aliases["Protein"] += ["protein"]
        aliases["Lemak_total"] += ["lemak"]
        aliases["Karbohidrat"] += ["kh"]
        aliases["Air"] += ["air"]

        def sum_by_alias(df, alias_list):
            for a in alias_list:
                col = lower_map.get(a.lower())
                if col:
                    return pd.to_numeric(df[col], errors="coerce").sum()
            return float("nan")

        # isi asupan dari (semua/terpilih) menu
        filled_any = False
        for k in AKG_COLS:
            tot = sum_by_alias(sel_df, aliases[k])
            if not pd.isna(tot):
                asupan[k] = float(tot)
                filled_any = True

        # untuk nutrien yang tidak ada kolomnya (mis. Omega3/6), set 0 agar tabel rapi
        if filled_any:
            for k in AKG_COLS:
                if k not in asupan or (isinstance(asupan[k], float) and math.isnan(asupan[k])):
                    asupan[k] = 0.0

else:
    st.caption("Isi asupan manual (per orang per hari).")
    for k in AKG_COLS:
        step = 50.0 if k in ["Energi","Karbohidrat","Air"] else (5.0 if k in ["Protein","Lemak_total","Serat"] else 0.1)
        asupan[k] = st.number_input(k, min_value=0.0, value=float(asupan[k]), step=step)

st.write("**Asupan Harian yang Dinilai**")
st.dataframe(pd.DataFrame([asupan]), use_container_width=True)

df_akg_pct = compute_akg_all(pd.Series(asupan), ref_akg)
st.write("**Persentase Pencapaian AKG – Semua Kelompok**")
st.dataframe(df_akg_pct, use_container_width=True)

with st.expander("🔎 Insight singkat (otomatis)"):
    # contoh cek kelompok pertama (bisa diubah sesuai kebutuhan)
    ref_row = df_akg_pct.iloc[0]
    crit = [c for c in AKG_COLS if ref_row[f"% {c}"] < 90]
    if crit:
        st.markdown("- **Nutrien potensial kurang (<90%)**: " + ", ".join(crit))
    else:
        st.markdown("- Tidak ada nutrien <90% pada kelompok pertama (cek kelompok lain).")
    st.markdown("- Nilai >100% = melebihi AKG; interpretasi klinis kontekstual (energi/lemak vs kebutuhan individu).")

# Visualisasi (Plotly)
colA, colB = st.columns(2)

# --- BAR CHART (Plotly) ---
with colA:
    target_group = st.selectbox(
        "Grafik batang (interaktif): pilih kelompok",
        ref_akg["Kelompok"].tolist(),
        index=1
    )
    row = df_akg_pct[df_akg_pct["Kelompok"]==target_group].iloc[0]
    labels = [c.replace("% ","") for c in row.index if c.startswith("% ")]
    vals = [row[f"% {c}"] for c in labels]
    st.session_state["akg_target_group"] = target_group
    fig_bar = go.Figure()
    fig_bar.add_bar(x=labels, y=vals, name="Pencapaian (%)")
    # garis 100%
    fig_bar.add_hline(y=100, line_dash="dash", annotation_text="100% AKG", annotation_position="top left")

    ymax = max(120, float(pd.Series(vals).max())+10 if len(vals) else 120)
    fig_bar.update_layout(
        title=f"Pencapaian AKG per Nutrien – {target_group}",
        yaxis_title="Pencapaian (%)",
        xaxis_title="Nutrien",
        yaxis=dict(range=[0, ymax]),
        margin=dict(l=40,r=20,t=60,b=40),
        height=420
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# --- RADAR CHART (Plotly) ---
with colB:
    groups_default = ["Anak 7–9 th","Laki-laki 13–15 th","Perempuan 16–18 th"]
    groups = st.multiselect(
        "Radar chart (interaktif): pilih 1–5 kelompok",
        ref_akg["Kelompok"].tolist(),
        default=groups_default
    )
    if groups:
        features = AKG_COLS  # order tetap
        fig_rad = go.Figure()
        for g in groups:
            rw = df_akg_pct[df_akg_pct["Kelompok"]==g].iloc[0]
            vals = [rw[f"% {c}"] for c in features]
            fig_rad.add_trace(go.Scatterpolar(
                r=vals,
                theta=features,
                fill="toself",
                name=g
            ))
        fig_rad.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 140])),
            title="Radar Pencapaian AKG – Perbandingan Kelompok",
            margin=dict(l=40,r=20,t=60,b=40),
            height=480,
            legend=dict(orientation="h", y=-0.2)
        )
        st.plotly_chart(fig_rad, use_container_width=True)

# ===================== 5B) ANALISIS OTOMATIS (GAP & RINGKASAN) =====================

def _safe_get(sr, k, default=np.nan):
    try:
        return float(sr.get(k, default))
    except Exception:
        return default

def compute_gap_series(asupan_dict, akg_row):
    """
    Parameters
    ----------
    asupan_dict : dict -> {nutrien: nilai_asupan}
    akg_row     : pd.Series -> baris AKG rujukan utk 1 kelompok

    Returns
    -------
    df_gap : DataFrame kolom [Target, Asupan, Pencapaian(%), Gap(Asupan-Target)]
    """
    # hanya nutrien yang muncul di keduanya (asupan & AKG)
    keys = []
    for k in akg_row.index:
        if k.lower() in ["kelompok"]: 
            continue
        if (k in asupan_dict) or (k in asupan_dict.keys()) or (k in [*asupan_dict]):
            keys.append(k)

    rows = []
    for k in keys:
        tgt = _safe_get(akg_row, k, np.nan)
        val = _safe_get(asupan_dict, k, np.nan)
        if pd.isna(tgt) or tgt == 0:
            pct = np.nan
            gap = np.nan
        else:
            pct = (val / tgt) * 100.0
            gap = val - tgt
        rows.append({"Nutrien": k, "Target": tgt, "Asupan": val, "Pencapaian(%)": pct, "Gap": gap})
    df = pd.DataFrame(rows)
    return df

def narrate_gap(df_gap, kelompok_label):
    """
    Buat narasi otomatis berbasis aturan sederhana: defisit <90%, memadai 90–120%, surplus >120%.
    Prioritaskan makro terlebih dulu, lalu mikro (kalau ada pada AKG).
    """
    if df_gap.empty:
        return "Data AKG atau asupan tidak tersedia untuk dianalisis."

    # kategori
    def_status = lambda p: ("Defisit" if p < 90 else ("Memadai" if p <= 120 else "Surplus")) if pd.notna(p) else "NA"

    df = df_gap.copy()
    df["Status"] = df["Pencapaian(%)"].apply(def_status)

    # urutkan makro dulu
    preferred_order = ["Energi","Protein","Lemak_total","Omega3","Omega6","Karbohidrat","Serat","Air"]
    df["_ord"] = df["Nutrien"].apply(lambda x: preferred_order.index(x) if x in preferred_order else 999)
    df = df.sort_values(["_ord","Nutrien"]).drop(columns=["_ord"])

    # ringkasan per kategori
    def _pick(df, status):
        d = df[df["Status"]==status].copy()
        # sort: paling bermasalah di atas (persen terjauh dari 100)
        d["dev"] = (d["Pencapaian(%)"] - 100).abs()
        return d.sort_values("dev", ascending=False).drop(columns=["dev"])

    df_def = _pick(df, "Defisit")
    df_sur = _pick(df, "Surplus")
    df_ok  = _pick(df, "Memadai")

    lines = []
    lines.append(f"**Ringkasan otomatis – {kelompok_label}:**")
    if not df_def.empty:
        top = min(5, len(df_def))
        items = [f"{r.Nutrien}: {r['Pencapaian(%)']:.1f}% (−{abs(r.Gap):.2f} dari target)" for _, r in df_def.head(top).iterrows()]
        lines.append("• **Defisit** → " + "; ".join(items) + ".")
    if not df_sur.empty:
        top = min(5, len(df_sur))
        items = [f"{r.Nutrien}: {r['Pencapaian(%)']:.1f}% (+{r.Gap:.2f} di atas target)" for _, r in df_sur.head(top).iterrows()]
        lines.append("• **Surplus** → " + "; ".join(items) + ".")
    if not df_ok.empty:
        top = min(5, len(df_ok))
        items = [f"{r.Nutrien}: {r['Pencapaian(%)']:.1f}%" for _, r in df_ok.head(top).iterrows()]
        lines.append("• **Memadai** → " + "; ".join(items) + ".")

    # rekomendasi sederhana berbasis makro
    recs = []
    # Energi
    rowE = df[df["Nutrien"]=="Energi"]
    if not rowE.empty and pd.notna(rowE["Pencapaian(%)"].iat[0]):
        if rowE["Pencapaian(%)"].iat[0] < 90:
            recs.append("Tingkatkan **Energi** (porsi/penambahan bahan kaya energi seperti minyak/karbohidrat kompleks).")
        elif rowE["Pencapaian(%)"].iat[0] > 120:
            recs.append("Pertimbangkan penyesuaian **Energi** (porsi atau frekuensi) agar tidak berlebihan.")
    # Protein
    rowP = df[df["Nutrien"]=="Protein"]
    if not rowP.empty and pd.notna(rowP["Pencapaian(%)"].iat[0]):
        if rowP["Pencapaian(%)"].iat[0] < 90:
            recs.append("Prioritaskan **Protein berkualitas** (telur, ikan, ayam tanpa kulit, kacang-kacangan/tempe).")
    # Serat
    rowS = df[df["Nutrien"]=="Serat"]
    if not rowS.empty and pd.notna(rowS["Pencapaian(%)"].iat[0]):
        if rowS["Pencapaian(%)"].iat[0] < 90:
            recs.append("Tambahkan **serat** (sayur berdaun, buah utuh, legum, serealia utuh).")
    # Lemak & PUFA
    rowL = df[df["Nutrien"]=="Lemak_total"]
    rowO3 = df[df["Nutrien"]=="Omega3"]
    rowO6 = df[df["Nutrien"]=="Omega6"]
    if not rowL.empty and pd.notna(rowL["Pencapaian(%)"].iat[0]) and rowL["Pencapaian(%)"].iat[0] > 120:
        recs.append("Pantau **Lemak_total**; gunakan teknik masak rendah minyak (rebus/panggang/air-fryer).")
    if not rowO3.empty and pd.notna(rowO3["Pencapaian(%)"].iat[0]) and rowO3["Pencapaian(%)"].iat[0] < 90:
        recs.append("Naikkan **Omega-3** (ikan berlemak, biji rami/chia, kenari).")

    if recs:
        lines.append("**Rekomendasi ringkas:** " + " ".join(recs))

    return "\n".join(lines)

# ==== jalankan jika AKG sudah dihitung ====
try:
    # ambil kelompok yg sedang ditampilkan di grafik batang (pakai var yang sama)
    target_group = st.session_state.get("akg_target_group", None)
except Exception:
    target_group = None

# Jika kamu punya variabel `target_group` saat plotting bar, simpan ke session_state:
# st.session_state["akg_target_group"] = target_group

# Kita pilih kelompok pertama jika tidak ada yang tersimpan:
if not target_group:
    target_group = ref_akg["Kelompok"].iloc[0]

# ambil baris AKG rujukan
akg_row = ref_akg[ref_akg["Kelompok"]==target_group].iloc[0]

# buat df gap
df_gap = compute_gap_series(asupan, akg_row)

st.subheader("🔎 Analisis Otomatis – Gap & Rekomendasi")
st.dataframe(
    df_gap.assign(**{"Pencapaian(%)": df_gap["Pencapaian(%)"].round(1), "Gap": df_gap["Gap"].round(2)}),
    use_container_width=True
)

# narasi AI-like (rule-based)
narasi = narrate_gap(df_gap, target_group)
st.markdown(narasi)
st.code(narasi, language="markdown")

# ---------- Download Excel ----------
st.subheader("6) Unduh Excel")
buffer = io.BytesIO()
with excel_writer(buffer) as writer:
    pd.DataFrame(st.session_state.rows).to_excel(writer, sheet_name="Input", index=False)
    df_per_bahan.to_excel(writer, sheet_name="Per Bahan", index=False)
    df_per_menu.to_excel(writer, sheet_name="Per Menu", index=False)
    st.session_state.yield_df.to_excel(writer, sheet_name="Yield Factors", index=False)
    st.session_state.ret_df.to_excel(writer, sheet_name="Retention Factors", index=False)
    # Tambahan AKG:
    akg_ref_df().to_excel(writer, sheet_name="AKG_Referensi", index=False)
    if 'df_akg_pct' in locals():
        pd.DataFrame([asupan]).to_excel(writer, sheet_name="Asupan_AKG", index=False)
        df_akg_pct.to_excel(writer, sheet_name="Pencapaian_AKG", index=False)

st.download_button(
    "⬇️ Download Hasil (Excel)",
    data=buffer.getvalue(),
    file_name="Hasil_FCT_TKPI.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# ---------- Footer ----------
st.markdown(
    """
    <hr style="margin-top:2rem;margin-bottom:0.5rem;">
    <div style="text-align:center;font-size:0.9rem;color:#555;">
        Create with love ❤️ by <a href="mailto:dedik2urniawan@gmail.com">dedik2urniawan@gmail.com</a><br/>
        part of <a href="https://www.tindikanting.id" style="text-decoration:underline;">Tindik Anting Analysis</a>
    </div>
    """,
    unsafe_allow_html=True
)
