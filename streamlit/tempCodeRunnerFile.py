"""
Dahomey_Intel — Dashboard GDELT 2025
Streamlit + Plotly
Auteur : Groupe 5 — BéninWatch

Améliorations v2 :
   Import CSV directement dans le dashboard
   Filtre par mois (sidebar) appliqué à toutes les pages
   Vocabulaire décideur (plus de "GoldsteinScale", "AvgTone", etc.)
   Tooltips explicatifs sur chaque indicateur
   Logique d'analyse identique à la v1
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────
# CONFIG PAGE
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Dahomey Intel · Analyse GDELT",
    page_icon="🇧🇯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS CUSTOM — rendu plus propre
# ─────────────────────────────────────────────
st.markdown("""
<style>
  .kpi-box {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 16px 20px;
    border-left: 4px solid #1D9E75;
    margin-bottom: 8px;
  }
  .kpi-title { font-size: 13px; color: #666; margin-bottom: 4px; }
  .kpi-value { font-size: 26px; font-weight: 600; color: #1a1a1a; }
  .kpi-sub   { font-size: 11px; color: #999; margin-top: 4px; }
  .alert-red    { background:#fdecea; border-left:4px solid #D85A30;
                  padding:12px 16px; border-radius:8px; margin:8px 0; }
  .alert-orange { background:#fff3e0; border-left:4px solid #EF9F27;
                  padding:12px 16px; border-radius:8px; margin:8px 0; }
  .alert-green  { background:#e8f5e9; border-left:4px solid #1D9E75;
                  padding:12px 16px; border-radius:8px; margin:8px 0; }
  .section-title { font-size:14px; font-weight:600;
                   color:#444; margin:12px 0 4px 0; }
  div[data-testid="stSidebar"] { background: #1a1a2e; }
  div[data-testid="stSidebar"] * { color: #eee !important; }
  div[data-testid="stSidebar"] .stRadio label { color: #eee !important; }
</style>
""", unsafe_allow_html=True)

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
    "CVL":"Civil","LEG":"Législatif","EDU":"Éducation",
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

# ── Renommage variables techniques → langage décideur
LABELS = {
    "goldstein_scale" : "Score de stabilité",
    "avg_tone"        : "Ton médiatique",
    "num_articles"    : "Couverture médiatique (articles)",
    "num_mentions"    : "Nombre de mentions",
    "num_sources"     : "Nombre de sources",
    "quad_class"      : "Type d'événement",
    "has_actor2"      : "Implique 2 acteurs",
}

# ── Explications courtes pour tooltips
TOOLTIPS = {
    "Score de stabilité"          : "De −10 (très déstabilisateur) à +10 (très stabilisateur). "
                                    "Mesure l'impact théorique de l'événement sur la stabilité du pays.",
    "Ton médiatique"              : "De −100 à +100. Mesure si les articles parlent de l'événement "
                                    "de façon négative (valeur basse) ou positive (valeur haute).",
    "Couverture médiatique"       : "Nombre d'articles de presse ayant relayé l'événement.",
    "Type d'événement"            : "1=Coop. verbale · 2=Coop. concrète · 3=Tension verbale · "
                                    "4=Conflit armé/Violence",
}

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
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🇧🇯 Dahomey Intel")
    st.markdown("**Analyse GDELT — Stabilité politique**")
    st.divider()

    # ── Import fichier
    st.markdown("###  Importer vos données")
    uploaded = st.file_uploader(
        "Glissez votre fichier CSV ici",
        type=["csv"],
        help="Fichier CSV issu de GDELT, nettoyé au format Dahomey Intel"
    )

    if uploaded is None:
        st.info("Aucun fichier chargé. Utilisation du fichier par défaut.")
        try:
            with open("DANHOMÈ_INTEL_final_clean.csv", "rb") as f:
                raw = f.read()
            filename = "DANHOMÈ_INTEL_final_clean.csv"
        except FileNotFoundError:
            st.error("Fichier par défaut introuvable. Veuillez importer un CSV.")
            st.stop()
    else:
        raw = uploaded.read()
        filename = uploaded.name
        st.success(f" {filename}")

    df_full = load_data(raw, filename)

    st.divider()

    # ── Filtre mois
    st.markdown("###  Période d'analyse")
    mois_dispo = [MONTH_SHORT[i] for i in range(12)
                  if MONTH_SHORT[i] in df_full["month_short"].values]

    filtre_type = st.radio(
        "Sélection",
        ["Toute l'année", "Semestre", "Trimestre", "Mois personnalisés"],
        label_visibility="collapsed"
    )

    if filtre_type == "Toute l'année":
        mois_sel = mois_dispo

    elif filtre_type == "Semestre":
        sem = st.selectbox("Semestre", ["1er semestre (Jan–Juin)", "2e semestre (Juil–Déc)"])
        mois_sel = mois_dispo[:6] if "1er" in sem else mois_dispo[6:]

    elif filtre_type == "Trimestre":
        tri = st.selectbox("Trimestre",
                           ["T1 (Jan–Mar)", "T2 (Avr–Juin)",
                            "T3 (Juil–Sep)", "T4 (Oct–Déc)"])
        tranche = {"T1":slice(0,3),"T2":slice(3,6),"T3":slice(6,9),"T4":slice(9,12)}
        key = tri[:2]
        mois_sel = mois_dispo[tranche[key]]

    else:
        mois_sel = st.multiselect(
            "Choisir les mois",
            options=mois_dispo,
            default=mois_dispo,
        )
        if not mois_sel:
            st.warning("Sélectionnez au moins un mois.")
            mois_sel = mois_dispo

    # Appliquer le filtre
    df = df_full[df_full["month_short"].isin(mois_sel)].copy()

    st.caption(f"**{len(df):,}** événements · {len(mois_sel)} mois")

    st.divider()

    # ── Navigation
    st.markdown("###  Navigation")
    page = st.radio(
        "Page",
        [" Vue d'ensemble",
         " Évolution dans le temps",
         " Relations entre indicateurs",
         " Qui agit ?",
         " Où ça se passe ?",
         " Focus Police / Nord"],
        label_visibility="collapsed"
    )


# ─────────────────────────────────────────────
# HELPER : bannière d'alerte automatique
# ─────────────────────────────────────────────
def alerte_stabilite(df):
    gold_moy = df["goldstein_scale"].mean()
    pct_conflit = (df["quad_class"] == 4).mean() * 100
    if gold_moy < 0 or pct_conflit > 20:
        st.markdown(f"""<div class="alert-red">
         <b>Alerte :</b> Score de stabilité moyen négatif ({gold_moy:.2f})
        ou taux de conflits armés élevé ({pct_conflit:.1f}%). Situation préoccupante.
        </div>""", unsafe_allow_html=True)
    elif gold_moy < 0.5 or pct_conflit > 14:
        st.markdown(f"""<div class="alert-orange">
         <b>Vigilance :</b> Score de stabilité faible ({gold_moy:.2f}).
        Surveillance accrue recommandée ({pct_conflit:.1f}% d'événements violents).
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class="alert-green">
         <b>Situation stable</b> sur la période sélectionnée —
        Score de stabilité moyen : {gold_moy:.2f}.
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPER : KPI card
# ─────────────────────────────────────────────
def kpi(title, value, sub="", color="#1D9E75"):
    st.markdown(f"""
    <div class="kpi-box" style="border-left-color:{color}">
      <div class="kpi-title">{title}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# PAGE 1 — VUE D'ENSEMBLE
# ═══════════════════════════════════════════════════════════
if page == " Vue d'ensemble":
    st.title(" Vue d'ensemble — Dahomey Intel")
    st.caption(f"Fichier : **{filename}** · Période : **{', '.join(mois_sel)}**")

    alerte_stabilite(df)
    st.divider()

    # ── KPIs
    c1, c2, c3, c4 = st.columns(4)
    gold = df["goldstein_scale"].mean()
    tone = df["avg_tone"].mean()
    pct_conflit = (df["quad_class"] == 4).mean() * 100
    pct_coop    = (df["quad_class"] == 1).mean() * 100

    with c1:
        kpi(" Événements analysés", f"{len(df):,}",
            f"sur {len(mois_sel)} mois", "#378ADD")
    with c2:
        col = GREEN if gold > 0 else RED
        kpi(" Score de stabilité moyen", f"{gold:+.2f}",
            "Échelle de −10 à +10 · positif = stabilisant", col)
    with c3:
        col = GREEN if tone > -1 else RED
        kpi("  Ton médiatique moyen", f"{tone:.2f}",
            "Comment les médias parlent des événements", col)
    with c4:
        col = RED if pct_conflit > 15 else ORANGE if pct_conflit > 10 else GREEN
        kpi(" Événements violents", f"{pct_conflit:.1f} %",
            f"{pct_coop:.1f} % de coopération", col)

    st.divider()

    # ── Explication indicateurs (décideur)
    with st.expander(" Comprendre les indicateurs — Guide décideur"):
        ic1, ic2 = st.columns(2)
        with ic1:
            st.markdown("""
** Score de stabilité** *(GoldsteinScale)*
> Chaque événement reçoit un score de **−10** (très déstabilisateur, ex: attentat)
> à **+10** (très stabilisateur, ex: accord de paix signé).
> La moyenne de ces scores donne le niveau de stabilité général du pays sur la période.

**  Ton médiatique** *(AvgTone)*
> Mesure si les journalistes parlent des événements de façon **négative ou positive**.
> Un score de −1.33 signifie que les médias internationaux couvrent le Bénin
> avec un léger biais négatif — phénomène courant pour les pays africains dans la presse mondiale.
""")
        with ic2:
            st.markdown("""
** Type d'événement** *(Quad Class)*
> Les événements sont classés en 4 catégories :
> -  **Coopération verbale** : déclarations positives, accords annoncés
> -  **Coopération concrète** : aide matérielle, projets réalisés
> -  **Tension verbale** : accusations, menaces, critiques
> -  **Conflit armé / Violence** : affrontements, attaques, incidents sécuritaires

** Acteurs** *(Actor Type)*
> Qui est impliqué dans l'événement : Gouvernement, Police, Militaire,
> Organisations Internationales, Société Civile, etc.
""")

    st.divider()

    # ── Distributions
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="section-title"> Répartition du score de stabilité</p>',
                    unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=df["goldstein_scale"], nbinsx=40,
            marker_color=GREEN, opacity=0.75, name="Score de stabilité"
        ))
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
            margin=dict(t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(" Chaque barre = nombre d'événements ayant ce score. "
                   "La majorité à droite de zéro = tendance stabilisatrice.")

    with col2:
        st.markdown('<p class="section-title">  Répartition du ton médiatique</p>',
                    unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(
            x=df["avg_tone"], nbinsx=40,
            marker_color=BLUE, opacity=0.75, name="Ton médiatique"
        ))
        mean_t = df["avg_tone"].mean()
        fig2.add_vline(x=mean_t, line_dash="dash", line_color=RED,
                       annotation_text=f"Moyenne : {mean_t:.2f}",
                       annotation_position="top right",
                       annotation_font_color=RED)
        fig2.add_vline(x=0, line_dash="dot", line_color="gray",
                       annotation_text="Neutre",
                       annotation_position="top left")
        fig2.update_layout(
            xaxis_title="Ton médiatique (négatif ← 0 → positif)",
            yaxis_title="",
            showlegend=False, template="plotly_white", height=320,
            margin=dict(t=10, b=10)
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.caption(" La plupart des valeurs sont légèrement négatives — "
                   "les médias internationaux couvrent le Bénin avec un biais critique structurel.")

    # ── Donut quad_class
    st.divider()
    st.markdown('<p class="section-title"> Répartition par type d\'événement</p>',
                unsafe_allow_html=True)
    qc = df["quad_label"].value_counts().reset_index()
    qc.columns = ["Type", "Count"]
    fig_pie = px.pie(
        qc, names="Type", values="Count",
        color="Type",
        color_discrete_map={v: QUAD_C[k] for k, v in QUAD_L.items()},
        hole=0.42
    )
    fig_pie.update_traces(
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>%{value:,} événements (%{percent})<extra></extra>"
    )
    fig_pie.update_layout(
        template="plotly_white", height=380,
        annotations=[dict(text="Types<br>d'événements",
                         x=0.5, y=0.5, font_size=13, showarrow=False)]
    )
    st.plotly_chart(fig_pie, use_container_width=True)


# ═══════════════════════════════════════════════════════════
# PAGE 2 — ÉVOLUTION TEMPORELLE
# ═══════════════════════════════════════════════════════════
elif page == " Évolution dans le temps":
    st.title(" Évolution dans le temps")
    st.caption("Comment la stabilité et la couverture médiatique ont-elles évolué mois par mois ?")

    alerte_stabilite(df)

    monthly = (
        df.groupby(["month_num", "month_short"])
        .agg(
            avg_goldstein=("goldstein_scale", "mean"),
            std_goldstein=("goldstein_scale", "std"),
            avg_tone=("avg_tone", "mean"),
            std_tone=("avg_tone", "std"),
            num_events=("event_code", "count"),
            pct_conflict=("quad_class", lambda x: (x == 4).mean() * 100),
            pct_coop=("quad_class", lambda x: (x == 1).mean() * 100),
        )
        .reset_index()
        .sort_values("month_num")
    )

    xi   = monthly["month_short"].tolist()
    g    = monthly["avg_goldstein"].values
    se_g = monthly["std_goldstein"].values / np.sqrt(monthly["num_events"].values)
    t    = monthly["avg_tone"].values
    se_t = monthly["std_tone"].values / np.sqrt(monthly["num_events"].values)
    pc   = monthly["pct_conflict"].values

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        subplot_titles=(
            " Score de stabilité mensuel",
            "  Ton médiatique mensuel",
            " % d'événements violents (conflits armés)"
        ),
        vertical_spacing=0.10
    )

    # ── Score stabilité + IC
    fig.add_trace(go.Scatter(
        x=xi + xi[::-1],
        y=list(g + 1.96*se_g) + list((g - 1.96*se_g)[::-1]),
        fill="toself", fillcolor="rgba(29,158,117,0.12)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Marge d'incertitude (95%)", showlegend=True
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=xi, y=g, mode="lines+markers",
        line=dict(color=GREEN, width=2.5),
        marker=dict(size=8, color="white", line=dict(color=GREEN, width=2.5)),
        name="Score de stabilité",
        hovertemplate="<b>%{x}</b><br>Score de stabilité : %{y:.2f}<extra></extra>"
    ), row=1, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color=RED,
                  line_width=1, opacity=0.5,
                  annotation_text="Seuil zéro", annotation_position="right",
                  row=1, col=1)
    fig.add_hline(y=g.mean(), line_dash="dot", line_color="gray",
                  line_width=1,
                  annotation_text=f"Moy. période ({g.mean():.2f})",
                  annotation_position="left",
                  row=1, col=1)

    # ── Ton médiatique + IC
    fig.add_trace(go.Scatter(
        x=xi + xi[::-1],
        y=list(t + 1.96*se_t) + list((t - 1.96*se_t)[::-1]),
        fill="toself", fillcolor="rgba(55,138,221,0.12)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Marge d'incertitude ton", showlegend=False
    ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=xi, y=t, mode="lines+markers",
        line=dict(color=BLUE, width=2.5),
        marker=dict(size=8, symbol="square", color="white",
                    line=dict(color=BLUE, width=2.5)),
        name="Ton médiatique",
        hovertemplate="<b>%{x}</b><br>Ton médiatique : %{y:.2f}<extra></extra>"
    ), row=2, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color="gray",
                  line_width=1, row=2, col=1)

    # ── % conflits
    bar_colors = [RED if v > 15 else ORANGE if v > 10 else GREEN for v in pc]
    fig.add_trace(go.Bar(
        x=xi, y=pc,
        marker_color=bar_colors,
        name="% conflits armés",
        hovertemplate="<b>%{x}</b><br>Conflits armés : %{y:.1f}%<extra></extra>"
    ), row=3, col=1)
    fig.add_hline(y=pc.mean(), line_dash="dot", line_color="gray",
                  line_width=1,
                  annotation_text=f"Moy. {pc.mean():.1f}%",
                  annotation_position="right",
                  row=3, col=1)

    fig.update_layout(
        height=650, template="plotly_white",
        legend=dict(orientation="h", y=1.04),
        margin=dict(t=60)
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Tableau détaillé
    with st.expander(" Tableau mensuel détaillé"):
        disp = monthly[["month_short","avg_goldstein","avg_tone",
                         "num_events","pct_conflict","pct_coop"]].copy()
        disp.columns = ["Mois", "Score stabilité",
                        "Ton médiatique", "Nb événements",
                        "% Conflits armés", "% Coopération verbale"]
        disp = disp.set_index("Mois")

        def color_gold(val):
            if val < 0:   return "color: #D85A30; font-weight:600"
            if val > 1:   return "color: #1D9E75; font-weight:600"
            return ""
        def color_conflict(val):
            if val > 15:  return "color: #D85A30; font-weight:600"
            if val > 10:  return "color: #EF9F27"
            return ""

        styled = (disp.style
                  .format("{:.2f}")
                  .applymap(color_gold, subset=["Score stabilité"])
                  .applymap(color_conflict, subset=["% Conflits armés"]))
        st.dataframe(styled, use_container_width=True)

    # ── Insight automatique
    st.divider()
    best  = monthly.loc[monthly["avg_goldstein"].idxmax(), "month_short"]
    worst = monthly.loc[monthly["avg_goldstein"].idxmin(), "month_short"]
    st.markdown(f"""
    <div class="alert-green">
     <b>Mois le plus stable :</b> {best} (score le plus élevé de la période)<br>
     <b>Mois le plus fragile :</b> {worst} (score le plus bas, à surveiller)
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# PAGE 3 — CORRÉLATIONS
# ═══════════════════════════════════════════════════════════
elif page == " Relations entre indicateurs":
    st.title(" Relations entre indicateurs")
    st.caption("Quels indicateurs évoluent ensemble ? "
               "Cette analyse aide à identifier les variables les plus prédictives.")

    cols_tech  = ["goldstein_scale","avg_tone","num_articles",
                  "num_mentions","num_sources","quad_class","has_actor2"]
    labels_fr  = ["Score de stabilité","Ton médiatique",
                  "Couverture (articles)","Nombre de mentions",
                  "Nombre de sources","Type d'événement","2 acteurs identifiés"]

    corr = df[cols_tech].corr()
    corr.index   = labels_fr
    corr.columns = labels_fr
    mask = np.triu(np.ones_like(corr, dtype=bool))
    corr_masked = corr.where(~mask)

    fig = go.Figure(go.Heatmap(
        z=corr_masked.values,
        x=labels_fr, y=labels_fr,
        colorscale="RdYlGn", zmid=0, zmin=-1, zmax=1,
        text=corr_masked.round(2).values,
        texttemplate="%{text}",
        hoverongaps=False,
        hovertemplate="<b>%{x}</b> × <b>%{y}</b><br>Corrélation : %{z:.2f}<extra></extra>",
        colorbar=dict(
            title="Force du lien",
            tickvals=[-1, -0.5, 0, 0.5, 1],
            ticktext=["−1<br>Opposés", "−0.5<br>Lien inverse",
                      "0<br>Aucun lien", "+0.5<br>Lien positif", "+1<br>Identiques"]
        )
    ))
    fig.update_layout(
        title="Comment les indicateurs sont-ils liés entre eux ?",
        height=560, template="plotly_white",
        xaxis=dict(tickangle=-35),
        margin=dict(t=60, b=80)
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Lecture simplifiée pour décideur
    st.divider()
    st.markdown("###  Ce que ça signifie concrètement")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="alert-red">
         <b>Lien fort négatif (−0.78)</b><br>
        <b>Score de stabilité ↔ Type d'événement</b><br><br>
        Plus l'événement est violent, plus le score de stabilité est bas.
        Ces deux indicateurs mesurent la même chose — ne pas les utiliser
        ensemble dans un modèle de prédiction.
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="alert-green">
         <b>Lien fort positif (+0.96)</b><br>
        <b>Couverture articles ↔ Nombre de mentions</b><br><br>
        Plus un événement est couvert par des articles,
        plus il est mentionné. Ces deux indicateurs sont redondants —
        utiliser l'un ou l'autre suffit.
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="alert-orange">
         <b>Lien modéré positif (+0.36)</b><br>
        <b>Score de stabilité ↔ Ton médiatique</b><br><br>
        Quand les événements sont plus stables, les médias en parlent
        de façon légèrement moins négative. Le lien existe
        mais n'est pas déterminant.
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# PAGE 4 — QUI AGIT ?
# ═══════════════════════════════════════════════════════════
elif page == " Qui agit ?":
    st.title(" Qui agit ? — Analyse des acteurs")
    st.caption("Quels acteurs sont les plus présents et quel est leur impact sur la stabilité ?")

    alerte_stabilite(df)
    st.divider()

    tab1, tab2, tab3 = st.tabs([
        " Acteurs les plus présents",
        " Impact sur la stabilité",
        "Qui agit — mois par mois ?"
    ])

    with tab1:
        top_act = (
            df[~df["actor1_name"].isin(["Acteur non identifié", "Unknown", "UNKNOWN"])]
            ["actor1_name"].value_counts().head(12).reset_index()
        )
        top_act.columns = ["Acteur", "Nombre d'événements"]
        top_act = top_act.sort_values("Nombre d'événements")

        fig = go.Figure(go.Bar(
            x=top_act["Nombre d'événements"],
            y=top_act["Acteur"],
            orientation="h",
            marker_color=BLUE, opacity=0.82,
            text=top_act["Nombre d'événements"].apply(lambda v: f"{v:,}"),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Événements : %{x:,}<extra></extra>"
        ))
        fig.update_layout(
            title="Acteurs les plus fréquemment impliqués dans les événements",
            xaxis_title="Nombre d'événements recensés",
            template="plotly_white", height=450,
            margin=dict(l=20, r=60)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(" 'BENIN' désigne les événements où le pays est cité comme entité principale. "
                   "Ce n'est pas un acteur humain mais une entité géopolitique.")

    with tab2:
        act_stats = (
            df[~df["actor1_type"].isin(["UNKNOWN", "Unknown"])]
            .groupby("actor1_type")
            .agg(count=("event_code","count"), avg_g=("goldstein_scale","mean"))
            .reset_index()
            .query("count >= 20")
            .sort_values("avg_g")
        )
        act_stats["Acteur"] = act_stats["actor1_type"].map(CAMEO).fillna(act_stats["actor1_type"])
        act_stats["Couleur"] = act_stats["avg_g"].apply(lambda g: RED if g < 0 else GREEN)
        act_stats["Interprétation"] = act_stats["avg_g"].apply(
            lambda g: " Déstabilisateur" if g < -1
            else " Légèrement négatif" if g < 0
            else " Stabilisateur" if g > 1
            else " Neutre"
        )

        fig = go.Figure(go.Bar(
            x=act_stats["avg_g"],
            y=act_stats["Acteur"],
            orientation="h",
            marker_color=act_stats["Couleur"], opacity=0.85,
            text=act_stats["avg_g"].round(2),
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Score de stabilité moyen : %{x:.2f}<br>"
                "<extra></extra>"
            )
        ))
        fig.add_vline(x=0, line_dash="dot", line_color="gray",
                      annotation_text="Seuil zéro", annotation_position="top right")
        fig.update_layout(
            title="Score de stabilité moyen par type d'acteur<br>"
                  "<sup>Vert = stabilisateur · Rouge = déstabilisateur</sup>",
            xaxis_title="Score de stabilité moyen",
            template="plotly_white", height=500,
            margin=dict(l=20, r=60)
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander(" Tableau détaillé par acteur"):
            show = act_stats[["Acteur","avg_g","count","Interprétation"]].copy()
            show.columns = ["Type d'acteur","Score stabilité moy.","Nb événements","Interprétation"]
            st.dataframe(show.set_index("Type d'acteur")
                         .style.format({"Score stabilité moy.":"{:.2f}"}),
                         use_container_width=True)

    with tab3:
        top_types = ["GOV","MIL","COP","CVL","LEG","EDU","IGO","MED","BUS","OPP"]
        df_f = df[df["actor1_type"].isin(top_types)].copy()
        df_f["Acteur"] = df_f["actor1_type"].map(CAMEO)

        pivot = df_f.pivot_table(
            values="goldstein_scale",
            index="Acteur",
            columns="month_short",
            aggfunc="mean"
        )
        col_order = [s for s in MONTH_SHORT if s in pivot.columns]
        pivot = pivot.reindex(columns=col_order)

        fig = go.Figure(go.Heatmap(
            z=pivot.values,
            x=col_order,
            y=pivot.index.tolist(),
            colorscale="RdYlGn", zmid=0, zmin=-5, zmax=5,
            text=np.round(pivot.values, 1),
            texttemplate="%{text}",
            colorbar=dict(
                title="Score stabilité",
                tickvals=[-5,-2.5,0,2.5,5],
                ticktext=["−5<br>Très déstab.","−2.5","0<br>Neutre","2.5","5<br>Très stab."]
            ),
            hovertemplate="<b>%{y}</b> en <b>%{x}</b><br>"
                          "Score de stabilité : %{z:.1f}<extra></extra>"
        ))
        fig.update_layout(
            title="Quel acteur a eu quel impact, et quel mois ?<br>"
                  "<sup>Rouge = déstabilisateur · Vert = stabilisateur · "
                  "Gris = aucune donnée ce mois-là</sup>",
            template="plotly_white", height=420,
            margin=dict(t=80)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(" Les cases vides signifient qu'aucun événement impliquant "
                   "cet acteur n'a été recensé ce mois-là dans la zone.")


# ═══════════════════════════════════════════════════════════
# PAGE 5 — OÙ ÇA SE PASSE ?
# ═══════════════════════════════════════════════════════════
elif page == " Où ça se passe ?":
    st.title(" Où ça se passe ? — Analyse géographique")
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
            x=locs["count"], y=locs["Localité"],
            orientation="h",
            marker_color=locs["zone"].map({"Nord (sensible)": RED, "Sud / Centre": GREEN}),
            opacity=0.85,
            text=locs["count"].apply(lambda v: f"{v:,}"),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Événements : %{x:,}<extra></extra>"
        ))
        import matplotlib.patches as _  # unused — légende manuelle
        fig.update_layout(
            title="Localités les plus touchées par les événements",
            xaxis_title="Nombre d'événements recensés",
            template="plotly_white", height=460,
            margin=dict(r=60)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(" Rouge = zone nord sensible ·  Vert = sud / centre")

    with col2:
        zone_stats = (
            df.groupby("zone")
            .agg(
                avg_g=("goldstein_scale","mean"),
                pct_c=("quad_class", lambda x: (x==4).mean()*100),
                count=("event_code","count")
            )
            .reset_index()
        )

        fig2 = go.Figure(go.Bar(
            x=zone_stats["zone"],
            y=zone_stats["avg_g"],
            marker_color=[RED, GREEN],
            text=zone_stats["avg_g"].round(2),
            textposition="outside",
            width=0.45,
            hovertemplate="<b>%{x}</b><br>Score stabilité : %{y:.2f}<extra></extra>"
        ))
        fig2.add_hline(y=0, line_dash="dash", line_color="gray",
                       annotation_text="Seuil zéro")
        fig2.update_layout(
            title="Score de stabilité moyen<br>Nord vs Sud / Centre",
            yaxis_title="Score de stabilité moyen",
            template="plotly_white", height=300
        )
        st.plotly_chart(fig2, use_container_width=True)

        nord_g = zone_stats.set_index("zone")["avg_g"].get("Nord (sensible)", 0)
        sud_g  = zone_stats.set_index("zone")["avg_g"].get("Sud / Centre", 0)
        ecart  = nord_g - sud_g
        st.metric("Écart Nord − Sud",
                  f"{ecart:.2f} points",
                  delta=f"{ecart:.2f}",
                  delta_color="inverse",
                  help="Différence du score de stabilité entre le nord et le sud/centre")

        nord_pct = zone_stats.set_index("zone")["pct_c"].get("Nord (sensible)", 0)
        sud_pct  = zone_stats.set_index("zone")["pct_c"].get("Sud / Centre", 0)
        st.metric("% conflits armés Nord",
                  f"{nord_pct:.1f} %",
                  delta=f"Sud : {sud_pct:.1f}%",
                  delta_color="inverse")

    # ── Boxplot quad_class
    st.divider()
    st.markdown("###  Score de stabilité selon le type d'événement")
    order  = [QUAD_L[k] for k in [1, 2, 3, 4]]
    colors = [QUAD_C[k] for k in [1, 2, 3, 4]]

    fig3 = go.Figure()
    for label, color in zip(order, colors):
        vals = df[df["quad_label"] == label]["goldstein_scale"].dropna()
        fig3.add_trace(go.Box(
            y=vals, name=label,
            marker_color=color, line_color=color,
            boxpoints="outliers", marker_size=3, opacity=0.8,
            hovertemplate=f"<b>{label}</b><br>Score : %{{y:.1f}}<extra></extra>"
        ))
    fig3.update_layout(
        xaxis_title="Type d'événement",
        yaxis_title="Score de stabilité",
        showlegend=False, template="plotly_white", height=380
    )
    st.plotly_chart(fig3, use_container_width=True)
    st.caption(" La boîte montre la distribution des scores. "
               "Les points isolés en dehors sont des cas extrêmes (outliers).")


# ═══════════════════════════════════════════════════════════
# PAGE 6 — FOCUS POLICE / NORD
# ═══════════════════════════════════════════════════════════
elif page == " Focus Police / Nord":
    st.title(" Focus Police × Nord — Hypothèse vérifiée")
    st.caption("La Police est-elle plus déstabilisatrice au Nord qu'au Sud ?")

    st.markdown("""
    <div class="alert-orange">
    🔍 <b>Hypothèse de départ :</b> Les creux de stabilité observés au Nord pourraient être
    liés aux interventions de la Police dans des contextes de crise sécuritaire.
    </div>""", unsafe_allow_html=True)

    st.divider()

    # ── Grouped bar acteurs Nord vs Sud
    st.subheader(" Impact de chaque acteur selon la zone géographique")

    actor_zone = (
        df[df["actor1_type"].isin(
            ["GOV","COP","MIL","CVL","IGO","OPP","UAF","MED","EDU","BUS"])]
        .groupby(["zone","actor1_type"])
        .agg(avg_gold=("goldstein_scale","mean"), count=("event_code","count"))
        .reset_index()
        .query("count >= 5")
    )
    actor_zone["Acteur"] = actor_zone["actor1_type"].map(CAMEO).fillna(actor_zone["actor1_type"])

    pivot_bar = (actor_zone
                 .pivot(index="Acteur", columns="zone", values="avg_gold")
                 .fillna(0)
                 .sort_values("Nord (sensible)"))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=" Nord (sensible)",
        x=pivot_bar.index, y=pivot_bar["Nord (sensible)"],
        marker_color=RED, opacity=0.85,
        hovertemplate="<b>%{x}</b> au Nord<br>Score stabilité : %{y:.2f}<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        name=" Sud / Centre",
        x=pivot_bar.index, y=pivot_bar["Sud / Centre"],
        marker_color=GREEN, opacity=0.85,
        hovertemplate="<b>%{x}</b> au Sud<br>Score stabilité : %{y:.2f}<extra></extra>"
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="gray",
                  annotation_text="Seuil zéro")
    fig.update_layout(
        barmode="group", xaxis_tickangle=-20,
        yaxis_title="Score de stabilité moyen",
        template="plotly_white", height=420,
        legend=dict(orientation="h", y=1.06)
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(" Un acteur avec une barre rouge plus basse que sa barre verte "
               "est significativement plus déstabilisateur au Nord qu'au Sud.")

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(" Volume et impact de la Police par zone")
        police_zone = (
            df[df["actor1_type"] == "COP"]
            .groupby("zone")
            .agg(count=("event_code","count"), avg_gold=("goldstein_scale","mean"))
            .reset_index()
        )
        fig2 = go.Figure(go.Bar(
            x=police_zone["zone"], y=police_zone["count"],
            marker_color=[RED, GREEN],
            text=[f"{int(r['count'])} événements<br>Score : {r['avg_gold']:.2f}"
                  for _, r in police_zone.iterrows()],
            textposition="outside", width=0.45,
            hovertemplate="<b>%{x}</b><br>Événements Police : %{y}<extra></extra>"
        ))
        fig2.update_layout(
            yaxis_title="Nombre d'interventions policières recensées",
            template="plotly_white", height=320
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.caption(" La Police intervient moins souvent au Nord "
                   "mais dans des contextes beaucoup plus graves.")

    with col2:
        st.subheader(" Impact de la Police mois par mois")
        police_pivot = (
            df[df["actor1_type"] == "COP"]
            .groupby(["zone","month_short"])["goldstein_scale"]
            .mean().unstack()
        )
        col_order = [s for s in MONTH_SHORT if s in police_pivot.columns]
        police_pivot = police_pivot.reindex(columns=col_order)

        fig3 = go.Figure(go.Heatmap(
            z=police_pivot.values,
            x=col_order, y=police_pivot.index.tolist(),
            colorscale="RdYlGn", zmid=0, zmin=-6, zmax=3,
            text=np.round(police_pivot.values, 1),
            texttemplate="%{text}",
            colorbar=dict(title="Score stabilité"),
            hovertemplate="<b>Police</b> · <b>%{y}</b> en <b>%{x}</b><br>"
                          "Score : %{z:.1f}<extra></extra>"
        ))
        fig3.update_layout(
            template="plotly_white", height=240,
            margin=dict(t=20, b=10)
        )
        st.plotly_chart(fig3, use_container_width=True)
        st.caption(" Juin au Nord = −6.0 : pic de déstabilisation maximal de l'année.")

    # ── Acteurs déstabilisateurs au Nord
    st.divider()
    st.subheader("🏴 Acteurs les plus déstabilisateurs au Nord — Classement complet")

    north_actors = (
        df[df["zone"] == "Nord (sensible)"]
        .groupby("actor1_type")
        .agg(avg_gold=("goldstein_scale","mean"), count=("event_code","count"))
        .reset_index()
        .query("count >= 5")
        .sort_values("avg_gold")
        .head(12)
    )
    north_actors["Acteur"] = (north_actors["actor1_type"].map(CAMEO)
                               .fillna(north_actors["actor1_type"]))
    north_actors["Couleur"] = north_actors["avg_gold"].apply(
        lambda g: RED if g < -2 else ORANGE if g < 0 else GREEN)

    fig4 = go.Figure(go.Bar(
        x=north_actors["avg_gold"],
        y=north_actors["Acteur"],
        orientation="h",
        marker_color=north_actors["Couleur"], opacity=0.85,
        text=[f"{g:.2f}  ({int(c)} événements)"
              for g, c in zip(north_actors["avg_gold"], north_actors["count"])],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Score stabilité : %{x:.2f}<extra></extra>"
    ))
    fig4.add_vline(x=0, line_dash="dot", line_color="gray",
                   annotation_text="Seuil zéro")
    fig4.update_layout(
        xaxis_title="Score de stabilité moyen au Nord",
        template="plotly_white", height=400,
        margin=dict(r=80)
    )
    st.plotly_chart(fig4, use_container_width=True)

    # ── Conclusion
    st.divider()
    st.markdown("""
    <div class="alert-red">
     <b>Conclusion — Hypothèse confirmée par les données</b><br><br>
    La Police intervient au Nord dans des contextes de crise extrême
    (score moyen −2.93 au Nord vs −1.47 au Sud).
    Les pics de déstabilisation en <b>juin (−6.0)</b> et <b>novembre (−4.9)</b>
    correspondent aux moments d'intervention policière les plus intenses au Nord.<br><br>
    Les acteurs structurellement les plus déstabilisateurs restent les
    <b>Rebelles (−9.53)</b> et les <b>Forces non-identifiées (−5.06)</b>,
    probablement liés à la menace terroriste sahélienne.
    La Police réagit à ces acteurs — elle n'est pas la cause première
    mais le <b>révélateur des crises sécuritaires du nord Bénin</b>.
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="alert-orange">
     <b>Recommandation pour les décideurs</b><br>
    Renforcer les mécanismes de coopération concrète (aide matérielle, projets)
    dans les localités nordiques : Alibori, Kandi, Porga, Karimama.
    La coopération concrète a un score de stabilité moyen de +7 —
    c'est le levier d'action le plus puissant identifié dans ces données.
    </div>""", unsafe_allow_html=True)