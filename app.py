"""Balochi Mini Dictionary – Streamlit version.

Tabs: Dictionary | Sentences | Quiz | About
Data lives in ./data (CSV, UTF-8). Nothing else is needed to run.
"""
import random
import re
import unicodedata
from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).parent / "data"
PAGE_SIZE = 25

st.set_page_config(page_title="Balochi Mini Dictionary", page_icon="📖", layout="centered")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&family=Noto+Naskh+Arabic&display=swap');
.rtl{direction:rtl;text-align:right;font-family:'Noto Nastaliq Urdu','Noto Naskh Arabic',serif;}
.bal{font-size:26px;line-height:2;color:#0f766e;}
.urd{font-size:19px;line-height:1.9;}
.eng{font-size:17px;font-weight:600;}
.mut{color:#6b7280;font-size:13px;}
.tag{display:inline-block;font-size:11px;border-radius:8px;padding:2px 8px;background:#fef3c7;color:#92400e;margin-right:4px;}
.tag.ok{background:#d1fae5;color:#065f46;}
.card{background:#fff;border:1px solid #e7e2d9;border-radius:14px;padding:10px 14px;margin-bottom:8px;}
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------- helpers
_DIACRITICS = re.compile("[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")


def norm(text) -> str:
    """Lower-case, strip Arabic diacritics and unify look-alike letters / Roman spellings."""
    s = unicodedata.normalize("NFKC", str(text)).lower()
    s = _DIACRITICS.sub("", s)
    for a, b in (("ي", "ی"), ("ى", "ی"), ("ك", "ک"), ("ە", "ہ"), ("ھ", "ہ"), ("ۃ", "ہ"),
                 ("ۓ", "ے"), ("ے", "ے")):
        s = s.replace(a, b)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"(.)\1+", r"\1", s)  # haabund / habund, durr / dur
    return re.sub(r"\s+", " ", s).strip()


@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    df = pd.read_csv(DATA / name, encoding="utf-8-sig", dtype=str).fillna("")
    df.columns = [c.strip() for c in df.columns]
    return df


@st.cache_data
def dictionary() -> pd.DataFrame:
    df = load_csv("dictionary.csv")
    cols = ["balochi_native", "urdu", "english", "roman_balochi", "roman_balochi_alternatives"]
    df["_all"] = df[cols].agg(" | ".join, axis=1).map(norm)
    for c in cols[:4]:
        df["_" + c] = df[c].map(norm)
    return df


@st.cache_data
def sentences_bal_en() -> pd.DataFrame:
    df = load_csv("sentences_balochi_english.csv")
    df["_dup"] = df.duplicated(subset=["Balochi_Sentence"], keep="first")
    df["_all"] = (df.Balochi_Sentence + " | " + df.English_Translation).map(norm)
    return df


@st.cache_data
def sentences_roman() -> pd.DataFrame:
    df = load_csv("sentences_roman_urdu_english.csv")
    # The file contains many machine-made filler lines ("The X kurt a Y nearby.")
    df["_auto"] = df.Roman_Balochi.str.contains(r"\bnazik a yak\b", regex=True)
    df["_dup"] = df.duplicated(subset=["Roman_Balochi"], keep="first")
    df["_all"] = (df.Roman_Balochi + " | " + df.Urdu_Translation + " | " + df.English_Translation).map(norm)
    return df


def paginate(total: int, key: str) -> tuple[int, int]:
    pages = max(1, -(-total // PAGE_SIZE))
    if pages > 1:
        page = st.number_input(f"Page (1–{pages})", 1, pages, 1, key=key)
    else:
        page = 1
    start = (page - 1) * PAGE_SIZE
    return start, start + PAGE_SIZE


def badge(status: str) -> str:
    ok = status == "verified"
    return f'<span class="tag {"ok" if ok else ""}">{"verified" if ok else "needs review"}</span>'


# ------------------------------------------------------------------- UI
st.title("📖 Balochi Mini Dictionary")
tab_dict, tab_sent, tab_quiz, tab_about = st.tabs(["🔍 Dictionary", "💬 Sentences", "🎯 Quiz", "ℹ️ About"])

# ---------------------------------------------------------------- Dictionary
with tab_dict:
    df = dictionary()
    q = st.text_input("Search in English, Urdu, Roman or Balochi script", key="dq",
                      placeholder="e.g. water, پانی, wash, آب")
    c1, c2 = st.columns(2)
    lang = c1.selectbox("Search in", ["All", "English", "Urdu", "Roman Balochi", "Balochi script"])
    cats = ["All categories"] + sorted(df.category.unique())
    cat = c2.selectbox("Category", cats)

    res = df
    if cat != "All categories":
        res = res[res.category == cat]
    if q.strip():
        nq = norm(q)
        col = {"All": "_all", "English": "_english", "Urdu": "_urdu",
               "Roman Balochi": "_roman_balochi", "Balochi script": "_balochi_native"}[lang]
        res = res[res[col].str.contains(re.escape(nq), na=False)]
        # exact matches first
        res = res.assign(_rank=(~res["_english"].eq(nq)).astype(int)).sort_values("_rank", kind="stable")

    st.caption(f"{len(res)} of {len(df)} entries")
    if res.empty:
        st.info("No match found. Try another spelling or a shorter word.")
    s, e = paginate(len(res), "dp")
    for _, r in res.iloc[s:e].iterrows():
        alt = f'<div class="mut">Also: {r.roman_balochi_alternatives}</div>' if r.roman_balochi_alternatives else ""
        st.markdown(
            f"""<div class="card">
<div class="rtl bal">{r.balochi_native}</div>
<div class="eng">{r.english} <span class="mut">· {r.roman_balochi}</span></div>
<div class="rtl urd">{r.urdu}</div>{alt}
<div style="margin-top:4px"><span class="tag" style="background:#e0f2fe;color:#075985">{r.category}</span>{badge(r.verification_status)}</div>
</div>""",
            unsafe_allow_html=True,
        )

# ----------------------------------------------------------------- Sentences
with tab_sent:
    src = st.radio(
        "Sentence set",
        ["Balochi script ↔ English (500)", "Roman Balochi ↔ Urdu ↔ English (800)"],
        horizontal=True,
    )
    q = st.text_input("Search sentences", key="sq", placeholder="e.g. hello, نام, nam")

    if src.startswith("Balochi"):
        sd = sentences_bal_en()
        c1, c2 = st.columns(2)
        cat = c1.selectbox("Category", ["All"] + sorted(sd.Category.unique()), key="sc1")
        dia = c2.selectbox("Dialect", ["All"] + sorted(sd.Dialect_Variant.unique()), key="sd1")
        hide = st.checkbox("Hide repeated sentences", value=True, key="h1",
                           help="This file repeats the same sentences several times.")
        res = sd
        if hide:
            res = res[~res._dup]
        if cat != "All":
            res = res[res.Category == cat]
        if dia != "All":
            res = res[res.Dialect_Variant == dia]
        if q.strip():
            res = res[res._all.str.contains(re.escape(norm(q)), na=False)]
        st.caption(f"{len(res)} sentences")
        s, e = paginate(len(res), "sp1")
        for _, r in res.iloc[s:e].iterrows():
            st.markdown(
                f"""<div class="card"><div class="rtl bal">{r.Balochi_Sentence}</div>
<div class="eng">{r.English_Translation}</div>
<div class="mut">{r.Category} · {r.Dialect_Variant}</div></div>""",
                unsafe_allow_html=True,
            )
        csv = res.drop(columns=[c for c in res.columns if c.startswith("_")]).to_csv(index=False).encode("utf-8-sig")
    else:
        sd = sentences_roman()
        cat = st.selectbox("Category", ["All"] + sorted(sd.Category.unique()), key="sc2")
        hide = st.checkbox("Hide auto-generated filler sentences", value=True, key="h2",
                           help="Most rows in this file follow one machine-made pattern "
                                "(\"The X kurt a Y nearby.\") and are not real Balochi.")
        res = sd
        if hide:
            res = res[~res._auto & ~res._dup]
        if cat != "All":
            res = res[res.Category == cat]
        if q.strip():
            res = res[res._all.str.contains(re.escape(norm(q)), na=False)]
        st.caption(f"{len(res)} sentences")
        s, e = paginate(len(res), "sp2")
        for _, r in res.iloc[s:e].iterrows():
            st.markdown(
                f"""<div class="card"><div class="eng">{r.Roman_Balochi}</div>
<div class="rtl urd">{r.Urdu_Translation}</div>
<div>{r.English_Translation}</div>
<div class="mut">{r.Category}</div></div>""",
                unsafe_allow_html=True,
            )
        csv = res.drop(columns=[c for c in res.columns if c.startswith("_")]).to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Download these results (CSV)", csv, "sentences.csv", "text/csv")

# ---------------------------------------------------------------------- Quiz
with tab_quiz:
    df = dictionary()
    st.write("Pick the correct English meaning. *(Practice mode – entries are not yet verified.)*")
    mode = st.radio("Show", ["Balochi script", "Roman Balochi"], horizontal=True)

    def new_question():
        pool = df[df.english.str.len() < 40]
        row = pool.sample(1).iloc[0]
        wrong = pool[pool.english != row.english].english.drop_duplicates().sample(3).tolist()
        opts = wrong + [row.english]
        random.shuffle(opts)
        st.session_state.q = {"id": row.entry_id, "opts": opts, "ans": row.english}
        st.session_state.answered = None

    if "score" not in st.session_state:
        st.session_state.score = [0, 0]
    if "q" not in st.session_state:
        new_question()

    qd = st.session_state.q
    row = df[df.entry_id == qd["id"]].iloc[0]
    if mode == "Balochi script":
        st.markdown(f'<div class="rtl bal" style="text-align:center">{row.balochi_native}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="eng" style="text-align:center;font-size:26px">{row.roman_balochi}</div>', unsafe_allow_html=True)

    choice = st.radio("Meaning", qd["opts"], index=None, key=f"c_{qd['id']}",
                      disabled=st.session_state.answered is not None)
    if choice is not None and st.session_state.answered is None:
        st.session_state.answered = choice
        st.session_state.score[1] += 1
        if choice == qd["ans"]:
            st.session_state.score[0] += 1
        st.rerun()
    if st.session_state.answered is not None:
        if st.session_state.answered == qd["ans"]:
            st.success("Correct!")
        else:
            st.error(f"Not quite. Answer: {qd['ans']}")
        if st.button("Next ➡️"):
            new_question()
            st.rerun()
    st.caption(f"Score: {st.session_state.score[0]} / {st.session_state.score[1]}")

# --------------------------------------------------------------------- About
with tab_about:
    d, a, b = dictionary(), sentences_bal_en(), sentences_roman()
    st.markdown(
        f"""
**Data loaded**
- Dictionary: **{len(d)}** entries
- Balochi ↔ English sentences: **{len(a)}** rows ({int((~a._dup).sum())} unique)
- Roman ↔ Urdu ↔ English sentences: **{len(b)}** rows ({int((~b._auto & ~b._dup).sum())} real, non-filler)

All dictionary entries are marked *needs review*: please have a native speaker verify them.
To change the data, edit the CSV files in the `data/` folder and redeploy.
"""
    )
