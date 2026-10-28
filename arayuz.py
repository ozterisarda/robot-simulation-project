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

    def _ekrani_kur(self):


        self.pencere.columnconfigure(0, weight=1)
        self.pencere.rowconfigure(2, weight=1)
        entete = tk.Frame(self.pencere, bg=RENK["gece"], padx=22, pady=12)
        entete.grid(row=0, column=0, sticky="ew")
        tk.Label(entete, text="DEPO / ROBOT", fg="white", bg=RENK["gece"], font=("Segoe UI", 22, "bold")).pack(side="left")
        tk.Label(entete, text="Depo operasyonları simülatörü", fg="#bbcedf", bg=RENK["gece"], font=("Segoe UI", 11)).pack(side="left", padx=24)
        tk.Label(entete, text="PROGRAMLAMA LAB I\nArda Özteriş · Ahmet B. Karaca", justify="right", fg="#bbcedf", bg=RENK["gece"], font=("Segoe UI", 9)).pack(side="right")

        toolbar = ttk.Frame(self.pencere, padding=(18, 10))
        toolbar.grid(row=1, column=0, sticky="ew")
        ttk.Button(toolbar, text="Klasör yükle", command=self.klasor_sec).pack(side="left")
        ttk.Button(toolbar, text="Dosyaları seç", command=self.dosyalari_sec).pack(side="left", padx=6)
        self.ornek = ttk.Combobox(toolbar, state="readonly", width=18, values=["Tanıtım senaryosu"] + [f"Deneme verisi {i}" for i in range(1, 6)])
        self.ornek.current(0)
        self.ornek.pack(side="left", padx=(8, 5))
        self.ornek.bind("<<ComboboxSelected>>", self.ornek_yukle)
        ttk.Button(toolbar, text="Sonuçları kaydet", command=self.kaydet_sec).pack(side="right")
        ttk.Button(toolbar, text="Yardım", command=self.rehber).pack(side="right", padx=6)

        govde = ttk.Frame(self.pencere, padding=(18, 0, 18, 10))
        govde.grid(row=2, column=0, sticky="nsew")
        govde.columnconfigure(0, weight=1)
        govde.columnconfigure(1, weight=0, minsize=320)
        govde.rowconfigure(0, weight=1)
        sol = ttk.Frame(govde, style="Card.TFrame", padding=14)
        sol.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        sol.columnconfigure(0, weight=1)
        sol.rowconfigure(2, weight=1)
        baslik = ttk.Frame(sol, style="Card.TFrame")
        baslik.grid(row=0, column=0, sticky="ew")
        ttk.Label(baslik, text="Depo haritası", style="Title.TLabel").pack(side="left")
        ttk.Checkbutton(baslik, text="Ziyaret izleri", variable=self.iz_goster, command=self.harita_ciz).pack(side="right")
        ttk.Label(sol, textvariable=self.kaynak, style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 12))
        self.canvas = tk.Canvas(sol, bg=RENK["gece"], highlightthickness=0, height=340)
        self.canvas.grid(row=2, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda e: self.harita_ciz())
        self.canvas.bind("<Motion>", self.hucre_goster)
        self.canvas.bind("<Leave>", lambda e: self.hucre_bilgisi.set("Hücre ayrıntısı için haritanın üzerinde gezinin."))
        aciklama = ttk.Frame(sol, style="Card.TFrame")
        aciklama.grid(row=3, column=0, sticky="ew", pady=(10, 4))
        for ad, renk in [("Duvar", RENK["duvar"]), ("Kutu", RENK["kutu"]), ("Teslim", RENK["teslim"]), ("Şarj", RENK["sarj"])]:
            tk.Label(aciklama, bg=renk, width=2).pack(side="left", padx=(0, 4))
            ttk.Label(aciklama, text=ad, style="Muted.TLabel").pack(side="left", padx=(0, 12))
        ttk.Label(sol, textvariable=self.hucre_bilgisi, style="Muted.TLabel").grid(row=4, column=0, sticky="w", pady=(4, 0))

        sag = ttk.Frame(govde, style="Card.TFrame", padding=16, width=320)
        sag.grid(row=0, column=1, sticky="nsew")
        sag.columnconfigure(0, weight=1)
        ttk.Label(sag, text="Robotun durumu", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        self.batarya_cubugu = ttk.Progressbar(sag, style="Battery.Horizontal.TProgressbar", maximum=100)
        self.batarya_cubugu.grid(row=1, column=0, sticky="ew", pady=(12, 3))
        ttk.Label(sag, textvariable=self.degerler["batarya"], style="Muted.TLabel").grid(row=2, column=0, sticky="w")
        metrikler = ttk.Frame(sag, style="Card.TFrame")
        metrikler.grid(row=3, column=0, sticky="ew", pady=10)
        for i, (ad, etiket) in enumerate([("konum", "KONUM"), ("yon", "YÖN"), ("yuk", "YÜK"), ("teslim", "TESLİM"), ("carpisma", "ÇARPIŞMA"), ("toplam_adim", "HÜCRE ADIMI")]):
            kutu = ttk.Frame(metrikler, style="Card.TFrame", padding=(0, 4, 18, 4))
            kutu.grid(row=i // 2, column=i % 2, sticky="w")
            ttk.Label(kutu, text=etiket, style="Muted.TLabel").pack(anchor="w")
            ttk.Label(kutu, textvariable=self.degerler[ad], style="Value.TLabel").pack(anchor="w")
        ttk.Label(sag, text="SIRADAKİ KOMUT", style="Muted.TLabel").grid(row=4, column=0, sticky="w")
        ttk.Label(sag, textvariable=self.sonraki, font=("Consolas", 15, "bold"), foreground=RENK["vurgu"]).grid(row=5, column=0, sticky="w", pady=(3, 10))


        self.sekmeler = ttk.Notebook(self.pencere, height=110)
        self.sekmeler.grid(row=4, column=0, sticky="ew", padx=18, pady=(0, 10))
        komut_paneli = ttk.Frame(self.sekmeler, style="Card.TFrame")
        hata_paneli = ttk.Frame(self.sekmeler, style="Card.TFrame")
        self.sekmeler.add(komut_paneli, text="Komutlar")
        self.sekmeler.add(hata_paneli, text="Hatalı satırlar")
        self.komut_agaci = self._tablo(komut_paneli, [("no", "#", 35), ("komut", "Komut", 165)], height=5)
        self.komut_agaci.tag_configure("tamam", foreground="#7b8d9d")
        self.komut_agaci.tag_configure("siradaki", foreground=RENK["vurgu"], background="#e5f6f5")
        self.hata_metni = tk.Text(hata_paneli, width=30, height=5, wrap="word", relief="flat", font=("Segoe UI", 9), bg="#fff8ed", padx=8, pady=6)
        hata_scroll = ttk.Scrollbar(hata_paneli, command=self.hata_metni.yview)
        hata_scroll.pack(side="right", fill="y")
        self.hata_metni.pack(fill="both", expand=True)
        self.hata_metni.configure(yscrollcommand=hata_scroll.set, state="disabled")

        kontroller = ttk.Frame(self.pencere, padding=(18, 0, 18, 10))
        kontroller.grid(row=3, column=0, sticky="ew")
        self.adim_buton = ttk.Button(kontroller, text="Adım  →", style="Accent.TButton", command=self.adim)
        self.adim_buton.pack(side="left")
        self.calistir_buton = ttk.Button(kontroller, text="Tümünü çalıştır", command=self.calistir_duraklat)
        self.calistir_buton.pack(side="left", padx=7)
        ttk.Button(kontroller, text="Sıfırla", command=self.sifirla).pack(side="left")
        ttk.Label(kontroller, text="Yavaş", background=RENK["zemin"], style="Muted.TLabel").pack(side="left", padx=(20, 3))
        ttk.Scale(kontroller, from_=1000, to=30, variable=self.hiz, length=130).pack(side="left")
        ttk.Label(kontroller, text="Hızlı", background=RENK["zemin"], style="Muted.TLabel").pack(side="left", padx=3)
        ttk.Label(kontroller, textvariable=self.degerler["ilerleme"], background=RENK["zemin"]).pack(side="right")

        log_paneli = ttk.Frame(self.sekmeler, style="Card.TFrame", padding=(14, 8))
        self.sekmeler.insert(0, log_paneli, text="İşlem geçmişi")
        self.sekmeler.select(0)
        self.log_agaci = self._tablo(log_paneli, [("adim", "#", 40), ("komut", "Komut", 140), ("x", "X", 45), ("y", "Y", 45), ("yon", "Yön", 50), ("batarya", "Batarya", 80), ("olay", "Olay", 160)], height=3)
        self.log_agaci.tag_configure("uyari", foreground="#a44717", background="#fff4e7")
        durum_cubugu = tk.Frame(self.pencere, bg=RENK["gece"], padx=18, pady=8)
        durum_cubugu.grid(row=5, column=0, sticky="ew")
        tk.Label(durum_cubugu, textvariable=self.durum_mesaji, fg="white", bg=RENK["gece"], font=("Segoe UI", 9), anchor="w").pack(fill="x")

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

    def _kisayollari_kur(self):
        self.pencere.bind("<F6>", lambda e: self.adim())
        self.pencere.bind("<F5>", lambda e: self.calistir_duraklat())
        self.pencere.bind("<Control-r>", lambda e: self.sifirla())
        self.pencere.bind("<Control-o>", lambda e: self.klasor_sec())

    def klasor_sec(self):
        self.duraklat()
        klasor = filedialog.askdirectory(title="Üç girdi dosyasının bulunduğu klasörü seçin", initialdir=KOK)
        if klasor:
            self.klasor_yukle(klasor)

    def klasor_yukle(self, klasor):
        klasor = Path(klasor)
        return self.dosya_yukle(klasor / "harita.txt", klasor / "komutlar.txt", klasor / "ayarlar.json")

    def dosyalari_sec(self):
        self.duraklat()
        yollar = []
        for ad, tur in [("harita.txt", "*.txt"), ("komutlar.txt", "*.txt"), ("ayarlar.json", "*.json")]:
            yol = filedialog.askopenfilename(title=f"{ad} dosyasını seçin", initialdir=KOK, filetypes=[("Girdi dosyası", tur), ("Tüm dosyalar", "*.*")])
            if not yol:
                return
            yollar.append(yol)
        self.dosya_yukle(*yollar)

    def dosya_yukle(self, harita, komut, ayar):
        self.duraklat()
        try:
            izgara, baslangic = sim.harita_oku(harita)
            ayarlar = sim.ayarlari_oku(ayar)
            komutlar, hatalar = sim.komutlari_oku(komut)
        except (OSError, ValueError, UnicodeError) as hata:
            messagebox.showerror("Dosyalar yüklenemedi", str(hata), parent=self.pencere)
            return False

        self.ilk_veri = (izgara, baslangic, ayarlar)
        self.komutlar, self.hatalar = komutlar, hatalar
        self.kaynak.set(str(Path(harita).parent.name) + f"  /  {len(izgara[0])} × {len(izgara)} hücre")
        self.komut_agaci.delete(*self.komut_agaci.get_children())
        for i, k in enumerate(komutlar):
            self.komut_agaci.insert("", "end", iid=str(i), values=(i + 1, sim.komut_metni(k)))
        self.hata_metni.configure(state="normal")
        self.hata_metni.delete("1.0", "end")
        for hata in hatalar:
            self.hata_metni.insert("end", f"Satır {hata['satir']}: {hata['icerik']}\n{hata['neden']}\n\n")
        if not hatalar:
            self.hata_metni.insert("end", "Hatalı komut satırı bulunmadı.")
        self.hata_metni.configure(state="disabled")
        self.sekmeler.tab(2, text=f"Hatalı satırlar ({len(hatalar)})")
        self.sifirla()
        self.durum_mesaji.set(f"Yüklendi: {len(komutlar)} geçerli komut, {len(hatalar)} hatalı satır. F6: adım · F5: çalıştır / duraklat")
        return True

    def ornek_yukle(self, olay=None):
        secim = self.ornek.current()
        yol = KOK / "demo_verileri" / "tanitim" if secim == 0 else KOK / "deneme_verileri" / f"veri_{secim}"
        self.klasor_yukle(yol)

    def sifirla(self):
        self.duraklat()
        if self.ilk_veri is None:
            return
        izgara, baslangic, ayarlar = self.ilk_veri
        self.durum = sim.yeni_durum(izgara, baslangic, ayarlar)
        self.durum["hatali_satirlar"] = list(self.hatalar)
        self.indeks = 0
        self.log_agaci.delete(*self.log_agaci.get_children())
        for iid in self.komut_agaci.get_children():
            self.komut_agaci.item(iid, tags=())
        self.durum_mesaji.set("Başlangıç durumuna dönüldü. Dosyalar yeniden okunmadı.")
        self.guncelle()

    def adim(self, otomatik=False):
        if self.calisiyor and not otomatik:
            self.duraklat()
        if self.durum is None or self.durum["durdu"] or self.indeks >= len(self.komutlar):
            return
        sim.komut_uygula(self.durum, self.komutlar[self.indeks])
        self.komut_agaci.item(str(self.indeks), tags=("tamam",))
        self.indeks += 1
        kayit = self.durum["log"][-1]
        uyari = kayit["olay"] in ("GECERSIZ", "CARPISMA", "BATARYA_BITTI", "YOL_YOK")
        iid = self.log_agaci.insert("", "end", values=[kayit[k] for k in sim.LOG_ALANLARI], tags=("uyari",) if uyari else ())
        self.log_agaci.see(iid)
        self.durum_mesaji.set(OLAYLAR.get(kayit["olay"], kayit["olay"]))
        self.guncelle()
        if self.durum["durdu"] or self.indeks >= len(self.komutlar):
            self.duraklat()
            try:
                self.ciktilari_kaydet(KOK / "ciktilar")
                son = "Enerji yetersiz; durdu." if self.durum["durdu"] else "Tüm komutlar tamamlandı."
                self.durum_mesaji.set(son + " Sonuç ve log ciktilar klasörüne kaydedildi.")
            except OSError as hata:
                messagebox.showerror("Çıktı kaydedilemedi", str(hata), parent=self.pencere)

    def calistir_duraklat(self):
        if self.calisiyor:
            self.duraklat()
            self.durum_mesaji.set("Duraklatıldı. Adım ile devam edebilirsiniz.")
            return
        if self.durum is None or self.durum["durdu"] or self.indeks >= len(self.komutlar):
            return
        self.calisiyor = True
        self.calistir_buton.configure(text="Duraklat")
        self._otomatik_adim()

    def _otomatik_adim(self):
        self.zamanlayici = None
        if not self.calisiyor:
            return
        self.adim(otomatik=True)
        if self.calisiyor:


            self.zamanlayici = self.pencere.after(max(30, int(self.hiz.get())), self._otomatik_adim)

    def duraklat(self):
        self.calisiyor = False
        if self.zamanlayici is not None:
            self.pencere.after_cancel(self.zamanlayici)
            self.zamanlayici = None
        if hasattr(self, "calistir_buton"):
            self.calistir_buton.configure(text="Tümünü çalıştır")

    def ciktilari_kaydet(self, klasor):
        klasor = Path(klasor)
        klasor.mkdir(parents=True, exist_ok=True)
        sim.sonuc_yaz(sim.durum_sonucu(self.durum), klasor / "sonuc.json")
        sim.log_yaz(self.durum["log"], klasor / "log.csv")

    def kaydet_sec(self):
        self.duraklat()
        if self.durum is None:
            return
        klasor = filedialog.askdirectory(title="sonuc.json ve log.csv için klasör seçin", initialdir=KOK)
        if not klasor:
            return
        if any((Path(klasor) / ad).exists() for ad in ("sonuc.json", "log.csv")):
            if not messagebox.askyesno("Mevcut çıktılar", "Bu klasördeki sonuc.json ve log.csv dosyalarının üzerine yazılsın mı?", parent=self.pencere):
                return
        try:
            self.ciktilari_kaydet(klasor)
            self.durum_mesaji.set(f"Mevcut durum kaydedildi: {klasor}")
        except OSError as hata:
            messagebox.showerror("Kayıt hatası", str(hata), parent=self.pencere)

    def guncelle(self):
        d = self.durum
        if d is None:
            return
        x, y = d["konum"]
        self.degerler["konum"].set(f"({x}, {y})")
        self.degerler["yon"].set({"K": "↑ Kuzey", "D": "→ Doğu", "G": "↓ Güney", "B": "← Batı"}[d["yon"]])
        self.degerler["batarya"].set(f"{d['batarya']} / {d['ayarlar']['batarya_kapasitesi']} enerji")
        self.degerler["yuk"].set("1 kutu" if d["yuk"] else "Boş")
        for ad in ("teslim", "carpisma", "toplam_adim"):
            self.degerler[ad].set(str(d[ad]))
        kapasite = d["ayarlar"]["batarya_kapasitesi"]
        self.batarya_cubugu["value"] = 100 * d["batarya"] / kapasite if kapasite else 0
        self.degerler["ilerleme"].set(f"{self.indeks} / {len(self.komutlar)} komut işlendi")
        bitti = d["durdu"] or self.indeks >= len(self.komutlar)
        self.adim_buton.configure(state="disabled" if bitti else "normal")
        self.calistir_buton.configure(state="disabled" if bitti else "normal")
        self.sonraki.set("DURDU" if d["durdu"] else "TAMAMLANDI" if bitti else sim.komut_metni(self.komutlar[self.indeks]))
        if not bitti:
            self.komut_agaci.item(str(self.indeks), tags=("siradaki",))
            self.komut_agaci.see(str(self.indeks))
        self.harita_ciz()

    def harita_ciz(self):
        if self.durum is None:
            return
        c = self.canvas
        c.delete("all")
        harita = self.durum["izgara"]
        satir, sutun = len(harita), len(harita[0])
        w, h = max(c.winfo_width(), 100), max(c.winfo_height(), 100)
        boyut = max(1, min((w - 52) / sutun, (h - 52) / satir, 65))
        self.hucre_boyutu = boyut
        ox, oy = (w - sutun * boyut) / 2, (h - satir * boyut) / 2 + 8
        self.harita_ofset = (ox, oy)
        font = ("Segoe UI", max(6, int(boyut * .32)), "bold")
        for x in range(sutun):
            if boyut >= 16:
                c.create_text(ox + (x + .5) * boyut, oy - 14, text=x, fill="#adc0d1", font=("Segoe UI", 8))
        for y, hucreler in enumerate(harita):
            if boyut >= 16:
                c.create_text(ox - 17, oy + (y + .5) * boyut, text=y, fill="#adc0d1", font=("Segoe UI", 8))
            for x, hucre in enumerate(hucreler):
                renk = {"#": RENK["duvar"], ".": RENK["bos"], "K": RENK["kutu"], "T": RENK["teslim"], "S": RENK["sarj"]}.get(hucre, RENK["bos"])
                ziyaret = self.durum["ziyaretler"].get((x, y), 0)
                if self.iz_goster.get() and hucre == "." and ziyaret:
                    renk = "#d4eceb" if ziyaret == 1 else "#b3dcd9"
                x1, y1 = ox + x * boyut, oy + y * boyut
                c.create_rectangle(x1 + 1, y1 + 1, x1 + boyut - 1, y1 + boyut - 1, fill=renk, outline="")
                if hucre in "KTS" and boyut >= 15:
                    c.create_text(x1 + boyut / 2, y1 + boyut / 2, text=hucre, fill=RENK["yazi"], font=font)
                elif self.iz_goster.get() and hucre == "." and ziyaret and boyut >= 25:
                    c.create_text(x1 + boyut / 2, y1 + boyut / 2, text=str(ziyaret), fill="#699e9b", font=("Segoe UI", 8))
        x, y = self.durum["konum"]
        cx, cy = ox + (x + .5) * boyut, oy + (y + .5) * boyut
        rayon = boyut * .32
        c.create_oval(cx - rayon, cy - rayon, cx + rayon, cy + rayon, fill=RENK["vurgu"], outline="white", width=2)
        dx, dy = sim.YON_VEKTORLERI[self.durum["yon"]]

        c.create_polygon(cx + dx * rayon * .8, cy + dy * rayon * .8,
                         cx - dx * rayon * .5 - dy * rayon * .5, cy - dy * rayon * .5 + dx * rayon * .5,
                         cx - dx * rayon * .5 + dy * rayon * .5, cy - dy * rayon * .5 - dx * rayon * .5,
                         fill="white", outline="")
        if self.durum["yuk"]:
            c.create_rectangle(cx + rayon * .3, cy + rayon * .3, cx + rayon, cy + rayon, fill=RENK["kutu"], outline="white")

    def hucre_goster(self, olay):
        if self.durum is None:
            return
        ox, oy = self.harita_ofset
        x, y = int((olay.x - ox) // self.hucre_boyutu), int((olay.y - oy) // self.hucre_boyutu)
        h = self.durum["izgara"]
        if 0 <= y < len(h) and 0 <= x < len(h[0]):
            ad = {"#": "Duvar", ".": "Boş", "K": "Kutu", "T": "Teslim noktası", "S": "Şarj"}[h[y][x]]
            self.hucre_bilgisi.set(f"({x}, {y}) · {ad} · {self.durum['ziyaretler'].get((x, y), 0)} ziyaret")

    def rehber(self):
        messagebox.showinfo("Kısa kullanım rehberi", "1. Klasör veya üç ayrı girdi dosyası yükleyin.\n2. Adım (F6) bir komutu bütünüyle işler.\n3. Tümünü çalıştır (F5) komutları sırayla oynatır.\n4. Sıfırla (Ctrl+R) haritayı ve bataryayı geri getirir.\n5. Bitişte çıktılar otomatik olarak ciktilar klasörüne yazılır.\n\nK: kutu · T: teslim · S: şarj\nYönler: K kuzey, D doğu, G güney, B batı.\nKoordinat (x, y): sütun, satır; sol üst (0, 0).\n\nGIT x y en kısa hücre yolunu kullanır.\nKullanım ayrıntıları README.md dosyasındadır.", parent=self.pencere)

    def kapat(self):
        self.duraklat()
        self.pencere.destroy()
