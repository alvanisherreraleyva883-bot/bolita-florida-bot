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
acumulado = {} # {user_id: {texto, total}}
pendientes = {} # {user_id: {jugada}}
resultados_hoy = {"dia": None, "noche": None}

def get_fecha(): return datetime.now(zona).strftime("%d/%m/%Y")
def get_hora(): return datetime.now(zona).strftime("%I:%M %p")
def es_admin(m): return m.from_user.id == ADMIN_ID or m.chat.id == CANAL_ADMIN_ID
def horario_abierto():
    h = datetime.now(zona).hour + datetime.now(zona).minute/60
    return (9 <= h < 13.1) or (15 <= h < 21.1)

def menu_principal():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🎲 JUGAR AHORA", callback_data="jugar"),
        InlineKeyboardButton("🦩 VER TIRADA FLORIDA", callback_data="ver_ganador"),
        InlineKeyboardButton("📖 REGLAS Y PAGOS", callback_data="reglas"),
        InlineKeyboardButton("💳 DATOS DE PAGO", callback_data="pago")
    )
    return kb

def boton_atras():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⬅️ ATRÁS AL MENÚ", callback_data="menu"))
    return kb

# Texto de bienvenida BONITO que quieres
BIENVENIDA = (
"🎱🔥 *¡BIENVENIDOS A JUGAR LA LOTERÍA DE LA FLORIDA!* 🔥🦩\n"
"━━━━━━━━━━━━━━━━━━━━\n"
"💎 *BOLITA RECOGIDA.FLORIDA* 💎\n"
"La más rápida y segura de Cuba 🇨🇺\n"
"━━━━━━━━━━━━━━━━━━━━\n"
"💰 *PAGOS OFICIALES:*\n"
"🎯 FIJO se paga a *80 CUP* x cada $1\n"
"🔄 CORRIDO se paga a *20 CUP* x cada $1\n"
"━━━━━━━━━━━━━━━━━━━━\n"
"🕘 *HORARIO:*\n"
"☀️ Mañana: 9:00 AM - 1:00 PM\n"
"🌙 Tarde: 3:00 PM - 9:00 PM\n"
"━━━━━━━━━━━━━━━━━━━━\n"
"✍️ *EJEMPLO PARA JUGAR:*\n"
"`12 100 fijo`\n"
"`45 50 corrido`\n"
"`08 50 fijo 50 corrido`\n"
"━━━━━━━━━━━━━━━━━━━━\n"
"👇 Toca un botón para empezar 👇"
)

try:
    bot.set_my_commands([
        BotCommand("start","🎱 Menú Florida"),
        BotCommand("ganador","🦩 Ver tirada"),
        BotCommand("misjugadas","📋 Mis jugadas")
    ])
except: pass

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, BIENVENIDA, parse_mode="Markdown", reply_markup=menu_principal())

@bot.message_handler(commands=['misjugadas'])
def mis(m):
    data = acumulado.get(m.from_user.id)
    if not data:
        bot.reply_to(m, "No tienes jugadas acumuladas.\nVe a /start y dale JUGAR", reply_markup=boton_atras())
    else:
        bot.reply_to(m, f"📋 Tus jugadas:\n{data['texto']}\n💵 Total: ${data['total']}", reply_markup=boton_atras())

