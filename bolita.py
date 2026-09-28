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

BIENVENIDA = (
"🎱🔥 *¡BIENVENIDOS A JUGAR LA LOTERÍA DE LA FLORIDA!* 🔥🦩\n"
"━━━━━━━━━━━━━━━━━━━━\n"
"💎 *BOLITA RECOGIDA.FLORIDA* 💎\n"
"━━━━━━━━━━━━━━━━━━━━\n"
"💰 *PAGOS:*\n"
"🎯 FIJO *80 CUP* x $1 (Tope $200)\n"
"🔄 CORRIDO *20 CUP* x $1 (Tope $400)\n"
"━━━━━━━━━━━━━━━━━━━━\n"
"🕘 9AM-1PM y 3PM-9PM\n"
"✍️ `20-10` | `20-50-10` | `10/19=10`\n"
"━━━━━━━━━━━━━━━━━━━━\n"
)

try: bot.set_my_commands([BotCommand("start","🎱 Menú"), BotCommand("ganador","🦩 Ver tirada")])
except: pass

@bot.message_handler(commands=['start'])
def start(m): bot.send_message(m.chat.id, BIENVENIDA, parse_mode="Markdown", reply_markup=menu_principal())

@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    if c.data == "menu": bot.edit_message_text(BIENVENIDA, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=menu_principal())
    elif c.data == "jugar":
        kb=InlineKeyboardMarkup(); kb.add(InlineKeyboardButton("⬅️ ATRÁS", callback_data="menu"))
        bot.edit_message_text("🎲 *COMO JUGAR:*\n\n`20-10` = 20 fijo 10 (tope fijo 200)\n`20-50-10` = 50 fijo + 10 corrido\n`10/19=10` = línea 10-19 a 10 fijo c/u = $100", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
    elif c.data == "reglas": bot.edit_message_text("📖 *TOPES:*\n🎯 FIJO máx $200 por número\n🔄 CORRIDO máx $400 por número\nSon topes separados.", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=boton_atras())
    elif c.data == "ver_ganador":
        dia=resultados_hoy["dia"]; noche=resultados_hoy["noche"]; txt=f"🦩 *FLORIDA - {get_fecha()}*\n"; txt+=f"☀️ DÍA: {dia['fijo']} {dia['c1']} {dia['c2']}\n" if dia else "☀️ DÍA: ⏳\n"; txt+=f"🌙 NOCHE: {noche['fijo']} {noche['c1']} {noche['c2']}" if noche else "🌙 NOCHE: ⏳"
        kb=InlineKeyboardMarkup(); kb.add(InlineKeyboardButton("🔄 Actualizar", callback_data="ver_ganador"), InlineKeyboardButton("⬅️ ATRÁS", callback_data="menu"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)
    elif c.data.startswith("aprobar_") or c.data.startswith("rechazar_"):
        if c.from_user.id!=ADMIN_ID: return
        uid=int(c.data.split("_")[1])
        if "aprobar" in c.data: acumulado.pop(uid, None); bot.send_message(uid, "✅ APROBADA 🍀"); bot.edit_message_text(f"✅ Aprobado {uid}", c.message.chat.id, c.message.message_id)
        else:
            if uid in acumulado:
                for num,cant,tipo in acumulado[uid]['lineas']:
                    if tipo=="fijo": tope_fijo[num]-=cant
                    else: tope_corrido[num]-=cant
                acumulado.pop(uid, None)
            bot.send_message(uid, "❌ Rechazada"); bot.edit_message_text(f"❌ Rechazado {uid}", c.message.chat.id, c.message.message_id)

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
    jugadas_nuevas = [] # (num, cant, tipo)
    texto_nuevo = ""; total_nuevo = 0

    # 1. LINEA 10/19=10 -> es FIJO por defecto
    lm = re.findall(r'(\d{1,2})\s*/\s*(\d{1,2})\s*=\s*(\d+)', txt)
    if lm:
        for ini_s, fin_s, cant_s in lm:
            ini=int(ini_s); fin=int(fin_s); cant=int(cant_s)
            if abs(fin-ini)!=9: bot.reply_to(m, f"❌ Línea {ini}/{fin} debe ser 10 números", reply_markup=boton_atras()); return
            if ini>fin: ini,fin=fin,ini
            for n in range(ini, fin+1):
                ns=str(n).zfill(2)
                if tope_fijo[ns] + cant > 200:
                    bot.reply_to(m, f"⛔ FIJO *{ns} COMPLETO* Fijo lleva ${tope_fijo[ns]}/200. No cabe línea {ini}/{fin}={cant}", parse_mode="Markdown", reply_markup=boton_atras()); return
            for n in range(ini, fin+1):
                ns=str(n).zfill(2); jugadas_nuevas.append((ns, cant, "fijo"))
            texto_nuevo+=f"LÍNEA {str(ini).zfill(2)}/{str(fin).zfill(2)}={cant} FIJO ${cant} c/u = ${cant*10}\n"; total_nuevo+=cant*10
    else:
        # 2. 20-50-10
        md = re.findall(r'(\d{1,2})\s*-\s*(\d+)\s*-\s*(\d+)', txt)
        if md:
            for num_s, fijo_s, corr_s in md:
                num=num_s.zfill(2); fijo=int(fijo_s); corr=int(corr_s)
                if tope_fijo[num] + fijo > 200:
                    bot.reply_to(m, f"⛔ FIJO *{num} COMPLETO* Fijo ${tope_fijo[num]}/200, intentas {fijo}", parse_mode="Markdown", reply_markup=boton_atras()); return
                if tope_corrido[num] + corr > 400:
                    bot.reply_to(m, f"⛔ CORRIDO *{num} COMPLETO* Corrido ${tope_corrido[num]}/400, intentas {corr}", parse_mode="Markdown", reply_markup=boton_atras()); return
                jugadas_nuevas.append((num, fijo, "fijo")); jugadas_nuevas.append((num, corr, "corrido"))
                texto_nuevo+=f"{num} - {fijo} fijo - {corr} corrido\n"; total_nuevo+=fijo+corr
        else:
            # 3. 20-10 simple es FIJO
            ms = re.findall(r'(\d{1,2})\s*-\s*(\d+)\b', txt)
            if ms:
                for num_s, cant_s in ms:
                    num=num_s.zfill(2); cant=int(cant_s)
                    if tope_fijo[num] + cant > 200:
                        bot.reply_to(m, f"⛔ FIJO *{num} COMPLETO* Fijo ${tope_fijo[num]}/200, quedan ${200-tope_fijo[num]}", parse_mode="Markdown", reply_markup=boton_atras()); return
                    jugadas_nuevas.append((num, cant, "fijo")); texto_nuevo+=f"{num}-{cant} fijo\n"; total_nuevo+=cant
            else:
                # fallback viejo 20 10 fijo / corrido
                mo = re.findall(r'(\d{1,2})\s+(\d+)\s*(fijo|corrido)?', txt)
                if not mo: bot.reply_to(m, "❌ Usa `20-10` o `20-50-10` o `10/19=10`", parse_mode="Markdown", reply_markup=boton_atras()); return
                for num_s, cant_s, tipo in mo:
                    num=num_s.zfill(2); cant=int(cant_s); tipo=tipo or "fijo"
                    if tipo=="fijo" and tope_fijo[num]+cant>200:
                        bot.reply_to(m, f"⛔ FIJO *{num} COMPLETO* ${tope_fijo[num]}/200", parse_mode="Markdown", reply_markup=boton_atras()); return
                    if tipo=="corrido" and tope_corrido[num]+cant>400:
                        bot.reply_to(m, f"⛔ CORRIDO *{num} COMPLETO* ${tope_corrido[num]}/400", parse_mode="Markdown", reply_markup=boton_atras()); return
                    jugadas_nuevas.append((num, cant, tipo)); texto_nuevo+=f"{num}-{cant} {tipo}\n"; total_nuevo+=cant

    if not jugadas_nuevas: return
    for num,cant,tipo in jugadas_nuevas:
        if tipo=="fijo": tope_fijo[num]+=cant
        else: tope_corrido[num]+=cant

    uid=m.from_user.id
    if uid in acumulado:
        texto_final=acumulado[uid]['texto']+texto_nuevo; total_final=acumulado[uid]['total']+total_nuevo; lineas_final=acumulado[uid]['lineas']+jugadas_nuevas
    else:
        texto_final=texto_nuevo; total_final=total_nuevo; lineas_final=jugadas_nuevas
    acumulado[uid]={"texto":texto_final,"total":total_final,"lineas":lineas_final}

    bot.reply_to(m, f"🧾 *TICKET*\n━━━━━━━━━━━━\n{texto_final}\n💵 Total: *${total_final}*\n━━━━━━━━━━━━\n💳 `{TARJETA}`\n📱 `{TELEFONO}`\n\n⚠️ Envía captura", parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def foto(m):
    uid=m.from_user.id
    if uid not in acumulado: bot.reply_to(m, "Primero jugada Ej: 20-10"); return
    data=acumulado[uid]; kb=InlineKeyboardMarkup(row_width=2); kb.add(InlineKeyboardButton("✅ Aprobar", callback_data=f"aprobar_{uid}"), InlineKeyboardButton("❌ Rechazar", callback_data=f"rechazar_{uid}"))
    bot.forward_message(ADMIN_ID, m.chat.id, m.message_id); bot.send_message(ADMIN_ID, f"🔔 {uid}\n{data['texto']}\n${data['total']}\nFijo:{tope_fijo} Corr:{tope_corrido}", reply_markup=kb)
    bot.reply_to(m, "📤 Enviada. Espera aprobación 🙏", reply_markup=boton_atras())

print("TOPES SEPARADOS FIJO 200 CORRIDO 400 ON")
bot.infinity_polling()
