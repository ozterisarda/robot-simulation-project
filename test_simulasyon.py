from copy import deepcopy
import csv
import json
from pathlib import Path
import random
import tempfile
import unittest

import simulasyon as s


class SimulasyonTestleri(unittest.TestCase):
    def setUp(self):
        self.gecici = tempfile.TemporaryDirectory()
        self.klasor = Path(self.gecici.name)
        self.addCleanup(self.gecici.cleanup)

    def hazirla(self, harita="#######\n#R....#\n#######\n", **degisiklik):
        yol = self.klasor / "harita.txt"
        yol.write_text(harita, encoding="utf-8")
        izgara, baslangic = s.harita_oku(yol)
        ayarlar = dict(s.VARSAYILAN_AYARLAR, **degisiklik)
        return s.yeni_durum(izgara, baslangic, ayarlar)

    def test_kismi_hareket_ve_kalan_komutlarin_iptali(self):
        d = self.hazirla(batarya_kapasitesi=5, adim_maliyeti=2)
        self.assertEqual(s.komut_uygula(d, ("ILERI", 4)), "BATARYA_BITTI")
        self.assertEqual((d["konum"], d["batarya"], d["toplam_adim"]), ((3, 1), 1, 2))
        self.assertEqual(s.komut_uygula(d, ("SOL", None)), "DURDU")
        self.assertEqual((d["yon"], len(d["log"])), ("D", 1))

    def test_tam_sifira_inip_sarj_olabilme(self):
        d = self.hazirla("#####\n#RS.#\n#####\n", batarya_kapasitesi=2, adim_maliyeti=2)
        s.komut_uygula(d, ("ILERI", 1))
        self.assertEqual((d["batarya"], d["durdu"]), (0, False))
        self.assertEqual(s.komut_uygula(d, ("SARJ", None)), "SARJ")
        self.assertEqual(d["batarya"], 2)

    def test_enerji_yetmeyen_donus_yonu_degistirmez(self):
        d = self.hazirla(batarya_kapasitesi=1, donus_maliyeti=2)
        s.komut_uygula(d, ("SAG", None))
        self.assertEqual((d["yon"], d["batarya"], d["durdu"]), ("D", 1, True))

    def test_donusun_enerjiyi_tam_tuketmesi(self):
        d = self.hazirla(batarya_kapasitesi=2, donus_maliyeti=2)
        s.komut_uygula(d, ("SOL", None))
        self.assertEqual((d["yon"], d["batarya"], d["durdu"]), ("K", 0, False))
        self.assertEqual(s.komut_uygula(d, ("SOL", None)), "BATARYA_BITTI")

    def test_carpisma_tek_ceza_ve_sonraki_komuta_devam(self):
        d = self.hazirla(adim_maliyeti=1, carpisma_cezasi=3, donus_maliyeti=0)
        self.assertEqual(s.komut_uygula(d, ("ILERI", 10**9)), "CARPISMA")
        self.assertEqual((d["konum"], d["toplam_adim"], d["carpisma"], d["batarya"]), ((5, 1), 4, 1, 93))
        s.komut_uygula(d, ("SOL", None))
        self.assertEqual(d["yon"], "K")

    def test_carpisma_cezasi_esit_ve_buyuk(self):
        for enerji, durdu in [(3, False), (2, True)]:
            with self.subTest(enerji=enerji):
                d = self.hazirla("###\n#R#\n###\n", batarya_kapasitesi=enerji, carpisma_cezasi=3)
                s.komut_uygula(d, ("ILERI", 1))
                self.assertEqual((d["batarya"], d["durdu"], d["carpisma"]), (0, durdu, 1))

    def test_harita_disina_cikma(self):
        d = self.hazirla("R.\n..\n", baslangic_yonu="K", carpisma_cezasi=4)
        s.komut_uygula(d, ("ILERI", 1))
        self.assertEqual((d["konum"], d["batarya"], d["carpisma"]), ((0, 0), 96, 1))

    def test_al_birak_tekrar_al_ve_teslim(self):
        d = self.hazirla("########\n#RK..T.#\n########\n", adim_maliyeti=1, yuk_carpani=3)
        for k in [("ILERI", 1), ("AL", None), ("ILERI", 1), ("BIRAK", None)]:
            s.komut_uygula(d, k)
        self.assertEqual((d["yuk"], d["izgara"][1][3], d["batarya"]), (False, "K", 96))
        for k in [("AL", None), ("ILERI", 2), ("BIRAK", None)]:
            s.komut_uygula(d, k)
        self.assertEqual((d["yuk"], d["teslim"], d["batarya"], d["izgara"][1][5]), (False, 1, 90, "T"))

    def test_ikinci_kutu_alinmaz_ve_sarj_ustune_birakilmaz(self):
        d = self.hazirla("#######\n#RKKS.#\n#######\n", adim_maliyeti=1)
        for k in [("ILERI", 1), ("AL", None), ("ILERI", 1)]:
            s.komut_uygula(d, k)
        self.assertEqual(s.komut_uygula(d, ("AL", None)), "GECERSIZ")
        self.assertEqual(s.komut_uygula(d, ("BIRAK", None)), "GECERSIZ")
        s.komut_uygula(d, ("ILERI", 1))
        self.assertEqual(s.komut_uygula(d, ("BIRAK", None)), "GECERSIZ")
        self.assertEqual((d["yuk"], d["izgara"][1][4]), (True, "S"))

    def test_gecersiz_eylemler_enerji_harcamaz(self):
        d = self.hazirla()
        for ad in ("AL", "BIRAK", "SARJ"):
            self.assertEqual(s.komut_uygula(d, (ad, None)), "GECERSIZ")
        self.assertEqual(d["batarya"], 100)

    def test_ziyaret_esitliginde_y_sonra_x(self):
        d = self.hazirla("....\n.R..\n....\n", adim_maliyeti=0, donus_maliyeti=0)
        for k in [("SOL", None), ("ILERI", 1), ("SOL", None), ("ILERI", 1)]:
            s.komut_uygula(d, k)
        self.assertEqual(s.durum_sonucu(d)["en_cok_ziyaret_edilen"], [0, 0])
        self.assertEqual(sum(d["ziyaretler"].values()), d["toplam_adim"] + 1)

    def test_hatalar_bos_satirlarla_numaralanir_ve_sonuca_tasinir(self):
        yol = self.klasor / "komutlar.txt"
        yol.write_text("SAG\n\nILERI 0\nsol\nILERI 2.5\nAL 1\nGIT 2 1\nGIT -1 2\n", encoding="utf-8")
        komutlar, hatalar = s.komutlari_oku(yol)
        self.assertIsInstance(komutlar, list)
        self.assertEqual([h["satir"] for h in hatalar], [3, 4, 5, 6, 8])
        d = self.hazirla()
        sonuc, _ = s.simulasyonu_calistir(d["izgara"], d["konum"], komutlar, d["ayarlar"])
        self.assertEqual(sonuc["hatali_satirlar"], hatalar)

    def test_bozuk_haritalar(self):
        for metin in ("", "R..\n..", "...\n...", "RR.\n...", "RX.\n..."):
            with self.subTest(metin=metin):
                with self.assertRaises(ValueError):
                    self.hazirla(metin)

    def test_json_ve_ayar_dogrulama(self):
        yol = self.klasor / "ayarlar.json"
        for veri in ("{", "[]", "{}", json.dumps(dict(s.VARSAYILAN_AYARLAR, adim_maliyeti=-1)), json.dumps(dict(s.VARSAYILAN_AYARLAR, yuk_carpani=True))):
            with self.subTest(veri=veri):
                yol.write_text(veri, encoding="utf-8")
                with self.assertRaises(ValueError):
                    s.ayarlari_oku(yol)

    def test_utf8_bom_destegi(self):
        yol = self.klasor / "harita.txt"
        yol.write_text("R.\n..\n", encoding="utf-8-sig")
        self.assertEqual(s.harita_oku(yol)[1], (0, 0))

    def test_yeni_durum_girdileri_degistirmez(self):
        d = self.hazirla("#####\n#RK.#\n#####\n")
        ozgun = deepcopy(d["izgara"])
        ikinci = s.yeni_durum(d["izgara"], (1, 1), d["ayarlar"])
        s.komut_uygula(ikinci, ("ILERI", 1))
        s.komut_uygula(ikinci, ("AL", None))
        self.assertEqual(d["izgara"], ozgun)
        s.harita_metni(ikinci)
        self.assertEqual(ikinci["izgara"][1][2], ".")

    def test_bfs_engelin_cevresindeki_en_kisa_yol(self):
        d = self.hazirla("#######\n#R#...#\n#.#.#.#\n#.....#\n#######\n", batarya_kapasitesi=100, adim_maliyeti=1, donus_maliyeti=1)
        yol = s.en_kisa_yol(d, (3, 1))
        self.assertEqual(len(yol), 6)
        self.assertEqual(s.komut_uygula(d, ("GIT", (3, 1))), "HAREKET")
        self.assertEqual((d["konum"], d["toplam_adim"], d["batarya"], len(d["log"])), ((3, 1), 6, 91, 1))

    def test_bfs_hedefte_duvar_disarisi_ve_ulasilamaz(self):
        d = self.hazirla("#######\n#R#...#\n#######\n")
        for hedef in ((3, 1), (2, 1), (20, 20)):
            self.assertEqual(s.komut_uygula(d, ("GIT", hedef)), "YOL_YOK")
        self.assertEqual(s.komut_uygula(d, ("GIT", (1, 1))), "HEDEFTE")
        self.assertEqual((d["batarya"], d["carpisma"]), (100, 0))

    def test_bfs_yol_ortasinda_enerji_yetmemesi(self):
        d = self.hazirla(batarya_kapasitesi=3, adim_maliyeti=2)
        s.komut_uygula(d, ("GIT", (5, 1)))
        self.assertEqual((d["konum"], d["batarya"], d["durdu"]), ((2, 1), 1, True))

    def test_bfs_180_derece_donuste_kismi_enerji(self):
        d = self.hazirla(".....\n..R..\n.....\n", batarya_kapasitesi=1, donus_maliyeti=1)
        s.komut_uygula(d, ("GIT", (1, 1)))
        self.assertEqual((d["konum"], d["yon"], d["batarya"], d["durdu"]), ((2, 1), "G", 0, True))

    def test_json_csv_gercek_dosyaya_yazilir(self):
        d = self.hazirla()
        s.komut_uygula(d, ("ILERI", 2))
        s.sonuc_yaz(s.durum_sonucu(d), self.klasor / "sonuc.json")
        s.log_yaz(d["log"], self.klasor / "log.csv")
        veri = json.loads((self.klasor / "sonuc.json").read_text(encoding="utf-8"))
        self.assertIs(type(veri["yuk"]), bool)
        with (self.klasor / "log.csv").open(encoding="utf-8", newline="") as dosya:
            satirlar = list(csv.DictReader(dosya))
        self.assertEqual((len(satirlar), satirlar[0]["komut"], satirlar[0]["x"]), (1, "ILERI 2", "3"))

    def test_verilen_bes_veride_ve_rastgele_komutlarda_tutarlilik(self):
        rng = random.Random(217)
        kok = Path(__file__).resolve().parent
        for i in range(1, 6):
            klasor = kok / "deneme_verileri" / f"veri_{i}"
            izgara, baslangic = s.harita_oku(klasor / "harita.txt")
            ayarlar = s.ayarlari_oku(klasor / "ayarlar.json")
            komutlar, _ = s.komutlari_oku(klasor / "komutlar.txt")
            sonuc, log = s.simulasyonu_calistir(izgara, baslangic, komutlar, ayarlar)
            d = s.yeni_durum(izgara, baslangic, ayarlar)
            d["hatali_satirlar"] = komutlar.hatalar
            for k in komutlar:
                s.komut_uygula(d, k)
            self.assertEqual(sonuc, s.durum_sonucu(d))
            self.assertEqual(log, d["log"])
            for _ in range(20):
                d = s.yeni_durum(izgara, baslangic, ayarlar)
                for _ in range(80):
                    ad = rng.choice(["ILERI", "SAG", "SOL", "AL", "BIRAK", "SARJ"])
                    s.komut_uygula(d, (ad, rng.randint(1, 7) if ad == "ILERI" else None))
                    x, y = d["konum"]
                    self.assertNotEqual(d["izgara"][y][x], "#")
                    self.assertGreaterEqual(d["batarya"], 0)
                    self.assertLessEqual(d["batarya"], ayarlar["batarya_kapasitesi"])
                    self.assertEqual(sum(d["ziyaretler"].values()), d["toplam_adim"] + 1)


if __name__ == "__main__":
    unittest.main()
