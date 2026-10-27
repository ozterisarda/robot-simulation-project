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