@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    if c.data == "menu":
        bot.edit_message_text(BIENVENIDA, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=menu_principal())
    elif c.data == "jugar":
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ ATRÁS", callback_data="menu"))
        bot.edit_message_text(
"🎲 *PARA JUGAR - MUY FÁCIL:*\n"
"━━━━━━━━━━━━\n"
"Escribe en el chat así:\n"
"`número cantidad tipo`\n\n"
"Ejemplo:\n"
"`12 100 fijo`\n"
"`45 200 corrido`\n\n"
"⚠️ Si pones varios se suman solos.",
            c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
    elif c.data == "reglas":
        bot.edit_message_text(
"📖 *REGLAS FLORIDA*\n"
"━━━━━━━━━━━━\n"
"🎯 Fijo: *80 CUP* x $1\n"
"🔄 Corrido: *20 CUP* x $1\n"
"💵 Apuesta mínima $10\n"
"💵 Máxima $500 por número\n"
"❌ No se edita jugada\n"
"✅ Se paga al momento de salir la tirada",
            c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=boton_atras())
    elif c.data == "pago":
        bot.edit_message_text(
f"💳 *DATOS DE PAGO*\n"
"━━━━━━━━━━━━\n"
"💳 Tarjeta: `{TARJETA}`\n"
"📱 Tel: `{TELEFONO}`\n\n"
"⚠️ Envía captura después de jugar",
            c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=boton_atras())
    elif c.data == "ver_ganador":
        fecha=get_fecha()
        dia=resultados_hoy["dia"]; noche=resultados_hoy["noche"]
        txt=f"🦩 *TIRADA FLORIDA - {fecha}*\n━━━━━━━━━━━━\n"
        txt+=f"☀️ DÍA 1:35 PM\n🎯 Fijo: `{dia['fijo']}`\n🔄 C1: `{dia['c1']}` C2: `{dia['c2']}`\n━━━━━━━━━━━━\n" if dia else "☀️ DÍA: ⏳ Esperando\n━━━━━━━━━━━━\n"
        txt+=f"🌙 NOCHE 9:50 PM\n🎯 Fijo: `{noche['fijo']}`\n🔄 C1: `{noche['c1']}` C2: `{noche['c2']}`" if noche else "🌙 NOCHE: ⏳ Esperando"
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔄 Actualizar", callback_data="ver_ganador"), InlineKeyboardButton("⬅️ ATRÁS", callback_data="menu"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
    elif c.data.startswith("aprobar_") or c.data.startswith("rechazar_"):
        if c.from_user.id!= ADMIN_ID: return
        uid = int(c.data.split("_")[1])
        if "aprobar" in c.data:
            acumulado.pop(uid, None); pendientes.pop(uid, None)
            bot.send_message(uid, "✅ *Tu jugada fue APROBADA* ✅\nMucha suerte! 🍀", parse_mode="Markdown")
            bot.edit_message_text(f"✅ Aprobado {uid}", c.message.chat.id, c.message.message_id)
        else:
            acumulado.pop(uid, None); pendientes.pop(uid, None)
            bot.send_message(uid, "❌ Jugada rechazada. Verifica la captura.")
            bot.edit_message_text(f"❌ Rechazado {uid}", c.message.chat.id, c.message.message_id)

@bot.message_handler(commands=['ganador'])
def ganador(m):
    fecha=get_fecha(); dia=resultados_hoy["dia"]; noche=resultados_hoy["noche"]
    txt=f"🦩 *FLORIDA - {fecha}*\n"
    txt+=f"Fijo DIA: {dia['fijo']} | C1:{dia['c1']} C2:{dia['c2']}\n" if dia else "DIA: esperando\n"
    txt+=f"Fijo NOCHE: {noche['fijo']} | C1:{noche['c1']} C2:{noche['c2']}" if noche else "NOCHE: esperando"
    bot.send_message(m.chat.id, txt, parse_mode="Markdown", reply_markup=boton_atras())

@bot.message_handler(commands=['set_dia'])
def set_dia(m):
    if not es_admin(m): return
    try:
        _, f, c1, c2 = m.text.split()
        resultados_hoy["dia"] = {"fijo":f.zfill(2),"c1":c1.zfill(2),"c2":c2.zfill(2)}
        bot.reply_to(m, f"✅ DIA {f} {c1} {c2} guardado")
    except: bot.reply_to(m, "Usa: /set_dia 13 20 28")

@bot.message_handler(commands=['set_noche'])
def set_noche(m):
    if not es_admin(m): return
    try:
        _, f, c1, c2 = m.text.split()
        resultados_hoy["noche"] = {"fijo":f.zfill(2),"c1":c1.zfill(2),"c2":c2.zfill(2)}
        bot.reply_to(m, f"✅ NOCHE {f} {c1} {c2} guardado")
        acumulado.clear()
    except: bot.reply_to(m, "Usa: /set_noche 45 12 89")

@bot.message_handler(func=lambda m: True, content_types=['text'])
def jugada(m):
    if m.text.startswith('/'): return
    if not horario_abierto():
        bot.reply_to(m, "⏰ Cerrado. Horario 9AM-1PM y 3PM-9PM", reply_markup=boton_atras())
        return
    match = re.findall(r'(\d{1,2})\s+(\d+)\s*(fijo|corrido)?', m.text.lower())
    if not match:
        bot.reply_to(m, "❌ Formato mal. Ej: `12 100 fijo`", parse_mode="Markdown", reply_markup=boton_atras())
        return
    texto=""; total=0
    for num,cant,tipo in match:
        tipo = tipo or "fijo"
        texto+=f"{num.zfill(2)} - ${cant} {tipo}\n"
        total+=int(cant)

    uid=m.from_user.id
    if uid in acumulado:
        texto = acumulado[uid]['texto'] + texto
        total = acumulado[uid]['total'] + total
    acumulado[uid]={"texto":texto,"total":total}

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Ya transferí - Enviar captura", callback_data="jugar"))
    bot.reply_to(m,
f"🧾 *TICKET PRE-RESERVA*\n"
f"━━━━━━━━━━━━\n"
f"{texto}\n"
f"💵 Total a pagar: *${total}*\n"
f"━━━━━━━━━━━━\n"
f"💳 `{TARJETA}`\n"
f"📱 `{TELEFONO}`\n\n"
f"👉 Ahora envía la CAPTURA de la transferencia",
    parse_mode="Markdown", reply_markup=kb)
    pendientes[uid]=True

@bot.message_handler(content_types=['photo'])
def foto(m):
    uid=m.from_user.id
    if uid not in acumulado:
        bot.reply_to(m, "Primero manda tu jugada tipo `12 100 fijo`", parse_mode="Markdown")
        return
    data=acumulado[uid]
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("✅ Aprobar", callback_data=f"aprobar_{uid}"), InlineKeyboardButton("❌ Rechazar", callback_data=f"rechazar_{uid}"))
    bot.forward_message(ADMIN_ID, m.chat.id, m.message_id)
    bot.send_message(ADMIN_ID,
f"🔔 Nueva jugada de @{m.from_user.username or uid} ID:{uid}\n"
f"{data['texto']}\nTotal ${data['total']}\nFecha {get_fecha()} {get_hora()}",
    reply_markup=kb)
    bot.reply_to(m, "📤 Captura enviada al admin. Espera aprobación. 🙏", reply_markup=boton_atras())

print("FLORIDA FINAL BONITO CON SISTEMA ON")
bot.infinity_polling()
