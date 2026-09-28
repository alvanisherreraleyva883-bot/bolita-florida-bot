import os, re, pytz, telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from datetime import datetime

TOKEN = os.getenv("TOKEN") or "PEGA_AQUI_TU_TOKEN"
CANAL_ADMIN_ID = -1004418942264
ADMIN_ID = 7450751212
TARJETA = "9238-1299-7507-3018"
TELEFONO = "55348244"

bot = telebot.TeleBot(TOKEN)
zona = pytz.timezone('America/Havana')
acumulado = {}
pendientes = {}
resultados_hoy = {"fecha": "", "dia": None, "noche": None}

def get_fecha(): return datetime.now(zona).strftime("%d/%m/%Y")
def es_admin(m): return m.chat.id == CANAL_ADMIN_ID or m.from_user.id == ADMIN_ID
def horario_abierto():
    h = datetime.now(zona).hour + datetime.now(zona).minute/60
    return (9 <= h < 13) or (15 <= h < 21)

try:
    bot.set_my_commands([BotCommand("start","Empezar"), BotCommand("ganador","Ver tirada")])
except: pass

@bot.message_handler(commands=['ganador'])
def ganador(m):
    f=get_fecha(); d=resultados_hoy["dia"]; n=resultados_hoy["noche"]
    txt=f"🦩 TIRADA FLORIDA - {f}\n\n"
    txt+=f"☀️ DIA 1:35 PM\n🎯 Fijo: {d['fijo']}\n🔄 Corr1: {d['c1']}\n🔄 Corr2: {d['c2']}\n\n" if d else "☀️ DIA: esperando\n\n"
    txt+=f"🌙 NOCHE 9:50 PM\n🎯 Fijo: {n['fijo']}\n🔄 Corr1: {n['c1']}\n🔄 Corr2: {n['c2']}" if n else "🌙 NOCHE: esperando\n"
    bot.reply_to(m, txt)

@bot.message_handler(commands=['set_dia'])
def set_dia(m):
    if not es_admin(m): return
    try:
        _,f,c1,c2=m.text.split()
        resultados_hoy["dia"]={"fijo":f.zfill(2),"c1":c1.zfill(2),"c2":c2.zfill(2)}
        bot.reply_to(m, f"✅ DIA {f} {c1} {c2} guardado")
    except: bot.reply_to(m, "Usa: /set_dia 13 20 28")

@bot.message_handler(commands=['set_noche'])
def set_noche(m):
    if not es_admin(m): return
    try:
        _,f,c1,c2=m.text.split()
        resultados_hoy["noche"]={"fijo":f.zfill(2),"c1":c1.zfill(2),"c2":c2.zfill(2)}
        acumulado.clear()
        bot.reply_to(m, f"✅ NOCHE {f} {c1} {c2} guardado")
    except: bot.reply_to(m, "Usa: /set_noche 45 12 89")

@bot.message_handler(commands=['start'])
def start(m): bot.reply_to(m, "🎱 Bolita Florida\nJuega: 12 50 fijo\nResultados: /ganador")

@bot.message_handler(func=lambda m: True, content_types=['text'])
def jugada(m):
    if m.text.startswith('/'): return
    bot.reply_to(m, "Manda tu jugada tipo 12 50 fijo y luego la captura\nTarjeta 9238-1299-7507-3018")

print("bolita.py ON")
bot.infinity_polling()
