# 🥗 Food Composition Tool (FCT) – TKPI 2017 + AKG Analyzer

**FCT-TKPI** adalah aplikasi Streamlit untuk:
- menghitung **komposisi gizi** per-bahan dan per-menu berbasis **TKPI 2017**,
- mengoreksi **BDD (edible portion)**, **yield** (perubahan berat setelah memasak), dan **retensi nutrien**,
- mengevaluasi **AKG (Angka Kecukupan Gizi)** dengan **visualisasi interaktif** (bar & radar).

Aplikasi cocok untuk **akademisi, praktisi gizi, industri pangan,** dan **peneliti** yang membutuhkan perhitungan transparan, dapat direproduksi, dan berlandaskan rujukan ilmiah.

---

## 🔬 Dasar Ilmiah & Metodologi

### 1) Koreksi berat: BDD dan Yield
BDD mengacu pada **bagian dapat dimakan** dari bahan (mis. tanpa kulit/tulang) berdasarkan TKPI. Yield merefleksikan **perubahan berat** pasca pemasakan (penyerapan/kehilangan air/minyak).

\[
w_{\text{edible}} = w_{\text{input}} \times \frac{\text{BDD}(\%)}{100}, \qquad 
w_{\text{final}} = w_{\text{edible}} \times \text{Yield}(\text{metode})
\]

### 2) Retensi nutrien
Retensi nutrien memperhitungkan **degradasi** vitamin/mineral saat pemasakan.

\[
N_{\text{akhir}} = \left(\frac{N_{100}}{100}\right) \times w_{\text{final}} \times \text{Retensi}_N(\text{metode})
\]

### 3) Agregasi per Menu
\[
N_{\text{menu}} = \sum_i N_{\text{akhir},i}
\]

**Catatan ilmiah:**
- Vitamin **C** dan provitamin **A** lebih labil terhadap panas/oksidasi dibanding mineral dan makronutrien.
- Faktor **yield** & **retensi** default mengikuti kisaran **USDA FNDDS** dan **USDA Retention Factors**; pengguna dapat **override** via CSV atau update di kode.

### 4) Evaluasi vs AKG
Asupan harian (dari penjumlahan 1 atau lebih menu) dibandingkan dengan **AKG** per kelompok umur/jenis kelamin:

\[
\% \text{Pencapaian}_N = \frac{\text{Asupan}_N}{\text{AKG}_N} \times 100\%
\]

AKG yang disertakan:  
**Anak 7–9 th**, **Laki-laki & Perempuan** usia **10–12**, **13–15**, **16–18** tahun.

---

## 📦 Fitur Utama

- **Database TKPI default 2017** + opsi **upload** TKPI terbaru (XLSX/CSV).
- **Mapping kolom TKPI** di sidebar → fleksibel untuk variasi header (mis. *ENERGI* vs *Energi (kkal)*).
- Perhitungan **Per Bahan** & **Per Menu** (BDD → Yield → Retensi).
- **Analisis AKG**:
  - sumber asupan: **Dari Per Menu** (default: jumlah semua menu bila tidak dipilih) atau **Input manual**,
  - grafik **Bar** & **Radar** via **Plotly** (interaktif).
- **Ekspor Excel**: input, per-bahan, per-menu, faktor yield/retensi, referensi AKG, asupan & pencapaian AKG.
- **UI**: panduan metodologi (LaTeX), footer, dan gaya note biru.

---

## 🗂️ Struktur Proyek (minimal)
fct-tkpi/
├─ app.py # aplikasi Streamlit
├─ requirements.txt
├─ TKPI 2017.xlsx # database default (opsional; <100MB)
├─ sample_yield_factors.csv # contoh faktor yield (opsional)
├─ sample_retention_factors.csv# contoh faktor retensi (opsional)
└─ README.md


> **Catatan:** untuk file besar, lebih baik **diunggah dari UI** ketimbang dipush ke GitHub.

---

## ⚙️ Instalasi Lokal

```bash
# 1) siapkan environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 2) install dependency
pip install -r requirements.txt

# 3) jalankan aplikasi
streamlit run app.py

☁️ Deploy ke Streamlit Community Cloud

Push proyek ini ke GitHub (repo publik).

Masuk ke https://share.streamlit.io/

New app → pilih repo, branch, dan file app.py.

Klik Deploy. Selesai ✅

🧑‍💻 Cara Pakai (ringkas)

Pilih sumber TKPI (default 2017 atau upload).

Cek “⚙️ Kolom TKPI (mapping)” → samakan nama kolom dengan header dataset Anda.

Tambah Menu → Tambah Bahan ke Menu → pilih bahan TKPI, berat (g/kg), metode masak.

Lihat hasil Per Bahan & Per Menu.

Buka Analisis AKG:

“Dari Per Menu” (default: jumlah semua menu bila tidak dipilih), atau

“Input manual” kalau mau mengetik asupan sendiri.

Unduh Excel yang berisi semua hasil perhitungan.

📚 Rujukan

TKPI 2017 – Direktorat Gizi, Kementerian Kesehatan RI.

USDA Table of Nutrient Retention Factors (Release 6, 2007).

USDA FoodData Central / FNDDS – Cooking Yields.

FAO/INFOODS Guidelines – Food matching & documentation standards.
❤️ Kredit

Create with love by dedik2urniawan@gmail.com

Part of Tindik Anting Analysis
.
