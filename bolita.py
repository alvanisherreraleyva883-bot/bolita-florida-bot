import os, re, pytz, telebot, time, logging, threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from datetime import datetime

logging.basicConfig(level=logging.INFO)

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

def resetear_topes():
    tope_fijo.update({str(i).zfill(2):0 for i in range(100)})
    tope_corrido.update({str(i).zfill(2):0 for i in range(100)})
    acumulado.clear()
    return True

def auto_reset_hilo():
    while True:
        try:
            ahora = datetime.now(zona)
            if ahora.hour == 13 and ahora.minute == 36:
                resetear_topes()
                try: bot.send_message(CANAL_ADMIN_ID, "♻️ *AUTO RESET 1:36 PM* - Todos los topes en 0 para la tirada de la noche", parse_mode="Markdown")
                except: pass
                time.sleep(60)
            if ahora.hour == 21 and ahora.minute == 51:
                resetear_topes()
                try: bot.send_message(CANAL_ADMIN_ID, "♻️ *AUTO RESET 9:51 PM* - Todos los topes en 0 para mañana", parse_mode="Markdown")
                except: pass
                time.sleep(60)
            time.sleep(30)
        except: time.sleep(30)

threading.Thread(target=auto_reset_hilo, daemon=True).start()

def menu_principal():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🎲 JUGAR AHORA", callback_data="jugar"), InlineKeyboardButton("🦩 VER TIRADA FLORIDA", callback_data="ver_ganador"), InlineKeyboardButton("📖 REGLAS Y PAGOS", callback_data="reglas"))
    return kb
def boton_atras():
    kb = InlineKeyboardMarkup(); kb.add(InlineKeyboardButton("⬅️ ATRÁS AL MENÚ", callback_data="menu")); return kb

def texto_ganador_bonito():
    dia = resultados_hoy["dia"]
    noche = resultados_hoy["noche"]
    txt = f"🦩 *RESULTADOS FLORIDA - {get_fecha()}* 🦩\n"
    txt += "━━━━━━━━━━━━━━━━━━━━\n\n"
    txt += "☀️ *TIRADA DEL DÍA - 1:35 PM*\n"
    if dia:
        txt += f"🎯 *Fijo:* `{dia['fijo']}`\n"
        txt += f"🔄 *Corridos:* `{dia['c1']}` - `{dia['c2']}`\n"
    else:
        txt += "⏳ *Esperando resultado...*\n"
    txt += "\n━━━━━━━━━━━━━━━━━━━━\n\n"
    txt += "🌙 *TIRADA DE LA NOCHE - 9:50 PM*\n"
    if noche:
        txt += f"🎯 *Fijo:* `{noche['fijo']}`\n"
        txt += f"🔄 *Corridos:* `{noche['c1']}` - `{noche['c2']}`\n"
    else:
        txt += "⏳ *Esperando resultado...*\n"
    txt += "\n━━━━━━━━━━━━━━━━━━━━\n"
    txt += "💎 *BOLITA RECOGIDA.FLORIDA*"
    return txt

def texto_topes(minimo=1):
    txt = f"📊 *TOPES ACTUALES - {get_fecha()}*\n"
    txt += "━━━━━━━━━━━━━━━━━━━━\n"
    hay = False
    topados_fijo = []
    for i in range(100):
        num = str(i).zfill(2)
        val = tope_fijo[num]
        if val >= minimo:
            topados_fijo.append(f"{num}: ${val}/200")
            hay = True
    if topados_fijo:
        txt += "🎯 *FIJOS:*\n"
        for j in range(0, len(topados_fijo), 5):
            txt += " | ".join(topados_fijo[j:j+5]) + "\n"
    else:
        txt += "🎯 *FIJOS:* Ninguno\n"
    txt += "\n━━━━━━━━━━━━━━━━━━━━\n"
    topados_corr = []
    for i in range(100):
        num = str(i).zfill(2)
        val = tope_corrido[num]
        if val >= minimo:
            topados_corr.append(f"{num}: ${val}/400")
            hay = True
    if topados_corr:
        txt += "🔄 *CORRIDOS:*\n"
        for j in range(0, len(topados_corr), 5):
            txt += " | ".join(topados_corr[j:j+5]) + "\n"
    else:
        txt += "🔄 *CORRIDOS:* Ninguno\n"
    if not hay:
        txt += "\n✅ Todo en 0, pueden jugar todo"
    txt += "\n━━━━━━━━━━━━━━━━━━━━"
    return txt

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

try: bot.set_my_commands([BotCommand("start","🎱 Menú"), BotCommand("ganador","🦩 Ver tirada"), BotCommand("reset","♻️ Resetear topes"), BotCommand("topes","📊 Ver topados")])
except: pass

