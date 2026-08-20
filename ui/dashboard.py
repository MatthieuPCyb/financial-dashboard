"""Écran Tableau de bord : résumé du mois en cours."""

from datetime import datetime

import customtkinter as ctk

import database as db
from config import MOIS_FR, COULEUR_ACCENT, COULEUR_DANGER, COULEUR_SUCCES


class CategoryRow(ctk.CTkFrame):
    """Une ligne de catégorie avec un bouton pour dérouler ses sous-catégories."""

    def __init__(self, master, month, categorie, total, couleur, **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)
        self.month = month
        self.categorie = categorie
        self.expanded = False
        self.sub_frame = None

        self.grid_columnconfigure(1, weight=1)

        self.toggle_btn = ctk.CTkButton(
            self,
            text="▸",
            width=28,
            height=28,
            font=("Segoe UI", 13),
            fg_color="transparent",
            text_color="gray70",
            hover_color=("gray85", "gray25"),
            command=self._toggle,
        )
        self.toggle_btn.grid(row=0, column=0, padx=(8, 4), pady=10)

        pastille = ctk.CTkLabel(self, text="●", text_color=couleur, font=("Segoe UI", 14), width=16)
        pastille.grid(row=0, column=1, sticky="w", padx=(0, 4), pady=10)

        nom_label = ctk.CTkLabel(self, text=categorie, font=("Segoe UI", 13))
        nom_label.grid(row=0, column=1, sticky="w", padx=(24, 0), pady=10)

        total_label = ctk.CTkLabel(
            self, text=f"{total:,.0f} €".replace(",", " "), font=("Segoe UI", 13, "bold")
        )
        total_label.grid(row=0, column=2, sticky="e", padx=12, pady=10)

    def _toggle(self):
        self.expanded = not self.expanded
        if self.expanded:
            self.toggle_btn.configure(text="▾")
            self._show_subcategories()
        else:
            self.toggle_btn.configure(text="▸")
            if self.sub_frame is not None:
                self.sub_frame.destroy()
                self.sub_frame = None

    def _show_subcategories(self):
        self.sub_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.sub_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=(36, 12), pady=(0, 8))
        self.sub_frame.grid_columnconfigure(0, weight=1)

        sous_rows = db.subcategory_breakdown(self.month, self.categorie)

        if not sous_rows:
            ctk.CTkLabel(
                self.sub_frame,
                text="Aucune sous-catégorie",
                font=("Segoe UI", 11),
                text_color="gray60",
            ).grid(row=0, column=0, sticky="w", pady=2)
            return

        for i, row in enumerate(sous_rows):
            nom = row["sous_categorie"] or "Non classé"
            ctk.CTkLabel(
                self.sub_frame, text=nom, font=("Segoe UI", 11), text_color="gray70"
            ).grid(row=i, column=0, sticky="w", pady=2)
            ctk.CTkLabel(
                self.sub_frame,
                text=f"{row['total']:,.0f} €".replace(",", " "),
                font=("Segoe UI", 11),
                text_color="gray70",
            ).grid(row=i, column=1, sticky="e", pady=2)


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure((0, 1, 2), weight=1)

        self.title_label = ctk.CTkLabel(self, font=("Segoe UI", 15))
        self.title_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=4, pady=(4, 12))

        self.card_revenus = self._make_card(1, "Revenus")
        self.card_depenses = self._make_card(1, "Dépenses", col=1)
        self.card_epargne = self._make_card(1, "Épargne", col=2)

        self.category_frame = ctk.CTkScrollableFrame(self, corner_radius=12, label_text="Dépenses par catégorie")
        self.category_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=4, pady=12)
        self.category_frame.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.refresh()

    def _make_card(self, row, label, col=0):
        card = ctk.CTkFrame(self, corner_radius=12)
        card.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
        ctk.CTkLabel(card, text=label, font=("Segoe UI", 12), text_color="gray60").pack(
            anchor="w", padx=16, pady=(12, 0)
        )
        value_label = ctk.CTkLabel(card, text="0 €", font=("Segoe UI", 22, "bold"))
        value_label.pack(anchor="w", padx=16, pady=(2, 14))
        card.value_label = value_label
        return card

    def refresh(self):
        month = datetime.now().strftime("%Y-%m")
        month_label = f"{MOIS_FR[datetime.now().month - 1]} {datetime.now().year}"
        self.title_label.configure(text=month_label)

        revenus, depenses = db.monthly_summary(month)
        epargne = revenus - depenses

        self.card_revenus.value_label.configure(text=f"{revenus:,.0f} €".replace(",", " "))
        self.card_depenses.value_label.configure(
            text=f"{depenses:,.0f} €".replace(",", " "), text_color=COULEUR_DANGER
        )
        self.card_epargne.value_label.configure(
            text=f"{epargne:,.0f} €".replace(",", " "),
            text_color=COULEUR_SUCCES if epargne >= 0 else COULEUR_DANGER,
        )

        self._draw_category_list(month)

    def _draw_category_list(self, month):
        for widget in self.category_frame.winfo_children():
            widget.destroy()

        rows = db.category_breakdown(month)

        if not rows:
            ctk.CTkLabel(
                self.category_frame,
                text="Aucune dépense ce mois-ci",
                font=("Segoe UI", 12),
                text_color="gray60",
            ).grid(row=0, column=0, sticky="w", padx=8, pady=12)
            return

        for i, row in enumerate(rows):
            item = CategoryRow(
                self.category_frame,
                month=month,
                categorie=row["categorie"],
                total=row["total"],
                couleur=row["couleur"],
            )
            item.grid(row=i, column=0, sticky="ew", pady=3)