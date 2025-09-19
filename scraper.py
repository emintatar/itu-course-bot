# scraper.py (FİNAL VERSİYON - EN DOĞRU VE EN HIZLI YÖNTEM)
import requests
from bs4 import BeautifulSoup

# İsteğin normal bir tarayıcıdan geldiğini belirtmek için header
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest' # Bu header, isteğin bir Ajax isteği olduğunu belirtir, önemlidir.
}

def get_bolum_id(seviye_anahtari, bolum_kodu):
    """Verilen bölüm kodunun (örn: ALM) sayısal ID'sini bulur."""
    
    # Bu URL, bölüm listesini JSON olarak döner.
    url = f"https://obs.itu.edu.tr/public/DersProgram/SearchBransKoduByProgramSeviye?programSeviyeTipiAnahtari={seviye_anahtari}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        bolumler = response.json() # Gelen cevabı JSON'a çevir
        
        # Gelen listede bizim istediğimiz bölümü bul ve ID'sini döndür
        for bolum in bolumler:
            if bolum['dersBransKodu'] == bolum_kodu:
                return bolum['bransKoduId']
        return None # Bulamazsa None döndür
        
    except requests.exceptions.RequestException as e:
        print(f"Bölüm ID'si alınırken hata: {e}")
        return None

def kontenjan_getir(egitim_seviyesi, bolum_kodu, crn):
    """Nihai ve doğru yöntemle bir dersin kontenjan durumunu çeker."""
    
    # Sitenin kullandığı seviye anahtarları (Lisans için 'LS')
    seviye_anahtar_map = {
        'LISANS': 'LS',
        'ONLISANS': 'OL',
        'LISANSUSTU': 'LU'
    }
    seviye_anahtari = seviye_anahtar_map.get(egitim_seviyesi, 'LS')
    
    # 1. Adım: Bölümün sayısal ID'sini al
    bolum_id = get_bolum_id(seviye_anahtari, bolum_kodu)
    if not bolum_id:
        print(f"{bolum_kodu} için bölüm ID'si bulunamadı.")
        return "HATA"
        
    # 2. Adım: Doğru URL'e, doğru parametrelerle GET isteği yap
    data_url = f"https://obs.itu.edu.tr/public/DersProgram/DersProgramSearch?programSeviyeTipiAnahtari={seviye_anahtari}&dersBransKoduId={bolum_id}"
    
    try:
        response = requests.get(data_url, headers=headers)
        response.raise_for_status()
        
        # Gelen cevap doğrudan tablonun HTML'idir.
        soup = BeautifulSoup(response.text, 'lxml')
        
        for satir in soup.find_all('tr'):
            hucreler = satir.find_all('td')
            if len(hucreler) > 10 and hucreler[0].text.strip() == str(crn):
                kapasite = int(hucreler[9].text.strip())
                yazilan = int(hucreler[10].text.strip())
                
                if yazilan < kapasite:
                    return "BOS"
                else:
                    return "DOLU"
        
        return "CRN_BULUNAMADI"

    except requests.exceptions.RequestException as e:
        print(f"Ders bilgisi alınırken hata: {e}")
        return "HATA"