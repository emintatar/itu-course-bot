# bot.py

import os
from dotenv import load_dotenv # YENİ EKLENEN SATIR
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from scraper import kontenjan_getir

load_dotenv() # YENİ EKLENEN SATIR

# --- AYARLAR ---
# Token'ı koddan kaldırıp, bunun yerine ortam değişkeninden okuyoruz
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
# Kontrol sıklığı (saniye cinsinden). 60 = 1 dakika
KONTROL_ARALIGI = 60 

# --- VERİ SAKLAMA ---
# Kullanıcı verilerini saklamak için basit bir sözlük.
# Format: { chat_id: {crn1: {'bolum': 'ECN', 'seviye': 'LISANS', 'son_durum': 'BILINMIYOR'}, crn2: ...} }
user_data = {}

# --- SOHBET DURUMLARI (DERS EKLEME İÇİN) ---
CRN_GIR, BOLUM_GIR = range(2)

# --- BOT KOMUTLARI ---

# bot.py dosyasında sadece bu fonksiyonu bul ve değiştir:

def start(update, context):
    # Bu fonksiyon /start komutuna cevap verir.
    update.message.reply_text(
        "Merhaba Özgü! Ders seçimi maceranda sana yardımcı olmak için buradayım. 😊\n\n"
        "Eklemek istediğin bir ders varsa /ekle komutunu kullanabilirsin.\n"
        "Tüm komutları görmek için /help yazabilirsin."
    )

def help_command(update, context):
    # Bu fonksiyon /help komutuna cevap verir.
    update.message.reply_text(
        "İşte yapabildiklerim:\n\n"
        "/ekle - Takip etmek istediğin yeni bir dersi listeye eklerim.\n"
        "/liste - Hangi dersleri takip ettiğimizi gösteririm.\n"
        "/sil <CRN> - Listeden bir dersi silerim.\n\n"
        "Umarım aradığın dersi hemen bulursun! ✨"
    )

def ekle_baslat(update, context):
    # /ekle sohbetini başlatır.
    update.message.reply_text("Harika! Takip listene eklemek istediğin dersin 5 haneli CRN kodunu alabilir miyim?")
    return CRN_GIR

def crn_al(update, context):
    # Kullanıcıdan CRN'i alır.
    crn = update.message.text
    if not crn.isdigit() or len(crn) != 5:
        update.message.reply_text("Geçersiz CRN. Lütfen 5 haneli bir sayı gir.")
        return CRN_GIR

    context.user_data['crn'] = crn
    update.message.reply_text(f"Süper, şimdi de bölüm kodunu rica edeyim. (Örn: END, MAT)")
    return BOLUM_GIR

def bolum_al(update, context):
    # Kullanıcıdan bölümü alır ve dersi kaydeder.
    bolum = update.message.text.upper()
    crn = context.user_data['crn']
    chat_id = update.message.chat_id

    if chat_id not in user_data:
        user_data[chat_id] = {}
    
    user_data[chat_id][crn] = {'bolum': bolum, 'seviye': 'LISANS', 'son_durum': 'BILINMIYOR'}

    update.message.reply_text(f"İşte bu kadar! {bolum} bölümündeki {crn} CRN'li ders artık takibimde. Kontenjan açıldığı an sana haber vereceğim! 😉")
    context.user_data.clear()
    return ConversationHandler.END

def cancel(update, context):
    update.message.reply_text("İşlem iptal edildi.")
    context.user_data.clear()
    return ConversationHandler.END

def liste(update, context):
    # /liste komutuna cevap verir.
    chat_id = update.message.chat_id
    if chat_id not in user_data or not user_data[chat_id]:
        update.message.reply_text("Şu an takipte olduğumuz bir ders yok. Eklemek için /ekle yazabilirsin.")
        return

    message = "Özgü, şu an takip ettiğimiz dersler şunlar:\n"
    for crn, data in user_data[chat_id].items():
        durum = data.get('son_durum', 'Henüz kontrol edilmedi')
        message += f"- CRN: {crn}, Bölüm: {data['bolum']}, Durum: {durum}\n"
    
    update.message.reply_text(message)

def sil(update, context):
    # /sil komutuna cevap verir.
    chat_id = update.message.chat_id
    if not context.args:
        update.message.reply_text("Lütfen silmek istediğiniz CRN'i belirtin. Örneğin: /sil 12775")
        return
    
    crn_to_delete = context.args[0]
    
    if chat_id in user_data and crn_to_delete in user_data[chat_id]:
        del user_data[chat_id][crn_to_delete]
        update.message.reply_text(f"{crn_to_delete} CRN'li dersi listeden çıkardım. Umarım ihtiyacın kalmamıştır! 👍")
    else:
        update.message.reply_text("Bu CRN takip listenizde bulunmuyor.")

# --- OTOMATİK KONTROL MEKANİZMASI ---

# --- OTOMATİK KONTROL MEKANİZMASI (YENİ VERSİYON) ---

def kontrol_et(context):
    # Arka planda periyodik olarak çalışır ve bildirim gönderir.
    print("Periyodik kontrol çalışıyor...")
    if not user_data:
        return

    for chat_id, dersler in user_data.items():
        for crn, data in dersler.items():
            print(f"Kontrol ediliyor -> CRN: {crn}, Bölüm: {data['bolum']}")
            yeni_durum = kontenjan_getir(data['seviye'], data['bolum'], crn)
            
            if yeni_durum == "BOS":
                context.bot.send_message(
                    chat_id=chat_id, 
                    text=f"Özgü, müjde! ✨ {data['bolum']} bölümündeki {crn} CRN'li derste kontenjan açıldı! Acele et, yerler dolmadan al! 🏃‍♀️"
                )
            
            data['son_durum'] = yeni_durum
    print("Kontrol tamamlandı.")


# --- BOTU BAŞLATAN ANA FONKSİYON ---

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Ders ekleme sohbet yapısı
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('ekle', ekle_baslat)],
        states={
            CRN_GIR: [MessageHandler(Filters.text & ~Filters.command, crn_al)],
            BOLUM_GIR: [MessageHandler(Filters.text & ~Filters.command, bolum_al)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("liste", liste))
    dp.add_handler(CommandHandler("sil", sil))
    
    # Otomatik kontrolcüyü başlat
    job_queue = updater.job_queue
    job_queue.run_repeating(kontrol_et, interval=KONTROL_ARALIGI, first=10)
    
    print("Bot başlatılıyor...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()