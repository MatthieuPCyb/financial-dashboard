"""Écran Paramètres : gestion des catégories et export des données."""

import csv
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk

import database as db


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self._build_categories_section()
        self._build_export_section()
        self.refresh()

    def _build_categories_section(self):
        card = ctk.CTkFrame(self, corner_radius=12)
        card.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 12))

        ctk.CTkLabel(card, text="Catégories", font=("Segoe UI", 13)).pack(anchor="w", padx=16, pady=(14, 8))

        self.categories_list = ctk.CTkFrame(card, fg_color="transparent")
        self.categories_list.pack(fill="x", padx=16)

        add_row = ctk.CTkFrame(card, fg_color="transparent")
        add_row.pack(fill="x", padx=16, pady=(10, 16))
        self.new_category_entry = ctk.CTkEntry(add_row, placeholder_text="Nom de la nouvelle catégorie")
        self.new_category_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(add_row, text="+ Ajouter", width=100, command=self._add_category).pack(side="left")

    def _build_export_section(self):
        card = ctk.CTkFrame(self, corner_radius=12)
        card.grid(row=1, column=0, sticky="ew", padx=4, pady=4)

        ctk.CTkLabel(card, text="Données", font=("Segoe UI", 13)).pack(anchor="w", padx=16, pady=(14, 8))
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(row, text="Exporter en CSV", command=self._export_csv).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row, text="Ouvrir le dossier de la base", command=self._show_db_location).pack(side="left")

    def refresh(self):
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
        if messagebox.askyesno("Confirmer", "Supprimer cette catégorie ? Les transactions associées seront conservées sans catégorie."):
            db.delete_category(category_id)
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
            writer.writerow(["Date", "Catégorie", "Type", "Note", "Montant"])
            for t in transactions:
                writer.writerow([t["date"], t["categorie_nom"] or "", t["type"], t["note"] or "", t["montant"]])

        messagebox.showinfo("Export réussi", f"Les transactions ont été exportées vers :\n{path}")

    def _show_db_location(self):
        messagebox.showinfo("Emplacement de la base", f"La base de données se trouve ici :\n{db.DB_PATH}")
