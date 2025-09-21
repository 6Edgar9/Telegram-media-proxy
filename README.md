# Telegram Media Proxy Bot

Servicio en Python (Flask) que recibe **videos** e **imágenes** enviados al bot de Telegram, obtiene el `file_path` vía API, crea un `uid` público y expone `/stream/<uid>` para usar en tu web (`<video>` o `<img>`) **sin exponer el token** del bot.

---

## 0. Requisitos previos
- Token del bot creado con [@BotFather](https://t.me/BotFather).
- Python 3.8+ instalado.
- Conexión a Internet (sin firewall que bloquee `api.telegram.org`).
- Editor de texto (VSCode, nano, Notepad++, etc.).

---

## 1. Código principal
Guarda tu script como `bot_streamer.py` en la raíz del proyecto. El código debe leer el token desde la variable de entorno `BOT_TOKEN` y exponer los endpoints `/webhook` y `/stream/<uid>`.

(Coloca aquí tu `bot_streamer.py` — o guarda el archivo en la misma carpeta donde esté este README.)

---

## 2. Instalación y ejecución — LINUX

### 2.1 Instalar Python y utilidades
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip curl
```

### 2.2 Crear proyecto y entorno virtual
```bash
mkdir -p ~/telegram_videos
cd ~/telegram_videos
python3 -m venv venv
source venv/bin/activate
```

### 2.3 Instalar dependencias (dentro del venv)
```bash
pip install --upgrade pip
pip install flask requests
```

### 2.4 Copiar `bot_streamer.py`
Pega `bot_streamer.py` en `~/telegram_videos/`.

### 2.5 Definir variable de entorno con tu token
Temporal (solo para la sesión actual):
```bash
export BOT_TOKEN="123456789:ABC-DEF..."
```

Persistente (agregar a `~/.bashrc` o `~/.profile`):
```bash
echo 'export BOT_TOKEN="123456789:ABC-DEF..."' >> ~/.bashrc
source ~/.bashrc
```

> **IMPORTANTE:** Reemplaza `123456789:ABC-DEF...` por tu token real.

### 2.6 Ejecutar el bot (modo prueba)
```bash
source venv/bin/activate
python bot_streamer.py
```
Verás `Running on http://0.0.0.0:5000` si se inicia correctamente.

---

## 3. Instalación y ejecución — WINDOWS (PowerShell)

### 3.1 Instalar Python
Descarga e instala Python 3 desde https://www.python.org/downloads/ y marca "Add Python to PATH" durante la instalación.

### 3.2 Crear carpeta y entorno virtual
Abre PowerShell:
```powershell
mkdir C:\telegram_videos
cd C:\telegram_videos
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la ejecución de scripts:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3.3 Instalar dependencias
Con el venv activado:
```powershell
pip install --upgrade pip
pip install flask requests
```

### 3.4 Copiar `bot_streamer.py`
Pega `bot_streamer.py` en `C:\telegram_videos\`.

### 3.5 Definir variable de entorno (temporal)
En la sesión actual:
```powershell
$env:BOT_TOKEN = "123456789:ABC-DEF..."
```

Para guardarlo permanentemente (usuario actual):
```powershell
setx BOT_TOKEN "123456789:ABC-DEF..."
# cierra y abre PowerShell para que surta efecto
```

### 3.6 Ejecutar (modo prueba)
```powershell
cd C:\telegram_videos
.\venv\Scripts\Activate.ps1
python bot_streamer.py
```

---

## 4. Exponer el bot: Cloudflare Tunnel (recomendado)
Cloudflare Tunnel evita abrir puertos y suele ser más fiable/seguro que otras alternativas.

### 4.1 Linux — instalación básica
```bash
curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb
cloudflared --version
```

### 4.2 Windows — descarga e instalación
Descarga el instalador MSI desde la web oficial de Cloudflare y ejecútalo. Luego en PowerShell:
```powershell
cloudflared --version
```

### 4.3 Login y crear túnel
```bash
cloudflared tunnel login
cloudflared tunnel create telegram-bot
```
Esto guardará credenciales en `~/.cloudflared/<UUID>.json`.

### 4.4 Configurar `config.yml` (ejemplo)
Ubicación:
- Linux: `~/.cloudflared/config.yml`
- Windows: `%USERPROFILE%\.cloudflared\config.yml`

Contenido de ejemplo:
```yaml
tunnel: <NOMBRE_O_UUID_DEL_TUNNEL>
credentials-file: /home/tuusuario/.cloudflared/<UUID>.json

ingress:
  - hostname: bot.midominio.com        # opcional: si tienes dominio en Cloudflare
    service: http://localhost:5000
  - service: http_status:404
```

Si no tienes dominio, puedes usar:
```bash
cloudflared tunnel --url http://localhost:5000
```
que te dará una URL `trycloudflare.com`.

### 4.5 Ejecutar el túnel
```bash
cloudflared tunnel run telegram-bot
```

---

## 5. Registrar webhook en Telegram
Con la URL pública (ej.: `https://mi-url.cloudflared.com`):

Usando `curl`:
```bash
curl -F "url=https://mi-url.cloudflared.com/webhook" "https://api.telegram.org/bot<TU_TOKEN>/setWebhook"
```

O en el navegador:
```
https://api.telegram.org/bot<TU_TOKEN>/setWebhook?url=https://mi-url.cloudflared.com/webhook
```

Respuesta esperada:
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

Si recibes `{"ok":false,...}` revisa el mensaje (URL inaccesible o token inválido).

---

## 6. Probar el flujo
1. Envía una **foto** o **video** al bot desde Telegram.  
2. Revisa la consola donde corre `bot_streamer.py` (logs/errores).  
3. El bot responderá con una URL pública tipo: `https://mi-url/stream/<uid>`.  
4. Pégala en el navegador o úsala en tu HTML:

Video:
```html
<video controls width="640">
  <source src="https://mi-url/stream/abcdef123..." type="video/mp4">
</video>
```

Imagen:
```html
<img src="https://mi-url/stream/abcdef123..." width="640" alt="Foto">
```

---

## 7. Errores comunes y cómo resolverlos

- **Failed to establish a new connection: [Errno 101] Network is unreachable**  
  Tu servidor no conecta a `api.telegram.org`. Verifica conexión, DNS y firewall.  
  Prueba: `ping api.telegram.org` y `curl https://api.telegram.org/bot<TOKEN>/getMe`.

- **Webhook devuelve 500 y Flask muestra `did not return a valid response`**  
  Asegúrate de que todas las ramas de `webhook()` realizan un `return` (el ejemplo del repo ya lo hace).

- **`requests` timeout o error al descargar de Telegram**  
  Revisa que el servidor tenga salida HTTPS y que no esté bloqueada por firewall o proxy.

- **Token inválido**  
  Ejecuta: `curl "https://api.telegram.org/bot<TU_TOKEN>/getMe"` y comprueba `ok: true`.

- **Cloudflared no arranca o antivirus lo bloquea**  
  Si Cloudflare presenta problemas en Windows prueba a ejecutar desde PowerShell con permisos o usar la versión oficial MSI.

---

## 8. Ejecutar como servicio / inicio automático

### 8.1 Linux — systemd (ejemplo)
Crea `/etc/systemd/system/bot_streamer.service` con el siguiente contenido:
```ini
[Unit]
Description=Bot Streamer Flask App
After=network.target

[Service]
User=tuusuario
WorkingDirectory=/home/tuusuario/telegram_videos
Environment=BOT_TOKEN=123456789:ABC-DEF...
ExecStart=/home/tuusuario/telegram_videos/venv/bin/python /home/tuusuario/telegram_videos/bot_streamer.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
Luego:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bot_streamer
sudo systemctl start bot_streamer
sudo journalctl -u bot_streamer -f
```
> Recomendación: en vez de escribir el token en el service file, usa `EnvironmentFile=` con un archivo protegido.

### 8.2 Windows — Task Scheduler o nssm
- **Task Scheduler**: crea una tarea que ejecute `python C:\telegram_videos\bot_streamer.py` al iniciar (elige la cuenta con permisos adecuados).  
- **nssm**: instala nssm y crea un servicio que ejecute `C:\telegram_videos\venv\Scripts\python.exe C:\telegram_videos\bot_streamer.py`.

---

## 9. Seguridad y mejoras recomendadas
- **No expongas el token**: nunca incluyas `api.telegram.org/file/bot<TOKEN>/...` en HTML público. El código usa `uid` y proxy para evitarlo.
- **Expiración de enlaces**: guarda timestamp junto al `uid` y rechaza requests antiguas si quieres que caduquen.
- **Autenticación**: añade verificación (JWT, cookies) si los archivos deben ser privados.
- **Cache**: descarga y cachea archivos en tu servidor o en un CDN/S3 para reducir latencia (y evita depender de Telegram).  
- **Límites**: Telegram puede borrar archivos o el `file_path` puede caducar; para producción considera copiar el archivo a tu almacenamiento.

---

#### Dios, Assembly y la Patria
#### Edrem