@bot.message_handler(commands=['start'])
def start(m): bot.send_message(m.chat.id, BIENVENIDA, parse_mode="Markdown", reply_markup=menu_principal())

@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    if c.data == "menu":
        bot.edit_message_text(BIENVENIDA, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=menu_principal())
    elif c.data == "jugar":
        kb=InlineKeyboardMarkup(); kb.add(InlineKeyboardButton("⬅️ ATRÁS", callback_data="menu"))
        bot.edit_message_text("✨ *HAGA SU JUGADA* ✨\n━━━━━━━━━━━━\nEjemplo:\n`10-10` para fijo\n`10-50-10` para fijo y corrido\n`50/59=20` para líneas\n━━━━━━━━━━━━\n💡 Línea es del 50 al 59 a 20 pesos c/u = $200 total", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
    elif c.data == "reglas":
        bot.edit_message_text("📖 *REGLAS*\n🎯 FIJO 80 CUP x $1 - Tope $200\n🔄 CORRIDO 20 CUP x $1 - Tope $400", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=boton_atras())
    elif c.data == "ver_ganador":
        kb=InlineKeyboardMarkup(); kb.add(InlineKeyboardButton("🔄 Actualizar", callback_data="ver_ganador"), InlineKeyboardButton("⬅️ ATRÁS", callback_data="menu"))
        bot.edit_message_text(texto_ganador_bonito(), c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
    elif c.data.startswith("aprobar_") or c.data.startswith("rechazar_"):
        if c.from_user.id!=ADMIN_ID: return
        uid=int(c.data.split("_")[1])
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
    bot.send_message(m.chat.id, texto_ganador_bonito(), parse_mode="Markdown", reply_markup=boton_atras())

@bot.message_handler(commands=['set_dia'])
def set_dia(m):
    if not es_admin(m): return
    try:
        _, f,c1,c2=m.text.split()
        resultados_hoy["dia"]={"fijo":f.zfill(2),"c1":c1.zfill(2),"c2":c2.zfill(2)}
        bot.reply_to(m, f"✅ DIA guardado: Fijo {f} Corridos {c1}-{c2}\nRecuerda usar /reset cuando quieras liberar topes")
    except: pass

@bot.message_handler(commands=['set_noche'])
def set_noche(m):
    if not es_admin(m): return
    try:
        _, f,c1,c2=m.text.split()
        resultados_hoy["noche"]={"fijo":f.zfill(2),"c1":c1.zfill(2),"c2":c2.zfill(2)}
        bot.reply_to(m, f"✅ NOCHE guardado: Fijo {f} Corridos {c1}-{c2}\nRecuerda usar /reset cuando quieras liberar topes")
    except: pass

@bot.message_handler(commands=['reset'])
def reset_cmd(m):
    if not es_admin(m): return
    resetear_topes()
    bot.reply_to(m, "♻️ *TODOS LOS TOPES EN 0* - Ya pueden volver a jugar todos los números", parse_mode="Markdown")

@bot.message_handler(commands=['topes'])
def ver_topes(m):
    if not es_admin(m): return
    try:
        partes = m.text.split()
        minimo = int(partes[1]) if len(partes) > 1 else 1
    except:
        minimo = 1
    bot.send_message(m.chat.id, texto_topes(minimo), parse_mode="Markdown")

@bot.message_handler(func=lambda m: True, content_types=['text'])
def jugada(m):
    if m.text.startswith('/'): return
    if not horario_abierto(): bot.reply_to(m, "⏰ Cerrado 9AM-1PM y 3PM-9PM", reply_markup=boton_atras()); return
    txt_original = m.text.strip()
    jugadas_nuevas = []
    texto_nuevo = ""
    total_nuevo = 0
    for match in re.finditer(r'(\d{1,2})\s*/\s*(\d{1,2})\s*=\s*(\d+)', txt_original):
        ini=int(match.group(1)); fin=int(match.group(2)); cant=int(match.group(3))
        if abs(fin-ini)!=9: bot.reply_to(m, f"❌ Línea {match.group(0)} debe ser 10 números. Ej: 10/19=20", reply_markup=boton_atras()); return
        if ini>fin: ini,fin=fin,ini
        for n in range(ini, fin+1):
            ns=str(n).zfill(2)
            if tope_fijo[ns] + cant > 200:
                bot.reply_to(m, f"⛔ FIJO *{ns} COMPLETO* lleva ${tope_fijo[ns]}/200. Quedan ${200-tope_fijo[ns]}", parse_mode="Markdown", reply_markup=boton_atras()); return
        for n in range(ini, fin+1):
            ns=str(n).zfill(2); jugadas_nuevas.append((ns, cant, "fijo"))
        texto_nuevo += f"LÍNEA {str(ini).zfill(2)}/{str(fin).zfill(2)}={cant} = ${cant} c/u = ${cant*10}\n"
        total_nuevo += cant*10
    txt_sin_lineas = re.sub(r'(\d{1,2})\s*/\s*(\d{1,2})\s*=\s*(\d+)', ' ', txt_original)
    for match in re.finditer(r'(\d{1,2})\s*-\s*(\d+)\s*-\s*(\d+)', txt_sin_lineas):
        num=match.group(1).zfill(2); fijo=int(match.group(2)); corr=int(match.group(3))
        if tope_fijo[num] + fijo > 200: bot.reply_to(m, f"⛔ FIJO *{num}* completo ${tope_fijo[num]}/200", parse_mode="Markdown", reply_markup=boton_atras()); return
        if tope_corrido[num] + corr > 400: bot.reply_to(m, f"⛔ CORRIDO *{num}* completo ${tope_corrido[num]}/400", parse_mode="Markdown", reply_markup=boton_atras()); return
        jugadas_nuevas.append((num, fijo, "fijo")); jugadas_nuevas.append((num, corr, "corrido"))
        texto_nuevo += f"{num} - {fijo} fijo - {corr} corrido\n"; total_nuevo += fijo+corr
    txt_sin_dobles = re.sub(r'(\d{1,2})\s*-\s*(\d+)\s*-\s*(\d+)', ' ', txt_sin_lineas)
    for match in re.finditer(r'(\d{1,2})\s*-\s*(\d+)', txt_sin_dobles):
        num=match.group(1).zfill(2); cant=int(match.group(2))
        if tope_fijo[num] + cant > 200: bot.reply_to(m, f"⛔ FIJO *{num}* completo ${tope_fijo[num]}/200 quedan ${200-tope_fijo[num]}", parse_mode="Markdown", reply_markup=boton_atras()); return
        jugadas_nuevas.append((num, cant, "fijo")); texto_nuevo += f"{num}-{cant} fijo\n"; total_nuevo += cant
    if not jugadas_nuevas:
        bot.reply_to(m, "❌ Formato mal. Usa:\n`10-10`\n`10-50-10`\n`50/59=20`", parse_mode="Markdown", reply_markup=boton_atras()); return
    for num,cant,tipo in jugadas_nuevas:
        if tipo=="fijo": tope_fijo[num]+=cant
        else: tope_corrido[num]+=cant
    uid=m.from_user.id
    acumulado[uid]={"texto":texto_nuevo,"total":total_nuevo,"lineas":jugadas_nuevas}
    bot.reply_to(m, f"🧾 *TICKET CONFIRMADO*\n━━━━━━━━━━━━\n{texto_nuevo}\n💵 Total a pagar: *${total_nuevo}*\n━━━━━━━━━━━━\n💳 *Transfiera a:*\n`{TARJETA}`\n📱 *Confirme al:*\n`{TELEFONO}`\n━━━━━━━━━━━━\n⚠️ *OBLIGATORIO enviar captura de Transfermóvil*\n🛡️ No se aceptan capturas editadas o falsas.\nJugada 100% segura con BOLITA RECOGIDA.FLORIDA", parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def foto(m):
    uid=m.from_user.id
    if uid not in acumulado: bot.reply_to(m, "Primero manda tu jugada. Ej: 10-10"); return
    data=acumulado[uid]
    nombre = f"@{m.from_user.username}" if m.from_user.username else m.from_user.first_name
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("✅ Aprobar", callback_data=f"aprobar_{uid}"), InlineKeyboardButton("❌ Rechazar", callback_data=f"rechazar_{uid}"))
    texto_admin = (f"🔔 *NUEVA JUGADA*\n━━━━━━━━━━━━\n👤 Usuario: {nombre}\n🆔 ID: `{uid}`\n━━━━━━━━━━━━\n{data['texto']}\n💵 Total: *${data['total']}*\n━━━━━━━━━━━━")
    bot.forward_message(CANAL_ADMIN_ID, m.chat.id, m.message_id)
    bot.send_message(CANAL_ADMIN_ID, texto_admin, parse_mode="Markdown", reply_markup=kb)
    bot.reply_to(m, "📤 *Captura enviada, por favor espere un momento que su jugada sea verificada y aprobada. Gracias por preferirnos* 🙏", parse_mode="Markdown")

print("BOT SEPARADO GANADOR Y RESET + AUTO RESET + TOPES")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
    except Exception as e:
        print(f"⚠️ Caída: {e} - Reiniciando 5s...")
        time.sleep(5)
