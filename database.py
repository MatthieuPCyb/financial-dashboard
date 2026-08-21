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
    ("Charges", "#378ADD"),
    ("Courses", "#639922"),
    ("Transport", "#BA7517"),
    ("Variable", "#E24B4A"),
    ("Abonnement", "#D4537E"),
    ("Banque & Assurance", "#D4537E"),
]


def get_connection():
    """Ouvre une connexion à la base de données (crée le dossier si besoin)."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crée les tables si elles n'existent pas encore, migre le schéma si besoin,
    et ajoute des catégories par défaut."""
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
        CREATE TABLE IF NOT EXISTS sous_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            categorie_id INTEGER NOT NULL,
            FOREIGN KEY (categorie_id) REFERENCES categories(id) ON DELETE CASCADE,
            UNIQUE(nom, categorie_id)
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
            sous_categorie_id INTEGER,
            FOREIGN KEY (categorie_id) REFERENCES categories(id) ON DELETE SET NULL,
            FOREIGN KEY (sous_categorie_id) REFERENCES sous_categories(id) ON DELETE SET NULL
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

    # Migration : les bases créées avant cette version stockaient la
    # sous-catégorie en texte libre (colonne "sous_categorie"). On la
    # remplace par une vraie relation vers la table "sous_categories".
    cur.execute("PRAGMA table_info(transactions)")
    colonnes = {row[1] for row in cur.fetchall()}

    if "sous_categorie_id" not in colonnes:
        cur.execute("ALTER TABLE transactions ADD COLUMN sous_categorie_id INTEGER")

        if "sous_categorie" in colonnes:
            anciennes = cur.execute(
                """
                SELECT DISTINCT sous_categorie, categorie_id FROM transactions
                WHERE sous_categorie IS NOT NULL AND sous_categorie != ''
                  AND categorie_id IS NOT NULL
                """
            ).fetchall()

            for nom, categorie_id in anciennes:
                cur.execute(
                    "INSERT OR IGNORE INTO sous_categories (nom, categorie_id) VALUES (?, ?)",
                    (nom, categorie_id),
                )
                ligne = cur.execute(
                    "SELECT id FROM sous_categories WHERE nom = ? AND categorie_id = ?",
                    (nom, categorie_id),
                ).fetchone()
                if ligne:
                    cur.execute(
                        "UPDATE transactions SET sous_categorie_id = ? "
                        "WHERE sous_categorie = ? AND categorie_id = ?",
                        (ligne["id"], nom, categorie_id),
                    )

            try:
                cur.execute("ALTER TABLE transactions DROP COLUMN sous_categorie")
            except sqlite3.OperationalError:
                pass  # anciennes versions de SQLite ne supportent pas DROP COLUMN

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


# ---------- Sous-catégories ----------

def get_subcategories(categorie_id=None):
    """Sans argument : retourne toutes les sous-catégories avec le nom de
    leur catégorie parente (categorie_nom). Avec categorie_id : ne retourne
    que les sous-catégories de cette catégorie."""
    conn = get_connection()
    if categorie_id:
        rows = conn.execute(
            "SELECT * FROM sous_categories WHERE categorie_id = ? ORDER BY nom",
            (categorie_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT sc.*, c.nom AS categorie_nom
            FROM sous_categories sc
            JOIN categories c ON c.id = sc.categorie_id
            ORDER BY c.nom, sc.nom
            """
        ).fetchall()
    conn.close()
    return rows


def add_subcategory(nom, categorie_id):
    conn = get_connection()
    conn.execute(
        "INSERT INTO sous_categories (nom, categorie_id) VALUES (?, ?)",
        (nom, categorie_id),
    )
    conn.commit()
    conn.close()


def delete_subcategory(subcategorie_id):
    conn = get_connection()
    conn.execute("DELETE FROM sous_categories WHERE id = ?", (subcategorie_id,))
    conn.commit()
    conn.close()


# ---------- Transactions ----------

def add_transaction(montant, date, categorie_id, type_, note="", sous_categorie_id=None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO transactions (montant, date, categorie_id, type, note, sous_categorie_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (montant, date, categorie_id, type_, note, sous_categorie_id),
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
               c.nom AS categorie_nom, c.couleur AS categorie_couleur,
               sc.nom AS sous_categorie_nom
        FROM transactions t
        LEFT JOIN categories c ON c.id = t.categorie_id
        LEFT JOIN sous_categories sc ON sc.id = t.sous_categorie_id
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
    """Retourne le total des dépenses par catégorie pour le mois donné ('YYYY-MM').

    Chaque ligne contient : categorie (nom), total, couleur.
    Seules les catégories ayant au moins une dépense ce mois-ci sont retournées,
    triées par total décroissant.
    """
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT c.nom AS categorie, c.couleur AS couleur, SUM(t.montant) AS total
        FROM transactions t
        JOIN categories c ON c.id = t.categorie_id
        WHERE strftime('%Y-%m', t.date) = ? AND t.type = 'depense'
        GROUP BY c.id
        ORDER BY total DESC
        """,
        (month,),
    ).fetchall()
    conn.close()
    return rows


def subcategory_breakdown(month, categorie):
    """Retourne le total des dépenses par sous-catégorie, pour une catégorie
    (nom) et un mois ('YYYY-MM') donnés.

    Chaque ligne contient : sous_categorie, total. Les dépenses sans
    sous-catégorie renseignée sont regroupées sous une valeur NULL
    (affichée comme "Non classé" côté interface).
    """
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT sc.nom AS sous_categorie, SUM(t.montant) AS total
        FROM transactions t
        JOIN categories c ON c.id = t.categorie_id
        LEFT JOIN sous_categories sc ON sc.id = t.sous_categorie_id
        WHERE strftime('%Y-%m', t.date) = ? AND c.nom = ? AND t.type = 'depense'
        GROUP BY t.sous_categorie_id
        ORDER BY total DESC
        """,
        (month, categorie),
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