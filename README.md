# 🚌 CombiBot — Reserva automática de Expreso Castelar

Bot de automatización para realizar reservas diarias en la app móvil de **Expreso Castelar**, usando Appium + Python sobre un emulador Android. Se programa una vez y reserva solo todos los días sin que tengas que hacer nada.

---

## 🎯 ¿Para qué sirve?

La app de Expreso Castelar abre las reservas con anticipación y si no reservás a tiempo te quedás sin lugar. Este bot:

- Se ejecuta automáticamente todos los días a la hora que configures
- Detecta qué día debe reservar según la configuración de cada usuario
- Abre el emulador Android, entra a la app, hace login y completa toda la reserva solo
- Soporta **múltiples usuarios** con distintos recorridos, horarios y paradas
- Si algo falla, reintenta hasta 3 veces automáticamente
- Genera un log detallado de cada ejecución para que puedas ver qué pasó

---

## 🧰 Requisitos previos

Necesitás instalar todo esto antes de poder usar el bot. Seguí el orden.

### 1. Python 3.12+
Descargalo de [python.org](https://www.python.org/downloads/)

> ⚠️ Durante la instalación, marcá la opción **"Add Python to PATH"**

Verificá que quedó instalado:
```bash
python --version
```

### 2. Node.js 18+
Descargalo de [nodejs.org](https://nodejs.org)

Verificá que quedó instalado:
```bash
node --version
```

### 3. Appium
Con Node.js instalado, abrí una terminal y ejecutá:
```bash
npm install -g appium
appium driver install uiautomator2
```

Verificá que quedó instalado:
```bash
appium --version
```

### 4. Android Studio + Emulador
Descargalo de [developer.android.com/studio](https://developer.android.com/studio)

Una vez instalado:
1. Abrí Android Studio → **More Actions** → **Virtual Device Manager**
2. Click en **Create Device**
3. Elegí **Pixel 6** → Next
4. Elegí **API 36** (descargalo si no lo tenés) → Next → Finish
5. Anotá el nombre del AVD que creaste (lo vas a necesitar en la configuración)

> ⚠️ Asegurate de que `adb` esté en el PATH. Normalmente está en `C:\Users\TU_USUARIO\AppData\Local\Android\Sdk\platform-tools`

Verificá:
```bash
adb --version
```

### 5. Instalar la app en el emulador
1. Iniciá el emulador desde Android Studio
2. Descargá el APK de Expreso Castelar
3. Arrastrá el APK al emulador o instalalo con:
```bash
adb install ruta\al\archivo.apk
```

### 6. ChromeDriver
El emulador usa Chrome internamente para las vistas web de la app. Necesitás una versión compatible.

1. Iniciá el emulador
2. Abrí Chrome en el emulador y fijate la versión (Configuración → Acerca de Chrome)
3. Descargá el ChromeDriver correspondiente de [chromedriver.chromium.org](https://chromedriver.chromium.org/downloads)
4. Descomprimilo y guardá `chromedriver.exe` en la carpeta del proyecto

### 7. Librerías Python
```bash
pip install Appium-Python-Client selenium
```

---

## 📁 Estructura del proyecto

```
Appium/
├── Combi.py                  # Script principal del bot
├── usuarios_ejemplo.json     # Ejemplo de configuración (copialo y renombralo)
├── usuarios.json             # Tu archivo real con tus datos (NO subir a git)
├── README.md                 # Este archivo
├── .gitignore                # Archivos que git ignora
└── chromedriver-win64/       # ChromeDriver (NO incluido en el repo, descargarlo)
    └── chromedriver.exe
```

---

## ⚙️ Configuración paso a paso

### Paso 1 — Cloná el repositorio
```bash
git clone https://github.com/tuusuario/combibot.git
cd combibot
```

### Paso 2 — Configurá las rutas en `Combi.py`

Abrí `Combi.py` y editá la sección `CONFIG` al principio del archivo:

```python
# ----------------- CONFIG -----------------
CHROMEDRIVER       = r"C:\TuRuta\chromedriver.exe"         # Ruta al chromedriver.exe
USUARIOS_JSON      = r"C:\TuRuta\usuarios.json"            # Ruta a tu usuarios.json
LOG_FILE           = r"C:\TuRuta\combi_log.txt"            # Donde se guarda el log
EMULATOR_PATH      = r"C:\TuRuta\emulator.exe"             # Ruta al emulador de Android
AVD_NAME           = "Nombre_de_tu_AVD"                    # Nombre del AVD que creaste
NODE_PATH          = r"C:\TuRuta\node.exe"                 # Ruta a node.exe
APPIUM_CLI         = r"C:\TuRuta\appium\build\lib\main.js" # Ruta al main.js de appium
LOCK_FILE          = r"C:\TuRuta\combi.lock"               # Archivo de lock
APAGAR_AL_TERMINAR = True  # True = apaga la PC al terminar, False = no apaga
```

**¿Dónde están esas rutas?** Podés encontrarlas así:

- `node.exe` → en la terminal: `where node`
- `appium main.js` → en la terminal: `where appium` y navegá hasta la carpeta
- `emulator.exe` → normalmente en `C:\Users\TU_USUARIO\AppData\Local\Android\Sdk\emulator\emulator.exe`
- `AVD_NAME` → es el nombre que aparece en el Virtual Device Manager de Android Studio

### Paso 3 — Creá tu `usuarios.json`

Copiá el archivo de ejemplo:
```bash
copy usuarios_ejemplo.json usuarios.json
```

Abrí `usuarios.json` y completá con tus datos reales:

```json
[
  {
    "email": "tuemail@gmail.com",
    "password": "tupassword",
    "dias": [3],
    "recorrido": "CASTELAR POR BAJO",
    "horario": "07:45",
    "parada": "2DA RIVADAVIA 19907",
    "pago": "Efectivo"
  }
]
```

**¿Qué significa cada campo?**

| Campo | Descripción |
|---|---|
| `email` | Email con el que entrás a la app |
| `password` | Contraseña de la app |
| `dias` | Días de la semana a reservar (ver tabla abajo) |
| `recorrido` | Nombre exacto del recorrido como aparece en la app |
| `horario` | Horario exacto en formato `HH:MM` |
| `parada` | Nombre exacto de la parada como aparece en la app |
| `pago` | Forma de pago: `Efectivo` u otras opciones de la app |

**Tabla de días:**

| Número | Día |
|---|---|
| 0 | Lunes |
| 1 | Martes |
| 2 | Miércoles |
| 3 | Jueves |
| 4 | Viernes |
| 5 | Sábado |
| 6 | Domingo |

> 💡 Podés poner varios días: `"dias": [0, 2, 4]` reserva lunes, miércoles y viernes.
> 💡 Podés poner varios usuarios en el mismo archivo, uno por cada persona que quiera reservar.

---

## 🤖 ¿Cómo funciona la lógica de días?

El script se ejecuta todos los días y reserva para el **día siguiente** según la configuración de cada usuario.

**Ejemplo:** Si hoy es **viernes** y un usuario tiene `"dias": [3]` (jueves), el script reserva para el **jueves de la semana siguiente**.

---

## 🚀 Programar la ejecución automática (Task Scheduler)

Para que el bot corra solo todos los días sin que tengas que hacer nada:

1. Creá un archivo `reservar combi.bat` con este contenido (editá las rutas):

```bat
@echo off
set PYTHON=C:\TuRuta\python.exe
set SCRIPT=C:\TuRuta\Combi.py
set TASK_NAME=CombiBot

schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
schtasks /create /tn "%TASK_NAME%" /tr "\"%PYTHON%\" \"%SCRIPT%\"" /sc DAILY /st 00:05 /f /it

if %ERRORLEVEL% == 0 (
    echo [OK] Tarea creada exitosamente.
) else (
    echo [ERROR] Ejecuta como Administrador.
)
pause
```

2. Click derecho sobre el .bat → **Ejecutar como administrador**
3. Listo, el bot va a correr todos los días a las 00:05

**Comandos útiles:**
```bash
# Ver estado de la tarea
schtasks /query /tn "CombiBot" /fo LIST /v

# Ejecutar manualmente ahora
schtasks /run /tn "CombiBot"

# Eliminar la tarea
schtasks /delete /tn "CombiBot" /f
```

> ⚠️ La PC tiene que estar **encendida y con sesión iniciada** a la hora que programaste. No funciona con la sesión bloqueada ni la PC apagada.

---

## 📋 Requisitos del sistema en resumen

- ✅ Windows 10/11
- ✅ PC encendida y con sesión activa a la hora programada
- ✅ Conexión a internet
- ✅ Emulador Android configurado con la app instalada

---

## 📝 Logs

Cada ejecución genera entradas en `combi_log.txt`:

```
2026-03-27 00:05:01 [INFO] ✔ Emulador listo.
2026-03-27 00:05:08 [INFO] ✔ Pantalla principal cargada.
2026-03-27 00:05:12 [INFO] ✔ Día seleccionado correctamente.
2026-03-27 00:05:15 [INFO] ✔ Recorrido clickeado: CASTELAR POR BAJO
2026-03-27 00:05:20 [INFO] ✔ Reserva completada para usuario@gmail.com el 2026-03-28.
```

Si algo falla, el log te va a decir exactamente en qué paso falló.

---

## 🔧 Solución de problemas comunes

**El bot dice "Ya hay una instancia corriendo"**
→ Borrá el archivo `combi.lock` de la carpeta del proyecto y volvé a ejecutar.

**No encuentra el emulador**
→ Verificá que `EMULATOR_PATH` y `AVD_NAME` en `Combi.py` sean correctos.

**Falla en el login**
→ Verificá que el email y password en `usuarios.json` sean correctos y que la app esté instalada en el emulador.

**Falla al seleccionar el horario**
→ El horario en `usuarios.json` debe ser exactamente igual a como aparece en la app, incluyendo los dos puntos (ejemplo: `07:45`).

**La tarea del Task Scheduler no corre**
→ Verificá que la PC esté encendida y con sesión activa. Ejecutá el .bat como Administrador.

---

## ⚠️ Notas de seguridad

- Si `APAGAR_AL_TERMINAR = True`, tenés 60 segundos para cancelar el apagado con `shutdown /a`

---

## 🤝 Contribuciones

Pull requests bienvenidos. Para cambios grandes, abrí un issue primero.

---

## 📄 Licencia

MIT
