"""Écran Dépenses : formulaire d'ajout + tableau des transactions."""

from datetime import datetime
from tkinter import ttk, messagebox

import customtkinter as ctk

import database as db


class ExpensesFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_form()
        self._build_filters()
        self._build_table()
        self.refresh()

    # ---------- Formulaire d'ajout ----------

    def _build_form(self):
        form = ctk.CTkFrame(self, corner_radius=12)
        form.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 12))
        for i in range(5):
            form.grid_columnconfigure(i, weight=1)

        ctk.CTkLabel(form, text="Nouvelle transaction", font=("Segoe UI", 12), text_color="gray60").grid(
            row=0, column=0, columnspan=5, sticky="w", padx=14, pady=(12, 6)
        )

        self.entry_montant = ctk.CTkEntry(form, placeholder_text="Montant (€)")
        self.entry_montant.grid(row=1, column=0, sticky="ew", padx=(14, 6), pady=(0, 12))

        self.type_var = ctk.StringVar(value="depense")
        self.menu_type = ctk.CTkOptionMenu(form, values=["depense", "revenu"], variable=self.type_var)
        self.menu_type.grid(row=1, column=1, sticky="ew", padx=6, pady=(0, 12))

        self.categories = db.get_categories()
        noms_categories = [c["nom"] for c in self.categories] or ["Aucune catégorie"]
        self.cat_var = ctk.StringVar(value=noms_categories[0])
        self.menu_categorie = ctk.CTkOptionMenu(form, values=noms_categories, variable=self.cat_var)
        self.menu_categorie.grid(row=1, column=2, sticky="ew", padx=6, pady=(0, 12))

        self.entry_date = ctk.CTkEntry(form, placeholder_text="AAAA-MM-JJ")
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_date.grid(row=1, column=3, sticky="ew", padx=6, pady=(0, 12))

        self.entry_note = ctk.CTkEntry(form, placeholder_text="Note (optionnel)")
        self.entry_note.grid(row=1, column=4, sticky="ew", padx=(6, 14), pady=(0, 12))

        ctk.CTkButton(form, text="+ Ajouter", command=self._add_transaction).grid(
            row=2, column=4, sticky="e", padx=(6, 14), pady=(0, 14)
        )

    def _add_transaction(self):
        try:
            montant = float(self.entry_montant.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Erreur", "Le montant doit être un nombre.")
            return
        if montant <= 0:
            messagebox.showerror("Erreur", "Le montant doit être positif.")
            return

        date = self.entry_date.get().strip()
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Erreur", "La date doit être au format AAAA-MM-JJ.")
            return

        categorie = next((c for c in self.categories if c["nom"] == self.cat_var.get()), None)
        categorie_id = categorie["id"] if categorie else None

        db.add_transaction(
            montant=montant,
            date=date,
            categorie_id=categorie_id,
            type_=self.type_var.get(),
            note=self.entry_note.get().strip(),
        )

        self.entry_montant.delete(0, "end")
        self.entry_note.delete(0, "end")
        self.refresh()

    # ---------- Filtres ----------

    def _build_filters(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 8))

        ctk.CTkLabel(bar, text="Mois :", font=("Segoe UI", 12)).pack(side="left", padx=(0, 6))
        self.filter_month = ctk.CTkEntry(bar, width=110)
        self.filter_month.insert(0, datetime.now().strftime("%Y-%m"))
        self.filter_month.pack(side="left", padx=(0, 12))

        ctk.CTkButton(bar, text="Filtrer", width=80, command=self.refresh).pack(side="left")

    # ---------- Tableau ----------

    def _build_table(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Budget.Treeview", rowheight=28, font=("Segoe UI", 11))
        style.configure("Budget.Treeview.Heading", font=("Segoe UI", 11, "bold"))

        columns = ("date", "categorie", "type", "note", "montant")
        self.tree = ttk.Treeview(
            self, columns=columns, show="headings", style="Budget.Treeview", selectmode="browse"
        )
        headers = {"date": "Date", "categorie": "Catégorie", "type": "Type", "note": "Note", "montant": "Montant"}
        widths = {"date": 90, "categorie": 110, "type": 80, "note": 200, "montant": 90}
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col], anchor="w" if col != "montant" else "e")

        self.tree.grid(row=2, column=0, sticky="nsew", padx=4, pady=4)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=2, column=1, sticky="ns")

        delete_btn = ctk.CTkButton(self, text="Supprimer la ligne sélectionnée", command=self._delete_selected)
        delete_btn.grid(row=3, column=0, sticky="w", padx=4, pady=8)

    def _delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        transaction_id = self.tree.item(selected[0], "tags")[0]
        db.delete_transaction(int(transaction_id))
        self.refresh()

    def refresh(self):
        self.categories = db.get_categories()
        noms_categories = [c["nom"] for c in self.categories] or ["Aucune catégorie"]
        self.menu_categorie.configure(values=noms_categories)

        for row in self.tree.get_children():
            self.tree.delete(row)

        month = self.filter_month.get().strip() or None
        for t in db.get_transactions(month=month):
            signe = "+" if t["type"] == "revenu" else "-"
            self.tree.insert(
                "",
                "end",
                values=(
                    t["date"],
                    t["categorie_nom"] or "—",
                    "Revenu" if t["type"] == "revenu" else "Dépense",
                    t["note"] or "",
                    f"{signe}{t['montant']:.2f} €",
                ),
                tags=(str(t["id"]),),
            )
