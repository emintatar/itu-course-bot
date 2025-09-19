# bot.py
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from scraper import kontenjan_getir # Çalıştığını doğruladığımız scraper'ımız

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

def start(update, context):
    update.message.reply_text(
        "Merhaba! İTÜ Kontenjan Takip Botu'na hoş geldin.\n"
        "Ders eklemek için /ekle komutunu kullanabilirsin.\n"
        "Yardım için /help yazabilirsin."
    )

def help_command(update, context):
    update.message.reply_text(
        "/ekle - Takip listene yeni bir ders ekler.\n"
        "/liste - Takip ettiğin dersleri gösterir.\n"
        "/sil <CRN> - Belirtilen CRN'i takip listenden siler.\n"
        "/cancel - Devam eden bir işlemi iptal eder."
    )

def ekle_baslat(update, context):
    update.message.reply_text("Yeni bir ders ekleyelim. Lütfen dersin 5 haneli CRN kodunu yaz.")
    return CRN_GIR

def crn_al(update, context):
    crn = update.message.text
    if not crn.isdigit() or len(crn) != 5:
        update.message.reply_text("Geçersiz CRN. Lütfen 5 haneli bir sayı gir.")
        return CRN_GIR # Aynı adımda kal

    context.user_data['crn'] = crn
    update.message.reply_text(f"Anladım, CRN: {crn}. Şimdi bu dersin bölüm kodunu yaz. (Örn: MAT, ECN, END)")
    return BOLUM_GIR

# bot.py dosyasında bu fonksiyonu bulup değiştirin:

# bot.py dosyasında bu fonksiyonu bulup eski haline getirin:

def bolum_al(update, context):
    bolum = update.message.text.upper()
    crn = context.user_data['crn']
    chat_id = update.message.chat_id

    if chat_id not in user_data:
        user_data[chat_id] = {}
    
    # --- GERİ ALINAN SATIR ---
    # Yeni dersi eklerken durumu tekrar "BILINMIYOR" olarak başlatıyoruz.
    user_data[chat_id][crn] = {'bolum': bolum, 'seviye': 'LISANS', 'son_durum': 'BILINMIYOR'}

    update.message.reply_text(f"✅ Tamamdır! {bolum} bölümündeki {crn} CRN'li ders listeye eklendi.")
    context.user_data.clear() # Geçici veriyi temizle
    return ConversationHandler.END

def cancel(update, context):
    update.message.reply_text("İşlem iptal edildi.")
    context.user_data.clear()
    return ConversationHandler.END

def liste(update, context):
    chat_id = update.message.chat_id
    if chat_id not in user_data or not user_data[chat_id]:
        update.message.reply_text("Takip listen boş.")
        return

    message = "Takip Listen:\n"
    for crn, data in user_data[chat_id].items():
        durum = data.get('son_durum', 'Henüz kontrol edilmedi')
        message += f"- CRN: {crn}, Bölüm: {data['bolum']}, Durum: {durum}\n"
    
    update.message.reply_text(message)

def sil(update, context):
    chat_id = update.message.chat_id
    if not context.args:
        update.message.reply_text("Lütfen silmek istediğiniz CRN'i belirtin. Örneğin: /sil 12775")
        return
    
    crn_to_delete = context.args[0]
    
    if chat_id in user_data and crn_to_delete in user_data[chat_id]:
        del user_data[chat_id][crn_to_delete]
        update.message.reply_text(f"{crn_to_delete} CRN'li ders takip listenden çıkarıldı.")
    else:
        update.message.reply_text("Bu CRN takip listenizde bulunmuyor.")

# --- OTOMATİK KONTROL MEKANİZMASI ---

# --- OTOMATİK KONTROL MEKANİZMASI (YENİ VERSİYON) ---

def kontrol_et(context):
    print("Periyodik kontrol çalışıyor...")
    if not user_data:
        return # Takip edilen ders yoksa boşuna çalışma

    # Tüm kullanıcıları ve derslerini döngüye al
    for chat_id, dersler in user_data.items():
        for crn, data in dersler.items():
            print(f"Kontrol ediliyor -> CRN: {crn}, Bölüm: {data['bolum']}")
            yeni_durum = kontenjan_getir(data['seviye'], data['bolum'], crn)
            
            # --- DEĞİŞEN MANTIK ---
            # Eğer derste yer varsa, her kontrol edildiğinde haber ver.
            if yeni_durum == "BOS":
                context.bot.send_message(
                    chat_id=chat_id, 
                    text=f"📢 {data['bolum']} bölümündeki {crn} CRN'li derste yer var!"
                )
            
            # Son durumu her zaman güncelle (listenin güncel kalması için önemli)
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