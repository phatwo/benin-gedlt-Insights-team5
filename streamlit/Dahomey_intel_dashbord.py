"""
Dahomey_Intel — Dashboard GDELT 2025
Streamlit + Plotly — v6 : zero unsafe_allow_html
Auteur : Groupe 5 — BéninWatch
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import re
import math

# ─────────────────────────────────────────────
# CONFIG PAGE
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Dahomey Intel · Analyse GDELT",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────
GREEN  = "#1D9E75"
BLUE   = "#378ADD"
ORANGE = "#EF9F27"
RED    = "#D85A30"

MONTH_ORDER = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]
MONTH_SHORT  = ["Jan","Fév","Mar","Avr","Mai","Juin",
                "Juil","Aoû","Sep","Oct","Nov","Déc"]

NORTH_KW = ["Alibori","Kandi","Porga","Karimama","Atakora",
            "Djougou","Parakou","Tchaourou","Tanguieta","Malanville"]

CAMEO = {
    "GOV":"Gouvernement","COP":"Police","MIL":"Militaire",
    "CVL":"Civil","LEG":"Législatif","EDU":"Education",
    "IGO":"Org. Internationale","MED":"Médias","BUS":"Entreprises",
    "JUD":"Judiciaire","OPP":"Opposition","UAF":"Forces non-identifiées",
    "ELI":"Élites politiques","SPY":"Renseignement","REB":"Rebelles",
    "HLH":"Santé","UNKNOWN":"Inconnu"
}

QUAD_L = {
    1: "Coopération verbale",
    2: "Coopération concrète",
    3: "Tension verbale",
    4: "Conflit armé / Violence"
}
QUAD_C = {1: GREEN, 2: BLUE, 3: ORANGE, 4: RED}

# ─────────────────────────────────────────────
# HELPERS NATIFS — remplacent les div HTML
# ─────────────────────────────────────────────
def alerte(niveau: str, texte: str):
    """Affiche une bannière d'alerte avec st.error / st.warning / st.success."""
    if niveau == "red":
        st.error(texte)
    elif niveau == "orange":
        st.warning(texte)
    else:
        st.success(texte)

def kpi(label: str, valeur: str, sous_texte: str = "", col=None):
    """Affiche un KPI via st.metric natif."""
    cible = col if col else st
    cible.metric(label=label, value=valeur, delta=sous_texte if sous_texte else None,
                 delta_color="off")

def alerte_stabilite(df):
    gold_moy    = df["goldstein_scale"].mean()
    pct_conflit = (df["quad_class"] == 4).mean() * 100
    if gold_moy < 0 or pct_conflit > 20:
        alerte("red",
               f"Alerte — Score de stabilité moyen négatif ({gold_moy:.2f}) "
               f"ou taux de conflits armés élevé ({pct_conflit:.1f} %). Situation préoccupante.")
    elif gold_moy < 0.5 or pct_conflit > 14:
        alerte("orange",
               f"Vigilance — Score de stabilité faible ({gold_moy:.2f}). "
               f"Surveillance accrue recommandée ({pct_conflit:.1f} % d'événements violents).")
    else:
        alerte("green",
               f"Situation stable sur la période — "
               f"Score de stabilité moyen : {gold_moy:.2f}.")

# ─────────────────────────────────────────────
# CHARGEMENT DONNÉES
# ─────────────────────────────────────────────
@st.cache_data
def load_data(raw_bytes: bytes, filename: str) -> pd.DataFrame:
    import io
    df = pd.read_csv(io.BytesIO(raw_bytes))
    df["month_num"] = df["month_name"].apply(
        lambda x: MONTH_ORDER.index(x) + 1 if x in MONTH_ORDER else 0)
    df["month_short"] = df["month_num"].apply(
        lambda x: MONTH_SHORT[x - 1] if 1 <= x <= 12 else "?")
    df["zone"] = df["geo_full_name"].apply(
        lambda x: "Nord (sensible)"
        if any(k in str(x) for k in NORTH_KW) else "Sud / Centre")
    df["actor_label"] = df["actor1_type"].map(CAMEO).fillna(df["actor1_type"])
    df["quad_label"]  = df["quad_class"].map(QUAD_L)
    return df

# ─────────────────────────────────────────────
# HELPER — extraire pays depuis source_url
# ─────────────────────────────────────────────
def extract_pays_source(df: pd.DataFrame) -> pd.DataFrame:
    def get_domain(url):
        try:
            m = re.search(r'https?://(?:www\.)?([^/]+)', str(url))
            return m.group(1) if m else None
        except Exception:
            return None

    TLD_MAP = {
        ".ng":"Nigeria",".bj":"Bénin",".gh":"Ghana",".sn":"Sénégal",
        ".ci":"Côte d'Ivoire",".tg":"Togo",".ml":"Mali",".bf":"Burkina Faso",
        ".ne":"Niger",".cm":"Cameroun",".za":"Afrique du Sud",".ke":"Kenya",
        ".tz":"Tanzanie",".ug":"Ouganda",".et":"Ethiopie",".ma":"Maroc",
        ".dz":"Algérie",".tn":"Tunisie",".eg":"Egypte",".rw":"Rwanda",
        ".cd":"RD Congo",".fr":"France",".de":"Allemagne",".uk":"Royaume-Uni",
        ".co.uk":"Royaume-Uni",".es":"Espagne",".it":"Italie",".pt":"Portugal",
        ".be":"Belgique",".nl":"Pays-Bas",".ch":"Suisse",".ru":"Russie",
        ".us":"Etats-Unis",".ca":"Canada",".br":"Brésil",".mx":"Mexique",
        ".cn":"Chine",".jp":"Japon",".in":"Inde",".au":"Australie",
        ".sg":"Singapour",".com":"Etats-Unis / Intl",
        ".org":"International",".net":"International",".info":"International",
    }
    COUNTRY_COORDS = {
        "Nigeria":           {"lat":9.08,  "lon":8.67,   "iso":"NGA"},
        "Bénin":             {"lat":9.31,  "lon":2.32,   "iso":"BEN"},
        "Ghana":             {"lat":7.94,  "lon":-1.02,  "iso":"GHA"},
        "Sénégal":           {"lat":14.50, "lon":-14.45, "iso":"SEN"},
        "Côte d'Ivoire":     {"lat":7.54,  "lon":-5.55,  "iso":"CIV"},
        "Togo":              {"lat":8.62,  "lon":0.82,   "iso":"TGO"},
        "Mali":              {"lat":17.57, "lon":-3.99,  "iso":"MLI"},
        "Burkina Faso":      {"lat":12.36, "lon":-1.53,  "iso":"BFA"},
        "Niger":             {"lat":17.61, "lon":8.08,   "iso":"NER"},
        "Cameroun":          {"lat":3.85,  "lon":11.50,  "iso":"CMR"},
        "Afrique du Sud":    {"lat":-30.56,"lon":22.94,  "iso":"ZAF"},
        "Kenya":             {"lat":-0.02, "lon":37.91,  "iso":"KEN"},
        "France":            {"lat":46.23, "lon":2.21,   "iso":"FRA"},
        "Allemagne":         {"lat":51.17, "lon":10.45,  "iso":"DEU"},
        "Royaume-Uni":       {"lat":55.38, "lon":-3.44,  "iso":"GBR"},
        "Espagne":           {"lat":40.46, "lon":-3.75,  "iso":"ESP"},
        "Portugal":          {"lat":39.40, "lon":-8.22,  "iso":"PRT"},
        "Belgique":          {"lat":50.50, "lon":4.47,   "iso":"BEL"},
        "Etats-Unis / Intl": {"lat":37.09, "lon":-95.71, "iso":"USA"},
        "Etats-Unis":        {"lat":37.09, "lon":-95.71, "iso":"USA"},
        "Canada":            {"lat":56.13, "lon":-106.35,"iso":"CAN"},
        "Australie":         {"lat":-25.27,"lon":133.78, "iso":"AUS"},
        "Inde":              {"lat":20.59, "lon":78.96,  "iso":"IND"},
        "Chine":             {"lat":35.86, "lon":104.20, "iso":"CHN"},
        "Russie":            {"lat":61.52, "lon":105.32, "iso":"RUS"},
        "Maroc":             {"lat":31.79, "lon":-7.09,  "iso":"MAR"},
        "Algérie":           {"lat":28.03, "lon":1.66,   "iso":"DZA"},
        "Tunisie":           {"lat":33.89, "lon":9.54,   "iso":"TUN"},
        "Egypte":            {"lat":26.82, "lon":30.80,  "iso":"EGY"},
        "International":     {"lat":0.0,   "lon":0.0,    "iso":""},
    }

    def tld_to_country(domain):
        if not domain:
            return "Inconnu"
        for tld in sorted(TLD_MAP.keys(), key=len, reverse=True):
            if domain.endswith(tld):
                return TLD_MAP[tld]
        return "Autres / Inconnu"

    df = df.copy()
    df["domain"]      = df["source_url"].apply(get_domain)
    df["pays_source"] = df["domain"].apply(tld_to_country)
    df["pays_iso"]    = df["pays_source"].map(lambda x: COUNTRY_COORDS.get(x,{}).get("iso",""))
    df["pays_lat"]    = df["pays_source"].map(lambda x: COUNTRY_COORDS.get(x,{}).get("lat",None))
    df["pays_lon"]    = df["pays_source"].map(lambda x: COUNTRY_COORDS.get(x,{}).get("lon",None))
    return df

# ─────────────────────────────────────────────
# INFERENCE XGBoost — pure Python (pas de dépendance xgboost)
# ─────────────────────────────────────────────
def _sigmoid(x):
    return 1.0 / (1.0 + math.exp(-max(-500.0, min(500.0, float(x)))))

def _predict_tree(tree, x):
    node = 0
    left  = tree["left_children"]
    right = tree["right_children"]
    idx   = tree["split_indices"]
    cond  = tree["split_conditions"]
    w     = tree["base_weights"]
    while True:
        if left[node] == -1:
            return w[node]
        node = left[node] if x[idx[node]] < cond[node] else right[node]

@st.cache_resource
def load_xgb_model(model_path: str):
    import json as _json
    with open(model_path) as f:
        return _json.load(f)

