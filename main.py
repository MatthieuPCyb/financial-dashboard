"""
MonBudget — application de gestion de budget personnel.

Lancer l'application :
    python main.py
"""

import customtkinter as ctk

import database as db
from ui.sidebar import Sidebar
from ui.dashboard import DashboardFrame
from ui.expenses import ExpensesFrame
from ui.savings import SavingsFrame
from ui.stats import StatsFrame
from ui.settings import SettingsFrame

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MonBudget")
        self.geometry("1000x680")
        self.minsize(820, 560)

        db.init_db()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, on_navigate=self.show_frame)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.frames = {
            "dashboard": DashboardFrame(self.content),
            "depenses": ExpensesFrame(self.content),
            "epargne": SavingsFrame(self.content),
            "statistiques": StatsFrame(self.content),
            "parametres": SettingsFrame(self.content),
        }
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        self.sidebar.set_active("dashboard")
        self.show_frame("dashboard")

    def show_frame(self, key):
        frame = self.frames[key]
        # Rafraîchit les données à chaque changement d'onglet
        if hasattr(frame, "refresh"):
            frame.refresh()
        frame.tkraise()


if __name__ == "__main__":
    app = App()
    app.mainloop()
