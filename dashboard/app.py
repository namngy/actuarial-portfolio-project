"""Dashboard de suivi de portefeuille auto : A/E, S/P et alertes de dérive.

Lancement depuis la racine du repo :
    streamlit run dashboard/app.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Suivi de portefeuille auto", layout="wide")

DATA = Path(__file__).resolve().parent.parent / "data" / "monitoring_sim.csv"

DIMENSIONS = {
    "Portefeuille entier": None,
    "Tranche d'âge": "age_group",
    "Tranche de bonus-malus": "bm_group",
    "Cellule (âge × bonus-malus)": "cellule",
}


@st.cache_data
def charger():
    sim = pd.read_csv(DATA)
    sim["cellule"] = sim["age_group"] + " | BM " + sim["bm_group"]
    return sim


def borne(texte):
    """'(17, 25]' -> 17 : sert à trier les tranches dans l'ordre naturel."""
    return int(texte.split(",")[0].strip("( "))


def cle_tri(texte):
    if " | BM " in texte:
        age, bm = texte.split(" | BM ")
        return borne(age) * 1000 + borne(bm)
    return borne(texte)


def agreger(d, cles, phi, z, min_att):
    """Somme les montants par groupe, puis calcule A/E, S/P, seuil et alerte."""
    t = (d.groupby(cles)[["sin_attendus", "sin_reels", "prime", "cout"]]
           .sum().reset_index())
    t["AE"] = t["sin_reels"] / t["sin_attendus"]
    t["SP"] = t["cout"] / t["prime"]
    t["seuil"] = z * np.sqrt(phi / t["sin_attendus"])
    t["fiable"] = t["sin_attendus"] >= min_att
    t["alerte"] = ((t["AE"] - 1).abs() > t["seuil"]) & t["fiable"]
    return t


def graphique_ae(serie, mois, titre):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=serie["mois"], y=1 + serie["seuil"],
                             line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=serie["mois"], y=1 - serie["seuil"],
                             line=dict(width=0), fill="tonexty",
                             fillcolor="rgba(130,130,130,0.2)",
                             name="Zone normale", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=serie["mois"], y=serie["AE"],
                             mode="lines+markers", name="A/E"))
    al = serie[serie["alerte"]]
    fig.add_trace(go.Scatter(x=al["mois"], y=al["AE"], mode="markers",
                             marker=dict(color="red", size=12, symbol="diamond"),
                             name="Alerte"))
    fig.add_hline(y=1, line_dash="dash", line_color="grey")
    fig.add_vline(x=mois, line_dash="dot", line_color="grey")
    fig.update_layout(title=f"A/E par mois : {titre}", height=380,
                      xaxis=dict(dtick=1, title="Mois"), yaxis_title="A/E",
                      margin=dict(t=50, b=40))
    return fig


def graphique_sp(serie, mois, titre):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=serie["mois"], y=serie["SP"],
                             mode="lines+markers", name="S/P"))
    fig.add_hline(y=1, line_dash="dash", line_color="grey")
    fig.add_vline(x=mois, line_dash="dot", line_color="grey")
    fig.update_layout(title=f"S/P par mois : {titre}", height=380,
                      xaxis=dict(dtick=1, title="Mois"),
                      yaxis=dict(tickformat=".0%", title="S/P"),
                      margin=dict(t=50, b=40))
    return fig


sim = charger()
mois_max = int(sim["mois"].max())

# ---------------------------------------------------------------- paramètres
with st.sidebar:
    st.header("Paramètres")
    nom_dim = st.radio("Segmentation", list(DIMENSIONS))
    cle = DIMENSIONS[nom_dim]
    mois = st.slider("Mois analysé", 1, mois_max, mois_max)
    z = st.slider("Seuil d'alerte (z)", 1.5, 4.0, 2.0, 0.5)
    phi = st.slider("Surdispersion φ", 1.0, 2.5, 1.75, 0.05)
    min_att = st.number_input("Sinistres attendus minimum par segment",
                              min_value=1, max_value=100, value=10)
    if cle is None:
        choix = "Tous"
    else:
        valeurs = sorted(sim[cle].unique(), key=cle_tri)
        choix = st.selectbox("Segment suivi dans le temps", ["Tous"] + valeurs)

if choix == "Tous":
    sel, titre = sim, "portefeuille entier"
else:
    sel, titre = sim[sim[cle] == choix], choix

serie = agreger(sel, ["mois"], phi, z, min_att)
cour = serie[serie["mois"] == mois].iloc[0]

if cle is not None:
    tab = agreger(sim[sim["mois"] == mois], [cle], phi, z, min_att)
    tab["ordre"] = tab[cle].map(cle_tri)
    tab = tab.sort_values("ordre")