def xgb_predict_proba(model_json: dict, x_dict: dict) -> float:
    learner       = model_json["learner"]
    feature_names = learner["feature_names"]
    trees         = learner["gradient_booster"]["model"]["trees"]
    bs_raw        = learner["learner_model_param"]["base_score"]
    base_score    = float(re.findall(r"[\d.E+-]+", bs_raw)[0])
    x = [float(x_dict.get(feat, 0.0)) for feat in feature_names]
    raw = math.log(base_score / (1.0 - base_score))
    for tree in trees:
        raw += _predict_tree(tree, x)
    return _sigmoid(raw)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Dahomey Intel")
    st.markdown("**Analyse GDELT — Stabilité politique**")
    st.divider()

    st.markdown("### Importer vos données")
    uploaded = st.file_uploader(
        "Glissez votre fichier CSV ici", type=["csv"],
        help="Fichier CSV issu de GDELT, nettoyé au format Dahomey Intel"
    )

    if uploaded is None:
        import glob as _glob
        # Recherche automatique du CSV dans le dossier courant
        _candidates = sorted(
            _glob.glob("*.csv") +
            _glob.glob("DANHOM*.csv") +
            _glob.glob("dahom*.csv") +
            _glob.glob("GDELT*.csv")
        )
        _candidates = list(dict.fromkeys(_candidates))  # dédoublonner
        if _candidates:
            _default = _candidates[0]
            with open(_default, "rb") as f:
                raw = f.read()
            filename = _default
            st.info(f"Fichier chargé automatiquement : **{filename}**")
        else:
            st.error(
                "Aucun fichier CSV trouvé dans le dossier. "
                "Glissez votre fichier ci-dessus."
            )
            st.stop()
    else:
        raw = uploaded.read()
        filename = uploaded.name
        st.success(filename)

    df_full = load_data(raw, filename)

    st.divider()
    st.markdown("### Période d'analyse")
    mois_dispo = [MONTH_SHORT[i] for i in range(12)
                  if MONTH_SHORT[i] in df_full["month_short"].values]

    filtre_type = st.radio(
        "Sélection",
        ["Toute l'année", "Semestre", "Trimestre", "Mois personnalisés"],
        label_visibility="collapsed", key="radio_filtre"
    )

    if filtre_type == "Toute l'année":
        mois_sel = mois_dispo
    elif filtre_type == "Semestre":
        sem = st.selectbox("Semestre",
                           ["1er semestre (Jan-Juin)", "2e semestre (Juil-Déc)"],
                           key="sel_sem")
        mois_sel = mois_dispo[:6] if "1er" in sem else mois_dispo[6:]
    elif filtre_type == "Trimestre":
        tri = st.selectbox("Trimestre",
                           ["T1 (Jan-Mar)","T2 (Avr-Juin)","T3 (Juil-Sep)","T4 (Oct-Déc)"],
                           key="sel_tri")
        tranche = {"T1":slice(0,3),"T2":slice(3,6),"T3":slice(6,9),"T4":slice(9,12)}
        mois_sel = mois_dispo[tranche[tri[:2]]]
    else:
        mois_sel = st.multiselect("Choisir les mois", options=mois_dispo,
                                  default=mois_dispo, key="multi_mois")
        if not mois_sel:
            st.warning("Sélectionnez au moins un mois.")
            mois_sel = mois_dispo

    df = df_full[df_full["month_short"].isin(mois_sel)].copy()
    st.caption(f"**{len(df):,}** événements — {len(mois_sel)} mois")
    st.divider()

    st.markdown("### Navigation")
    page = st.radio(
        "Page",
        ["Vue d'ensemble",
         "Evolution dans le temps",
         "Relations entre indicateurs",
         "Qui agit ?",
         "Ou ca se passe ?",
         "Focus Police / Nord",
         "Carte du Bénin",
         "Qui parle du Bénin ?",
         "Prédictions IA"],
        label_visibility="collapsed", key="radio_page"
    )


# ═══════════════════════════════════════════════════════════
# PAGE 1 — VUE D'ENSEMBLE
# ═══════════════════════════════════════════════════════════
if page == "Vue d'ensemble":
    st.title("Vue d'ensemble — Dahomey Intel")
    st.caption(f"Fichier : **{filename}** — Période : **{', '.join(mois_sel)}**")

    alerte_stabilite(df)
    st.divider()

    gold        = df["goldstein_scale"].mean()
    tone        = df["avg_tone"].mean()
    pct_conflit = (df["quad_class"] == 4).mean() * 100
    pct_coop    = (df["quad_class"] == 1).mean() * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Evénements analysés", f"{len(df):,}", f"{len(mois_sel)} mois")
    c2.metric("Score de stabilité moyen", f"{gold:+.2f}",
              "Echelle −10 à +10 — positif = stabilisant")
    c3.metric("Ton médiatique moyen", f"{tone:.2f}",
              "Comment les médias parlent des événements")
    c4.metric("Evénements violents", f"{pct_conflit:.1f} %",
              f"Coopération : {pct_coop:.1f} %")

    st.divider()

    with st.expander("Comprendre les indicateurs — Guide décideur"):
        ic1, ic2 = st.columns(2)
        with ic1:
            st.markdown("""
**Score de stabilité** *(GoldsteinScale)*
> Chaque événement reçoit un score de **-10** (très déstabilisateur)
> à **+10** (très stabilisateur).
> La moyenne donne le niveau de stabilité général du pays.

**Ton médiatique** *(AvgTone)*
> Mesure si les journalistes parlent des événements de façon négative ou positive.
> Un score négatif indique un biais critique — fréquent pour les pays africains
> dans la presse internationale.
""")
        with ic2:
            st.markdown("""
**Type d'événement** *(Quad Class)*
> - **Coopération verbale** : déclarations positives, accords annoncés
> - **Coopération concrète** : aide matérielle, projets réalisés
> - **Tension verbale** : accusations, menaces, critiques
> - **Conflit armé / Violence** : affrontements, attaques, incidents

**Acteurs** *(Actor Type)*
> Qui est impliqué : Gouvernement, Police, Militaire,
> Organisations Internationales, Société Civile, etc.
""")

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Répartition du score de stabilité**")
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=df["goldstein_scale"], nbinsx=40,
                                   marker_color=GREEN, opacity=0.75))
        mean_g = df["goldstein_scale"].mean()
        fig.add_vline(x=mean_g, line_dash="dash", line_color=RED,
                      annotation_text=f"Moyenne : {mean_g:.2f}",
                      annotation_position="top right",
                      annotation_font_color=RED)
        fig.add_vline(x=0, line_dash="dot", line_color="gray",
                      annotation_text="Seuil zéro",
                      annotation_position="top left")
        fig.update_layout(
            xaxis_title="Score de stabilité (−10 = déstabilisant · +10 = stabilisant)",
            yaxis_title="Nombre d'événements",
            showlegend=False, template="plotly_white", height=320,
            margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True, key="chart_1")
        st.caption("Chaque barre = nombre d'événements ayant ce score.")

    with col2:
        st.markdown("**Répartition du ton médiatique**")
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(x=df["avg_tone"], nbinsx=40,
                                    marker_color=BLUE, opacity=0.75))
        mean_t = df["avg_tone"].mean()
        fig2.add_vline(x=mean_t, line_dash="dash", line_color=RED,
                       annotation_text=f"Moyenne : {mean_t:.2f}",
                       annotation_position="top right",
                       annotation_font_color=RED)
        fig2.add_vline(x=0, line_dash="dot", line_color="gray",
                       annotation_text="Neutre", annotation_position="top left")
        fig2.update_layout(
            xaxis_title="Ton médiatique (négatif ← 0 → positif)",
            showlegend=False, template="plotly_white", height=320,
            margin=dict(t=10, b=10))
        st.plotly_chart(fig2, use_container_width=True, key="chart_2")
        st.caption("La majorité des valeurs légèrement négatives reflète un biais "
                   "critique structurel de la presse internationale.")

    st.divider()
    st.markdown("**Répartition par type d'événement**")
    qc = df["quad_label"].value_counts().reset_index()
    qc.columns = ["Type", "Count"]
    fig_pie = px.pie(qc, names="Type", values="Count", color="Type",
                     color_discrete_map={v: QUAD_C[k] for k, v in QUAD_L.items()},
                     hole=0.42)
    fig_pie.update_traces(textinfo="label+percent",
                          hovertemplate="<b>%{label}</b><br>%{value:,} événements (%{percent})<extra></extra>")
    fig_pie.update_layout(template="plotly_white", height=380,
                          annotations=[dict(text="Types", x=0.5, y=0.5,
                                           font_size=13, showarrow=False)])
    st.plotly_chart(fig_pie, use_container_width=True, key="chart_3")


