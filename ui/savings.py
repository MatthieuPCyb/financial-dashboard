"""Écran Épargne : objectifs avec barres de progression + historique des versements."""

from tkinter import messagebox

import customtkinter as ctk

import database as db


class SavingsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 8))
        ctk.CTkLabel(header, text="Objectifs d'épargne", font=("Segoe UI", 13)).pack(side="left")
        ctk.CTkButton(header, text="+ Nouvel objectif", command=self._open_new_goal_dialog).pack(side="right")

        self.goals_container = ctk.CTkFrame(self, fg_color="transparent")
        self.goals_container.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        self.goals_container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Historique des versements", font=("Segoe UI", 13)).grid(
            row=2, column=0, sticky="w", padx=4, pady=(16, 6)
        )
        self.history_container = ctk.CTkFrame(self, corner_radius=12)
        self.history_container.grid(row=3, column=0, sticky="ew", padx=4, pady=4)

        self.refresh()

    def refresh(self):
        for widget in self.goals_container.winfo_children():
            widget.destroy()

        goals = db.get_savings_goals()
        if not goals:
            ctk.CTkLabel(self.goals_container, text="Aucun objectif pour le moment.", text_color="gray60").pack(
                anchor="w", pady=8
            )
        for goal in goals:
            self._build_goal_card(goal)

        for widget in self.history_container.winfo_children():
            widget.destroy()
        history = db.get_savings_history()
        if not history:
            ctk.CTkLabel(self.history_container, text="Aucun versement enregistré.", text_color="gray60").pack(
                anchor="w", padx=14, pady=12
            )
        for h in history:
            row = ctk.CTkFrame(self.history_container, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=4)
            ctk.CTkLabel(row, text=f"{h['date']}  ·  {h['objectif']}", anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"+{h['montant']:.2f} €", text_color="#639922").pack(side="right")

    def _build_goal_card(self, goal):
        card = ctk.CTkFrame(self.goals_container, corner_radius=12)
        card.pack(fill="x", pady=4)
        card.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(top, text=goal["nom"], font=("Segoe UI", 13, "bold")).pack(side="left")
        ctk.CTkLabel(
            top, text=f"{goal['montant_actuel']:.0f} € / {goal['montant_cible']:.0f} €", text_color="gray60"
        ).pack(side="right")

        progress = min(goal["montant_actuel"] / goal["montant_cible"], 1.0) if goal["montant_cible"] else 0
        bar = ctk.CTkProgressBar(card)
        bar.set(progress)
        bar.pack(fill="x", padx=14, pady=(0, 10))

        bottom = ctk.CTkFrame(card, fg_color="transparent")
        bottom.pack(fill="x", padx=14, pady=(0, 12))
        amount_entry = ctk.CTkEntry(bottom, placeholder_text="Montant à ajouter", width=140)
        amount_entry.pack(side="left")
        ctk.CTkButton(
            bottom,
            text="Verser",
            width=80,
            command=lambda gid=goal["id"], entry=amount_entry: self._add_contribution(gid, entry),
        ).pack(side="left", padx=8)

    def _add_contribution(self, goal_id, entry):
        try:
            montant = float(entry.get().replace(",", "."))
            if montant <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Entrez un montant valide et positif.")
            return
        db.add_saving_contribution(goal_id, montant)
        self.refresh()

    def _open_new_goal_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Nouvel objectif d'épargne")
        dialog.geometry("320x220")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Nom de l'objectif").pack(anchor="w", padx=16, pady=(16, 2))
        nom_entry = ctk.CTkEntry(dialog)
        nom_entry.pack(fill="x", padx=16)

        ctk.CTkLabel(dialog, text="Montant cible (€)").pack(anchor="w", padx=16, pady=(12, 2))
        montant_entry = ctk.CTkEntry(dialog)
        montant_entry.pack(fill="x", padx=16)

        def save():
            nom = nom_entry.get().strip()
            try:
                montant_cible = float(montant_entry.get().replace(",", "."))
                if not nom or montant_cible <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Erreur", "Vérifiez le nom et le montant cible.")
                return
            db.add_savings_goal(nom, montant_cible)
            dialog.destroy()
            self.refresh()

        ctk.CTkButton(dialog, text="Créer l'objectif", command=save).pack(pady=20)
