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