# ═══════════════════════════════════════════════════════════
# PAGE 2 — EVOLUTION TEMPORELLE
# ═══════════════════════════════════════════════════════════
elif page == "Evolution dans le temps":
    st.title("Evolution dans le temps")
    st.caption("Comment la stabilité et la couverture médiatique ont-elles évolué mois par mois ?")

    alerte_stabilite(df)

    monthly = (
        df.groupby(["month_num", "month_short"])
        .agg(
            avg_goldstein=("goldstein_scale","mean"),
            std_goldstein=("goldstein_scale","std"),
            avg_tone=("avg_tone","mean"),
            std_tone=("avg_tone","std"),
            num_events=("event_code","count"),
            pct_conflict=("quad_class", lambda x: (x==4).mean()*100),
            pct_coop=("quad_class", lambda x: (x==1).mean()*100),
        )
        .reset_index().sort_values("month_num")
    )

    xi   = monthly["month_short"].tolist()
    g    = monthly["avg_goldstein"].values
    se_g = monthly["std_goldstein"].values / np.sqrt(monthly["num_events"].values)
    t    = monthly["avg_tone"].values
    se_t = monthly["std_tone"].values / np.sqrt(monthly["num_events"].values)
    pc   = monthly["pct_conflict"].values

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        subplot_titles=("Score de stabilité mensuel",
                                        "Ton médiatique mensuel",
                                        "% d'événements violents"),
                        vertical_spacing=0.10)

    fig.add_trace(go.Scatter(
        x=xi+xi[::-1],
        y=list(g+1.96*se_g)+list((g-1.96*se_g)[::-1]),
        fill="toself", fillcolor="rgba(29,158,117,0.12)",
        line=dict(color="rgba(0,0,0,0)"), name="Marge (95%)", showlegend=True
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=xi, y=g, mode="lines+markers",
        line=dict(color=GREEN, width=2.5),
        marker=dict(size=8, color="white", line=dict(color=GREEN, width=2.5)),
        name="Score de stabilité",
        hovertemplate="<b>%{x}</b><br>Score : %{y:.2f}<extra></extra>"
    ), row=1, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color=RED, line_width=1,
                  opacity=0.5, annotation_text="Seuil zéro",
                  annotation_position="right", row=1, col=1)
    fig.add_hline(y=g.mean(), line_dash="dot", line_color="gray", line_width=1,
                  annotation_text=f"Moy. ({g.mean():.2f})",
                  annotation_position="left", row=1, col=1)

    fig.add_trace(go.Scatter(
        x=xi+xi[::-1],
        y=list(t+1.96*se_t)+list((t-1.96*se_t)[::-1]),
        fill="toself", fillcolor="rgba(55,138,221,0.12)",
        line=dict(color="rgba(0,0,0,0)"), showlegend=False
    ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=xi, y=t, mode="lines+markers",
        line=dict(color=BLUE, width=2.5),
        marker=dict(size=8, symbol="square", color="white",
                    line=dict(color=BLUE, width=2.5)),
        name="Ton médiatique",
        hovertemplate="<b>%{x}</b><br>Ton : %{y:.2f}<extra></extra>"
    ), row=2, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color="gray",
                  line_width=1, row=2, col=1)

    bar_colors = [RED if v > 15 else ORANGE if v > 10 else GREEN for v in pc]
    fig.add_trace(go.Bar(x=xi, y=pc, marker_color=bar_colors,
                         name="% conflits armés",
                         hovertemplate="<b>%{x}</b><br>Conflits : %{y:.1f}%<extra></extra>"
                         ), row=3, col=1)
    fig.add_hline(y=pc.mean(), line_dash="dot", line_color="gray", line_width=1,
                  annotation_text=f"Moy. {pc.mean():.1f}%",
                  annotation_position="right", row=3, col=1)

    fig.update_layout(height=650, template="plotly_white",
                      legend=dict(orientation="h", y=1.04), margin=dict(t=60))
    st.plotly_chart(fig, use_container_width=True, key="chart_4")

    with st.expander("Tableau mensuel détaillé"):
        disp = monthly[["month_short","avg_goldstein","avg_tone",
                        "num_events","pct_conflict","pct_coop"]].copy()
        disp.columns = ["Mois","Score stabilité","Ton médiatique",
                        "Nb événements","% Conflits armés","% Coopération"]
        disp = disp.set_index("Mois")
        def color_gold(val):
            if val < 0:  return "color: #D85A30; font-weight:600"
            if val > 1:  return "color: #1D9E75; font-weight:600"
            return ""
        def color_conflict(val):
            if val > 15: return "color: #D85A30; font-weight:600"
            if val > 10: return "color: #EF9F27"
            return ""
        styled = (disp.style.format("{:.2f}")
                  .applymap(color_gold, subset=["Score stabilité"])
                  .applymap(color_conflict, subset=["% Conflits armés"]))
        st.dataframe(styled, use_container_width=True, key="df_1")

    st.divider()
    best  = monthly.loc[monthly["avg_goldstein"].idxmax(), "month_short"]
    worst = monthly.loc[monthly["avg_goldstein"].idxmin(), "month_short"]
    st.success(f"Mois le plus stable : **{best}** — Mois le plus fragile : **{worst}**")


# ═══════════════════════════════════════════════════════════
# PAGE 3 — CORRELATIONS
# ═══════════════════════════════════════════════════════════
elif page == "Relations entre indicateurs":
    st.title("Relations entre indicateurs")
    st.caption("Quels indicateurs évoluent ensemble ?")

    cols_tech = ["goldstein_scale","avg_tone","num_articles",
                 "num_mentions","num_sources","quad_class","has_actor2"]
    labels_fr = ["Score de stabilité","Ton médiatique",
                 "Couverture (articles)","Nombre de mentions",
                 "Nombre de sources","Type d'événement","2 acteurs identifiés"]

    corr = df[cols_tech].corr()
    corr.index   = labels_fr
    corr.columns = labels_fr
    mask = np.triu(np.ones_like(corr, dtype=bool))
    corr_masked = corr.where(~mask)

    fig = go.Figure(go.Heatmap(
        z=corr_masked.values, x=labels_fr, y=labels_fr,
        colorscale="RdYlGn", zmid=0, zmin=-1, zmax=1,
        text=corr_masked.round(2).values, texttemplate="%{text}",
        hoverongaps=False,
        hovertemplate="<b>%{x}</b> × <b>%{y}</b><br>Corrélation : %{z:.2f}<extra></extra>",
        colorbar=dict(title="Force du lien",
                      tickvals=[-1,-0.5,0,0.5,1],
                      ticktext=["-1 Opposés","-0.5 Lien inverse",
                                "0 Aucun lien","+0.5 Lien positif","+1 Identiques"])
    ))
    fig.update_layout(title="Comment les indicateurs sont-ils liés entre eux ?",
                      height=560, template="plotly_white",
                      xaxis=dict(tickangle=-35), margin=dict(t=60, b=80))
    st.plotly_chart(fig, use_container_width=True, key="chart_5")

    st.divider()
    st.markdown("### Ce que ca signifie concrètement")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.error("**Lien fort négatif (−0.78)** — Score de stabilité vs Type d'événement\n\n"
                 "Plus l'événement est violent, plus le score est bas. "
                 "Ces deux indicateurs sont redondants.")
    with c2:
        st.success("**Lien fort positif (+0.96)** — Couverture articles vs Mentions\n\n"
                   "Plus un événement est couvert, plus il est mentionné. "
                   "Utiliser l'un ou l'autre suffit.")
    with c3:
        st.warning("**Lien modéré positif (+0.36)** — Score de stabilité vs Ton médiatique\n\n"
                   "Quand les événements sont plus stables, les médias en parlent "
                   "moins négativement. Lien modéré.")


# ═══════════════════════════════════════════════════════════
# PAGE 4 — QUI AGIT ?
# ═══════════════════════════════════════════════════════════
elif page == "Qui agit ?":
    st.title("Qui agit ? — Analyse des acteurs")
    st.caption("Quels acteurs sont les plus présents et quel est leur impact sur la stabilité ?")

    alerte_stabilite(df)
    st.divider()

    tab1, tab2, tab3 = st.tabs([
        "Acteurs les plus présents",
        "Impact sur la stabilité",
        "Qui agit — mois par mois ?"
    ])

    with tab1:
        top_act = (
            df[~df["actor1_name"].isin(["Acteur non identifié","Unknown","UNKNOWN"])]
            ["actor1_name"].value_counts().head(12).reset_index()
        )
        top_act.columns = ["Acteur","Nombre d'événements"]
        top_act = top_act.sort_values("Nombre d'événements")
        fig = go.Figure(go.Bar(
            x=top_act["Nombre d'événements"], y=top_act["Acteur"],
            orientation="h", marker_color=BLUE, opacity=0.82,
            text=top_act["Nombre d'événements"].apply(lambda v: f"{v:,}"),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Evénements : %{x:,}<extra></extra>"
        ))
        fig.update_layout(title="Acteurs les plus fréquemment impliqués",
                          xaxis_title="Nombre d'événements recensés",
                          template="plotly_white", height=450,
                          margin=dict(l=20, r=60))
        st.plotly_chart(fig, use_container_width=True, key="chart_6")
        st.caption("'BENIN' désigne les événements où le pays est cité comme entité principale.")

    with tab2:
        act_stats = (
            df[~df["actor1_type"].isin(["UNKNOWN","Unknown"])]
            .groupby("actor1_type")
            .agg(count=("event_code","count"), avg_g=("goldstein_scale","mean"))
            .reset_index()
            .query("count >= 20")
            .sort_values("avg_g")
        )
        act_stats["Acteur"]     = act_stats["actor1_type"].map(CAMEO).fillna(act_stats["actor1_type"])
        act_stats["Couleur"]    = act_stats["avg_g"].apply(lambda g: RED if g < 0 else GREEN)
        act_stats["Interp."]    = act_stats["avg_g"].apply(
            lambda g: "Déstabilisateur" if g < -1
            else "Légèrement négatif" if g < 0
            else "Stabilisateur" if g > 1
            else "Neutre"
        )
        fig = go.Figure(go.Bar(
            x=act_stats["avg_g"], y=act_stats["Acteur"], orientation="h",
            marker_color=act_stats["Couleur"], opacity=0.85,
            text=act_stats["avg_g"].round(2), textposition="outside",
            hovertemplate="<b>%{y}</b><br>Score : %{x:.2f}<extra></extra>"
        ))
        fig.add_vline(x=0, line_dash="dot", line_color="gray",
                      annotation_text="Seuil zéro", annotation_position="top right")
        fig.update_layout(
            title="Score de stabilité moyen par type d'acteur",
            xaxis_title="Score de stabilité moyen",
            template="plotly_white", height=500, margin=dict(l=20, r=60))
        st.plotly_chart(fig, use_container_width=True, key="chart_7")

        with st.expander("Tableau détaillé par acteur"):
            show = act_stats[["Acteur","avg_g","count","Interp."]].copy()
            show.columns = ["Type d'acteur","Score stabilité moy.","Nb événements","Interprétation"]
            st.dataframe(show.set_index("Type d'acteur")
                         .style.format({"Score stabilité moy.":"{:.2f}"}),
                         use_container_width=True, key="df_2")

    with tab3:
        top_types = ["GOV","MIL","COP","CVL","LEG","EDU","IGO","MED","BUS","OPP"]
        df_f = df[df["actor1_type"].isin(top_types)].copy()
        df_f["Acteur"] = df_f["actor1_type"].map(CAMEO)
        pivot = df_f.pivot_table(values="goldstein_scale", index="Acteur",
                                  columns="month_short", aggfunc="mean")
        col_order = [s for s in MONTH_SHORT if s in pivot.columns]
        pivot = pivot.reindex(columns=col_order)
        fig = go.Figure(go.Heatmap(
            z=pivot.values, x=col_order, y=pivot.index.tolist(),
            colorscale="RdYlGn", zmid=0, zmin=-5, zmax=5,
            text=np.round(pivot.values, 1), texttemplate="%{text}",
            colorbar=dict(title="Score stabilité",
                          tickvals=[-5,-2.5,0,2.5,5],
                          ticktext=["-5 Très déstab.","-2.5","0 Neutre","2.5","5 Très stab."]),
            hovertemplate="<b>%{y}</b> en <b>%{x}</b><br>Score : %{z:.1f}<extra></extra>"
        ))
        fig.update_layout(
            title="Quel acteur a eu quel impact, et quel mois ?",
            template="plotly_white", height=420, margin=dict(t=80))
        st.plotly_chart(fig, use_container_width=True, key="chart_8")
        st.caption("Les cases vides = aucun événement impliquant cet acteur ce mois-là.")


