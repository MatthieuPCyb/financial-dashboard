"""Écran Tableau de bord : résumé du mois en cours."""

from datetime import datetime

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import database as db
from config import MOIS_FR, COULEUR_ACCENT, COULEUR_DANGER, COULEUR_SUCCES


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure((0, 1, 2), weight=1)

        self.title_label = ctk.CTkLabel(self, font=("Segoe UI", 15))
        self.title_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=4, pady=(4, 12))

        self.card_revenus = self._make_card(1, "Revenus")
        self.card_depenses = self._make_card(1, "Dépenses", col=1)
        self.card_epargne = self._make_card(1, "Épargne", col=2)

        self.chart_frame = ctk.CTkFrame(self, corner_radius=12)
        self.chart_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=4, pady=12)
        self.grid_rowconfigure(2, weight=1)

        self.canvas = None
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

        self._draw_chart(month)

    def _draw_chart(self, month):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.chart_frame, text="Dépenses par catégorie", font=("Segoe UI", 12), text_color="gray60"
        ).pack(anchor="w", padx=16, pady=(12, 0))

        rows = db.category_breakdown(month)
        fig = Figure(figsize=(6, 2.6), dpi=100)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        ax.set_facecolor("none")

        if rows:
            noms = [r["categorie"] for r in rows]
            totaux = [r["total"] for r in rows]
            couleurs = [r["couleur"] for r in rows]
            ax.bar(noms, totaux, color=couleurs)
        else:
            ax.text(0.5, 0.5, "Aucune dépense ce mois-ci", ha="center", va="center", transform=ax.transAxes)

        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        self.canvas = canvas
