# MonBudget

Application de bureau (Python + CustomTkinter) pour suivre son budget mensuel, ses dépenses par catégorie et son épargne.

## Installation

```bash
# 1. Se placer dans le dossier du projet
cd budget_app

# 2. (recommandé) créer un environnement virtuel
python -m venv venv
source venv/bin/activate      # sur Windows : venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt
```

## Lancer l'application

```bash
python main.py
```

Une base de données SQLite (`data/budget.db`) est créée automatiquement au premier lancement, avec quelques catégories par défaut.

## Structure du projet

```
budget_app/
├── main.py              # Point d'entrée, fenêtre principale, navigation
├── database.py           # Toutes les requêtes SQLite (aucune requête ailleurs)
├── config.py              # Constantes visuelles (couleurs, polices, mois)
├── requirements.txt
├── data/
│   └── budget.db          # Créé automatiquement
└── ui/
    ├── sidebar.py          # Barre de navigation latérale
    ├── dashboard.py        # Écran Tableau de bord
    ├── expenses.py         # Écran Dépenses (ajout + tableau filtrable)
    ├── savings.py          # Écran Épargne (objectifs + historique)
    ├── stats.py            # Écran Statistiques (graphiques matplotlib)
    └── settings.py         # Écran Paramètres (catégories, export CSV)
```

## Schéma de la base de données

- **categories** (id, nom, couleur)
- **transactions** (id, montant, date, categorie_id, type, note)
- **objectifs_epargne** (id, nom, montant_cible, montant_actuel, date_limite)
- **versements_epargne** (id, objectif_id, montant, date)

## Pistes d'évolution

- Récurrence automatique pour les dépenses fixes (loyer, abonnements)
- Alertes de dépassement de budget par catégorie
- Import de relevés bancaires (CSV)
- Comparaison d'une année sur l'autre
