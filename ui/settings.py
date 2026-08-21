"""Écran Paramètres : gestion des catégories, sous-catégories et export des données."""

import csv
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk

import database as db


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Conteneur défilable qui englobe l'ensemble des sections
        self.scrollable_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_container.grid(row=0, column=0, sticky="nsew")
        self.scrollable_container.grid_columnconfigure(0, weight=1)

        self._build_categories_section()
        self._build_subcategories_section()
        self._build_export_section()
        self.refresh()

    def _build_categories_section(self):
        card = ctk.CTkFrame(self.scrollable_container, corner_radius=12)
        card.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 12))

        ctk.CTkLabel(card, text="Catégories", font=("Segoe UI", 13)).pack(anchor="w", padx=16, pady=(14, 8))

        self.categories_list = ctk.CTkFrame(card, fg_color="transparent")
        self.categories_list.pack(fill="x", padx=16)

        add_row = ctk.CTkFrame(card, fg_color="transparent")
        add_row.pack(fill="x", padx=16, pady=(10, 16))
        self.new_category_entry = ctk.CTkEntry(add_row, placeholder_text="Nom de la nouvelle catégorie")
        self.new_category_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(add_row, text="+ Ajouter", width=100, command=self._add_category).pack(side="left")

    def _build_subcategories_section(self):
        card = ctk.CTkFrame(self.scrollable_container, corner_radius=12)
        card.grid(row=1, column=0, sticky="ew", padx=4, pady=(4, 12))

        ctk.CTkLabel(card, text="Sous-catégories", font=("Segoe UI", 13)).pack(anchor="w", padx=16, pady=(14, 8))

        self.subcategories_list = ctk.CTkFrame(card, fg_color="transparent")
        self.subcategories_list.pack(fill="x", padx=16)

        add_row = ctk.CTkFrame(card, fg_color="transparent")
        add_row.pack(fill="x", padx=16, pady=(10, 16))

        self.subcat_parent_categories = db.get_categories()
        noms = [c["nom"] for c in self.subcat_parent_categories] or ["Aucune catégorie"]
        self.subcat_parent_var = ctk.StringVar(value=noms[0])
        self.subcat_parent_menu = ctk.CTkOptionMenu(
            add_row, values=noms, variable=self.subcat_parent_var, width=140
        )
        self.subcat_parent_menu.pack(side="left", padx=(0, 8))

        self.new_subcategory_entry = ctk.CTkEntry(add_row, placeholder_text="Nom de la nouvelle sous-catégorie")
        self.new_subcategory_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(add_row, text="+ Ajouter", width=100, command=self._add_subcategory).pack(side="left")

    def _build_export_section(self):
        card = ctk.CTkFrame(self.scrollable_container, corner_radius=12)
        card.grid(row=2, column=0, sticky="ew", padx=4, pady=4)

        ctk.CTkLabel(card, text="Données", font=("Segoe UI", 13)).pack(anchor="w", padx=16, pady=(14, 8))
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(row, text="Exporter en CSV", command=self._export_csv).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row, text="Ouvrir le dossier de la base", command=self._show_db_location).pack(side="left")

    def refresh(self):
        # Catégories
        for widget in self.categories_list.winfo_children():
            widget.destroy()

        for cat in db.get_categories():
            row = ctk.CTkFrame(self.categories_list, fg_color="transparent")
            row.pack(fill="x", pady=3)
            swatch = ctk.CTkLabel(row, text="  ", fg_color=cat["couleur"], width=14, corner_radius=3)
            swatch.pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row, text=cat["nom"], anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row, text="Supprimer", width=80, fg_color="transparent", border_width=1,
                text_color=("gray10", "gray90"),
                command=lambda cid=cat["id"]: self._delete_category(cid),
            ).pack(side="right")

        # Sous-catégories
        self.subcat_parent_categories = db.get_categories()
        noms = [c["nom"] for c in self.subcat_parent_categories] or ["Aucune catégorie"]
        self.subcat_parent_menu.configure(values=noms)
        if self.subcat_parent_var.get() not in noms:
            self.subcat_parent_var.set(noms[0])

        for widget in self.subcategories_list.winfo_children():
            widget.destroy()

        sous_categories = db.get_subcategories()
        if not sous_categories:
            ctk.CTkLabel(
                self.subcategories_list, text="Aucune sous-catégorie pour le moment.", text_color="gray60"
            ).pack(anchor="w", pady=4)

        for sc in sous_categories:
            row = ctk.CTkFrame(self.subcategories_list, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=sc["nom"], anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"({sc['categorie_nom']})", text_color="gray60").pack(
                side="left", padx=(8, 0)
            )
            ctk.CTkButton(
                row, text="Supprimer", width=80, fg_color="transparent", border_width=1,
                text_color=("gray10", "gray90"),
                command=lambda scid=sc["id"]: self._delete_subcategory(scid),
            ).pack(side="right")

    def _add_category(self):
        nom = self.new_category_entry.get().strip()
        if not nom:
            return
        try:
            db.add_category(nom)
        except Exception:
            messagebox.showerror("Erreur", "Cette catégorie existe déjà.")
            return
        self.new_category_entry.delete(0, "end")
        self.refresh()

    def _delete_category(self, category_id):
        if messagebox.askyesno(
            "Confirmer",
            "Supprimer cette catégorie ? Les transactions associées seront conservées sans catégorie, "
            "et ses sous-catégories seront supprimées.",
        ):
            db.delete_category(category_id)
            self.refresh()

    def _add_subcategory(self):
        nom = self.new_subcategory_entry.get().strip()
        if not nom:
            return
        categorie = next(
            (c for c in self.subcat_parent_categories if c["nom"] == self.subcat_parent_var.get()), None
        )
        if not categorie:
            messagebox.showerror("Erreur", "Créez d'abord une catégorie.")
            return
        try:
            db.add_subcategory(nom, categorie["id"])
        except Exception:
            messagebox.showerror("Erreur", "Cette sous-catégorie existe déjà pour cette catégorie.")
            return
        self.new_subcategory_entry.delete(0, "end")
        self.refresh()

    def _delete_subcategory(self, subcategorie_id):
        if messagebox.askyesno("Confirmer", "Supprimer cette sous-catégorie ?"):
            db.delete_subcategory(subcategorie_id)
            self.refresh()

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
            filetypes=[("Fichier CSV", "*.csv")],
        )
        if not path:
            return

        transactions = db.get_transactions()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Catégorie", "Sous-catégorie", "Type", "Note", "Montant"])
            for t in transactions:
                writer.writerow([
                    t["date"],
                    t["categorie_nom"] or "",
                    t["sous_categorie_nom"] or "",
                    t["type"],
                    t["note"] or "",
                    t["montant"],
                ])

        messagebox.showinfo("Export réussi", f"Les transactions ont été exportées vers :\n{path}")

    def _show_db_location(self):
        messagebox.showinfo("Emplacement de la base", f"La base de données se trouve ici :\n{db.DB_PATH}")