# ═══════════════════════════════════════════════════════════
# PAGE 5 — OU CA SE PASSE ?
# ═══════════════════════════════════════════════════════════
elif page == "Ou ca se passe ?":
    st.title("Ou ca se passe ? — Analyse géographique")
    st.caption("Quelles zones du Bénin concentrent les événements et l'instabilité ?")

    alerte_stabilite(df)
    st.divider()

    col1, col2 = st.columns([1.4, 1])

    with col1:
        locs = (
            df[~df["geo_full_name"].isin(["Benin","Bénin"])]
            ["geo_full_name"].value_counts().head(14).reset_index()
        )
        locs.columns = ["loc","count"]
        locs["Localité"] = locs["loc"].apply(lambda x: x.split(",")[0].strip())
        locs["zone"]     = locs["loc"].apply(
            lambda x: "Nord (sensible)" if any(k in x for k in NORTH_KW) else "Sud / Centre")
        locs = locs.sort_values("count")
        fig = go.Figure(go.Bar(
            x=locs["count"], y=locs["Localité"], orientation="h",
            marker_color=locs["zone"].map({"Nord (sensible)": RED, "Sud / Centre": GREEN}),
            opacity=0.85,
            text=locs["count"].apply(lambda v: f"{v:,}"), textposition="outside",
            hovertemplate="<b>%{y}</b><br>Evénements : %{x:,}<extra></extra>"
        ))
        fig.update_layout(title="Localités les plus touchées",
                          xaxis_title="Nombre d'événements recensés",
                          template="plotly_white", height=460, margin=dict(r=60))
        st.plotly_chart(fig, use_container_width=True, key="chart_9")
        st.caption("Rouge = zone nord sensible — Vert = sud / centre")

    with col2:
        zone_stats = (
            df.groupby("zone")
            .agg(avg_g=("goldstein_scale","mean"),
                 pct_c=("quad_class", lambda x: (x==4).mean()*100),
                 count=("event_code","count"))
            .reset_index()
        )
        fig2 = go.Figure(go.Bar(
            x=zone_stats["zone"], y=zone_stats["avg_g"],
            marker_color=[RED, GREEN],
            text=zone_stats["avg_g"].round(2), textposition="outside",
            width=0.45,
            hovertemplate="<b>%{x}</b><br>Score : %{y:.2f}<extra></extra>"
        ))
        fig2.add_hline(y=0, line_dash="dash", line_color="gray",
                       annotation_text="Seuil zéro")
        fig2.update_layout(title="Score de stabilité moyen — Nord vs Sud",
                           yaxis_title="Score de stabilité moyen",
                           template="plotly_white", height=300)
        st.plotly_chart(fig2, use_container_width=True, key="chart_10")

        nord_g = zone_stats.set_index("zone")["avg_g"].get("Nord (sensible)", 0)
        sud_g  = zone_stats.set_index("zone")["avg_g"].get("Sud / Centre", 0)
        st.metric("Ecart Nord − Sud", f"{nord_g - sud_g:.2f} points",
                  delta=f"{nord_g - sud_g:.2f}", delta_color="inverse")
        nord_pct = zone_stats.set_index("zone")["pct_c"].get("Nord (sensible)", 0)
        sud_pct  = zone_stats.set_index("zone")["pct_c"].get("Sud / Centre", 0)
        st.metric("% conflits armés Nord", f"{nord_pct:.1f} %",
                  delta=f"Sud : {sud_pct:.1f}%", delta_color="inverse")

    st.divider()
    st.markdown("### Score de stabilité selon le type d'événement")
    order  = [QUAD_L[k] for k in [1,2,3,4]]
    colors = [QUAD_C[k] for k in [1,2,3,4]]
    fig3 = go.Figure()
    for label, color in zip(order, colors):
        vals = df[df["quad_label"] == label]["goldstein_scale"].dropna()
        fig3.add_trace(go.Box(
            y=vals, name=label, marker_color=color, line_color=color,
            boxpoints="outliers", marker_size=3, opacity=0.8,
            hovertemplate=f"<b>{label}</b><br>Score : %{{y:.1f}}<extra></extra>"
        ))
    fig3.update_layout(xaxis_title="Type d'événement", yaxis_title="Score de stabilité",
                       showlegend=False, template="plotly_white", height=380)
    st.plotly_chart(fig3, use_container_width=True, key="chart_11")


# ═══════════════════════════════════════════════════════════
# PAGE 6 — FOCUS POLICE / NORD
# ═══════════════════════════════════════════════════════════
elif page == "Focus Police / Nord":
    st.title("Focus Police × Nord — Hypothèse vérifiée")
    st.caption("La Police est-elle plus déstabilisatrice au Nord qu'au Sud ?")

    st.warning("Hypothèse de départ : Les creux de stabilité observés au Nord pourraient être "
               "liés aux interventions de la Police dans des contextes de crise sécuritaire.")
    st.divider()

    st.subheader("Impact de chaque acteur selon la zone géographique")
    actor_zone = (
        df[df["actor1_type"].isin(["GOV","COP","MIL","CVL","IGO","OPP","UAF","MED","EDU","BUS"])]
        .groupby(["zone","actor1_type"])
        .agg(avg_gold=("goldstein_scale","mean"), count=("event_code","count"))
        .reset_index().query("count >= 5")
    )
    actor_zone["Acteur"] = actor_zone["actor1_type"].map(CAMEO).fillna(actor_zone["actor1_type"])
    pivot_bar = (actor_zone.pivot(index="Acteur", columns="zone", values="avg_gold")
                 .fillna(0).sort_values("Nord (sensible)"))
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Nord (sensible)", x=pivot_bar.index,
                         y=pivot_bar["Nord (sensible)"],
                         marker_color=RED, opacity=0.85,
                         hovertemplate="<b>%{x}</b> au Nord<br>Score : %{y:.2f}<extra></extra>"))
    fig.add_trace(go.Bar(name="Sud / Centre", x=pivot_bar.index,
                         y=pivot_bar["Sud / Centre"],
                         marker_color=GREEN, opacity=0.85,
                         hovertemplate="<b>%{x}</b> au Sud<br>Score : %{y:.2f}<extra></extra>"))
    fig.add_hline(y=0, line_dash="dot", line_color="gray", annotation_text="Seuil zéro")
    fig.update_layout(barmode="group", xaxis_tickangle=-20,
                      yaxis_title="Score de stabilité moyen",
                      template="plotly_white", height=420,
                      legend=dict(orientation="h", y=1.06))
    st.plotly_chart(fig, use_container_width=True, key="chart_12")
    st.caption("Une barre rouge plus basse que la verte = acteur plus déstabilisateur au Nord.")

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Volume et impact de la Police par zone")
        police_zone = (
            df[df["actor1_type"] == "COP"].groupby("zone")
            .agg(count=("event_code","count"), avg_gold=("goldstein_scale","mean"))
            .reset_index()
        )
        fig2 = go.Figure(go.Bar(
            x=police_zone["zone"], y=police_zone["count"],
            marker_color=[RED, GREEN],
            text=[f"{int(r['count'])} événements / Score : {r['avg_gold']:.2f}"
                  for _, r in police_zone.iterrows()],
            textposition="outside", width=0.45,
            hovertemplate="<b>%{x}</b><br>Evénements Police : %{y}<extra></extra>"
        ))
        fig2.update_layout(yaxis_title="Interventions policières recensées",
                           template="plotly_white", height=320)
        st.plotly_chart(fig2, use_container_width=True, key="chart_13")
        st.caption("La Police intervient moins souvent au Nord mais dans des contextes plus graves.")

    with col2:
        st.subheader("Impact de la Police mois par mois")
        police_pivot = (
            df[df["actor1_type"] == "COP"]
            .groupby(["zone","month_short"])["goldstein_scale"].mean().unstack()
        )
        col_order = [s for s in MONTH_SHORT if s in police_pivot.columns]
        police_pivot = police_pivot.reindex(columns=col_order)
        fig3 = go.Figure(go.Heatmap(
            z=police_pivot.values, x=col_order, y=police_pivot.index.tolist(),
            colorscale="RdYlGn", zmid=0, zmin=-6, zmax=3,
            text=np.round(police_pivot.values, 1), texttemplate="%{text}",
            colorbar=dict(title="Score stabilité"),
            hovertemplate="Police · <b>%{y}</b> en <b>%{x}</b><br>Score : %{z:.1f}<extra></extra>"
        ))
        fig3.update_layout(template="plotly_white", height=240, margin=dict(t=20, b=10))
        st.plotly_chart(fig3, use_container_width=True, key="chart_14")
        st.caption("Juin au Nord = −6.0 : pic de déstabilisation maximal de l'année.")

    st.divider()
    st.subheader("Acteurs les plus déstabilisateurs au Nord")
    north_actors = (
        df[df["zone"] == "Nord (sensible)"].groupby("actor1_type")
        .agg(avg_gold=("goldstein_scale","mean"), count=("event_code","count"))
        .reset_index().query("count >= 5").sort_values("avg_gold").head(12)
    )
    north_actors["Acteur"]  = north_actors["actor1_type"].map(CAMEO).fillna(north_actors["actor1_type"])
    north_actors["Couleur"] = north_actors["avg_gold"].apply(
        lambda g: RED if g < -2 else ORANGE if g < 0 else GREEN)
    fig4 = go.Figure(go.Bar(
        x=north_actors["avg_gold"], y=north_actors["Acteur"], orientation="h",
        marker_color=north_actors["Couleur"], opacity=0.85,
        text=[f"{g:.2f}  ({int(c)} événements)"
              for g, c in zip(north_actors["avg_gold"], north_actors["count"])],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Score : %{x:.2f}<extra></extra>"
    ))
    fig4.add_vline(x=0, line_dash="dot", line_color="gray", annotation_text="Seuil zéro")
    fig4.update_layout(xaxis_title="Score de stabilité moyen au Nord",
                       template="plotly_white", height=400, margin=dict(r=80))
    st.plotly_chart(fig4, use_container_width=True, key="chart_15")

    st.divider()
    st.error(
        "**Conclusion — Hypothèse confirmée par les données**\n\n"
        "La Police intervient au Nord dans des contextes de crise extrême "
        "(score moyen −2.93 au Nord vs −1.47 au Sud). "
        "Les pics de déstabilisation en **juin (−6.0)** et **novembre (−4.9)** "
        "correspondent aux moments d'intervention policière les plus intenses. "
        "Les acteurs les plus déstabilisateurs restent les **Rebelles (−9.53)** "
        "et les **Forces non-identifiées (−5.06)**. "
        "La Police est le révélateur des crises, pas leur cause première."
    )
    st.warning(
        "**Recommandation pour les décideurs**\n\n"
        "Renforcer la coopération concrète (aide matérielle, projets) "
        "dans les localités nordiques : Alibori, Kandi, Porga, Karimama. "
        "La coopération concrète a un score de stabilité moyen de +7 — "
        "levier d'action le plus puissant identifié dans ces données."
    )


