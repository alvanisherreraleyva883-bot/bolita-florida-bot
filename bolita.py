import os, re, pytz, telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from datetime import datetime

TOKEN = os.getenv("TOKEN") or "PEGA_TU_TOKEN"
ADMIN_ID = 7450751212
CANAL_ADMIN_ID = -1004418942264
TARJETA = "9238-1299-7507-3018"
TELEFONO = "55348244"

bot = telebot.TeleBot(TOKEN)
zona = pytz.timezone('America/Havana')

acumulado = {}
resultados_hoy = {"dia": None, "noche": None}
tope_numeros = {str(i).zfill(2): 0 for i in range(100)}

def get_fecha(): return datetime.now(zona).strftime("%d/%m/%Y")
def es_admin(m): return m.from_user.id == ADMIN_ID or m.chat.id == CANAL_ADMIN_ID
def horario_abierto():
    h = datetime.now(zona).hour + datetime.now(zona).minute/60
    return (9 <= h < 13.1) or (15 <= h < 21.1)

def menu_principal():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🎲 JUGAR AHORA", callback_data="jugar"),
        InlineKeyboardButton("🦩 VER TIRADA FLORIDA", callback_data="ver_ganador"),
        InlineKeyboardButton("📖 REGLAS Y PAGOS", callback_data="reglas")
    )
    return kb

def boton_atras():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⬅️ ATRÁS AL MENÚ", callback_data="menu"))
    return kb

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
"✍️ *EJEMPLO:*\n"
"`12 100 fijo` - un número\n"
"`linea 2 10 fijo` - línea 20 al 29\n"
"`linea 0 50 corrido` - línea 00 al 09\n"
"━━━━━━━━━━━━━━━━━━━━\n"
"👇 Toca un botón para empezar 👇"
)

try:
    bot.set_my_commands([BotCommand("start","🎱 Menú"), BotCommand("ganador","🦩 Ver tirada")])
except: pass

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, BIENVENIDA, parse_mode="Markdown", reply_markup=menu_principal())

