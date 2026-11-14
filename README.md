# Pricing, souscription et suivi d'un portefeuille d'assurance auto

Projet personnel d'actuariat non-vie en Python, construit sur le jeu de données réel
**French Motor Third-Party Liability** (freMTPL2) : 668 897 contrats après nettoyage.

Il reproduit la chaîne de travail d'un actuaire : **fixer un prix** (pricing), **décider qui accepter et à
quelles conditions** (souscription), puis **surveiller que la réalité reste conforme aux prévisions**
(suivi de portefeuille).

> La démarche complète, avec les choix expliqués et les limites, est détaillée dans la
> [note technique](reports/note_technique.pdf) (7 pages).

## Résultats clés

| Volet | Résultat |
|---|---|
| Pricing | Prime pure moyenne de **169,28 €** par année d'exposition, pour un coût réel de **169,29 €** |
| Variable clé | La fréquence de sinistres passe de **7,5 % à 56,8 %** entre les meilleurs et les pires bonus-malus |
| Modèle de fréquence | Poisson avec interaction âge × bonus-malus : AIC en baisse de **358 points** par rapport au modèle sans interaction |
| Grands sinistres | 39 sinistres de plus de 100 000 € (0,16 % du total) pèsent **24 % du coût** : plafonnement à 100 000 € et chargement séparé de 28,10 € par année d'exposition |
| Souscription | Sur 36 profils tarifaires : 18 acceptés (99 % de l'exposition), 8 surprimés, 8 en revue manuelle, 2 refusés |
| Capital simplifié | **15,6 M€** (26,6 % du coût annuel moyen) par simulation Monte-Carlo, **2,6 M€** si les sinistres sont plafonnés à 100 000 € |
| Suivi de portefeuille | Dérive de fréquence simulée détectée dès le mois où elle apparaît, sans fausse alerte avant |

## Démarche

1. **Exploration et nettoyage** : jointure des tables de fréquence et de sévérité, détection de 9 116 polices
   incohérentes (sinistre déclaré sans montant), retirées du jeu de données.
2. **Fréquence** : régression de Poisson avec l'exposition en offset, variables en tranches, diagnostic de
   surdispersion (1,75), comparaison des sinistres observés et attendus par profil, ajout d'une interaction.
3. **Sévérité** : régression Gamma sur les coûts plafonnés à 100 000 €, chargement séparé pour la part
   au-dessus du plafond.
4. **Prime pure** : fréquence × sévérité + chargement grands sinistres, contrôlée contre le coût réel.
5. **Souscription** : seuil de crédibilité (30 sinistres), règle accepter / surprime / refuser / revue manuelle,
   mesure de l'impact sur le portefeuille.
6. **Capital** : simulation de 5 000 années, quantile à 99,5 %.
7. **Suivi** : indicateurs A/E et S/P, seuil d'alerte statistique, dashboard interactif sur une dérive simulée.

## Structure du dépôt

```
.
├── README.md
├── requirements.txt
├── notebooks/
│   ├── 01_eda.ipynb                  # exploration, nettoyage, fréquence par âge et bonus-malus
│   ├── 02_pricing_frequency.ipynb    # modèles de fréquence et de sévérité, prime pure
│   ├── 03_underwriting_risk.ipynb    # crédibilité, règle de souscription, capital simplifié
│   └── 04_portfolio_monitoring.ipynb # simulation de 12 mois et règle d'alerte
├── src/
│   └── data_loading.py               # chargement et nettoyage des données
├── dashboard/
│   └── app.py                        # tableau de bord Streamlit
├── data/
│   └── monitoring_sim.csv            # données simulées lues par le dashboard
└── reports/
    └── note_technique.pdf            # note technique de synthèse
```

## Reproduire le projet

**1. Installer les dépendances**

```bash
git clone https://github.com/<ton-pseudo>/actuarial-portfolio-project.git
cd actuarial-portfolio-project
python -m pip install -r requirements.txt
```

**2. Lancer les notebooks dans l'ordre** (`python -m jupyter lab`) : 01, 02, 03, 04.

Les données sont téléchargées depuis OpenML au premier lancement. Le notebook 02 enregistre un fichier
`data/portfolio_priced.parquet` (volumineux, non versionné) que le notebook 03 relit, et le notebook 04 produit
`data/monitoring_sim.csv`. Il faut donc respecter cet ordre.

**3. Lancer le dashboard**, depuis la racine du dépôt :

```bash
python -m streamlit run dashboard/app.py
```

Il permet de choisir la segmentation (portefeuille, âge, bonus-malus, profil), le mois, le seuil d'alerte,
et affiche l'A/E avec sa zone normale, le S/P, un tableau des segments en alerte et une carte de chaleur.

## Limites

Elles sont détaillées dans la note technique (section 7). Les principales :

- pas de jeu de test : les modèles sont évalués sur les données qui ont servi à les estimer ;
- l'interaction âge × bonus-malus donne des prix instables aux petits profils, contenus par un seuil de
  crédibilité arbitraire ;
- le capital est une borne basse simplifiée (pas de risque de réserve, pas de réassurance, sinistres limités à
  ceux observés) ;
- la dérive de suivi est simulée : le dispositif est démontré, pas validé sur des données réelles.

## Outils

Python, pandas, NumPy, statsmodels, scikit-learn, Plotly, Streamlit, JupyterLab.

## Données

Jeu de données freMTPL2freq et freMTPL2sev (OpenML), utilisé à des fins pédagogiques.
