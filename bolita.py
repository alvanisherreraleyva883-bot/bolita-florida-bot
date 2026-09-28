import os, pytz, telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from datetime import datetime

TOKEN = os.getenv("TOKEN") or "PEGA_AQUI_TU_TOKEN"
CANAL_ADMIN_ID = -1004418942264
ADMIN_ID = 7450751212

bot = telebot.TeleBot(TOKEN)
zona = pytz.timezone('America/Havana')
resultados_hoy = {"fecha": "", "dia": None, "noche": None}

def get_fecha(): return datetime.now(zona).strftime("%d/%m/%Y")

def menu_principal():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🎲 JUGAR", callback_data="jugar"),
        InlineKeyboardButton("🦩 VER TIRADA FLORIDA", callback_data="ver_ganador"),
        InlineKeyboardButton("📖 REGLAS Y PAGOS", callback_data="reglas")
    )
    return kb

def boton_atras():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⬅️ ATRÁS", callback_data="menu"))
    return kb

try:
    bot.set_my_commands([
        BotCommand("start","🎱 Menú principal"),
        BotCommand("ganador","🦩 Ver tirada")
    ])
except: pass

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id,
"🎱 *BOLITA RECOGIDA - FLORIDA* 🦩\n"
"━━━━━━━━━━━━━━━\n"
"👋 Bienvenido!\n"
"Selecciona una opción:",
parse_mode="Markdown", reply_markup=menu_principal())

@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    if c.data == "menu":
        bot.edit_message_text(
"🎱 *BOLITA RECOGIDA - FLORIDA* 🦩\n"
"━━━━━━━━━━━━━━━\n"
"👋 Menú principal:",
            c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=menu_principal())
    
    elif c.data == "jugar":
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ ATRÁS", callback_data="menu"))
        bot.edit_message_text(
"✍️ *COMO JUGAR:*\n"
"━━━━━━━━━━━━━━━\n"
"`12 50 fijo`\n"
"`12 30 corrido`\n"
"`12 50 fijo 50 corrido`\n"
"━━━━━━━━━━━━━━━\n"
"💳 Tarjeta: `9238-1299-7507-3018`\n"
"📲 `55348244`\n\n"
"👉 Escribe tu jugada directo en el chat",
            c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)

    elif c.data == "reglas":
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ ATRÁS", callback_data="menu"))
        bot.edit_message_text(
"📖 *REGLAS Y PAGOS*\n"
"━━━━━━━━━━━━━━━\n"
"💰 Fijo paga *$80* x cada $1\n"
"🔄 Corrido paga *$20* x cada $1\n"
"🕘 Horario: 9AM-1PM y 3PM-9PM\n"
"💵 Máx $200 por número\n"
"━━━━━━━━━━━━━━━",
            c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)

    elif c.data == "ver_ganador":
        fecha=get_fecha()
        dia=resultados_hoy["dia"]
        noche=resultados_hoy["noche"]
        txt=f"🦩 *TIRADA FLORIDA - {fecha}*\n━━━━━━━━━━━━━━━\n"
        if dia: txt+=f"☀️ *DÍA 1:35 PM*\n🎯 Fijo: `{dia['fijo']}`\n🔄 Corr1: `{dia['c1']}`\n🔄 Corr2: `{dia['c2']}`\n━━━━━━━━━━━━━━━\n"
        else: txt+=f"☀️ *DÍA 1:35 PM:* ⏳ Esperando\n━━━━━━━━━━━━━━━\n"
        if noche: txt+=f"🌙 *NOCHE 9:50 PM*\n🎯 Fijo: `{noche['fijo']}`\n🔄 Corr1: `{noche['c1']}`\n🔄 Corr2: `{noche['c2']}`\n"
        else: txt+=f"🌙 *NOCHE 9:50 PM:* ⏳ Esperando\n"
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔄 Actualizar", callback_data="ver_ganador"),
               InlineKeyboardButton("⬅️ ATRÁS", callback_data="menu"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)

@bot.message_handler(commands=['ganador'])
def ganador(m):
    fecha=get_fecha(); dia=resultados_hoy["dia"]; noche=resultados_hoy["noche"]
    txt=f"🦩 *TIRADA FLORIDA - {fecha}*\n━━━━━━━━━━━━━━━\n"
    if dia: txt+=f"☀️ DÍA\n🎯 Fijo: `{dia['fijo']}` | Corr: `{dia['c1']}` `{dia['c2']}`\n"
    else: txt+=f"☀️ DÍA: esperando\n"
    if noche: txt+=f"🌙 NOCHE\n🎯 Fijo: `{noche['fijo']}` | Corr: `{noche['c1']}` `{noche['c2']}`\n"
    else: txt+=f"🌙 NOCHE: esperando\n"
    bot.send_message(m.chat.id, txt, parse_mode="Markdown", reply_markup=boton_atras())

@bot.message_handler(commands=['set_dia'])
def set_dia(m):
    if m.from_user.id != ADMIN_ID and m.chat.id != CANAL_ADMIN_ID: return
    try:
        _, f, c1, c2 = m.text.split()
        resultados_hoy["dia"] = {"fijo":f.zfill(2), "c1":c1.zfill(2), "c2":c2.zfill(2)}
        bot.reply_to(m, f"✅ DIA guardado: {f} {c1} {c2}")
    except: bot.reply_to(m, "Usa: /set_dia 13 20 28")

@bot.message_handler(commands=['set_noche'])
def set_noche(m):
    if m.from_user.id != ADMIN_ID and m.chat.id != CANAL_ADMIN_ID: return
    try:
        _, f, c1, c2 = m.text.split()
        resultados_hoy["noche"] = {"fijo":f.zfill(2), "c1":c1.zfill(2), "c2":c2.zfill(2)}
        bot.reply_to(m, f"✅ NOCHE guardado: {f} {c1} {c2}")
    except: bot.reply_to(m, "Usa: /set_noche 45 12 89")

print("bolita.py CON BOTONES ATRAS ON")
bot.infinity_polling()
