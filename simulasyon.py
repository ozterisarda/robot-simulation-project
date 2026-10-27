import argparse

from collections import deque

from copy import deepcopy

import csv

import json

from pathlib import Path

import re

YONLER = ("K", "D", "G", "B")

YON_VEKTORLERI = {"K": (0, -1), "D": (1, 0), "G": (0, 1), "B": (-1, 0)}

VARSAYILAN_AYARLAR = {
    "batarya_kapasitesi": 100, "baslangic_yonu": "D", "adim_maliyeti": 2,
    "yuk_carpani": 2, "donus_maliyeti": 1, "carpisma_cezasi": 5,
}

LOG_ALANLARI = ("adim", "komut", "x", "y", "yon", "batarya", "olay")


class KomutListesi(list):


    def __init__(self, degerler=(), hatalar=None):
        super().__init__(degerler)
        self.hatalar = list(hatalar or [])


def harita_oku(dosya_yolu):

    satirlar = Path(dosya_yolu).read_text(encoding="utf-8-sig").splitlines()
    if not satirlar or not satirlar[0]:
        raise ValueError("Harita boş olamaz.")
    genislik = len(satirlar[0])
    if any(len(satir) != genislik for satir in satirlar):
        raise ValueError("Haritanın bütün satırları aynı uzunlukta olmalıdır.")
    baslangiclar = []
    izgara = []
    for y, satir in enumerate(satirlar):
        hucreler = list(satir)
        for x, hucre in enumerate(hucreler):
            if hucre not in "#.RKTS":
                raise ValueError(f"Haritada tanımsız hücre: {hucre!r}, konum ({x}, {y}).")
            if hucre == "R":
                baslangiclar.append((x, y))

                hucreler[x] = "."
        izgara.append(hucreler)
    if len(baslangiclar) != 1:
        raise ValueError("Haritada tam olarak bir R (robot başlangıcı) bulunmalıdır.")
    return izgara, baslangiclar[0]


def _ayarlari_dogrula(ayarlar):
    if not isinstance(ayarlar, dict):
        raise ValueError("Ayarlar bir JSON nesnesi olmalıdır.")
    eksik = set(VARSAYILAN_AYARLAR) - set(ayarlar)
    if eksik:
        raise ValueError("Eksik ayar: " + ", ".join(sorted(eksik)))
    if ayarlar["baslangic_yonu"] not in YONLER:
        raise ValueError("Başlangıç yönü K, D, G veya B olmalıdır.")
    for anahtar in VARSAYILAN_AYARLAR:
        if anahtar == "baslangic_yonu":
            continue
        deger = ayarlar[anahtar]

        if type(deger) is not int or deger < 0:
            raise ValueError(f"{anahtar} negatif olmayan bir tam sayı olmalıdır.")
    if ayarlar["yuk_carpani"] < 1:
        raise ValueError("yuk_carpani en az 1 olmalıdır.")
    return dict(ayarlar)