# ═══════════════════════════════════════════════════════════
# PAGE 7 — CARTE DU BÉNIN
# ═══════════════════════════════════════════════════════════
elif page == "Carte du Bénin":
    st.title("Carte du Bénin — Zones à risque")
    st.caption(f"Localisation géographique des événements — Période : {', '.join(mois_sel)}")

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        type_evt = st.multiselect(
            "Type d'événement",
            options=["Coopération verbale","Coopération concrète",
                     "Tension verbale","Conflit armé / Violence"],
            default=["Coopération verbale","Coopération concrète",
                     "Tension verbale","Conflit armé / Violence"],
            key="ms_type_evt"
        )
    with col_f2:
        min_events = st.slider("Minimum d'événements par zone", 1, 50, 5,
                               key="slider_min_events")
    with col_f3:
        indicateur = st.selectbox(
            "Colorier par",
            ["Score de stabilité moyen","% de conflits armés","Nombre d'événements"],
            key="sel_indicateur_carte"
        )

    st.divider()

    df_map = df.copy()
    df_map["quad_label"] = df_map["quad_class"].map(QUAD_L)
    if type_evt:
        df_map = df_map[df_map["quad_label"].isin(type_evt)]

    df_real = df_map[
        ~((df_map["latitude"].round(1) == 9.5) &
          (df_map["longitude"].round(2) == 2.25))
    ].copy()

    agg = (
        df_real.groupby(["geo_full_name","latitude","longitude"])
        .agg(count=("event_code","count"),
             avg_gold=("goldstein_scale","mean"),
             avg_tone=("avg_tone","mean"),
             pct_conflict=("quad_class", lambda x: (x==4).mean()*100),
             pct_coop=("quad_class", lambda x: (x==1).mean()*100),
             nb_articles=("num_articles","sum"))
        .reset_index().query(f"count >= {min_events}")
    )
    agg["ville"] = agg["geo_full_name"].apply(lambda x: x.split(",")[0].strip())

    if indicateur == "Score de stabilité moyen":
        agg["color_val"] = agg["avg_gold"]
        color_label = "Score stabilité"
        cmin, cmax, cmid = -6, 6, 0
        colorscale = "RdYlGn"
    elif indicateur == "% de conflits armés":
        agg["color_val"] = agg["pct_conflict"]
        color_label = "% conflits armés"
        cmin, cmax, cmid = 0, 60, 20
        colorscale = "RdYlGn_r"
    else:
        agg["color_val"] = agg["count"]
        color_label = "Nb événements"
        cmin = agg["count"].min()
        cmax = agg["count"].max()
        cmid = agg["count"].median()
        colorscale = "Blues"

    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
        lat=agg["latitude"], lon=agg["longitude"], mode="markers",
        marker=go.scattermapbox.Marker(
            size=np.clip(agg["count"] / agg["count"].max() * 50, 8, 55),
            color=agg["color_val"], colorscale=colorscale,
            cmin=cmin, cmax=cmax, cmid=cmid, opacity=0.82,
            colorbar=dict(title=color_label, thickness=14, len=0.65,
                          x=1.0, tickformat=".1f")
        ),
        text=agg.apply(lambda r: (
            f"<b>{r['ville']}</b><br>"
            f"Evénements : {int(r['count'])}<br>"
            f"Score stabilité : {r['avg_gold']:.2f}<br>"
            f"% Conflits : {r['pct_conflict']:.1f}%<br>"
            f"Ton médiatique : {r['avg_tone']:.2f}"
        ), axis=1),
        hoverinfo="text", hovertemplate="%{text}<extra></extra>", name=""
    ))
    fig.update_layout(
        mapbox=dict(style="carto-positron", center=dict(lat=9.3, lon=2.3), zoom=6.2),
        height=580, margin=dict(t=0, b=0, l=0, r=0), showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key="chart_16")

    l1, l2, l3 = st.columns(3)
    with l1:
        st.info("**Zone nord sensible**\nAlibori · Kandi · Porga · Karimama · Parakou")
    with l2:
        st.success("**Zone sud / centre**\nOuidah · Porto-Novo · Abomey · Lokossa")
    with l3:
        st.info(f"**{len(agg)} zones** affichées sur "
                f"{df_map['geo_full_name'].nunique()} localités recensées "
                f"(min. {min_events} événements/zone)")

    st.divider()
    st.subheader("Classement des zones par niveau de risque")
    agg_show = agg.sort_values("avg_gold").copy()
    agg_show["Niveau"] = agg_show["avg_gold"].apply(
        lambda g: "Très instable" if g < -2
        else "Instable" if g < 0
        else "Modéré" if g < 1
        else "Stable"
    )
    agg_show = agg_show[["ville","count","avg_gold","pct_conflict","avg_tone","Niveau"]].copy()
    agg_show.columns = ["Localité","Evénements","Score stabilité",
                        "% Conflits armés","Ton médiatique","Niveau de risque"]

    def color_gold_map(val):
        if val < -2: return "background-color:#fdecea;color:#D85A30;font-weight:600"
        if val <  0: return "background-color:#fff3e0"
        if val >  1: return "background-color:#e8f5e9;color:#1D9E75"
        return ""

    styled = (agg_show.set_index("Localité").style
              .format({"Score stabilité":"{:.2f}",
                       "% Conflits armés":"{:.1f}%",
                       "Ton médiatique":"{:.2f}"})
              .applymap(color_gold_map, subset=["Score stabilité"]))
    st.dataframe(styled, use_container_width=True, key="df_3")


# ═══════════════════════════════════════════════════════════
# PAGE 8 — QUI PARLE DU BÉNIN ?
# ═══════════════════════════════════════════════════════════
elif page == "Qui parle du Bénin ?":
    st.title("Qui parle du Bénin ? — Carte des médias")
    st.caption(
        "D'où viennent les articles qui couvrent le Bénin et quel est leur ton ? "
        f"Période : {', '.join(mois_sel)}"
    )

    df_media = extract_pays_source(df)
    df_media = df_media[
        ~df_media["pays_source"].isin(["Inconnu","Autres / Inconnu","International",""])
    ]

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        metrique = st.selectbox(
            "Colorier la carte par",
            ["Ton médiatique moyen (négatif = critique)",
             "Volume d'articles publiés",
             "Nombre d'événements couverts"],
            key="sel_metrique_medias"
        )
    with col_f2:
        min_pays = st.slider("Minimum d'articles par pays", 10, 500, 30,
                             key="slider_min_pays")

    st.divider()

    pays_stats = (
        df_media.groupby(["pays_source","pays_iso","pays_lat","pays_lon"])
        .agg(nb_evenements=("event_code","count"),
             nb_articles=("num_articles","sum"),
             avg_tone=("avg_tone","mean"),
             avg_gold=("goldstein_scale","mean"),
             pct_negatif=("avg_tone", lambda x: (x < -2).mean()*100),
             nb_sources=("num_sources","sum"))
        .reset_index()
        .query(f"nb_articles >= {min_pays}")
        .sort_values("nb_articles", ascending=False)
    )

    if len(pays_stats) == 0:
        st.warning("Aucun pays ne correspond aux critères. Réduisez le seuil minimum.")
    else:
        if "Ton médiatique" in metrique:
            pays_stats["color_val"] = pays_stats["avg_tone"]
            color_label = "Ton médiatique moyen"
            colorscale = "RdYlGn"
            cmin, cmax, cmid = -5, 5, 0
        elif "Volume" in metrique:
            pays_stats["color_val"] = pays_stats["nb_articles"]
            color_label = "Nombre d'articles"
            colorscale = "Blues"
            cmin = 0
            cmax = pays_stats["nb_articles"].max()
            cmid = pays_stats["nb_articles"].median()
        else:
            pays_stats["color_val"] = pays_stats["nb_evenements"]
            color_label = "Evénements couverts"
            colorscale = "Purples"
            cmin = 0
            cmax = pays_stats["nb_evenements"].max()
            cmid = pays_stats["nb_evenements"].median()

        fig = go.Figure()
        fig.add_trace(go.Choropleth(
            locations=pays_stats["pays_iso"], z=pays_stats["color_val"],
            colorscale=colorscale, zmid=cmid, zmin=cmin, zmax=cmax,
            text=pays_stats.apply(lambda r: (
                f"<b>{r['pays_source']}</b><br>"
                f"Articles : {int(r['nb_articles']):,}<br>"
                f"Evénements : {int(r['nb_evenements']):,}<br>"
                f"Ton moyen : {r['avg_tone']:.2f}<br>"
                f"% très négatifs : {r['pct_negatif']:.1f}%"
            ), axis=1),
            hovertemplate="%{text}<extra></extra>",
            colorbar=dict(title=color_label, thickness=14, len=0.65, tickformat=".1f"),
            showscale=True, name=""
        ))

        size_max = pays_stats["nb_articles"].max()
        fig.add_trace(go.Scattergeo(
            lat=pays_stats["pays_lat"], lon=pays_stats["pays_lon"],
            mode="markers+text",
            marker=dict(
                size=np.clip(pays_stats["nb_articles"] / size_max * 60, 8, 65),
                color=pays_stats["avg_tone"], colorscale="RdYlGn",
                cmin=-5, cmax=5, opacity=0.75,
                line=dict(color="white", width=1), showscale=False),
            text=pays_stats["pays_source"],
            textfont=dict(size=9, color="black"),
            textposition="top center",
            hovertext=pays_stats.apply(lambda r: (
                f"<b>{r['pays_source']}</b><br>"
                f"{int(r['nb_articles']):,} articles<br>"
                f"Ton : {r['avg_tone']:.2f}"
            ), axis=1),
            hovertemplate="%{hovertext}<extra></extra>",
            showlegend=False, name="Volume"
        ))
        fig.update_layout(
            geo=dict(showframe=False, showcoastlines=True, coastlinecolor="#aaa",
                     showland=True, landcolor="#f5f5f0", showocean=True,
                     oceancolor="#e8f4f8", showcountries=True, countrycolor="#ddd",
                     showlakes=False, projection_type="natural earth"),
            height=560, margin=dict(t=10, b=10, l=0, r=0), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key="chart_17")
        st.caption("La couleur des pays reflète l'indicateur sélectionné. "
                   "La taille des bulles est proportionnelle au volume d'articles.")

        st.divider()
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Pays ayant écrit sur le Bénin", f"{len(pays_stats)}")
        k2.metric("Pays le plus actif",
                  pays_stats.iloc[0]["pays_source"],
                  f"{int(pays_stats.iloc[0]['nb_articles']):,} articles")
        k3.metric("Ton médiatique moyen global",
                  f"{pays_stats['avg_tone'].mean():.2f}")
        most_neg = pays_stats.loc[pays_stats["avg_tone"].idxmin(), "pays_source"]
        k4.metric("Pays le plus critique", most_neg,
                  f"Ton : {pays_stats['avg_tone'].min():.2f}",
                  delta_color="inverse")

        st.divider()
        st.subheader("Détail par pays")
        show = pays_stats[["pays_source","nb_articles","nb_evenements",
                           "avg_tone","pct_negatif","avg_gold"]].copy()
        show.columns = ["Pays","Articles publiés","Evénements couverts",
                        "Ton médiatique moyen","% articles très négatifs",
                        "Score stabilité moyen"]

        def color_tone(val):
            if val < -2: return "background:#fdecea;color:#D85A30;font-weight:600"
            if val <  0: return "background:#fff3e0"
            if val >  1: return "background:#e8f5e9;color:#1D9E75"
            return ""
        def color_negatif(val):
            if val > 60: return "background:#fdecea;font-weight:600"
            if val > 40: return "background:#fff3e0"
            return ""

        styled = (show.set_index("Pays").style
                  .format({"Articles publiés":"{:,.0f}",
                           "Evénements couverts":"{:,.0f}",
                           "Ton médiatique moyen":"{:.2f}",
                           "% articles très négatifs":"{:.1f}%",
                           "Score stabilité moyen":"{:.2f}"})
                  .applymap(color_tone, subset=["Ton médiatique moyen"])
                  .applymap(color_negatif, subset=["% articles très négatifs"]))
        st.dataframe(styled, use_container_width=True, key="df_4")

        st.divider()
        st.subheader("Top pays par volume d'articles")
        top15 = pays_stats.head(15).sort_values("nb_articles")
        bar_colors = [RED if t < -2 else ORANGE if t < 0 else GREEN
                      for t in top15["avg_tone"]]
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=top15["nb_articles"], y=top15["pays_source"],
            orientation="h", marker_color=bar_colors, opacity=0.85,
            text=top15.apply(
                lambda r: f"{int(r['nb_articles']):,} articles / ton {r['avg_tone']:.2f}",
                axis=1),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Articles : %{x:,}<extra></extra>"
        ))
        fig2.add_vline(x=top15["nb_articles"].mean(), line_dash="dot",
                       line_color="gray", annotation_text="Moyenne",
                       annotation_position="top right")
        fig2.update_layout(xaxis_title="Nombre d'articles publiés",
                           template="plotly_white", height=440,
                           margin=dict(r=80), showlegend=False)
        st.plotly_chart(fig2, use_container_width=True, key="chart_18")

        lc1, lc2, lc3 = st.columns(3)
        lc1.error("**Ton < −2** : couverture très critique du Bénin")
        lc2.warning("**−2 < Ton < 0** : couverture légèrement négative")
        lc3.success("**Ton > 0** : couverture neutre ou positive")


