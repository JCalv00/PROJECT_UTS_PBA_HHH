"""KelpHHH Dataset Explorer (UTS PBA 2026/2027).

Menjalankan:  streamlit run KelpHHH_dataset_explorer.py
Data dibaca dari ../dataset/KelpHHH_dataset_annotation.jsonl (jika ada), jika tidak ada
dipakai ../dataset/KelpHHH_gold_overlap.jsonl. Dapat juga diunggah lewat sidebar.

Format baris JSONL:
{"id": 1, "text": "...", "labels": ["PENGIRIMAN"],
 "entities": [{"start": 0, "end": 5, "label": "PENGIRIMAN", "text": "Kurir"}]}
"""
import html
import itertools
import json
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

LABELS = ["PENGIRIMAN", "LAYANAN_PELANGGAN", "APLIKASI_PERFORMA", "USABILITY", "PEMBAYARAN", "PROMO_HARGA"]
COLORS = {
    "PENGIRIMAN": "#ffd166",
    "LAYANAN_PELANGGAN": "#ef9a9a",
    "APLIKASI_PERFORMA": "#ce93d8",
    "USABILITY": "#90caf9",
    "PEMBAYARAN": "#a5d6a7",
    "PROMO_HARGA": "#ffab91",
}
HERE = Path(__file__).resolve().parent
CANDIDATES = [
    HERE.parent / "dataset" / "KelpHHH_dataset_annotation.jsonl",
    HERE.parent / "dataset" / "KelpHHH_gold_overlap.jsonl",
    HERE / "KelpHHH_dataset_annotation.jsonl",
]

st.set_page_config(page_title="KelpHHH Dataset Explorer", layout="wide")


# ---------------------------------------------------------------- data
def parse_jsonl(lines):
    rows = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        r.setdefault("labels", [])
        r.setdefault("entities", [])
        rows.append(r)
    return rows


@st.cache_data(show_spinner=False)
def load_path(path: str):
    with open(path, encoding="utf-8") as f:
        return parse_jsonl(f)


def get_rows():
    up = st.sidebar.file_uploader("Unggah file anotasi (.jsonl)", type=["jsonl", "json"])
    if up is not None:
        return parse_jsonl(up.getvalue().decode("utf-8").splitlines()), f"upload: {up.name}"
    for p in CANDIDATES:
        if p.exists():
            return load_path(str(p)), p.name
    return [], ""


def render_highlight(text, entities):
    """Highlight span; mendukung overlap antarlabel (label ditumpuk sebagai badge)."""
    n = len(text)
    cover = [[] for _ in range(n)]
    for e in entities:
        for i in range(max(0, e["start"]), min(n, e["end"])):
            cover[i].append(e["label"])
    out, i = [], 0
    while i < n:
        labs = tuple(sorted(set(cover[i])))
        j = i
        while j < n and tuple(sorted(set(cover[j]))) == labs:
            j += 1
        chunk = html.escape(text[i:j])
        if labs:
            if len(labs) == 1:
                bg = COLORS.get(labs[0], "#ddd")
            else:
                c1, c2 = COLORS.get(labs[0], "#ddd"), COLORS.get(labs[1], "#ddd")
                bg = f"linear-gradient(90deg,{c1},{c2})"
            tag = "+".join(l.split("_")[0] for l in labs)
            out.append(
                f'<mark style="background:{bg};padding:1px 3px;border-radius:4px;color:#111">{chunk}'
                f'<sup style="font-size:0.6em;font-weight:700;margin-left:2px">{tag}</sup></mark>'
            )
        else:
            out.append(chunk)
        i = j
    return "".join(out)


rows, source = get_rows()
st.title("KelpHHH Dataset Explorer")
st.caption("Ulasan aplikasi e-commerce (Blibli, Google Play) | Multilabel aspek + span evidence")
if not rows:
    st.warning("Belum ada data. Letakkan KelpHHH_dataset_annotation.jsonl di folder ../dataset atau unggah lewat sidebar.")
    st.stop()
st.sidebar.success(f"Sumber data: {source} ({len(rows)} teks)")

