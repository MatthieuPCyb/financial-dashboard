"""
Module d'accès aux données (SQLite).
Toutes les requêtes SQL de l'application passent par ce fichier.
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "data" / "budget.db"

DEFAULT_CATEGORIES = [
    ("Loyer", "#378ADD"),
    ("Courses", "#639922"),
    ("Transport", "#BA7517"),
    ("Loisirs", "#E24B4A"),
    ("Santé", "#D4537E"),
    ("Autres", "#888780"),
]


def get_connection():
    """Ouvre une connexion à la base de données (crée le dossier si besoin)."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crée les tables si elles n'existent pas encore, et ajoute des catégories par défaut."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT UNIQUE NOT NULL,
            couleur TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            montant REAL NOT NULL,
            date TEXT NOT NULL,
            categorie_id INTEGER,
            type TEXT NOT NULL CHECK(type IN ('depense', 'revenu')),
            note TEXT,
            FOREIGN KEY (categorie_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS objectifs_epargne (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            montant_cible REAL NOT NULL,
            montant_actuel REAL NOT NULL DEFAULT 0,
            date_limite TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS versements_epargne (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            objectif_id INTEGER NOT NULL,
            montant REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (objectif_id) REFERENCES objectifs_epargne(id) ON DELETE CASCADE
        )
    """)

    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO categories (nom, couleur) VALUES (?, ?)", DEFAULT_CATEGORIES
        )

    conn.commit()
    conn.close()


# ---------- Catégories ----------

def get_categories():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM categories ORDER BY nom").fetchall()
    conn.close()
    return rows


def add_category(nom, couleur="#7F77DD"):
    conn = get_connection()
    conn.execute("INSERT INTO categories (nom, couleur) VALUES (?, ?)", (nom, couleur))
    conn.commit()
    conn.close()


def delete_category(category_id):
    conn = get_connection()
    conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()


# ---------- Transactions ----------

def add_transaction(montant, date, categorie_id, type_, note=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO transactions (montant, date, categorie_id, type, note) VALUES (?, ?, ?, ?, ?)",
        (montant, date, categorie_id, type_, note),
    )
    conn.commit()
    conn.close()


def delete_transaction(transaction_id):
    conn = get_connection()
    conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()


def get_transactions(month=None, category_id=None):
    """month au format 'YYYY-MM'. Retourne les transactions les plus récentes en premier."""
    conn = get_connection()
    query = """
        SELECT t.id, t.montant, t.date, t.type, t.note,
               c.nom AS categorie_nom, c.couleur AS categorie_couleur
        FROM transactions t
        LEFT JOIN categories c ON c.id = t.categorie_id
        WHERE 1=1
    """
    params = []
    if month:
        query += " AND strftime('%Y-%m', t.date) = ?"
        params.append(month)
    if category_id:
        query += " AND t.categorie_id = ?"
        params.append(category_id)
    query += " ORDER BY t.date DESC, t.id DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def monthly_summary(month):
    """Retourne (revenus, depenses) pour le mois donné ('YYYY-MM')."""
    conn = get_connection()
    row = conn.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN type = 'revenu' THEN montant ELSE 0 END), 0) AS revenus,
            COALESCE(SUM(CASE WHEN type = 'depense' THEN montant ELSE 0 END), 0) AS depenses
        FROM transactions
        WHERE strftime('%Y-%m', date) = ?
        """,
        (month,),
    ).fetchone()
    conn.close()
    return row["revenus"], row["depenses"]


def category_breakdown(month):
    """Répartition des dépenses par catégorie pour un mois donné."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT c.nom AS categorie, c.couleur AS couleur, SUM(t.montant) AS total
        FROM transactions t
        JOIN categories c ON c.id = t.categorie_id
        WHERE t.type = 'depense' AND strftime('%Y-%m', t.date) = ?
        GROUP BY c.id
        ORDER BY total DESC
        """,
        (month,),
    ).fetchall()
    conn.close()
    return rows


def monthly_trend(n_months=6):
    """Retourne les totaux dépenses/revenus des n derniers mois (du plus ancien au plus récent)."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT strftime('%Y-%m', date) AS mois,
               COALESCE(SUM(CASE WHEN type = 'revenu' THEN montant ELSE 0 END), 0) AS revenus,
               COALESCE(SUM(CASE WHEN type = 'depense' THEN montant ELSE 0 END), 0) AS depenses
        FROM transactions
        GROUP BY mois
        ORDER BY mois DESC
        LIMIT ?
        """,
        (n_months,),
    ).fetchall()
    conn.close()
    return list(reversed(rows))


# ---------- Épargne ----------

def get_savings_goals():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM objectifs_epargne ORDER BY id").fetchall()
    conn.close()
    return rows


def add_savings_goal(nom, montant_cible, date_limite=None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO objectifs_epargne (nom, montant_cible, montant_actuel, date_limite) VALUES (?, ?, 0, ?)",
        (nom, montant_cible, date_limite),
    )
    conn.commit()
    conn.close()


def add_saving_contribution(objectif_id, montant, date=None):
    date = date or datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    conn.execute(
        "INSERT INTO versements_epargne (objectif_id, montant, date) VALUES (?, ?, ?)",
        (objectif_id, montant, date),
    )
    conn.execute(
        "UPDATE objectifs_epargne SET montant_actuel = montant_actuel + ? WHERE id = ?",
        (montant, objectif_id),
    )
    conn.commit()
    conn.close()


def get_savings_history(limit=20):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT v.date, v.montant, o.nom AS objectif
        FROM versements_epargne v
        JOIN objectifs_epargne o ON o.id = v.objectif_id
        ORDER BY v.date DESC, v.id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return rows
