"""Écran Statistiques : évolution mensuelle + répartition par catégorie."""

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import database as db
from config import COULEUR_ACCENT, COULEUR_SUCCES


class StatsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 8))
        ctk.CTkLabel(header, text="Période :", font=("Segoe UI", 12)).pack(side="left", padx=(0, 6))

        self.period_var = ctk.StringVar(value="6 derniers mois")
        self.period_menu = ctk.CTkOptionMenu(
            header,
            values=["3 derniers mois", "6 derniers mois", "12 derniers mois"],
            variable=self.period_var,
            command=lambda _=None: self.refresh(),
        )
        self.period_menu.pack(side="left")

        self.chart_container = ctk.CTkFrame(self, fg_color="transparent")
        self.chart_container.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self.chart_container.grid_columnconfigure(0, weight=1)
        self.chart_container.grid_rowconfigure((0, 1), weight=1)

        self.refresh()

    def _months_count(self):
        return {"3 derniers mois": 3, "6 derniers mois": 6, "12 derniers mois": 12}[self.period_var.get()]

    def refresh(self):
        for widget in self.chart_container.winfo_children():
            widget.destroy()

        self._draw_trend_chart()
        self._draw_category_chart()

    def _draw_trend_chart(self):
        frame = ctk.CTkFrame(self.chart_container, corner_radius=12)
        frame.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        ctk.CTkLabel(frame, text="Évolution mensuelle", font=("Segoe UI", 12), text_color="gray60").pack(
            anchor="w", padx=16, pady=(12, 0)
        )

        data = db.monthly_trend(self._months_count())
        fig = Figure(figsize=(6, 2.4), dpi=100)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)
        ax.set_facecolor("none")

        if data:
            mois = [d["mois"] for d in data]
            depenses = [d["depenses"] for d in data]
            revenus = [d["revenus"] for d in data]
            x = range(len(mois))
            width = 0.35
            ax.bar([i - width / 2 for i in x], revenus, width, label="Revenus", color=COULEUR_SUCCES)
            ax.bar([i + width / 2 for i in x], depenses, width, label="Dépenses", color=COULEUR_ACCENT)
            ax.set_xticks(list(x))
            ax.set_xticklabels(mois, rotation=0)
            ax.legend(frameon=False, fontsize=8)
        else:
            ax.text(0.5, 0.5, "Pas encore de données", ha="center", va="center", transform=ax.transAxes)

        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    def _draw_category_chart(self):
        frame = ctk.CTkFrame(self.chart_container, corner_radius=12)
        frame.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        ctk.CTkLabel(
            frame, text="Répartition par catégorie (mois en cours)", font=("Segoe UI", 12), text_color="gray60"
        ).pack(anchor="w", padx=16, pady=(12, 0))

        from datetime import datetime

        month = datetime.now().strftime("%Y-%m")
        rows = db.category_breakdown(month)

        fig = Figure(figsize=(6, 2.4), dpi=100)
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(111)

        if rows:
            noms = [r["categorie"] for r in rows]
            totaux = [r["total"] for r in rows]
            couleurs = [r["couleur"] for r in rows]
            ax.pie(totaux, labels=noms, autopct="%1.0f%%", colors=couleurs, textprops={"fontsize": 8})
        else:
            ax.text(0.5, 0.5, "Aucune dépense ce mois-ci", ha="center", va="center", transform=ax.transAxes)
            ax.axis("off")

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