df = pd.DataFrame(
    {
        "id": [r.get("id", i) for i, r in enumerate(rows)],
        "text": [r["text"] for r in rows],
        "labels": [r["labels"] for r in rows],
        "entities": [r["entities"] for r in rows],
    }
)
df["n_chars"] = df["text"].str.len()
df["n_tokens"] = df["text"].str.split().str.len()
df["n_labels"] = df["labels"].str.len()
df["n_entities"] = df["entities"].str.len()
df["label_combo"] = df["labels"].apply(lambda x: " + ".join(sorted(x)) if x else "(tanpa label)")
all_labels = LABELS + sorted({l for ls in df["labels"] for l in ls} - set(LABELS))

page = st.sidebar.radio("Halaman", ["Overview", "Browse Data", "Multilabel Analysis", "NER Analysis", "Filter / Search"])

# ---------------------------------------------------------------- Overview
if page == "Overview":
    c = st.columns(4)
    c[0].metric("Jumlah teks", len(df))
    c[1].metric("Rata-rata kata/teks", f"{df.n_tokens.mean():.1f}")
    c[2].metric("Rata-rata label/teks", f"{df.n_labels.mean():.2f}")
    c[3].metric("Total span", int(df.n_entities.sum()))
    st.subheader("Taxonomy label")
    desc = {
        "PENGIRIMAN": "Kecepatan/ketepatan kirim, kurir, ekspedisi, kondisi kemasan paket.",
        "LAYANAN_PELANGGAN": "Respon dan penanganan CS/seller, refund, retur, komplain.",
        "APLIKASI_PERFORMA": "Kestabilan teknis: error, bug, lemot, force close, loading.",
        "USABILITY": "Kemudahan memakai aplikasi: tampilan, navigasi, pencarian, fitur.",
        "PEMBAYARAN": "Proses bayar/checkout, metode bayar, cicilan, saldo, kegagalan transaksi.",
        "PROMO_HARGA": "Diskon, voucher, gratis ongkir, cashback, harga.",
    }
    cnt = Counter(l for ls in df.labels for l in ls)
    ecnt = Counter(e["label"] for es in df.entities for e in es)
    st.dataframe(
        pd.DataFrame(
            {
                "Label": all_labels,
                "Definisi": [desc.get(l, "") for l in all_labels],
                "Jumlah teks": [cnt.get(l, 0) for l in all_labels],
                "Jumlah span": [ecnt.get(l, 0) for l in all_labels],
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.markdown(
        "Label Skema A (dokumen) dan label span Skema B memakai **satu set 6 label yang sama**. "
        "Sentimen tidak dianotasi. Ulasan tanpa aspek di-*Ignore* dan tidak masuk dataset."
    )
    st.subheader("Distribusi panjang teks")
    st.bar_chart(df["n_tokens"].clip(upper=60).value_counts().sort_index())

# ---------------------------------------------------------------- Browse
elif page == "Browse Data":
    per = st.sidebar.slider("Teks per halaman", 5, 50, 10)
    pages = max(1, (len(df) + per - 1) // per)
    pg = st.sidebar.number_input("Halaman", 1, pages, 1)
    sub = df.iloc[(pg - 1) * per : pg * per]
    st.write(f"Menampilkan {len(sub)} dari {len(df)} teks (halaman {pg}/{pages})")
    for _, r in sub.iterrows():
        with st.container(border=True):
            st.markdown(f"**ID {r['id']}**  |  label: `{', '.join(r['labels']) or '-'}`")
            st.markdown(render_highlight(r["text"], r["entities"]), unsafe_allow_html=True)
            if r["entities"]:
                st.caption(" ; ".join(f"{e['text']} = {e['label']} [{e['start']}:{e['end']}]" for e in r["entities"]))

# ---------------------------------------------------------------- Multilabel
elif page == "Multilabel Analysis":
    cnt = Counter(l for ls in df.labels for l in ls)
    dist = pd.Series({l: cnt.get(l, 0) for l in all_labels})
    st.subheader("Distribusi label")
    st.bar_chart(dist)
    mx, mn = dist.max(), dist[dist > 0].min() if (dist > 0).any() else 0
    st.write(f"**Imbalance ratio** (label terbanyak / tersedikit): {mx / mn:.2f}" if mn else "-")
    st.subheader("Jumlah label per teks")
    st.bar_chart(df["n_labels"].value_counts().sort_index())
    st.subheader("Kombinasi label terbanyak")
    combo = df["label_combo"].value_counts().head(15).rename_axis("kombinasi").reset_index(name="jumlah")
    st.dataframe(combo, use_container_width=True, hide_index=True)
    st.subheader("Co-occurrence label")
    M = pd.DataFrame(0, index=all_labels, columns=all_labels)
    for ls in df.labels:
        for a, b in itertools.product(set(ls), set(ls)):
            M.loc[a, b] += 1
    st.dataframe(M.style.background_gradient(cmap="Blues"), use_container_width=True)
    st.subheader("Korelasi (phi) antarlabel")
    B = pd.DataFrame({l: df.labels.apply(lambda x, l=l: int(l in x)) for l in all_labels})
    st.dataframe(B.corr().round(2).style.background_gradient(cmap="coolwarm", vmin=-1, vmax=1), use_container_width=True)

# ---------------------------------------------------------------- NER
elif page == "NER Analysis":
    ents = pd.DataFrame(
        [
            {"id": r["id"], "label": e["label"], "text": e["text"], "n_tokens": len(e["text"].split()), "n_chars": e["end"] - e["start"], "text_norm": e["text"].lower()}
            for _, r in df.iterrows()
            for e in r["entities"]
        ]
    )
    if ents.empty:
        st.info("Belum ada span pada data ini.")
        st.stop()
    st.subheader("Jumlah span per label")
    st.bar_chart(ents["label"].value_counts().reindex(all_labels).fillna(0))
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Span per teks")
        st.bar_chart(df["n_entities"].value_counts().sort_index())
    with c2:
        st.subheader("Panjang span (token)")
        st.bar_chart(ents["n_tokens"].clip(upper=15).value_counts().sort_index())
    st.subheader("Dominasi tag O (level token)")
    total_tok = int(df.n_tokens.sum())
    ent_tok = int(ents.n_tokens.sum())
    st.write(f"Token dalam span: {ent_tok} dari {total_tok} ({ent_tok / total_tok:.1%}); sisanya (**{1 - ent_tok / total_tok:.1%}**) bertag O. "
             "Perkiraan dihitung dari jumlah kata; span yang tumpang tindih dihitung dua kali.")
    st.subheader("Span paling sering muncul")
    lab = st.selectbox("Label", ["(semua)"] + all_labels)
    e2 = ents if lab == "(semua)" else ents[ents.label == lab]
    top = e2.groupby(["label", "text_norm"]).size().reset_index(name="jumlah").sort_values("jumlah", ascending=False).head(20)
    st.dataframe(top, use_container_width=True, hide_index=True)
    st.subheader("Contoh span yang di-highlight")
    pool = df[df.n_entities > 0]
    if lab != "(semua)":
        pool = pool[pool.entities.apply(lambda es: any(e["label"] == lab for e in es))]
    for _, r in pool.sample(min(8, len(pool)), random_state=1).iterrows() if len(pool) else []:
        st.markdown(render_highlight(r["text"], r["entities"]), unsafe_allow_html=True)
        st.divider()

# ---------------------------------------------------------------- Filter
else:
    q = st.text_input("Cari teks (tidak peka huruf besar/kecil)")
    f_labels = st.multiselect("Filter label dokumen", all_labels)
    mode = st.radio("Mode label", ["Mengandung salah satu", "Mengandung semua"], horizontal=True)
    f_ents = st.multiselect("Filter label span", all_labels)
    q_span = st.text_input("Cari teks di dalam span")
    m = pd.Series(True, index=df.index)
    if q:
        m &= df.text.str.contains(q, case=False, regex=False)
    if f_labels:
        m &= df.labels.apply(lambda x: all(l in x for l in f_labels) if mode.endswith("semua") else any(l in x for l in f_labels))
    if f_ents:
        m &= df.entities.apply(lambda es: any(e["label"] in f_ents for e in es))
    if q_span:
        m &= df.entities.apply(lambda es: any(q_span.lower() in e["text"].lower() for e in es))
    res = df[m]
    st.write(f"**{len(res)}** teks cocok")
    for _, r in res.head(50).iterrows():
        with st.container(border=True):
            st.markdown(f"**ID {r['id']}**  |  `{', '.join(r['labels']) or '-'}`")
            st.markdown(render_highlight(r["text"], r["entities"]), unsafe_allow_html=True)
    if len(res) > 50:
        st.caption("Menampilkan 50 hasil pertama.")
