from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


KOK = Path(__file__).resolve().parent
NUMARALAR = "250501031_250501030"
DOSYALAR = [
    "simulasyon.py", "arayuz.py", "test_calistir.py", "test_simulasyon.py",
    "test_arayuz.py", "teslim_hazirla.py", "README.md", "baslat.bat", ".gitignore",
    "rapor/rapor.pdf", "rapor/rapor.md", "dogrulama/sonuclar.json",
    "dogrulama/test_gunlugu.txt",
]
DIZINLER = ("paket_ornek", "deneme_verileri", "demo_verileri")


def main():
    hedef = KOK / "teslim"
    hedef.mkdir(exist_ok=True)
    eksikler = [ad for ad in DOSYALAR if not (KOK / ad).is_file()]
    if eksikler:
        raise SystemExit("Teslim paketi hazırlanamadı. Eksik: " + ", ".join(eksikler))
    kodlar = []
    for yol in sorted(KOK.glob("*.py")):
        kodlar.append(f"{'=' * 72}\nDOSYA: {yol.name}\n{'=' * 72}\n\n{yol.read_text(encoding='utf-8')}\n")
    metin = hedef / f"{NUMARALAR}.txt"
    metin.write_text("\n".join(kodlar), encoding="utf-8")
    arsiv = hedef / f"depo_robotu_{NUMARALAR}.zip"
    with ZipFile(arsiv, "w", compression=ZIP_DEFLATED) as z:
        for ad in DOSYALAR:
            z.write(KOK / ad, ad)
        for ad in DIZINLER:
            for yol in sorted((KOK / ad).rglob("*")):
                if yol.is_file() and "__pycache__" not in yol.parts:
                    z.write(yol, yol.relative_to(KOK))
        z.write(metin, metin.name)
    print(f"Kaynak dökümü: {metin}")
    print(f"Teslim paketi: {arsiv}")
    print("Paket oluşturuldu.")


if __name__ == "__main__":
    main()