# ------------------------------------------------------------------ en-tête
st.title("Suivi de portefeuille : assurance auto")
st.caption("Données simulées sur 12 mois à partir des modèles de pricing "
           "(une dérive de fréquence a été injectée sur un segment).")

c1, c2, c3, c4 = st.columns(4)
c1.metric("A/E (réels / attendus)", f"{cour['AE']:.2f}")
c2.metric("S/P (hors grands sinistres)", f"{cour['SP']:.0%}")
c3.metric("Sinistres réels / attendus",
          f"{cour['sin_reels']:.0f} / {cour['sin_attendus']:.0f}")
if cle is None:
    c4.metric("Statut", "ALERTE" if cour["alerte"] else "Normal")
else:
    c4.metric("Segments en alerte",
              f"{int(tab['alerte'].sum())} / {int(tab['fiable'].sum())}")

premiere = serie[serie["alerte"]]
if len(premiere):
    st.warning(f"Première alerte sur « {titre} » au mois {int(premiere['mois'].min())}.")
else:
    st.success(f"Aucune alerte sur « {titre} » sur les {mois_max} mois.")

# ---------------------------------------------------------------- graphiques
g1, g2 = st.columns(2)
g1.plotly_chart(graphique_ae(serie, mois, titre), key="ae")
g2.plotly_chart(graphique_sp(serie, mois, titre), key="sp")

# ------------------------------------------------- tableau et carte de chaleur
if cle is not None:
    st.subheader(f"Segments au mois {mois}")
    affiche = tab.copy()
    affiche["Statut"] = np.where(affiche["alerte"], "ALERTE",
                                 np.where(affiche["fiable"], "Normal",
                                          "Volume insuffisant"))
    affiche = affiche[[cle, "sin_attendus", "sin_reels", "AE", "seuil", "SP", "Statut"]]
    affiche.columns = ["Segment", "Attendus", "Réels", "A/E", "Seuil (±)", "S/P", "Statut"]

    def colorer(ligne):
        couleur = "background-color: rgba(255,0,0,0.25)" if ligne["Statut"] == "ALERTE" else ""
        return [couleur] * len(ligne)

    st.dataframe(
        affiche.style.apply(colorer, axis=1).format(
            {"Attendus": "{:.1f}", "Réels": "{:.0f}", "A/E": "{:.2f}",
             "Seuil (±)": "{:.2f}", "S/P": "{:.0%}"}),
        hide_index=True)

    st.subheader("Historique des A/E par segment")
    histo = agreger(sim, [cle, "mois"], phi, z, min_att)
    histo["txt"] = np.where(
        histo["fiable"],
        histo["AE"].round(2).astype(str) + np.where(histo["alerte"], " *", ""),
        "")
    histo.loc[~histo["fiable"], "AE"] = np.nan
    ordre = sorted(histo[cle].unique(), key=cle_tri)
    piv = histo.pivot(index=cle, columns="mois", values="AE").loc[ordre]
    piv_txt = histo.pivot(index=cle, columns="mois", values="txt").loc[ordre]
    fig = go.Figure(go.Heatmap(
        z=piv.values, x=piv.columns.tolist(), y=piv.index.tolist(),
        text=piv_txt.values, texttemplate="%{text}",
        colorscale="RdBu_r", zmid=1, zmin=0.5, zmax=1.5,
        colorbar=dict(title="A/E")))
    fig.update_layout(height=max(320, 30 * len(piv) + 110),
                      xaxis=dict(dtick=1, title="Mois"),
                      yaxis=dict(autorange="reversed"),
                      margin=dict(t=30, b=40))
    st.plotly_chart(fig, key="heatmap")
    st.caption("* = alerte. Cases vides : moins de sinistres attendus que le "
               "minimum fixé, donc trop peu fiable pour être testé.")

# ------------------------------------------------------------ méthode, limites
with st.expander("Méthode et limites"):
    st.markdown(
        """
**A/E** = sinistres réels / sinistres attendus par le modèle de fréquence.
**S/P** = coût réel / prime pure (sans le chargement grands sinistres).

**Seuil d'alerte.** Pour un segment avec *a* sinistres attendus, le nombre de
sinistres réels a une variance d'environ φ·a (φ = 1 pour un Poisson pur,
1,75 mesuré sur les données). L'écart-type de A/E est donc √(φ/a), et une
alerte se déclenche quand |A/E − 1| > z·√(φ/a).

**Limites.**
- Dérive simulée : le dataset d'origine n'a pas de dimension temporelle.
- La simulation est un Poisson pur (φ = 1), donc le seuil avec φ = 1,75 est prudent.
- L'approximation normale est mauvaise sous une dizaine de sinistres attendus.
- Plus on teste de segments et de mois, plus on obtient de fausses alertes.
- A/E ne voit que la fréquence : une dérive de sévérité n'apparaît que dans le S/P.
"""
    )
