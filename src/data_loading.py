"""
Chargement et jointure du dataset French Motor Third-Party Liability
(freMTPL2freq + freMTPL2sev) via OpenML.
"""

import pandas as pd
from sklearn.datasets import fetch_openml


def load_freMTPL(cache=True):
    """
    Charge et fusionne les données de fréquence et de sévérité.

    Returns
    -------
    pd.DataFrame
        Une ligne par police, avec les variables d'exposition,
        de profil de risque, le nombre de sinistres (ClaimNb)
        et le coût total des sinistres associés (ClaimAmount).
    """
    # Fréquence : une ligne par police
    freq = fetch_openml(data_id=41214, as_frame=True, parser="auto").frame

    # Sévérité : une ligne par sinistre (plusieurs lignes possibles par police)
    sev = fetch_openml(data_id=41215, as_frame=True, parser="auto").frame

    # Agrégation du coût total des sinistres par police
    sev_agg = sev.groupby("IDpol", as_index=False)["ClaimAmount"].sum()

    # Jointure gauche : les polices sans sinistre auront ClaimAmount = 0
    df = freq.merge(sev_agg, on="IDpol", how="left")
    df["ClaimAmount"] = df["ClaimAmount"].fillna(0)

    return df


if __name__ == "__main__":
    df = load_freMTPL()
    print(df.shape)
    print(df.head())