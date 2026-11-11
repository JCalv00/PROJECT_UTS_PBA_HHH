# Proyek UTS PBA - Kelompok HHH

Dataset ulasan aplikasi e-commerce (Blibli, Google Play) dengan anotasi multilabel aspek dan span evidence.

## Struktur
- `dataset/` : `KelpHHH_dataset_original.csv` (10.040 baris), `KelpHHH_dataset_clean.csv` (4.080 teks), `KelpHHH_dataset_annotation.jsonl` (990 teks, gold)
- `notebook/KelpHHH_dataset_EDA.ipynb` : cleaning + EDA
- `guideline/KelpHHH_annotation_guideline.pdf`
- `streamlit/KelpHHH_dataset_explorer.py` : dataset explorer
- `report/KelpHHH_laporan_UTS.pdf`, `code_pdf/KelpHHH_code_export_UTS.pdf`

## Menjalankan (Python 3.10+)
```
pip install -r requirements.txt
```
Notebook (jalankan dari folder `notebook/`, path relatif ke `../dataset/`):
```
cd notebook
jupyter nbconvert --to notebook --execute --inplace KelpHHH_dataset_EDA.ipynb
```
atau buka di Jupyter lalu *Restart & Run All*. Input: `../dataset/KelpHHH_dataset_original.csv`. Output: `../dataset/KelpHHH_dataset_clean.csv`.

Dataset explorer (jalankan dari folder `streamlit/`):
```
cd streamlit
streamlit run KelpHHH_dataset_explorer.py
```
Input: `../dataset/KelpHHH_dataset_annotation.jsonl`. File lain dapat diunggah lewat sidebar.

## Format anotasi (JSONL)
`{"id", "text", "labels": [...], "entities": [{"start", "end", "label", "text"}], "source"}`; offset karakter terhadap `text`.
Label: PENGIRIMAN, LAYANAN_PELANGGAN, APLIKASI_PERFORMA, USABILITY, PEMBAYARAN, PROMO_HARGA.
