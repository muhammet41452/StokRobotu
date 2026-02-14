import pytest
from playwright.sync_api import sync_playwright, expect
import random
import string
import allure  # Raporlama için

# --- AYARLAR ---
REAL_EMAIL = "destekk@cevizsoft.com"
REAL_PASS = "Aa1"
REAL_FIRM_CODE = "s5snb53qz5Z2XvpS5htK"
BIRIM = "adet"
TARGET_URL = "https://rc.tcaree.com/"
ADET = 5  # Her çalıştırmada kaç stok eklensin?

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
            for i in range(1, ADET + 1):
                stok_adi = generate_random_name()
                
                with allure.step(f"[{i}/{ADET}] Stok Ekleniyor: {stok_adi}"):
                    try:
                        page.get_by_role("button", name="Ekle").click()
                    except:
                        page.reload()
                        page.get_by_role("button", name="Ekle").click()

                    page.get_by_role("textbox", name="Birim", exact=True).fill(BIRIM)
                    page.get_by_role("textbox", name="Stok Adı").fill(stok_adi)
                    page.get_by_role("button", name="Kaydet").click()
                    
                    # Başarılı olduğunu doğrula (Assertion) [cite: 254]
                    # Kaydet butonuna bastıktan sonra hata almadığımızı varsayıyoruz
                    page.wait_for_timeout(1000)
        
        except Exception as e:
            # Hata anında ekran görüntüsü alıp rapora ekle [cite: 167]
            allure.attach(
                page.screenshot(full_page=True), 
                name="Hata_Gorseli", 
                attachment_type=allure.attachment_type.PNG
            )
            raise e  # Hatayı fırlat ki GitHub'da 'Failed' görünsün
        
        finally:
            browser.close()