def ayarlari_oku(dosya_yolu):

    try:
        ayarlar = json.loads(Path(dosya_yolu).read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as hata:
        raise ValueError(f"Ayarlar JSON biçiminde değil: satır {hata.lineno}.") from hata
    return _ayarlari_dogrula(ayarlar)


def komutlari_oku(dosya_yolu):

    komutlar = []
    hatalar = []
    satirlar = Path(dosya_yolu).read_text(encoding="utf-8-sig").splitlines()
    for no, icerik in enumerate(satirlar, start=1):
        parcalar = icerik.split()
        if not parcalar:


            continue
        ad = parcalar[0]
        neden = None
        if ad == "ILERI":
            if len(parcalar) != 2:
                neden = "ILERI tam olarak bir pozitif tam sayı alır."
            elif not re.fullmatch(r"[0-9]+", parcalar[1]) or int(parcalar[1]) <= 0:
                neden = "Adım sayısı sıfırdan büyük bir tam sayı olmalıdır."
            else:
                komutlar.append((ad, int(parcalar[1])))
        elif ad == "GIT":
            if len(parcalar) != 3 or any(not re.fullmatch(r"[0-9]+", p) for p in parcalar[1:]):
                neden = "GIT iki negatif olmayan tam sayı alır: GIT x y."
            else:
                komutlar.append((ad, (int(parcalar[1]), int(parcalar[2]))))
        elif ad in ("SAG", "SOL", "AL", "BIRAK", "SARJ"):
            if len(parcalar) != 1:
                neden = f"{ad} parametre almaz."
            else:
                komutlar.append((ad, None))
        else:
            neden = "Bilinmeyen komut; komutlar büyük harfle yazılmalıdır."
        if neden:
            hatalar.append({"satir": no, "icerik": icerik, "neden": neden})
    return KomutListesi(komutlar, hatalar), hatalar


def yeni_durum(izgara, baslangic, ayarlar):

    ayarlar = _ayarlari_dogrula(ayarlar)


    harita = deepcopy(izgara)
    if not harita or not harita[0] or any(len(s) != len(harita[0]) for s in harita):
        raise ValueError("Geçersiz ızgara.")
    x, y = baslangic
    if not (0 <= y < len(harita) and 0 <= x < len(harita[0])) or harita[y][x] == "#":
        raise ValueError("Robotun başlangıcı geçilebilir bir hücre olmalıdır.")
    if harita[y][x] == "R":
        harita[y][x] = "."
    return {
        "izgara": harita, "konum": (x, y), "yon": ayarlar["baslangic_yonu"],
        "batarya": ayarlar["batarya_kapasitesi"], "yuk": False,
        "teslim": 0, "carpisma": 0, "toplam_adim": 0,
        "batarya_bitti": False, "durdu": False, "ayarlar": ayarlar,
        "ziyaretler": {(x, y): 1}, "log": [], "hatali_satirlar": [],
        "son_olay": "HAZIR",
    }


def _enerji_harca(durum, maliyet):

    if maliyet > durum["batarya"]:
        durum["durdu"] = True
        durum["batarya_bitti"] = True
        return False
    durum["batarya"] -= maliyet


    return True


def _gecilebilir(durum, x, y):
    harita = durum["izgara"]
    return 0 <= y < len(harita) and 0 <= x < len(harita[0]) and harita[y][x] != "#"


def _bir_adim(durum):
    x, y = durum["konum"]
    dx, dy = YON_VEKTORLERI[durum["yon"]]
    hedef = (x + dx, y + dy)
    if not _gecilebilir(durum, *hedef):
        durum["carpisma"] += 1
        kalan = durum["batarya"] - durum["ayarlar"]["carpisma_cezasi"]
        durum["batarya"] = max(0, kalan)
        if kalan < 0:
            durum["durdu"] = durum["batarya_bitti"] = True
            return "BATARYA_BITTI"
        return "CARPISMA"
    maliyet = durum["ayarlar"]["adim_maliyeti"]
    if durum["yuk"]:
        maliyet *= durum["ayarlar"]["yuk_carpani"]
    if not _enerji_harca(durum, maliyet):
        return "BATARYA_BITTI"
    durum["konum"] = hedef
    durum["toplam_adim"] += 1
    durum["ziyaretler"][hedef] = durum["ziyaretler"].get(hedef, 0) + 1
    return "HAREKET"


def _don(durum, ad):
    if not _enerji_harca(durum, durum["ayarlar"]["donus_maliyeti"]):
        return "BATARYA_BITTI"
    indeks = YONLER.index(durum["yon"])
    durum["yon"] = YONLER[(indeks + (1 if ad == "SAG" else -1)) % 4]
    return "DONUS"


def komut_metni(komut):
    ad, parametre = komut
    if ad == "GIT":
        return f"GIT {parametre[0]} {parametre[1]}"
    return ad if parametre is None else f"{ad} {parametre}"


def komut_uygula(durum, komut):

    if durum["durdu"]:
        return "DURDU"
    ad, parametre = komut
    olay = "GECERSIZ"
    x, y = durum["konum"]
    hucre = durum["izgara"][y][x]
    if ad == "ILERI":
        if type(parametre) is int and parametre > 0:
            for _ in range(parametre):
                olay = _bir_adim(durum)
                if olay != "HAREKET":

                    break
    elif ad in ("SAG", "SOL"):
        olay = _don(durum, ad)
    elif ad == "AL" and hucre == "K" and not durum["yuk"]:
        durum["yuk"] = True
        durum["izgara"][y][x] = "."
        olay = "ALINDI"
    elif ad == "BIRAK" and durum["yuk"]:
        if hucre == "T":
            durum["yuk"] = False
            durum["teslim"] += 1
            olay = "TESLIM"
        elif hucre == ".":
            durum["yuk"] = False
            durum["izgara"][y][x] = "K"
            olay = "BIRAKILDI"
    elif ad == "SARJ" and hucre == "S":
        durum["batarya"] = durum["ayarlar"]["batarya_kapasitesi"]
        olay = "SARJ"
    durum["son_olay"] = olay
    x, y = durum["konum"]
    durum["log"].append({
        "adim": len(durum["log"]) + 1, "komut": komut_metni(komut),
        "x": x, "y": y, "yon": durum["yon"], "batarya": durum["batarya"], "olay": olay,
    })
    return olay


def durum_sonucu(durum):

    ziyaretler = durum["ziyaretler"]

    en_cok = min(ziyaretler, key=lambda p: (-ziyaretler[p], p[1], p[0]))
    return {
        "konum": list(durum["konum"]), "yon": durum["yon"],
        "batarya": durum["batarya"], "yuk": durum["yuk"],
        "teslim": durum["teslim"], "carpisma": durum["carpisma"],
        "toplam_adim": durum["toplam_adim"], "batarya_bitti": durum["batarya_bitti"],
        "en_cok_ziyaret_edilen": list(en_cok),
        "en_cok_ziyaret_sayisi": ziyaretler[en_cok],
        "hatali_satirlar": deepcopy(durum["hatali_satirlar"]),
    }


def simulasyonu_calistir(izgara, baslangic, komutlar, ayarlar):
    durum = yeni_durum(izgara, baslangic, ayarlar)
    durum["hatali_satirlar"] = deepcopy(getattr(komutlar, "hatalar", []))
    for komut in komutlar:
        if durum["durdu"]:
            break
        komut_uygula(durum, komut)
    return durum_sonucu(durum), durum["log"]


def sonuc_yaz(sonuc, dosya_yolu):
    Path(dosya_yolu).write_text(json.dumps(sonuc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def log_yaz(log, dosya_yolu):

    with open(dosya_yolu, "w", encoding="utf-8", newline="") as dosya:
        yazici = csv.DictWriter(dosya, fieldnames=LOG_ALANLARI)
        yazici.writeheader()
        yazici.writerows(log)


def harita_metni(durum):
    harita = deepcopy(durum["izgara"])
    x, y = durum["konum"]
    harita[y][x] = "R"
    return "\n".join("".join(satir) for satir in harita)


def main():

    parser = argparse.ArgumentParser(description="Depo robotu simülatörü")
    parser.add_argument("klasor", type=Path, help="harita.txt, komutlar.txt ve ayarlar.json içeren klasör")
    parser.add_argument("--cikti", type=Path, default=Path("ciktilar"))
    args = parser.parse_args()
    try:
        izgara, baslangic = harita_oku(args.klasor / "harita.txt")
        ayarlar = ayarlari_oku(args.klasor / "ayarlar.json")
        komutlar, _ = komutlari_oku(args.klasor / "komutlar.txt")
        sonuc, log = simulasyonu_calistir(izgara, baslangic, komutlar, ayarlar)
        args.cikti.mkdir(parents=True, exist_ok=True)
        sonuc_yaz(sonuc, args.cikti / "sonuc.json")
        log_yaz(log, args.cikti / "log.csv")
    except (OSError, ValueError, UnicodeError) as hata:
        parser.exit(1, f"Hata: {hata}\n")
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    print(f"Çıktılar: {args.cikti.resolve()}")


if __name__ == "__main__":
    main()
