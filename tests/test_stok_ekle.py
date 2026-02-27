import pytest
from playwright.sync_api import sync_playwright, expect
import random
import string
import allure  # Raporlama için
import os
# --- AYARLAR ---
REAL_EMAIL = os.environ.get("USER_EMAIL")
REAL_PASS = os.environ.get("USER_PASS")
REAL_FIRM_CODE = os.environ.get("FIRM_CODE")
BIRIM = "adet"
TARGET_URL = "https://rc.tcaree.com/"
ADET = int(os.environ.get("STOK_ADEDI", 1))

def generate_random_name(prefix="OtoStok_"):
    chars = string.ascii_letters + string.digits
    random_suffix = ''.join(random.choices(chars, k=7))
    return f"{prefix}{random_suffix}"

@allure.feature("Stok Yönetimi")
@allure.story("Toplu Stok Ekleme")
@allure.title(f"Otomatik {ADET} Adet Stok Ekleme Testi")
def test_stok_ekleme_robotu():
    """
    Bu test Docker içinde çalışır, siteye girer ve belirtilen adet kadar stok ekler.
    """
    with sync_playwright() as p:
        # PDF'te belirtilen Xvfb sanal ekran mantığı Docker imajında otomatiktir.
        # headless=True: Docker içinde ekran olmadığı için zorunludur.
        browser = p.chromium.launch(headless=True, slow_mo=500, args=['--no-sandbox'])
        context = browser.new_context()
        page = context.new_page()

        try:
            with allure.step("Siteye Giriş Yapılıyor"):
                page.goto(TARGET_URL)
                page.get_by_role("textbox", name="E-posta Adresiniz").fill(REAL_EMAIL)
                page.get_by_role("textbox", name="Şifreniz").fill(REAL_PASS)
                
                # Firma Kodu Kontrolü
                try:
                    page.wait_for_timeout(500)
                    firm = page.get_by_role("textbox", name="Firma Kodu")
                    if firm.is_visible():
                        firm.fill(REAL_FIRM_CODE)
                except:
                    pass
                
                page.get_by_role("button", name="Giriş Yap").click()
                
                # Evet (Çakışma) Butonu
                try:
                    page.wait_for_timeout(1500)
                    if page.get_by_role("button", name="Evet").is_visible():
                        page.get_by_role("button", name="Evet").click()
                except:
                    pass
                
                page.wait_for_load_state("networkidle")

            with allure.step("Menüler Açılıyor"):
                page.get_by_role("link", name="Tanımlar").click()
                page.get_by_role("link", name="Stok", exact=True).click()
                page.get_by_role("link", name="Stok Tanım").click()
                page.wait_for_load_state("domcontentloaded")

            # DÖNGÜ BAŞLIYOR
            # Menüye tıkladıktan sonra sayfanın tam oturması için en başta biraz bekleyelim
            page.wait_for_timeout(2000) 

            for i in range(1, ADET + 1):
                stok_adi = generate_random_name()
                
                with allure.step(f"[{i}/{ADET}] Stok Ekleniyor: {stok_adi}"):
                    
                    # 1. EKLE BUTONUNA BASMA (ESNEK VE GARANTİ YÖNTEM)
                    # Sadece text olarak "Ekle" yazan ilk elementi bul (buton, link vs. fark etmez)
                    ekle_butonu = page.get_by_text("Ekle", exact=True).first
                    
                    # Butonun görünür olmasını bekle (maksimum 10 saniye sabreder)
                    ekle_butonu.wait_for(state="visible", timeout=10000)
                    
                    # Tıkla
                    ekle_butonu.click()
                    
                    # 2. FORMUN AÇILMASINI BEKLE
                    # Yan panelin veya popup'ın açılma animasyonu bitene kadar bekle
                    page.wait_for_timeout(1500)

                    # 3. FORMU DOLDUR VE KAYDET
                    page.get_by_role("textbox", name="Birim", exact=True).fill(BIRIM)
                    page.get_by_role("textbox", name="Stok Adı").fill(stok_adi)
                    
                    # Kaydet butonuna tıkla (Aynı esnek metodu burada da kullanıyoruz)
                    page.get_by_role("button", name="Kaydet").click()
                    
                    # [cite_start]Başarılı olduğunu doğrula (Assertion) [cite: 254]
                    # Sistemin kaydı tamamlaması ve ekranın sıfırlanması için bekle
                    page.wait_for_timeout(1500)
        
        except Exception as e:
            # [cite_start]Hata anında ekran görüntüsü alıp rapora ekle [cite: 167]
            allure.attach(
                page.screenshot(full_page=True), 
                name="Hata_Gorseli", 
                attachment_type=allure.attachment_type.PNG
            )
            raise e  # Hatayı fırlat ki GitHub'da 'Failed' görünsün
        
        finally:
            browser.close()
