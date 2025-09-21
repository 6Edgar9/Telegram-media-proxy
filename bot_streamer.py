# bot que solo soporta videos o documentos


import os
import json
import uuid
import requests
from flask import Flask, request, jsonify, Response, stream_with_context

# --- CONFIG ---
TOKEN = os.environ.get("BOT_TOKEN", "").strip()  # coloca tu token aquí o exporta como variable de entorno
if not TOKEN:
    raise SystemExit("Define la variable de entorno BOT_TOKEN antes de ejecutar")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
MAPPING_FILE = "files_map.json"   # persistencia simple
# ---------------

app = Flask(__name__)

# Cargar o inicializar mapping (uuid -> file_path)
if os.path.exists(MAPPING_FILE):
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        files_map = json.load(f)
else:
    files_map = {}

def save_map():
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(files_map, f, ensure_ascii=False, indent=2)

def send_message(chat_id, text):
    """Envía mensaje simple al chat"""
    requests.post(f"{BASE_URL}/sendMessage", data={
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    """Recibe updates desde Telegram (setWebhook -> POST)"""
    update = request.get_json(force=True)
    # Soportamos message, channel_post, edited_message
    message = update.get("message") or update.get("channel_post") or update.get("edited_message")
    if not message:
        return jsonify({"ok": True})

    chat_id = message["chat"]["id"]

    # Buscar file_id en video, animation o document (si es video)
    file_id = None
    if "video" in message:
        file_id = message["video"]["file_id"]
    elif "animation" in message:
        file_id = message["animation"]["file_id"]
    elif "document" in message and message["document"].get("mime_type","").startswith("video"):
        file_id = message["document"]["file_id"]

    if not file_id:
        send_message(chat_id, "Por favor, envía un archivo de video (video o documento con vídeo).")
        return jsonify({"ok": True})

    # 1) obtener file_path con getFile
    r = requests.get(f"{BASE_URL}/getFile", params={"file_id": file_id}, timeout=15)
    j = r.json()
    if not j.get("ok"):
        send_message(chat_id, "Error obteniendo archivo desde Telegram.")
        return jsonify({"ok": True})

    file_path = j["result"]["file_path"]

    # 2) guardar mapping con uuid (para no exponer token ni file_path)
    uid = uuid.uuid4().hex
    files_map[uid] = file_path
    save_map()

    # 3) construir URL pública basada en la request (funciona con ngrok o con dominio)
    host = request.url_root.rstrip("/")   # ej. https://abc.ngrok.io
    public_url = f"{host}/stream/{uid}"

    # 4) responder al usuario con el enlace (y código de ejemplo)
    message_text = (
        f"Enlace público generado:\n{public_url}\n\n"
        "Puedes insertar este enlace en tu página con:\n"
        f"<video controls width=\"640\"><source src=\"{public_url}\" type=\"video/mp4\"></video>\n\n"
        "Nota: si quieres que otros lo reproduzcan desde tu web, comparte solo este enlace."
    )
    send_message(chat_id, message_text)
    return jsonify({"ok": True})

@app.route("/stream/<uid>")
def stream(uid):
    """Proxy que descarga el archivo de Telegram y lo reenvía al cliente sin exponer el token."""
    file_path = files_map.get(uid)
    if not file_path:
        return "No encontrado", 404

    telegram_file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"

    # Reenviar cabecera Range (si existe) para permitir seeking
    headers = {}
    range_header = request.headers.get("Range")
    if range_header:
        headers["Range"] = range_header

    r = requests.get(telegram_file_url, headers=headers, stream=True, timeout=30)

    # Propagar algunos headers útiles
    response_headers = {}
    for h in ("Content-Type", "Content-Range", "Accept-Ranges", "Content-Length", "Content-Disposition"):
        if h in r.headers:
            response_headers[h] = r.headers[h]

    return Response(stream_with_context(r.iter_content(chunk_size=8192)), status=r.status_code, headers=response_headers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
