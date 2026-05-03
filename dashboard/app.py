"""
BéninWatch — DANHOMÈ INTEL 2025
Dashboard interactif Streamlit + Plotly
Auteur : Groupe 5
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
    page_title="Benin_intel · GDELT 2025",
    page_icon="🇧🇯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# COULEURS & CONSTANTES
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
    "IGO":"Org. Intl","MED":"Médias","BUS":"Entreprises",
    "JUD":"Judiciaire","OPP":"Opposition","UAF":"Forces non-id.",
    "ELI":"Élites","SPY":"Renseignement","REB":"Rebelles",
    "HLH":"Santé","UNKNOWN":"Inconnu"
}

QUAD_L = {1:"Coop. verbale", 2:"Coop. matérielle",
          3:"Conflit verbal", 4:"Conflit matériel"}
QUAD_C = {1: GREEN, 2: BLUE, 3: ORANGE, 4: RED}


# ─────────────────────────────────────────────
# CHARGEMENT DONNÉES
# ─────────────────────────────────────────────
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    df["month_num"] = df["month_name"].apply(
        lambda x: MONTH_ORDER.index(x) + 1 if x in MONTH_ORDER else 0)
    df["month_short"] = df["month_num"].apply(
        lambda x: MONTH_SHORT[x - 1] if 1 <= x <= 12 else "?")

    df["zone"] = df["geo_full_name"].apply(
        lambda x: "Nord (sensible)"
        if any(k in str(x) for k in NORTH_KW)
        else "Sud / Centre")

    df["actor_label"] = df["actor1_type"].map(CAMEO).fillna(df["actor1_type"])
    df["quad_label"]  = df["quad_class"].map(QUAD_L)

    return df


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Flag_of_Benin.svg/320px-Flag_of_Benin.svg.png",
             width=80)
    st.title("BéninWatch")
    st.caption("GDELT · DANHOMÈ INTEL 2025")
    st.divider()

    data_path = st.text_input(
        " Chemin du CSV",
        value="DANHOMÈ_INTEL_final_clean.csv",
        help="Chemin vers ton fichier CSV GDELT nettoyé"
    )

    st.divider()
    page = st.radio(
        "Navigation",
        [" Vue d'ensemble",
         " Évolution temporelle",
         " Corrélations",
         " Analyse acteurs",
         " Géographie",
         " Focus Police/Nord"],
        label_visibility="collapsed"
    )


# ─────────────────────────────────────────────
# CHARGEMENT
# ─────────────────────────────────────────────
try:
    df = load_data("data/processed/DANHOMÈ_INTEL_final_clean.csv")
except FileNotFoundError:
    st.error(f" Fichier introuvable : `{data_path}`  \n"
             "Modifie le chemin dans la sidebar.")
    st.stop()


# ═══════════════════════════════════════════════
# PAGE 1 — VUE D'ENSEMBLE  (fig1)
# ═══════════════════════════════════════════════
if page == " Vue d'ensemble":
    st.title(" Distributions des indicateurs clés")
    st.caption("DANHOMÈ INTEL 2025 — Bénin")

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Événements totaux",  f"{len(df):,}")
    k2.metric("GoldsteinScale moy.", f"{df['goldstein_scale'].mean():.2f}")
    k3.metric("AvgTone moyen",       f"{df['avg_tone'].mean():.2f}")
    k4.metric("% Conflits matériels",
              f"{(df['quad_class']==4).mean()*100:.1f} %")

    st.divider()

    col1, col2 = st.columns(2)

    # — Goldstein histogram
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=df["goldstein_scale"], nbinsx=40,
            marker_color=GREEN, opacity=0.75,
            name="GoldsteinScale"
        ))
        mean_g = df["goldstein_scale"].mean()
        fig.add_vline(x=mean_g, line_dash="dash", line_color=RED,
                      annotation_text=f"Moy. {mean_g:.2f}",
                      annotation_position="top right")
        fig.add_vline(x=0, line_dash="dot", line_color="gray")
        fig.update_layout(
            title="Distribution du GoldsteinScale",
            xaxis_title="GoldsteinScale (−10 à +10)",
            yaxis_title="Fréquence",
            showlegend=False,
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

    # — AvgTone histogram
    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(
            x=df["avg_tone"], nbinsx=40,
            marker_color=BLUE, opacity=0.75,
            name="AvgTone"
        ))
        mean_t = df["avg_tone"].mean()
        fig2.add_vline(x=mean_t, line_dash="dash", line_color=RED,
                       annotation_text=f"Moy. {mean_t:.2f}",
                       annotation_position="top right")
        fig2.add_vline(x=0, line_dash="dot", line_color="gray")
        fig2.update_layout(
            title="Distribution de l'AvgTone",
            xaxis_title="AvgTone (ton médiatique)",
            yaxis_title="",
            showlegend=False,
            template="plotly_white"
        )
        st.plotly_chart(fig2, use_container_width=True)

    # — Pie quad_class
    st.subheader("Répartition par type d'événement (Quad Class)")
    qc = df["quad_label"].value_counts().reset_index()
    qc.columns = ["Type", "Count"]
    colors_pie = [QUAD_C[k] for k in [1,2,3,4] if QUAD_L[k] in qc["Type"].values]
    fig_pie = px.pie(qc, names="Type", values="Count",
                     color="Type",
                     color_discrete_map={v: QUAD_C[k] for k,v in QUAD_L.items()},
                     hole=0.38)
    fig_pie.update_layout(template="plotly_white")
    st.plotly_chart(fig_pie, use_container_width=True)


# ═══════════════════════════════════════════════
# PAGE 2 — ÉVOLUTION TEMPORELLE  (fig2)
# ═══════════════════════════════════════════════
elif page == " Évolution temporelle":
    st.title(" Évolution temporelle")

    monthly = (
        df.groupby(["month_num", "month_short"])
        .agg(
            avg_goldstein=("goldstein_scale", "mean"),
            std_goldstein=("goldstein_scale", "std"),
            avg_tone=("avg_tone", "mean"),
            std_tone=("avg_tone", "std"),
            num_events=("event_code", "count"),
            pct_conflict=("quad_class", lambda x: (x == 4).mean() * 100),
        )
        .reset_index()
        .sort_values("month_num")
    )

    xi     = monthly["month_short"].tolist()
    g      = monthly["avg_goldstein"].values
    se_g   = monthly["std_goldstein"].values / np.sqrt(monthly["num_events"].values)
    t      = monthly["avg_tone"].values
    se_t   = monthly["std_tone"].values / np.sqrt(monthly["num_events"].values)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=("Stabilité politique mensuelle (GoldsteinScale)",
                                        "Ton médiatique mensuel (AvgTone)"),
                        vertical_spacing=0.12)

    # ── Goldstein
    fig.add_trace(go.Scatter(
        x=xi + xi[::-1],
        y=list(g + 1.96 * se_g) + list((g - 1.96 * se_g)[::-1]),
        fill="toself", fillcolor=f"rgba(29,158,117,0.15)",
        line=dict(color="rgba(0,0,0,0)"), name="IC 95%", showlegend=True
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=xi, y=g, mode="lines+markers",
        line=dict(color=GREEN, width=2.5),
        marker=dict(size=8, color="white", line=dict(color=GREEN, width=2)),
        name="GoldsteinScale",
        hovertemplate="<b>%{x}</b><br>Goldstein: %{y:.2f}<extra></extra>"
    ), row=1, col=1)

    fig.add_hline(y=0, line_dash="dash", line_color=RED,
                  line_width=1, opacity=0.6, row=1, col=1)

    # ── AvgTone
    fig.add_trace(go.Scatter(
        x=xi + xi[::-1],
        y=list(t + 1.96 * se_t) + list((t - 1.96 * se_t)[::-1]),
        fill="toself", fillcolor=f"rgba(55,138,221,0.15)",
        line=dict(color="rgba(0,0,0,0)"), name="IC 95% tone", showlegend=False
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=xi, y=t, mode="lines+markers",
        line=dict(color=BLUE, width=2.5),
        marker=dict(size=8, symbol="square", color="white",
                    line=dict(color=BLUE, width=2)),
        name="AvgTone",
        hovertemplate="<b>%{x}</b><br>AvgTone: %{y:.2f}<extra></extra>"
    ), row=2, col=1)

    fig.add_hline(y=0, line_dash="dot", line_color="gray",
                  line_width=1, row=2, col=1)

    fig.update_layout(height=600, template="plotly_white",
                      legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig, use_container_width=True)

    # Tableau récap
    with st.expander(" Données mensuelles détaillées"):
        disp = monthly[["month_short","avg_goldstein","avg_tone",
                         "num_events","pct_conflict"]].copy()
        disp.columns = ["Mois","Goldstein moy.","AvgTone moy.","Nb événements","% Conflits"]
        disp = disp.set_index("Mois")
        st.dataframe(disp.style.format("{:.2f}"), use_container_width=True)


# ═══════════════════════════════════════════════
# PAGE 3 — CORRÉLATIONS  (fig3)
# ═══════════════════════════════════════════════
elif page == "🔗 Corrélations":
    st.title("🔗 Matrice de corrélation")

    cols = ["goldstein_scale","avg_tone","num_articles",
            "num_mentions","num_sources","quad_class","has_actor2"]
    labels_corr = ["Goldstein","AvgTone","Articles",
                   "Mentions","Sources","Quad class","A 2 acteurs"]

    corr = df[cols].corr()
    corr.index   = labels_corr
    corr.columns = labels_corr

    # Masque triangle sup
    mask = np.triu(np.ones_like(corr, dtype=bool))
    corr_masked = corr.where(~mask)

    fig = go.Figure(go.Heatmap(
        z=corr_masked.values,
        x=labels_corr,
        y=labels_corr,
        colorscale="RdYlGn",
        zmid=0, zmin=-1, zmax=1,
        text=corr_masked.round(2).values,
        texttemplate="%{text}",
        hoverongaps=False,
        colorbar=dict(title="r", len=0.8)
    ))
    fig.update_layout(
        title="Matrice de corrélation — DANHOMÈ INTEL 2025",
        height=550,
        template="plotly_white",
        xaxis=dict(tickangle=-35),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.info("**Lecture rapide** : Goldstein ↔ Quad class r=−0.78 (redondants) · "
            "Articles ↔ Mentions r=+0.96 (redondants). Éviter les deux dans un même modèle ML.")


# ═══════════════════════════════════════════════
# PAGE 4 — ACTEURS  (fig4)
# ═══════════════════════════════════════════════
elif page == "👤 Analyse acteurs":
    st.title("👤 Analyse des acteurs")

    tab1, tab2, tab3 = st.tabs(["Top acteurs", "Goldstein par type", "Heatmap acteur × mois"])

    # — Tab 1 : Top acteurs
    with tab1:
        top_act = (
            df[~df["actor1_name"].isin(["Acteur non identifié", "Unknown"])]
            ["actor1_name"].value_counts().head(10).reset_index()
        )
        top_act.columns = ["actor", "count"]
        top_act = top_act.sort_values("count")

        fig = go.Figure(go.Bar(
            x=top_act["count"], y=top_act["actor"],
            orientation="h",
            marker_color=BLUE, opacity=0.85,
            text=top_act["count"].apply(lambda v: f"{v:,}"),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Événements: %{x:,}<extra></extra>"
        ))
        fig.update_layout(
            title="Top 10 acteurs principaux",
            xaxis_title="Nombre d'événements",
            template="plotly_white", height=420
        )
        st.plotly_chart(fig, use_container_width=True)

    # — Tab 2 : Goldstein par type
    with tab2:
        act_stats = (
            df[df["actor1_type"] != "UNKNOWN"]
            .groupby("actor1_type")
            .agg(count=("event_code","count"), avg_g=("goldstein_scale","mean"))
            .reset_index()
            .query("count >= 30")
            .sort_values("avg_g")
        )
        act_stats["label"]  = act_stats["actor1_type"].map(CAMEO).fillna(act_stats["actor1_type"])
        act_stats["color"]  = act_stats["avg_g"].apply(lambda g: RED if g < 0 else GREEN)

        fig = go.Figure(go.Bar(
            x=act_stats["avg_g"], y=act_stats["label"],
            orientation="h",
            marker_color=act_stats["color"], opacity=0.85,
            text=act_stats["avg_g"].round(2),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Goldstein moy.: %{x:.2f}<extra></extra>"
        ))
        fig.add_vline(x=0, line_dash="dot", line_color="gray")
        fig.update_layout(
            title="GoldsteinScale moyen par type d'acteur",
            xaxis_title="GoldsteinScale moyen",
            template="plotly_white", height=480
        )
        st.plotly_chart(fig, use_container_width=True)

    # — Tab 3 : Heatmap
    with tab3:
        top_types = ["GOV","MIL","COP","CVL","LEG","EDU","IGO","MED","BUS","OPP"]
        df_f = df[df["actor1_type"].isin(top_types)].copy()
        df_f["actor_label"] = df_f["actor1_type"].map(CAMEO)

        pivot = df_f.pivot_table(
            values="goldstein_scale",
            index="actor_label",
            columns="month_short",
            aggfunc="mean"
        )
        col_order = [s for s in MONTH_SHORT if s in pivot.columns]
        pivot = pivot.reindex(columns=col_order)

        fig = go.Figure(go.Heatmap(
            z=pivot.values,
            x=col_order,
            y=pivot.index.tolist(),
            colorscale="RdYlGn",
            zmid=0, zmin=-5, zmax=5,
            text=np.round(pivot.values, 1),
            texttemplate="%{text}",
            colorbar=dict(title="Goldstein moy."),
            hovertemplate="<b>%{y}</b> · %{x}<br>Goldstein: %{z:.1f}<extra></extra>"
        ))
        fig.update_layout(
            title="GoldsteinScale par type d'acteur × mois<br>"
                  "<sup>rouge = déstabilisateur · vert = stabilisateur</sup>",
            template="plotly_white",
            height=420
        )
        st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════
# PAGE 5 — GÉOGRAPHIE  (fig5)
# ═══════════════════════════════════════════════
elif page == " Géographie":
    st.title(" Analyse géographique")

    col1, col2 = st.columns([1.3, 1])

    # — Top localités
    with col1:
        locs = (
            df[df["geo_full_name"] != "Benin"]
            ["geo_full_name"].value_counts().head(12).reset_index()
        )
        locs.columns = ["loc", "count"]
        locs["city"]  = locs["loc"].apply(lambda x: x.split(",")[0].strip())
        locs["zone"]  = locs["loc"].apply(
            lambda x: "Nord (sensible)" if any(k in x for k in NORTH_KW) else "Sud / Centre")
        locs = locs.sort_values("count")

        fig = go.Figure(go.Bar(
            x=locs["count"], y=locs["city"],
            orientation="h",
            marker_color=locs["zone"].map({"Nord (sensible)": RED, "Sud / Centre": GREEN}),
            opacity=0.85,
            text=locs["count"].apply(lambda v: f"{v:,}"),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Événements: %{x:,}<extra></extra>"
        ))
        fig.update_layout(
            title="Top localités — volume d'événements",
            xaxis_title="Nombre d'événements",
            template="plotly_white", height=450
        )
        st.plotly_chart(fig, use_container_width=True)

    # — Nord vs Sud bar
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
            text=zone_stats["avg_g"].round(2),
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Goldstein: %{y:.2f}<extra></extra>"
        ))
        fig2.add_hline(y=0, line_dash="dash", line_color="gray")
        fig2.update_layout(
            title="GoldsteinScale moyen<br>Nord vs Sud / Centre",
            yaxis_title="GoldsteinScale moyen",
            template="plotly_white", height=350
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.metric("Écart Nord−Sud",
                  f"{zone_stats.set_index('zone')['avg_g']['Nord (sensible)'] - zone_stats.set_index('zone')['avg_g']['Sud / Centre']:.2f}",
                  delta_color="inverse")

    # — Boxplot quad_class
    st.subheader("Goldstein par type d'événement")
    order  = [QUAD_L[k] for k in [1, 2, 3, 4]]
    colors = [QUAD_C[k] for k in [1, 2, 3, 4]]

    fig3 = go.Figure()
    for label, color in zip(order, colors):
        vals = df[df["quad_label"] == label]["goldstein_scale"].dropna()
        fig3.add_trace(go.Box(
            y=vals, name=label,
            marker_color=color,
            line_color=color,
            boxpoints="outliers",
            marker_size=3,
            opacity=0.8,
            hovertemplate=f"<b>{label}</b><br>Goldstein: %{{y:.1f}}<extra></extra>"
        ))
    fig3.update_layout(
        title="Distribution Goldstein par type d'événement",
        yaxis_title="GoldsteinScale",
        showlegend=False,
        template="plotly_white",
        height=400
    )
    st.plotly_chart(fig3, use_container_width=True)


# ═══════════════════════════════════════════════
# PAGE 6 — FOCUS POLICE / NORD  (fig_police_nord)
# ═══════════════════════════════════════════════
elif page == " Focus Police/Nord":
    st.title(" Focus Police × Nord — Hypothèse confirmée ?")

    # — Grouped bar : acteurs Nord vs Sud
    st.subheader("GoldsteinScale par type d'acteur — Nord vs Sud/Centre")

    actor_zone = (
        df[df["actor1_type"].isin(
            ["GOV","COP","MIL","CVL","IGO","OPP","UAF","MED","EDU","BUS"])]
        .groupby(["zone","actor1_type"])
        .agg(avg_gold=("goldstein_scale","mean"), count=("event_code","count"))
        .reset_index()
        .query("count >= 5")
    )
    actor_zone["label"] = actor_zone["actor1_type"].map(CAMEO).fillna(actor_zone["actor1_type"])

    pivot_bar = (actor_zone.pivot(index="label", columns="zone", values="avg_gold")
                 .fillna(0)
                 .sort_values("Nord (sensible)"))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Nord (sensible)",
        x=pivot_bar.index, y=pivot_bar["Nord (sensible)"],
        marker_color=RED, opacity=0.85,
        hovertemplate="<b>%{x}</b> Nord<br>Goldstein: %{y:.2f}<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        name="Sud / Centre",
        x=pivot_bar.index, y=pivot_bar["Sud / Centre"],
        marker_color=GREEN, opacity=0.85,
        hovertemplate="<b>%{x}</b> Sud<br>Goldstein: %{y:.2f}<extra></extra>"
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    fig.update_layout(
        barmode="group",
        xaxis_tickangle=-20,
        yaxis_title="GoldsteinScale moyen",
        template="plotly_white",
        legend=dict(orientation="h", y=1.05),
        height=420
    )
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    # — Volume Police par zone
    with col1:
        st.subheader("Volume & impact Police par zone")
        police_zone = (
            df[df["actor1_type"] == "COP"]
            .groupby("zone")
            .agg(count=("event_code","count"), avg_gold=("goldstein_scale","mean"))
            .reset_index()
        )
        fig2 = go.Figure(go.Bar(
            x=police_zone["zone"], y=police_zone["count"],
            marker_color=[RED, GREEN],
            text=[f"{int(r['count'])} événements<br>Gold: {r['avg_gold']:.2f}"
                  for _, r in police_zone.iterrows()],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Événements: %{y}<extra></extra>"
        ))
        fig2.update_layout(
            yaxis_title="Nombre d'événements",
            template="plotly_white", height=350
        )
        st.plotly_chart(fig2, use_container_width=True)

    # — Heatmap Police × Zone × Mois
    with col2:
        st.subheader("Impact Police par zone et mois")
        police_pivot = (
            df[df["actor1_type"] == "COP"]
            .groupby(["zone","month_short"])["goldstein_scale"]
            .mean().unstack()
        )
        col_order = [s for s in MONTH_SHORT if s in police_pivot.columns]
        police_pivot = police_pivot.reindex(columns=col_order)

        fig3 = go.Figure(go.Heatmap(
            z=police_pivot.values,
            x=col_order,
            y=police_pivot.index.tolist(),
            colorscale="RdYlGn",
            zmid=0, zmin=-6, zmax=3,
            text=np.round(police_pivot.values, 1),
            texttemplate="%{text}",
            colorbar=dict(title="Goldstein"),
            hovertemplate="<b>%{y}</b> · %{x}<br>Goldstein: %{z:.1f}<extra></extra>"
        ))
        fig3.update_layout(
            template="plotly_white", height=250,
            margin=dict(t=20, b=20)
        )
        st.plotly_chart(fig3, use_container_width=True)

    # — Top acteurs déstabilisateurs au Nord
    st.subheader("Acteurs les plus déstabilisateurs au Nord")
    north_actors = (
        df[df["zone"] == "Nord (sensible)"]
        .groupby("actor1_type")
        .agg(avg_gold=("goldstein_scale","mean"), count=("event_code","count"))
        .reset_index()
        .query("count >= 5")
        .sort_values("avg_gold")
        .head(10)
    )
    north_actors["label"] = (north_actors["actor1_type"].map(CAMEO)
                              .fillna(north_actors["actor1_type"]))
    north_actors["color"] = north_actors["avg_gold"].apply(lambda g: RED if g < 0 else GREEN)

    fig4 = go.Figure(go.Bar(
        x=north_actors["avg_gold"], y=north_actors["label"],
        orientation="h",
        marker_color=north_actors["color"], opacity=0.85,
        text=[f"{g:.2f} ({int(c)})"
              for g, c in zip(north_actors["avg_gold"], north_actors["count"])],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Goldstein: %{x:.2f}<extra></extra>"
    ))
    fig4.add_vline(x=0, line_dash="dot", line_color="gray")
    fig4.update_layout(
        xaxis_title="GoldsteinScale moyen",
        template="plotly_white", height=380
    )
    st.plotly_chart(fig4, use_container_width=True)

    st.success(" **Conclusion** : L'hypothèse est confirmée. La Police intervient au Nord "
               "dans des contextes de crise (Goldstein −2.93 en moy.) avec des pics "
               "catastrophiques en juin (−6.0) et novembre (−4.9). "
               "Les Rebelles (−9.53) et Forces non-id. (−5.06) dominent l'instabilité structurelle.")
