"""Barre latérale de navigation entre les différents écrans."""

import customtkinter as ctk


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate, **kwargs):
        super().__init__(master, width=190, corner_radius=0, **kwargs)
        self.on_navigate = on_navigate
        self.buttons = {}

        ctk.CTkLabel(
            self, text="💰 MonBudget", font=("Segoe UI", 17, "bold")
        ).pack(padx=16, pady=(20, 24), anchor="w")

        items = [
            ("dashboard", "Tableau de bord"),
            ("depenses", "Dépenses"),
            ("epargne", "Épargne"),
            ("statistiques", "Statistiques"),
            ("parametres", "Paramètres"),
        ]

        for key, label in items:
            btn = ctk.CTkButton(
                self,
                text=label,
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                command=lambda k=key: self._select(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.buttons[key] = btn

    def _select(self, key):
        for k, btn in self.buttons.items():
            if k == key:
                btn.configure(fg_color=("#B5D4F4", "#185FA5"))
            else:
                btn.configure(fg_color="transparent")
        self.on_navigate(key)

    def set_active(self, key):
        self._select(key)