@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    if c.data == "menu":
        bot.edit_message_text(BIENVENIDA, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=menu_principal())
    elif c.data == "jugar":
        kb = InlineKeyboardMarkup(); kb.add(InlineKeyboardButton("⬅️ ATRÁS", callback_data="menu"))
        bot.edit_message_text(
"🎲 *COMO JUGAR:*\n"
"━━━━━━━━━━━━\n"
"1️⃣ Número suelto:\n"
"`12 100 fijo`\n\n"
"2️⃣ LÍNEA (10 números):\n"
"`linea 2 10 fijo`\n"
"👉 Es del 20 al 29 a 10 c/u = $100 total\n\n"
"`linea 2 50 fijo`\n"
"👉 Del 20 al 29 a 50 c/u = $500 total\n\n"
"Línea 0 = 00-09\nLínea 1 = 10-19\nLínea 2 = 20-29\n... hasta Línea 9 = 90-99",
            c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
    elif c.data == "reglas":
        bot.edit_message_text("📖 *REGLAS*\n🎯 Fijo 80 CUP x $1\n🔄 Corrido 20 CUP x $1\n💵 Máx $200 por número\n📏 Línea = 10 números (ej: 20-29)\nSi un número llega a $200 queda completo ⛔", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=boton_atras())
    elif c.data == "ver_ganador":
        fecha=get_fecha(); dia=resultados_hoy["dia"]; noche=resultados_hoy["noche"]
        txt=f"🦩 *FLORIDA - {fecha}*\n"; txt+=f"☀️ DÍA: Fijo `{dia['fijo']}` C1 `{dia['c1']}` C2 `{dia['c2']}`\n" if dia else "☀️ DÍA: ⏳\n"
        txt+=f"🌙 NOCHE: Fijo `{noche['fijo']}` C1 `{noche['c1']}` C2 `{noche['c2']}`" if noche else "🌙 NOCHE: ⏳"
        kb = InlineKeyboardMarkup(); kb.add(InlineKeyboardButton("🔄 Actualizar", callback_data="ver_ganador"), InlineKeyboardButton("⬅️ ATRÁS", callback_data="menu"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
    elif c.data.startswith("aprobar_") or c.data.startswith("rechazar_"):
        if c.from_user.id!= ADMIN_ID: return
        uid = int(c.data.split("_")[1])
        if "aprobar" in c.data:
            acumulado.pop(uid, None)
            bot.send_message(uid, "✅ *APROBADA* 🍀 Mucha suerte!", parse_mode="Markdown")
            bot.edit_message_text(f"✅ Aprobado {uid}", c.message.chat.id, c.message.message_id)
        else:
            if uid in acumulado:
                for num,cant in acumulado[uid]['lineas']: tope_numeros[num] -= cant
                acumulado.pop(uid, None)
            bot.send_message(uid, "❌ Rechazada")
            bot.edit_message_text(f"❌ Rechazado {uid}", c.message.chat.id, c.message.message_id)

@bot.message_handler(commands=['ganador'])
def ganador(m):
    fecha=get_fecha(); dia=resultados_hoy["dia"]; noche=resultados_hoy["noche"]
    txt=f"🦩 *FLORIDA - {fecha}*\n"; txt+=f"DIA: {dia['fijo']} {dia['c1']} {dia['c2']}\n" if dia else "DIA: esperando\n"; txt+=f"NOCHE: {noche['fijo']} {noche['c1']} {noche['c2']}" if noche else "NOCHE: esperando"
    bot.send_message(m.chat.id, txt, parse_mode="Markdown", reply_markup=boton_atras())

@bot.message_handler(commands=['set_dia'])
def set_dia(m):
    if not es_admin(m): return
    try: _, f, c1, c2 = m.text.split(); resultados_hoy["dia"]={"fijo":f.zfill(2),"c1":c1.zfill(2),"c2":c2.zfill(2)}; bot.reply_to(m, f"✅ DIA {f}")
    except: pass

@bot.message_handler(commands=['set_noche'])
def set_noche(m):
    if not es_admin(m): return
    try:
        _, f, c1, c2 = m.text.split(); resultados_hoy["noche"]={"fijo":f.zfill(2),"c1":c1.zfill(2),"c2":c2.zfill(2)}
        bot.reply_to(m, f"✅ NOCHE {f} - Topes reiniciados"); tope_numeros.update({str(i).zfill(2):0 for i in range(100)}); acumulado.clear()
    except: pass

@bot.message_handler(func=lambda m: True, content_types=['text'])
def jugada(m):
    if m.text.startswith('/'): return
    if not horario_abierto():
        bot.reply_to(m, "⏰ Cerrado. 9AM-1PM y 3PM-9PM", reply_markup=boton_atras()); return

    texto_l = m.text.lower()
    texto_ticket = ""
    total = 0
    lineas = []

    # 1. DETECTAR LÍNEAS: linea 2 10 fijo | linea 20 10 fijo | 20-29 10 fijo
    patron_linea = re.findall(r'(?:linea\s+)?(\d{1,2})(?:\s*-\s*\d{1,2})?\s+(\d+)\s*(fijo|corrido)?', texto_l)
    # Pero filtramos: si dice linea, lo tomamos como linea
    if "linea" in texto_l or "línea" in texto_l or re.search(r'\d+\s*-\s*\d+\s+\d+', texto_l):
        # Ejemplo linea 2 10 fijo
        for match in re.finditer(r'linea\s+(\d{1,2})\s+(\d+)\s*(fijo|corrido)?', texto_l):
            num_linea = int(match.group(1))
            cant_por_num = int(match.group(2))
            tipo = match.group(3) or "fijo"
            # Si pone 20, 30 etc, convertir a linea 2, 3
            if num_linea >= 10:
                num_linea = num_linea // 10
            if num_linea <0 or num_linea>9: continue
            inicio = num_linea*10
            fin = inicio+9

            # Validar tope para los 10 numeros
            for n in range(inicio, fin+1):
                ns = str(n).zfill(2)
                if tope_numeros[ns] + cant_por_num > 200:
                    bot.reply_to(m, f"⛔ Línea {num_linea} no cabe. El {ns} solo le quedan {200-tope_numeros[ns]}", parse_mode="Markdown", reply_markup=boton_atras())
                    return

            for n in range(inicio, fin+1):
                ns = str(n).zfill(2)
                tope_numeros[ns] += cant_por_num
                lineas.append((ns, cant_por_num))

            subtotal_linea = cant_por_num * 10
            texto_ticket += f"LÍNEA {num_linea} ({str(inicio).zfill(2)}-{str(fin).zfill(2)}) - ${cant_por_num} c/u {tipo} = ${subtotal_linea}\n"
            total += subtotal_linea

        # Soporte para 20-29 50 fijo
        for match in re.finditer(r'(\d{1,2})\s*-\s*(\d{1,2})\s+(\d+)\s*(fijo|corrido)?', texto_l):
            ini = int(match.group(1)); fin = int(match.group(2)); cant = int(match.group(3)); tipo = match.group(4) or "fijo"
            if fin-ini!= 9: continue # solo lineas de 10
            if "linea" in texto_l: continue # ya contado arriba para no duplicar
            for n in range(ini, fin+1):
                ns = str(n).zfill(2)
                if tope_numeros[ns] + cant > 200:
                    bot.reply_to(m, f"⛔ Línea {ini}-{fin} no cabe. El {ns} solo le quedan {200-tope_numeros[ns]}", parse_mode="Markdown", reply_markup=boton_atras()); return
            for n in range(ini, fin+1):
                ns = str(n).zfill(2); tope_numeros[ns]+=cant; lineas.append((ns,cant))
            texto_ticket += f"LÍNEA {ini}-{fin} - ${cant} c/u {tipo} = ${cant*10}\n"; total+=cant*10

        if texto_ticket:
            uid=m.from_user.id
            if uid in acumulado:
                texto_ticket = acumulado[uid]['texto'] + texto_ticket
                total = acumulado[uid]['total'] + total
                lineas = acumulado[uid]['lineas'] + lineas
            acumulado[uid]={"texto":texto_ticket,"total":total,"lineas":lineas}
            bot.reply_to(m, f"🧾 *TICKET LÍNEA*\n━━━━━━━━━━━━\n{texto_ticket}\n💵 Total: *${total}*\n━━━━━━━━━━━━\n💳 `{TARJETA}`\n📱 `{TELEFONO}`\n\n⚠️ Transfiere y envía captura", parse_mode="Markdown")
            return

    # 2. SI NO ES LINEA, ES NUMERO NORMAL
    match = re.findall(r'(\d{1,2})\s+(\d+)\s*(fijo|corrido)?', texto_l)
    if not match:
        bot.reply_to(m, "❌ Ej: `12 100 fijo` o `linea 2 10 fijo`", parse_mode="Markdown", reply_markup=boton_atras()); return

    for num,cant,tipo in match:
        num=num.zfill(2); cant=int(cant); tipo=tipo or "fijo"
        if tope_numeros[num] + cant > 200:
            bot.reply_to(m, f"⛔ *Número {num} COMPLETO* - Solo quedan ${200-tope_numeros[num]}", parse_mode="Markdown", reply_markup=boton_atras()); return
        texto_ticket+=f"{num} - ${cant} {tipo}\n"; total+=cant; lineas.append((num,cant))

    for num,cant in lineas: tope_numeros[num]+=cant

    uid=m.from_user.id
    if uid in acumulado:
        texto_ticket = acumulado[uid]['texto'] + texto_ticket
        total = acumulado[uid]['total'] + total
        lineas = acumulado[uid]['lineas'] + lineas
    acumulado[uid]={"texto":texto_ticket,"total":total,"lineas":lineas}

    bot.reply_to(m, f"🧾 *TICKET*\n━━━━━━━━━━━━\n{texto_ticket}\n💵 Total: *${total}*\n━━━━━━━━━━━━\n💳 `{TARJETA}`\n📱 `{TELEFONO}`\n\n⚠️ Haz transferencia y envía captura", parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def foto(m):
    uid=m.from_user.id
    if uid not in acumulado: bot.reply_to(m, "Primero manda jugada"); return
    data=acumulado[uid]
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("✅ Aprobar", callback_data=f"aprobar_{uid}"), InlineKeyboardButton("❌ Rechazar", callback_data=f"rechazar_{uid}"))
    bot.forward_message(ADMIN_ID, m.chat.id, m.message_id)
    bot.send_message(ADMIN_ID, f"🔔 Jugada de {uid}\n{data['texto']}\nTotal ${data['total']}", reply_markup=kb)
    bot.reply_to(m, "📤 Captura enviada. Espera aprobación 🙏", reply_markup=boton_atras())

print("FLORIDA CON LINEAS ON")
bot.infinity_polling()
