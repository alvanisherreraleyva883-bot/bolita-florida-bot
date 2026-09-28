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
tope_fijo = {str(i).zfill(2): 0 for i in range(100)}
tope_corrido = {str(i).zfill(2): 0 for i in range(100)}

def get_fecha(): return datetime.now(zona).strftime("%d/%m/%Y")
def es_admin(m): return m.from_user.id == ADMIN_ID or m.chat.id == CANAL_ADMIN_ID
def horario_abierto():
    h = datetime.now(zona).hour + datetime.now(zona).minute/60
    return (9 <= h < 13.1) or (15 <= h < 21.1)

def menu_principal():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🎲 JUGAR AHORA", callback_data="jugar"), InlineKeyboardButton("🦩 VER TIRADA FLORIDA", callback_data="ver_ganador"), InlineKeyboardButton("📖 REGLAS Y PAGOS", callback_data="reglas"))
    return kb
def boton_atras():
    kb = InlineKeyboardMarkup(); kb.add(InlineKeyboardButton("⬅️ ATRÁS AL MENÚ", callback_data="menu")); return kb

# 1. CARTEL IGUALITO A LA FOTO 1 - NO SE TOCA
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
"`10-10` fijo\n"
"`10-50-10` fijo y corrido\n"
"`50/59=20` línea\n"
"━━━━━━━━━━━━━━━━━━━━\n"
"👇 Toca un botón para empezar 👇"
)

try: bot.set_my_commands([BotCommand("start","🎱 Menú"), BotCommand("ganador","🦩 Ver tirada")])
except: pass

@bot.message_handler(commands=['start'])
def start(m): bot.send_message(m.chat.id, BIENVENIDA, parse_mode="Markdown", reply_markup=menu_principal())

