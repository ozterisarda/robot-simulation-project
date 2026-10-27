from pathlib import Path

import tkinter as tk

from tkinter import filedialog, messagebox, ttk

import simulasyon as sim

KOK = Path(__file__).resolve().parent

RENK = {
    "zemin": "#f1f5f9", "kart": "#ffffff", "yazi": "#12243a",
    "soluk": "#64748b", "vurgu": "#087f8c", "gece": "#14283f",
    "duvar": "#34465b", "bos": "#edf2f7", "kutu": "#f3bc63",
    "teslim": "#9cddbc", "sarj": "#a9d5ff", "cizgi": "#d9e3ec",
}

OLAYLAR = {
    "HAZIR": "Dosyalar yüklendi. İlk komut için hazırsınız.",
    "HAREKET": "Robot ilerledi.", "DONUS": "Robot yön değiştirdi.",
    "ALINDI": "Kutu alındı.",
    "TESLIM": "Kutu teslim edildi.", "BIRAKILDI": "Kutu boş hücreye bırakıldı.",
    "SARJ": "Batarya tamamen doldu.", "CARPISMA": "Engel! Komutun kalan adımları iptal edildi.",
    "GECERSIZ": "Komut bu hücrede veya bu yük durumunda uygulanamaz.",
    "BATARYA_BITTI": "İşlem için enerji yetmedi. Simülasyon durdu.",
    "YOL_YOK": "Hedefe ulaşılabilen bir yol yok.", "HEDEFTE": "Robot zaten hedefte.",
}


class DepoUygulamasi:
    def _stilleri_kur(self):
        stil = ttk.Style(self.pencere)
        stil.theme_use("clam")
        stil.configure("TFrame", background=RENK["zemin"])
        stil.configure("Card.TFrame", background=RENK["kart"])
        stil.configure("TLabel", background=RENK["kart"], foreground=RENK["yazi"], font=("Segoe UI", 10))
        stil.configure("Muted.TLabel", foreground=RENK["soluk"], font=("Segoe UI", 9))
        stil.configure("Title.TLabel", font=("Segoe UI", 12, "bold"))
        stil.configure("Value.TLabel", font=("Segoe UI", 15, "bold"))
        stil.configure("TButton", padding=(12, 9), font=("Segoe UI", 10), background="#e5edf3", borderwidth=0)
        stil.map("TButton", background=[("active", "#d6e3ee")])
        stil.configure("Accent.TButton", background=RENK["vurgu"], foreground="white")
        stil.map("Accent.TButton", background=[("active", "#066a75"), ("disabled", "#c4d8dc")])
        stil.configure("TCheckbutton", background="white", font=("Segoe UI", 9))
        stil.configure("Treeview", font=("Segoe UI", 9), rowheight=27, background="white", fieldbackground="white", borderwidth=0)
        stil.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), padding=6, background="#e8eff5")
        stil.map("Treeview", background=[("selected", "#d3eef0")], foreground=[("selected", RENK["yazi"])])
        stil.configure("TNotebook", background="white", borderwidth=0)
        stil.configure("TNotebook.Tab", padding=(12, 7), font=("Segoe UI", 9))
        stil.configure("Battery.Horizontal.TProgressbar", background=RENK["vurgu"], troughcolor="#e5edf3", borderwidth=0)

    def _tablo(self, veli, sutunlar, height):
        cerceve = ttk.Frame(veli, style="Card.TFrame")
        cerceve.pack(fill="both", expand=True)
        agac = ttk.Treeview(cerceve, columns=[s[0] for s in sutunlar], show="headings", height=height)
        for ad, baslik, genislik in sutunlar:
            agac.heading(ad, text=baslik)
            agac.column(ad, width=genislik, minwidth=30, stretch=ad in ("komut", "olay"))
        kaydir = ttk.Scrollbar(cerceve, orient="vertical", command=agac.yview)
        agac.configure(yscrollcommand=kaydir.set)
        kaydir.pack(side="right", fill="y")
        agac.pack(side="left", fill="both", expand=True)
        return agac
