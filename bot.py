import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Configuração
TOKEN = "8400792141:AAEnM-3hW3Quf_uzwXCWbYtfm8ev6tN2pT0" 

# Buscar clima
def buscar_clima(lat, lon):
    """
    Usa a latitude e longitude para pegar a temperatura atual.
    Não precisa de chave de API.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "timezone": "auto"
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        dados = response.json()
        
        if 'current_weather' in dados:
            clima = dados['current_weather']
            temperatura = clima['temperature']
            codigo_clima = clima['weathercode']
            
            condicao = traduzir_codigo_wmo(codigo_clima)
            
            return f"{condicao} {temperatura}°C"
        else:
            return "Clima indisponível"
    except:
        return "Erro ao obter clima"

def traduzir_codigo_wmo(codigo):
    """Códigos WMO da Open-Meteo para texto"""
    if codigo == 0: return "☀️ Céu limpo,"
    if codigo in [1, 2, 3]: return "🌥️ Nublado,"
    if codigo in [45, 48]: return "🌫️ Nevoeiro,"
    if codigo in [51, 53, 55, 61, 63, 65]: return "🌧️ Chuva,"
    if codigo in [80, 81, 82]: return "☔ Pancadas de chuva,"
    if codigo >= 95: return "⛈️ Tempestade,"
    return "🌡️"

# Buscar endereço (Nominatim API)
def buscar_dados_endereco(endereco_usuario):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': endereco_usuario,
        'format': 'json',
        'addressdetails': 1,
        'countrycodes': 'br',
        'limit': 1
    }
    headers = {'User-Agent': 'BotCepWeather/1.0'}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        dados = response.json()

        if not dados:
            return None

        local = dados[0]
        info = local.get('address', {})
        
        # Pega Lat/Lon convertendo para float
        lat = float(local.get('lat'))
        lon = float(local.get('lon'))
        
        # Busca o clima agora que temos a lat/lon
        texto_clima = buscar_clima(lat, lon)
        
        # Monta o texto
        cep = info.get('postcode', 'Sem CEP')
        rua = info.get('road', 'Endereço sem rua')
        bairro = info.get('suburb') or info.get('neighbourhood') or ''
        cidade = info.get('city') or info.get('town') or info.get('municipality')
        estado = info.get('state')

        texto_final = (
            f"📍 **{rua}**\n"
            f"🏘️ {bairro}\n"
            f"🏙️ {cidade} - {estado}\n"
            f"📮 **CEP: `{cep}`**\n"
            f"-------------------\n"
            f"🌡️ **Agora:** {texto_clima}"
        )
        
        return {
            'texto': texto_final,
            'lat': lat,
            'lon': lon
        }

    except Exception as e:
        print(f"Erro: {e}")
        return {'erro': True}

# Handlers do telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Informações para você! 🦅\n\n"
        "Digite o endereço (ex.: Rua Pastor Hugo Gegembauer, Hortolândia) e eu te mostro qual o CEP e como está o tempo lá!",
        parse_mode='Markdown'
    )

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    chat_id = update.effective_chat.id
    
    await context.bot.send_chat_action(chat_id=chat_id, action='find_location')
    
    resultado = buscar_dados_endereco(msg)
    
    if resultado is None:
        await update.message.reply_text("❌ Local não encontrado")
    elif 'erro' in resultado:
        await update.message.reply_text("⚠️ Erro de conexão")
    else:
        # Envia Texto com CEP e Clima
        await update.message.reply_text(resultado['texto'], parse_mode='Markdown')
        
        # Envia Mapa
        await update.message.reply_location(
            latitude=resultado['lat'],
            longitude=resultado['lon']
        )

# Executar
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem))
    
    print("Bot on...")
    app.run_polling()