@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    if c.data == "menu":
        bot.edit_message_text(BIENVENIDA, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=menu_principal())
    elif c.data == "jugar":
        # 2. MENSAJE BONITO - FOTO 2
        kb=InlineKeyboardMarkup(); kb.add(InlineKeyboardButton("⬅️ ATRÁS", callback_data="menu"))
        bot.edit_message_text(
"✨ *HAGA SU JUGADA* ✨\n"
"━━━━━━━━━━━━\n"
"Ejemplo:\n"
"`10-10` para fijo\n"
"`10-50-10` para fijo y corrido\n"
"`50/59=20` para líneas\n"
"━━━━━━━━━━━━\n"
"💡 Línea es del 50 al 59 a 20 pesos c/u = $200 total",
            c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
    elif c.data == "reglas":
        bot.edit_message_text("📖 *REGLAS*\n🎯 FIJO 80 CUP x $1 - Tope $200\n🔄 CORRIDO 20 CUP x $1 - Tope $400", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=boton_atras())
    elif c.data == "ver_ganador":
        dia=resultados_hoy["dia"]; noche=resultados_hoy["noche"]; txt=f"🦩 *FLORIDA - {get_fecha()}*\n"; txt+=f"☀️ DÍA: {dia['fijo']} {dia['c1']} {dia['c2']}\n" if dia else "☀️ DÍA: ⏳\n"; txt+=f"🌙 NOCHE: {noche['fijo']} {noche['c1']} {noche['c2']}" if noche else "🌙 NOCHE: ⏳"
        kb=InlineKeyboardMarkup(); kb.add(InlineKeyboardButton("🔄 Actualizar", callback_data="ver_ganador"), InlineKeyboardButton("⬅️ ATRÁS", callback_data="menu"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
    elif c.data.startswith("aprobar_") or c.data.startswith("rechazar_"):
        if c.from_user.id!=ADMIN_ID: return
        uid=int(c.data.split("_")[1])
        # FIX 1: NO BORRAR LA JUGADA, SOLO AGREGAR ESTADO
        if "aprobar" in c.data:
            acumulado.pop(uid, None)
            bot.send_message(uid, "✅ *Su jugada ha sido aprobada, mucha suerte* 🍀\nGracias por jugar en BOLITA RECOGIDA.FLORIDA 💎", parse_mode="Markdown")
            try:
                texto_original = c.message.text
                bot.edit_message_text(f"{texto_original}\n\n✅ *APROBADA*", c.message.chat.id, c.message.message_id, parse_mode="Markdown")
            except:
                bot.edit_message_text(f"✅ APROBADA - {uid}", c.message.chat.id, c.message.message_id)
        else:
            if uid in acumulado:
                for num,cant,tipo in acumulado[uid]['lineas']:
                    if tipo=="fijo": tope_fijo[num]-=cant
                    else: tope_corrido[num]-=cant
                acumulado.pop(uid, None)
            bot.send_message(uid, "❌ *Su jugada ha sido rechazada.* Contacte al admin.", parse_mode="Markdown")
            try:
                texto_original = c.message.text
                bot.edit_message_text(f"{texto_original}\n\n❌ *RECHAZADA*", c.message.chat.id, c.message.message_id, parse_mode="Markdown")
            except:
                bot.edit_message_text(f"❌ RECHAZADA - {uid}", c.message.chat.id, c.message.message_id)

@bot.message_handler(commands=['ganador'])
def ganador(m):
    dia=resultados_hoy["dia"]; noche=resultados_hoy["noche"]; txt=f"🦩 {get_fecha()}\n"; txt+=f"DIA: {dia['fijo']} {dia['c1']} {dia['c2']}\n" if dia else "DIA: ---\n"; txt+=f"NOCHE: {noche['fijo']} {noche['c1']} {noche['c2']}" if noche else "NOCHE: ---"
    bot.send_message(m.chat.id, txt, parse_mode="Markdown", reply_markup=boton_atras())
@bot.message_handler(commands=['set_dia'])
def set_dia(m):
    if not es_admin(m): return
    try: _, f,c1,c2=m.text.split(); resultados_hoy["dia"]={"fijo":f.zfill(2),"c1":c1.zfill(2),"c2":c2.zfill(2)}; bot.reply_to(m, f"✅ DIA {f}")
    except: pass
@bot.message_handler(commands=['set_noche'])
def set_noche(m):
    if not es_admin(m): return
    try: _, f,c1,c2=m.text.split(); resultados_hoy["noche"]={"fijo":f.zfill(2),"c1":c1.zfill(2),"c2":c2.zfill(2)}; bot.reply_to(m, f"✅ NOCHE {f} - topes reset"); tope_fijo.update({str(i).zfill(2):0 for i in range(100)}); tope_corrido.update({str(i).zfill(2):0 for i in range(100)}); acumulado.clear()
    except: pass

@bot.message_handler(func=lambda m: True, content_types=['text'])
def jugada(m):
    if m.text.startswith('/'): return
    if not horario_abierto(): bot.reply_to(m, "⏰ Cerrado 9AM-1PM y 3PM-9PM", reply_markup=boton_atras()); return
    txt = m.text.lower().strip()
    jugadas_nuevas = []
    texto_nuevo = ""; total_nuevo = 0

    linea = re.search(r'(\d{1,2})\s*/\s*(\d{1,2})\s*=\s*(\d+)', txt)
    if linea:
        ini=int(linea.group(1)); fin=int(linea.group(2)); cant=int(linea.group(3))
        if abs(fin-ini)!=9: bot.reply_to(m, "❌ La línea debe ser 10 números. Ej: 50/59=20", reply_markup=boton_atras()); return
        if ini>fin: ini,fin=fin,ini
        for n in range(ini, fin+1):
            ns=str(n).zfill(2)
            if tope_fijo[ns] + cant > 200:
                bot.reply_to(m, f"⛔ FIJO *{ns} COMPLETO* lleva ${tope_fijo[ns]}/200. Quedan ${200-tope_fijo[ns]}", parse_mode="Markdown", reply_markup=boton_atras()); return
        for n in range(ini, fin+1):
            ns=str(n).zfill(2); jugadas_nuevas.append((ns, cant, "fijo"))
        texto_nuevo = f"LÍNEA {str(ini).zfill(2)}/{str(fin).zfill(2)}={cant} = ${cant} c/u = ${cant*10}\n"
        total_nuevo = cant*10
    else:
        doble = re.search(r'(\d{1,2})\s*-\s*(\d+)\s*-\s*(\d+)', txt)
        if doble:
            num=doble.group(1).zfill(2); fijo=int(doble.group(2)); corr=int(doble.group(3))
            if tope_fijo[num] + fijo > 200: bot.reply_to(m, f"⛔ FIJO *{num}* completo Fijo ${tope_fijo[num]}/200", parse_mode="Markdown", reply_markup=boton_atras()); return
            if tope_corrido[num] + corr > 400: bot.reply_to(m, f"⛔ CORRIDO *{num}* completo Corrido ${tope_corrido[num]}/400", parse_mode="Markdown", reply_markup=boton_atras()); return
            jugadas_nuevas.append((num, fijo, "fijo")); jugadas_nuevas.append((num, corr, "corrido"))
            texto_nuevo = f"{num} - {fijo} fijo - {corr} corrido\n"; total_nuevo = fijo+corr
        else:
            simple = re.search(r'(\d{1,2})\s*-\s*(\d+)$', txt)
            if not simple: simple = re.search(r'(\d{1,2})\s*-\s*(\d+)\b', txt)
            if not simple:
                bot.reply_to(m, "❌ Formato mal. Usa:\n`10-10`\n`10-50-10`\n`50/59=20`", parse_mode="Markdown", reply_markup=boton_atras()); return
            num=simple.group(1).zfill(2); cant=int(simple.group(2))
            if tope_fijo[num] + cant > 200: bot.reply_to(m, f"⛔ FIJO *{num}* completo ${tope_fijo[num]}/200 quedan ${200-tope_fijo[num]}", parse_mode="Markdown", reply_markup=boton_atras()); return
            jugadas_nuevas.append((num, cant, "fijo")); texto_nuevo = f"{num}-{cant} fijo\n"; total_nuevo = cant

    for num,cant,tipo in jugadas_nuevas:
        if tipo=="fijo": tope_fijo[num]+=cant
        else: tope_corrido[num]+=cant

    uid=m.from_user.id
    if uid in acumulado:
        texto_final=acumulado[uid]['texto']+texto_nuevo; total_final=acumulado[uid]['total']+total_nuevo; lineas_final=acumulado[uid]['lineas']+jugadas_nuevas
    else:
        texto_final=texto_nuevo; total_final=total_nuevo; lineas_final=jugadas_nuevas
    acumulado[uid]={"texto":texto_final,"total":total_final,"lineas":lineas_final}

    bot.reply_to(m,
f"🧾 *TICKET CONFIRMADO*\n"
f"━━━━━━━━━━━━\n"
f"{texto_final}\n"
f"💵 Total a pagar: *${total_final}*\n"
f"━━━━━━━━━━━━\n"
f"💳 *Transfiera a:*\n`{TARJETA}`\n"
f"📱 *Confirme al:*\n`{TELEFONO}`\n"
f"━━━━━━━━━━━━\n"
f"⚠️ *OBLIGATORIO enviar captura de Transfermóvil*\n"
f"🛡️ No se aceptan capturas editadas o falsas.\n"
f"Jugada 100% segura con BOLITA RECOGIDA.FLORIDA",
parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def foto(m):
    uid=m.from_user.id
    if uid not in acumulado: bot.reply_to(m, "Primero manda tu jugada. Ej: 10-10"); return
    data=acumulado[uid]
    nombre = f"@{m.from_user.username}" if m.from_user.username else m.from_user.first_name
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("✅ Aprobar", callback_data=f"aprobar_{uid}"), InlineKeyboardButton("❌ Rechazar", callback_data=f"rechazar_{uid}"))

    texto_admin = (
f"🔔 *NUEVA JUGADA*\n"
f"━━━━━━━━━━━━\n"
f"👤 Usuario: {nombre}\n"
f"🆔 ID: `{uid}`\n"
f"━━━━━━━━━━━━\n"
f"{data['texto']}\n"
f"💵 Total: *${data['total']}*\n"
f"━━━━━━━━━━━━"
    )
    bot.forward_message(CANAL_ADMIN_ID, m.chat.id, m.message_id)
    bot.send_message(CANAL_ADMIN_ID, texto_admin, parse_mode="Markdown", reply_markup=kb)
    # FIX 2 y 3: SIN BOTON ATRAS Y MENSAJE NUEVO
    bot.reply_to(m, "📤 *Captura enviada, por favor espere un momento que su jugada sea verificada y aprobada. Gracias por preferirnos* 🙏", parse_mode="Markdown")

print("FIX FINAL - APROBACION NO BORRA")
bot.infinity_polling()
