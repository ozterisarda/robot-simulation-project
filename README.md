# Depo Robotu Simülatörü

Python ve Tkinter ile geliştirilmiş depo robotu simülatörü. Robot; dosyalardan
okunan haritada hareket eder, kutu taşır, teslim yapar ve şarj olur. Sonuçlar
JSON ve CSV olarak kaydedilir.

**Ekip:** Arda Özteriş (250501031), Ahmet Bilgekağan Karaca (250501030).

## Gereksinimler ve başlatma

Python 3.10 veya üzeri ve Tkinter gerekir. Ek paket veya internet bağlantısı
gerekmez. Windows'ta `baslat.bat` dosyasını açın veya proje klasöründe çalıştırın:

```powershell
python arayuz.py
```

## Kullanım

Uygulama tanıtım senaryosuyla açılır. Farklı veriler için **Klasör yükle**
ile `harita.txt`, `komutlar.txt` ve `ayarlar.json` içeren klasörü seçin.
**Dosyaları seç** ile bu dosyaları ayrı ayrı da yükleyebilirsiniz.

| Kontrol | İşlev |
| --- | --- |
| Adım / F6 | Sıradaki komutu uygular |
| Tümünü çalıştır / F5 | Otomatik çalıştırır veya duraklatır |
| Sıfırla / Ctrl+R | Son yüklenen başlangıç durumuna döner |
| Klasör yükle / Ctrl+O | Girdi klasörü seçer |
| Sonuçları kaydet | Mevcut sonucu ve işlem kaydını dışarı aktarır |
| Ziyaret izleri | Ziyaret edilen hücreleri gösterir |

Bir Adım işlemi komutun tamamını çalıştırır. Komutlar ve Hatalı satırlar
sekmeleri ekranın altındadır. Harita üzerinde hücrenin koordinatı ve ziyaret
sayısı incelenebilir. Hız çubuğu, komutlar arasındaki beklemeyi değiştirir.

## Girdi biçimleri

Haritada `#` duvar, `.` boş zemin, `R` robot başlangıcı, `K` kutu,
`T` teslim noktası ve `S` şarj istasyonudur. Harita dikdörtgen olmalı ve
tam bir `R` içermelidir. Koordinatlar `(x, y)`, yani sütun ve satırdır;
sol üst köşe `(0, 0)` kabul edilir.

Komutlar büyük harfle yazılır:

```text
ILERI 3
SAG
SOL
AL
BIRAK
SARJ
GIT 9 1
```

`ILERI` pozitif tam sayı, `GIT` iki negatif olmayan tam sayı alır. Diğer
komutlar parametre almaz. Hatalı satırlar atlanır ve hata sekmesinde listelenir.
Boş satırlar hata değildir.

```json
{
  "batarya_kapasitesi": 100,
  "baslangic_yonu": "D",
  "adim_maliyeti": 2,
  "yuk_carpani": 2,
  "donus_maliyeti": 1,
  "carpisma_cezasi": 5
}
```

Başlangıç yönleri K, D, G ve B'dir. Maliyetler negatif olmayan tam sayı,
yük çarpanı en az 1 olmalıdır. Yük taşıma hareket maliyetini artırır.
`GIT`, en kısa hücre yolunu kullanır; kutu alma, teslim ve şarj işlemlerini
otomatik yapmaz.

## Çıktılar

Simülasyon bitince veya enerji yetersizliğinden durunca `ciktilar/sonuc.json`
ve `ciktilar/log.csv` güncellenir. Önceki otomatik çıktılar üzerine yazılır.
Saklamak istediğiniz çalışmaları Sonuçları kaydet ile farklı klasöre aktarın.

JSON; son konum, yön, batarya, yük, teslim, çarpışma, toplam hareket,
enerji nedeniyle durma, ziyaret özeti ve hatalı satırları içerir. CSV'de
işlenen geçerli komut başına bir satır bulunur. `adim` komut sırasını,
`toplam_adim` fiziksel hareket sayısını ifade eder.

## Komut satırı ve doğrulama

```powershell
python simulasyon.py demo_verileri/tanitim --cikti ciktilar/tanitim
python test_calistir.py paket_ornek
python -m unittest -v test_simulasyon test_arayuz
```

Örnek testler 6/6, ek kontroller 27/27 geçmektedir. Grafik arayüz testleri
Tkinter ve masaüstü oturumu gerektirir. Beş deneme veri seti ve bir tanıtım
senaryosu pakete dahildir. Yeni bir test paketi için:

```powershell
python test_calistir.py PAKET_YOLU
```

## Paket oluşturma

```powershell
python teslim_hazirla.py
```

`teslim/` içinde ZIP ve bütün Python kaynaklarını içeren
`250501031_250501030.txt` üretilir. Teknik rapor `rapor/rapor.pdf`
konumundadır. Doğrulama kayıtları `dogrulama/` klasöründedir.

## Sorun giderme

- Python bulunamazsa `py -3 arayuz.py` komutunu deneyin.
- Tkinter kurulumu `python -m tkinter` ile kontrol edilebilir.
- Dosya yüklenemezse hata mesajını, dosya biçimini ve kodlamasını kontrol edin.
- Enerji yetersizliğinde devam etmek için sıfırlayın veya başka veri yükleyin.
- Sıfırla dosyaları yeniden okumaz; değişen girdiler için yeniden yükleme gerekir.