# ═══════════════════════════════════════════════════════════
# PAGE 9 — PRÉDICTIONS IA (XGBoost)
# ═══════════════════════════════════════════════════════════
elif page == "Prédictions IA":
 
    # ── Chargement modèle ──────────────────────────────────────
    import os, glob as _mglob, json as _json
    _model_candidates = sorted(
        _mglob.glob("*.json") +
        _mglob.glob("dahome*.json") +
        _mglob.glob("DAHOM*.json") +
        _mglob.glob("xgboost*.json")
    )
    _model_candidates = [p for p in dict.fromkeys(_model_candidates)
                         if "metadata" not in p.lower()]
 
    model_json = None
    for _mp in _model_candidates:
        try:
            _c = load_xgb_model(_mp)
            if "learner" in _c:
                model_json = _c
                break
        except Exception:
            continue
 
    if model_json is None:
        st.error(
            "Modèle XGBoost introuvable.\n\n"
            "Placez **dahome_Intel_xgboost_v1.json** "
            "dans le même dossier que le dashboard."
        )
        st.stop()
 
    # ── Paramètres depuis metadata ──────────────────────────────
    SEUIL_STD      = 0.50
    SEUIL_SENSIBLE = 0.35
    AUC            = 0.87
    RECALL_50      = 0.75
    RECALL_35      = 0.81
    FEAT_COLS      = ["ema_30","sma_7","stress_index","volume_ratio",
                      "score_lag1","score_lag3","score_lag7",
                      "tone_ema_7","tone_stress",
                      "conflict_ratio_7d","conflict_momentum"]
 
    # ── Fonction calcul features ────────────────────────────────
    def compute_features(d: pd.DataFrame) -> pd.DataFrame:
        d = d.copy().sort_values("month_num")
        d["score"]    = d["goldstein_scale"]
        d["ema_30"]   = d["score"].ewm(span=30, adjust=False).mean()
        d["sma_7"]    = d["score"].rolling(7, min_periods=1).mean()
        d["stress_index"] = (
            ((d["quad_class"]==4).astype(float)*100)
            .rolling(7, min_periods=1).mean()
        )
        med = d["num_articles"].median()
        d["volume_ratio"]     = d["num_articles"] / (med + 1e-6)
        d["score_lag1"]       = d["score"].shift(1).fillna(d["score"])
        d["score_lag3"]       = d["score"].shift(3).fillna(d["score"])
        d["score_lag7"]       = d["score"].shift(7).fillna(d["score"])
        d["tone_ema_7"]       = d["avg_tone"].ewm(span=7, adjust=False).mean()
        d["tone_stress"]      = (d["avg_tone"].rolling(7, min_periods=1)
                                   .std().fillna(0))
        d["is_conflict"]      = (d["quad_class"]==4).astype(float)
        d["conflict_ratio_7d"]= d["is_conflict"].rolling(7, min_periods=1).mean()
        d["conflict_momentum"]= d["conflict_ratio_7d"].diff().fillna(0)
        return d
 
    # ── Calcul prédictions sur données chargées ─────────────────
    with st.spinner("Analyse des données en cours..."):
        feat_df = compute_features(df)
        probas  = []
        for _, row in feat_df.iterrows():
            x = {c: row[c] for c in FEAT_COLS}
            probas.append(xgb_predict_proba(model_json, x))
        feat_df["proba_crise"] = probas
 
        # Agrégation mensuelle
        monthly_pred = (
            feat_df.groupby(["month_num","month_short"])
            .agg(
                proba         = ("proba_crise",        "mean"),
                gold          = ("goldstein_scale",     "mean"),
                tone          = ("avg_tone",            "mean"),
                stress        = ("stress_index",        "mean"),
                conflict_r    = ("conflict_ratio_7d",   "mean"),
                nb_events     = ("event_code",          "count"),
            )
            .reset_index().sort_values("month_num")
        )
 
        # Extrapolation 6 mois futurs
        last_state = feat_df.tail(1)[FEAT_COLS].iloc[0].to_dict()
        avg_gold   = feat_df["goldstein_scale"].mean()
        avg_tone   = feat_df["avg_tone"].mean()
        avg_stress = feat_df["stress_index"].mean()
        avg_cr     = feat_df["conflict_ratio_7d"].mean()
 
        future_months = [
            "Jan 2026","Fév 2026","Mar 2026",
            "Avr 2026","Mai 2026","Juin 2026"
        ]
        future_preds = []
        state = last_state.copy()
        for mois in future_months:
            p = xgb_predict_proba(model_json, state)
            future_preds.append({"mois": mois, "proba": p,
                                  "gold":  state["ema_30"],
                                  "stress":state["stress_index"],
                                  "tone":  state["tone_ema_7"]})
            # Retour progressif vers la moyenne annuelle
            state["ema_30"]            = state["ema_30"]            * 0.85 + avg_gold  * 0.15
            state["sma_7"]             = state["sma_7"]             * 0.80 + avg_gold  * 0.20
            state["stress_index"]      = max(0, state["stress_index"] * 0.90 + avg_stress * 0.10)
            state["tone_ema_7"]        = state["tone_ema_7"]        * 0.85 + avg_tone  * 0.15
            state["conflict_ratio_7d"] = max(0, state["conflict_ratio_7d"] * 0.88 + avg_cr * 0.12)
            state["conflict_momentum"] = 0.0
            state["score_lag1"]        = state["ema_30"]
            state["score_lag3"]        = state["ema_30"]
            state["score_lag7"]        = state["ema_30"]
        future_df = pd.DataFrame(future_preds)
 
    # ═══════════════════════════════════════════════════════════
    # TITRE & CONTEXTE
    # ═══════════════════════════════════════════════════════════
    st.title(" Prédictions — Risque de crise sécuritaire")
    st.caption(
        f"Modèle IA entraîné sur les données GDELT · "
        f"Fiabilité : **{AUC*100:.0f}%** (AUC-ROC) · "
        f"Détection précoce : **{RECALL_35*100:.0f}%** des crises repérées avant qu'elles éclatent"
    )
 
    # ── Alerte globale basée sur la proba moyenne ───────────────
    proba_glob = float(feat_df["proba_crise"].mean())
    proba_futur = float(future_df["proba"].mean())
 
    if proba_glob >= SEUIL_STD:
        st.error(
            f" **ALERTE ÉLEVÉE** — Probabilité moyenne de crise : **{proba_glob*100:.1f}%** "
            f"sur la période analysée. Une intervention préventive est recommandée."
        )
    elif proba_glob >= SEUIL_SENSIBLE:
        st.warning(
            f" VIGILANCE — Probabilité moyenne de crise : **{proba_glob*100:.1f}%**. "
            f"Des signaux de tension ont été détectés. Surveillance renforcée conseillée."
        )
    else:
        st.success(
            f" **SITUATION MAÎTRISÉE** — Probabilité moyenne de crise : **{proba_glob*100:.1f}%**. "
            f"Aucun signal d'alerte majeur sur la période."
        )
 
    st.divider()
 
    # ═══════════════════════════════════════════════════════════
    # SECTION 1 — CE QUE PRÉDIT LE MODÈLE (explication décideur)
    # ═══════════════════════════════════════════════════════════
    with st.expander(" Comment fonctionne ce modèle ? — Guide décideur"):
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            st.markdown("""
**Ce que le modèle fait**
 
Il analyse automatiquement **11 indicateurs calculés** à partir des données GDELT
et estime la **probabilité qu'une période soit instable**.
 
Il détecte les schémas qui précèdent habituellement les crises :
montée des conflits armés, dégradation du ton médiatique,
baisse du score de stabilité sur plusieurs jours consécutifs.
""")
        with col_e2:
            st.markdown("""
**Comment lire les résultats**
 
-  **> 50 %** → Crise probable — action recommandée
-  **35–50 %** → Zone d'alerte — surveiller de près
-  **< 35 %** → Situation stable
 
Le modèle a été validé sur données historiques.
Il repère **81%** des crises avant qu'elles éclatent
(seuil sensible à 35%).
""")
        with col_e3:
            st.markdown("""
**Limites importantes**
 
Ce modèle est un **outil d'aide à la décision**, pas un oracle.
 
- Il se base sur des données médiatiques (GDELT)
  pas sur des renseignements terrain directs
- Une probabilité de 60% signifie **risque élevé**,
  pas une certitude
- Croiser avec d'autres sources avant toute décision critique
""")
 
    st.divider()
 
    # ═══════════════════════════════════════════════════════════
    # SECTION 2 — KPIs CLÉS
    # ═══════════════════════════════════════════════════════════
    st.subheader(" Résumé de la période analysée")
 
    mois_crise  = int((monthly_pred["proba"] >= SEUIL_STD).sum())
    mois_alerte = int(((monthly_pred["proba"] >= SEUIL_SENSIBLE) &
                       (monthly_pred["proba"] < SEUIL_STD)).sum())
    mois_stable = int((monthly_pred["proba"] < SEUIL_SENSIBLE).sum())
    mois_pire   = monthly_pred.loc[monthly_pred["proba"].idxmax(), "month_short"]
    mois_meill  = monthly_pred.loc[monthly_pred["proba"].idxmin(), "month_short"]
 
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Probabilité moy. de crise",
              f"{proba_glob*100:.1f} %",
              help="Moyenne sur tous les mois de la période")
    c2.metric("Mois en alerte élevée ",
              str(mois_crise),
              f"seuil > {SEUIL_STD*100:.0f}%")
    c3.metric("Mois en vigilance ",
              str(mois_alerte),
              f"seuil {SEUIL_SENSIBLE*100:.0f}–{SEUIL_STD*100:.0f}%")
    c4.metric("Mois les plus risqués",
              mois_pire,
              f"{monthly_pred.loc[monthly_pred['proba'].idxmax(),'proba']*100:.1f}%")
    c5.metric("Mois les plus sûrs",
              mois_meill,
              f"{monthly_pred.loc[monthly_pred['proba'].idxmin(),'proba']*100:.1f}%")
 
    st.divider()
 
    # ═══════════════════════════════════════════════════════════
    # SECTION 3 — GRAPHIQUE PRINCIPAL : PASSÉ + FUTUR
    # ═══════════════════════════════════════════════════════════
    st.subheader(" Probabilité de crise — Historique 2025 + Projection 2026")
    st.caption(
        "La barre représente la probabilité estimée pour chaque mois. "
        "Les 6 dernières barres (fond grisé) sont des **projections** "
        "basées sur la tendance de fin 2025."
    )
 
    # Préparer données combinées
    hist_x    = monthly_pred["month_short"].tolist()
    hist_y    = (monthly_pred["proba"] * 100).tolist()
    fut_x     = future_df["mois"].tolist()
    fut_y     = (future_df["proba"] * 100).tolist()
 
    all_x     = hist_x + fut_x
    all_y     = hist_y + fut_y
    is_future = [False]*len(hist_x) + [True]*len(fut_x)
 
    bar_colors = []
    for y, fut in zip(all_y, is_future):
        if fut:
            bar_colors.append("rgba(150,150,150,0.5)")   # gris = projection
        elif y >= SEUIL_STD*100:
            bar_colors.append(RED)
        elif y >= SEUIL_SENSIBLE*100:
            bar_colors.append(ORANGE)
        else:
            bar_colors.append(GREEN)
 
    fig_main = go.Figure()
 
    # Zone grisée pour les projections
    fig_main.add_vrect(
        x0=len(hist_x) - 0.5,
        x1=len(all_x) - 0.5,
        fillcolor="rgba(200,200,200,0.12)",
        line_width=0,
        annotation_text="Projections 2026",
        annotation_position="top right",
        annotation_font_size=11,
        annotation_font_color="gray"
    )
 
    # Barres
    fig_main.add_trace(go.Bar(
        x=all_x,
        y=all_y,
        marker_color=bar_colors,
        marker_line_color="white",
        marker_line_width=1,
        opacity=0.88,
        text=[f"{v:.1f}%" for v in all_y],
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Probabilité de crise : <b>%{y:.1f}%</b><extra></extra>"
        )
    ))
 
    # Seuils
    fig_main.add_hline(
        y=SEUIL_STD*100, line_dash="dash", line_color=RED, line_width=1.5,
        annotation_text=f" Seuil alerte élevée ({SEUIL_STD*100:.0f}%)",
        annotation_position="right", annotation_font_color=RED
    )
    fig_main.add_hline(
        y=SEUIL_SENSIBLE*100, line_dash="dot", line_color=ORANGE, line_width=1.5,
        annotation_text=f"👁 Seuil vigilance ({SEUIL_SENSIBLE*100:.0f}%)",
        annotation_position="right", annotation_font_color=ORANGE
    )
 
    # Ligne séparatrice historique / futur
    fig_main.add_vline(
        x=len(hist_x) - 0.5,
        line_dash="dot", line_color="gray", line_width=1,
    )
 
    fig_main.update_layout(
        xaxis_title="",
        yaxis_title="Probabilité de crise (%)",
        yaxis=dict(range=[0, 110]),
        template="plotly_white",
        height=440,
        margin=dict(t=20, r=160, b=10),
        showlegend=False,
        bargap=0.25,
    )
    st.plotly_chart(fig_main, use_container_width=True, key="chart_pred_main")
 
    # Légende
    lc1, lc2, lc3, lc4 = st.columns(4)
    lc1.error(" > 50% — Crise probable")
    lc2.warning(" 35–50% — Vigilance")
    lc3.success(" < 35% — Stable")
    lc4.info(" Projection 2026")
 
    st.divider()
 
    # ═══════════════════════════════════════════════════════════
    # SECTION 4 — TABLEAU DE BORD MENSUEL COMPLET
    # ═══════════════════════════════════════════════════════════
    st.subheader(" Tableau de bord mensuel — Lecture décideur")
    st.caption(
        "Chaque ligne = un mois. "
        "La colonne **Recommandation** traduit directement le niveau de risque "
        "en action concrète."
    )
 
    def recommandation(proba, gold, conflict):
        if proba >= SEUIL_STD:
            return " Intervention préventive recommandée"
        elif proba >= SEUIL_SENSIBLE:
            if conflict > 0.18:
                return " Renforcer présence sécuritaire Nord"
            else:
                return " Surveiller — augmenter coopération terrain"
        else:
            if gold > 1.2:
                return " Capitaliser — renforcer coopérations concrètes"
            else:
                return " Situation normale — maintien dispositif"
 
    monthly_pred["Recommandation"] = monthly_pred.apply(
        lambda r: recommandation(r["proba"], r["gold"], r["conflict_r"]), axis=1)
 
    display_table = monthly_pred[[
        "month_short","proba","gold","tone","stress","conflict_r","Recommandation"
    ]].copy()
    display_table.columns = [
        "Mois",
        "Risque de crise (%)",
        "Score stabilité",
        "Ton médiatique",
        "Stress sécuritaire (%)",
        "% conflits 7j",
        "Recommandation"
    ]
    display_table["Risque de crise (%)"] = (display_table["Risque de crise (%)"] * 100).round(1)
    display_table["% conflits 7j"]       = (display_table["% conflits 7j"]       * 100).round(1)
    display_table = display_table.set_index("Mois")
 
    def style_risque(val):
        if val >= SEUIL_STD*100:
            return "background-color:#fdecea;color:#D85A30;font-weight:700"
        elif val >= SEUIL_SENSIBLE*100:
            return "background-color:#fff3e0;color:#854F0B;font-weight:600"
        return "background-color:#e8f5e9;color:#0F6E56"
 
    def style_gold(val):
        if val < 0:  return "color:#D85A30;font-weight:600"
        if val > 1:  return "color:#1D9E75;font-weight:600"
        return ""
 
    styled_table = (
        display_table.style
        .format({
            "Risque de crise (%)": "{:.1f}%",
            "Score stabilité":     "{:.2f}",
            "Ton médiatique":      "{:.2f}",
            "Stress sécuritaire (%)": "{:.1f}%",
            "% conflits 7j":       "{:.1f}%",
        })
        .applymap(style_risque, subset=["Risque de crise (%)"])
        .applymap(style_gold,   subset=["Score stabilité"])
    )
    st.dataframe(styled_table, use_container_width=True, key="df_pred_table")
 
    st.divider()
 
    # ═══════════════════════════════════════════════════════════
    # SECTION 5 — PROJECTION 6 MOIS FUTURS
    # ═══════════════════════════════════════════════════════════
    st.subheader("Que peut-on attendre des 6 prochains mois ?")
    st.caption(
        "Projection basée sur la tendance de fin de période. "
        "Plus on s'éloigne dans le futur, moins la projection est précise. "
        "À utiliser comme signal de tendance, pas comme certitude."
    )
 
    # Jauge synthétique pour le prochain mois
    proba_next = float(future_df.iloc[0]["proba"])
    mois_next  = future_df.iloc[0]["mois"]
 
    col_g, col_txt = st.columns([1, 1.5])
    with col_g:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=proba_next * 100,
            number={"suffix": "%", "font": {"size": 42, "color":
                RED if proba_next >= SEUIL_STD
                else ORANGE if proba_next >= SEUIL_SENSIBLE
                else GREEN}},
            title={"text": f"Risque estimé<br><b>{mois_next}</b>",
                   "font": {"size": 14}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1,
                         "tickcolor": "gray",
                         "tickvals": [0, 35, 50, 75, 100],
                         "ticktext": ["0%","35%","50%","75%","100%"]},
                "bar": {"color":
                    RED    if proba_next >= SEUIL_STD
                    else ORANGE if proba_next >= SEUIL_SENSIBLE
                    else GREEN,
                    "thickness": 0.28},
                "bgcolor": "white",
                "steps": [
                    {"range": [0,  35], "color": "#e8f5e9"},
                    {"range": [35, 50], "color": "#fff3e0"},
                    {"range": [50,100], "color": "#fdecea"},
                ],
                "threshold": {
                    "line": {"color": RED, "width": 3},
                    "thickness": 0.75,
                    "value": SEUIL_STD * 100
                }
            }
        ))
        fig_gauge.update_layout(
            height=300,
            margin=dict(t=40, b=20, l=20, r=20),
            template="plotly_white"
        )
        st.plotly_chart(fig_gauge, use_container_width=True, key="chart_gauge_futur")
 
    with col_txt:
        tendance = " en amélioration" if proba_next < proba_glob else " en dégradation"
        st.markdown(f"### Tendance : {tendance}")
        st.markdown(f"""
La période de **décembre 2025** a été la plus risquée de l'année
avec une probabilité de crise à **{monthly_pred.iloc[-1]['proba']*100:.1f}%**.
 
Pour **{mois_next}**, le modèle estime un risque de **{proba_next*100:.1f}%**
— {'en dessous' if proba_next < SEUIL_STD else 'au-dessus'} du seuil d'alerte standard.
 
La tendance sur les 6 prochains mois est
**{'à la stabilisation progressive'
   if future_df['proba'].iloc[-1] < future_df['proba'].iloc[0]
   else 'à la dégradation'}**
si aucun événement exogène ne vient perturber la dynamique.
""")
 
        if proba_next >= SEUIL_SENSIBLE:
            st.warning(
                "**Action recommandée :**\n\n"
                "Renforcer les dispositifs de coopération concrète "
                "(aide matérielle, projets terrain) dans les zones nord "
                "identifiées comme sensibles : Alibori, Kandi, Porga."
            )
        else:
            st.success(
                "**Opportunité :**\n\n"
                "La période de stabilité relative est propice "
                "au lancement de programmes de coopération "
                "et au renforcement des institutions locales."
            )
 
    # Tableau projections futurs
    st.markdown("**Détail des projections mensuelles**")
    future_display = future_df.copy()
    future_display["Risque (%)"]     = (future_display["proba"] * 100).round(1)
    future_display["Score stabilité"]= future_display["gold"].round(2)
    future_display["Ton médiatique"] = future_display["tone"].round(2)
    future_display["Niveau"]         = future_display["proba"].apply(
        lambda p: " Alerte" if p >= SEUIL_STD
        else " Vigilance" if p >= SEUIL_SENSIBLE
        else " Stable"
    )
    future_display = future_display[[
        "mois","Risque (%)","Score stabilité","Ton médiatique","Niveau"
    ]].set_index("mois")
 
    st.dataframe(
        future_display.style.format({
            "Risque (%)":      "{:.1f}%",
            "Score stabilité": "{:.2f}",
            "Ton médiatique":  "{:.2f}",
        }),
        use_container_width=True,
        key="df_future"
    )
 
    st.caption(
        "⚠️ Les projections au-delà de 3 mois ont une incertitude croissante. "
        "Elles indiquent une **direction**, pas une valeur précise. "
        "Mettre à jour avec de nouvelles données GDELT pour affiner."
    )
 
    st.divider()
 
    # ═══════════════════════════════════════════════════════════
    # SECTION 6 — SIMULATEUR SCÉNARIOS
    # ═══════════════════════════════════════════════════════════
    st.subheader(" Simulateur — Et si la situation changeait ?")
    st.caption(
        "Faites varier les indicateurs pour simuler des scénarios hypothétiques. "
        "Utile pour évaluer l'impact de décisions politiques ou sécuritaires."
    )
 
    defaults = {c: float(feat_df[c].mean()) for c in FEAT_COLS}
 
    scenario = st.selectbox(
        "Partir d'un scénario prédéfini",
        ["Situation moyenne 2025",
         "Scénario optimiste (stabilité renforcée)",
         "Scénario pessimiste (dégradation sécuritaire)",
         "Scénario personnalisé"],
        key="sel_scenario"
    )
 
    if scenario == "Situation moyenne 2025":
        sc_vals = defaults.copy()
    elif scenario == "Scénario optimiste (stabilité renforcée)":
        sc_vals = {
            "ema_30": 2.0, "sma_7": 2.0, "stress_index": 5.0,
            "volume_ratio": 1.0, "score_lag1": 2.0,
            "score_lag3": 2.0, "score_lag7": 2.0,
            "tone_ema_7": 1.5, "tone_stress": 2.0,
            "conflict_ratio_7d": 0.05, "conflict_momentum": -0.01,
        }
    elif scenario == "Scénario pessimiste (dégradation sécuritaire)":
        sc_vals = {
            "ema_30": -1.5, "sma_7": -2.0, "stress_index": 40.0,
            "volume_ratio": 2.5, "score_lag1": -2.0,
            "score_lag3": -1.5, "score_lag7": -1.0,
            "tone_ema_7": -4.0, "tone_stress": 6.0,
            "conflict_ratio_7d": 0.45, "conflict_momentum": 0.08,
        }
    else:
        sc_vals = defaults.copy()
 
    # Sliders décideur (simplifiés — 4 leviers principaux)
    st.markdown("**Ajustez les leviers principaux :**")
    sl1, sl2, sl3, sl4 = st.columns(4)
 
    with sl1:
        niv_securite = st.slider(
            " Niveau de sécurité",
            min_value=-5.0, max_value=5.0,
            value=float(round(sc_vals["ema_30"], 1)), step=0.1,
            help="Score de stabilité tendanciel (-5=très instable, +5=très stable)"
        )
    with sl2:
        niv_conflits = st.slider(
            " Intensité des conflits",
            min_value=0.0, max_value=100.0,
            value=float(round(sc_vals["stress_index"], 0)), step=1.0,
            help="% d'événements violents (0=aucun, 100=tous violents)"
        )
    with sl3:
        niv_medias = st.slider(
            " Ton médiatique",
            min_value=-10.0, max_value=5.0,
            value=float(round(sc_vals["tone_ema_7"], 1)), step=0.1,
            help="Ton des médias (-10=très négatif, +5=positif)"
        )
    with sl4:
        niv_tendance = st.slider(
            " Tendance conflits",
            min_value=-0.1, max_value=0.1,
            value=float(round(sc_vals["conflict_momentum"], 3)), step=0.005,
            help="Négatif = conflits en baisse · Positif = conflits en hausse"
        )
 
    # Construire le vecteur de features
    x_sim = {
        "ema_30":            niv_securite,
        "sma_7":             niv_securite * 0.95,
        "stress_index":      niv_conflits,
        "volume_ratio":      sc_vals["volume_ratio"],
        "score_lag1":        niv_securite,
        "score_lag3":        niv_securite * 0.9,
        "score_lag7":        niv_securite * 0.85,
        "tone_ema_7":        niv_medias,
        "tone_stress":       sc_vals["tone_stress"],
        "conflict_ratio_7d": min(1.0, niv_conflits / 100.0),
        "conflict_momentum": niv_tendance,
    }
 
    proba_sim = xgb_predict_proba(model_json, x_sim)
 
    # Résultat simulation
    st.divider()
    res_col1, res_col2 = st.columns([1, 2])
 
    with res_col1:
        fig_sim = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=proba_sim * 100,
            delta={"reference": proba_glob * 100,
                   "valueformat": ".1f",
                   "suffix": "%",
                   "increasing": {"color": RED},
                   "decreasing": {"color": GREEN}},
            number={"suffix": "%", "font": {"size": 38}},
            title={"text": "Risque simulé", "font": {"size": 14}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color":
                    RED    if proba_sim >= SEUIL_STD
                    else ORANGE if proba_sim >= SEUIL_SENSIBLE
                    else GREEN,
                    "thickness": 0.28},
                "steps": [
                    {"range": [0,  35], "color": "#e8f5e9"},
                    {"range": [35, 50], "color": "#fff3e0"},
                    {"range": [50,100], "color": "#fdecea"},
                ],
                "threshold": {
                    "line": {"color": RED, "width": 3},
                    "thickness": 0.75, "value": 50
                }
            }
        ))
        fig_sim.update_layout(
            height=280, margin=dict(t=30, b=10, l=10, r=10),
            template="plotly_white"
        )
        st.plotly_chart(fig_sim, use_container_width=True, key="chart_sim")
 
    with res_col2:
        diff = proba_sim - proba_glob
        st.markdown(f"### Résultat du scénario : **{scenario}**")
 
        if proba_sim >= SEUIL_STD:
            st.error(
                f" **Risque élevé : {proba_sim*100:.1f}%**\n\n"
                "Ce scénario indique une situation de crise probable. "
                "Des mesures préventives immédiates sont recommandées."
            )
        elif proba_sim >= SEUIL_SENSIBLE:
            st.warning(
                f" **Zone d'alerte : {proba_sim*100:.1f}%**\n\n"
                "Ce scénario nécessite une surveillance renforcée "
                "et une préparation des dispositifs d'intervention."
            )
        else:
            st.success(
                f" **Situation stable : {proba_sim*100:.1f}%**\n\n"
                "Ce scénario est favorable. "
                "Opportunité de renforcer les programmes de développement."
            )
 
        if abs(diff) > 0.01:
            direction = "augmente" if diff > 0 else "diminue"
            st.markdown(
                f"Par rapport à la **situation moyenne 2025** ({proba_glob*100:.1f}%) : "
                f"le risque **{direction}** de **{abs(diff)*100:.1f} points**."
            )
 
        st.markdown("**Facteurs qui ont le plus d'influence dans ce scénario :**")
        facteurs = pd.DataFrame({
            "Levier": [
                "Niveau de sécurité (stabilité tendancielle)",
                "Intensité des conflits armés",
                "Ton médiatique international",
                "Tendance des conflits"
            ],
            "Valeur saisie": [
                f"{niv_securite:+.1f}",
                f"{niv_conflits:.0f}%",
                f"{niv_medias:+.1f}",
                f"{'↑ hausse' if niv_tendance > 0 else '↓ baisse' if niv_tendance < 0 else '→ stable'}"
            ],
            "Effet": [
                " Stabilisant" if niv_securite > 0 else " Déstabilisant",
                " Faible"      if niv_conflits < 15 else " Élevé",
                " Favorable"   if niv_medias > -1 else " Critique",
                " Baisse"      if niv_tendance < 0 else " Hausse" if niv_tendance > 0 else " Stable"
            ]
        })
        st.dataframe(facteurs.set_index("Levier"),
                     use_container_width=True,
                     key="df_facteurs")