from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from arayuz import DepoUygulamasi, KOK
import simulasyon as sim


class ArayuzTestleri(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = DepoUygulamasi(self.root)
        self.addCleanup(self.app.kapat)

    def test_adim_sifirla_ve_bilgi_paneli(self):
        self.app.adim()
        self.assertEqual(self.app.durum["konum"], (4, 1))
        self.assertEqual(self.app.degerler["konum"].get(), "(4, 1)")
        self.app.adim()
        self.assertTrue(self.app.durum["yuk"])
        self.app.sifirla()
        self.assertEqual((self.app.indeks, self.app.durum["konum"]), (0, (1, 1)))
        self.assertEqual(self.app.durum["izgara"][1][4], "K")
        self.assertEqual(len(self.app.log_agaci.get_children()), 0)

    def test_biten_ui_ile_toplu_motor_ayni_sonucu_verir(self):
        with tempfile.TemporaryDirectory() as hedef:
            with patch.object(self.app, "ciktilari_kaydet", wraps=lambda klasor: self._gecici_kaydet(hedef)) as kaydet:
                for _ in self.app.komutlar:
                    self.app.adim()
                self.assertEqual(kaydet.call_count, 1)
            izgara, baslangic, ayarlar = self.app.ilk_veri
            beklenen, log = sim.simulasyonu_calistir(izgara, baslangic, self.app.komutlar, ayarlar)
            self.assertEqual(sim.durum_sonucu(self.app.durum), beklenen)
            self.assertEqual(self.app.durum["log"], log)
            self.assertEqual(self.app.sonraki.get(), "TAMAMLANDI")
            self.assertTrue((Path(hedef) / "sonuc.json").is_file())

    def _gecici_kaydet(self, hedef):

        DepoUygulamasi.ciktilari_kaydet(self.app, hedef)

    def test_otomatik_calisma_duraklatma_ve_sifirlamada_timer_iptali(self):
        self.app.calistir_duraklat()
        self.assertEqual(self.app.indeks, 1)
        self.assertIsNotNone(self.app.zamanlayici)
        self.app.duraklat()
        self.assertIsNone(self.app.zamanlayici)
        self.app.calistir_duraklat()
        self.app.sifirla()
        self.assertFalse(self.app.calisiyor)
        self.assertEqual(self.app.indeks, 0)
        self.assertIsNone(self.app.zamanlayici)

    def test_bozuk_dosya_eski_oturumu_korur(self):
        self.app.adim()
        eski = self.app.durum
        with patch("arayuz.messagebox.showerror") as mesaj:
            self.assertFalse(self.app.klasor_yukle(KOK / "olmayan_klasor"))
        self.assertIs(self.app.durum, eski)
        mesaj.assert_called_once()

    def test_ornekler_ve_hata_paneli(self):
        for i in range(1, 6):
            self.app.ornek.current(i)
            self.app.ornek_yukle()
            self.assertEqual(self.app.indeks, 0)
            self.assertIn("Satır", self.app.hata_metni.get("1.0", "end"))
            self.assertEqual(len(self.app.komut_agaci.get_children()), len(self.app.komutlar))


if __name__ == "__main__":
    unittest.main()
