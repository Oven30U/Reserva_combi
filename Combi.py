from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
#HOLAA
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput

from datetime import date, timedelta
import time
import subprocess
import json
import sys
import logging
import os

PKG = "com.app.reservacombi.expresocastelar"

# ----------------- CONFIG -----------------
PERMISSION_CHECK_LOOPS = 3
LOGIN_MAX_WAIT         = 10
IMPLICIT_WAIT          = 4
WAIT_TIMEOUT           = 15
CHROMEDRIVER           = r"C:\Users\ovenp\OneDrive\Desktop\Appium\chromedriver-win64\chromedriver-win64\chromedriver.exe"
USUARIOS_JSON          = r"C:\Users\ovenp\OneDrive\Desktop\Appium\usuarios.json"
APAGAR_AL_TERMINAR     = True
LOG_FILE               = r"C:\Users\ovenp\OneDrive\Desktop\Appium\combi_log.txt"
EMULATOR_PATH          = r"C:\Users\ovenp\AppData\Local\Android\Sdk\emulator\emulator.exe"
AVD_NAME               = "Pixel_6"
APPIUM_CLI             = r"C:\Users\ovenp\AppData\Roaming\npm\node_modules\appium\build\lib\main.js"
NODE_PATH              = r"C:\Program Files\nodejs\node.exe"
LOCK_FILE              = r"C:\Users\ovenp\OneDrive\Desktop\Appium\combi.lock"
# -----------------------------------------

# =======================================================
# HELPERS
# =======================================================

def configurar_log():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    import builtins
    def print_y_log(*args, **kwargs):
        msg = " ".join(str(a) for a in args)
        logging.info(msg)
    builtins.print = print_y_log


def tap_xy_native(driver, x, y):
    driver.switch_to.context("NATIVE_APP")
    finger = PointerInput("touch", "finger1")
    action = ActionBuilder(driver, mouse=finger)
    action.pointer_action.move_to_location(int(x), int(y))
    action.pointer_action.pointer_down()
    action.pointer_action.pointer_up()
    action.perform()


def get_webview_context(driver):
    contexts = driver.contexts
    for ctx in contexts:
        if "WEBVIEW" in ctx and "expresocastelar" in ctx:
            return ctx
    for ctx in contexts:
        if "WEBVIEW" in ctx and "stetho" not in ctx:
            return ctx
    return None


def iniciar_emulador_si_necesario():
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=10)
    if "emulator-5554" in result.stdout:
        print("✔ Emulador ya está corriendo.")
        return

    print("Iniciando emulador...")
    subprocess.Popen(
        [EMULATOR_PATH, "-avd", AVD_NAME, "-no-snapshot-load", "-gpu", "swiftshader_indirect"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Cerrar el crash dialog del emulador si aparece
    import threading
    def cerrar_crash_dialog():
        time.sleep(5)
        for _ in range(30):
            try:
                import subprocess as sp
                sp.run([
                    "powershell", "-Command",
                    """
                    Add-Type -AssemblyName UIAutomationClient
                    $btn = [System.Windows.Automation.AutomationElement]::RootElement.FindFirst(
                        [System.Windows.Automation.TreeScope]::Descendants,
                        (New-Object System.Windows.Automation.PropertyCondition(
                            [System.Windows.Automation.AutomationElement]::NameProperty, "Don't send"
                        ))
                    )
                    if ($btn) {
                        $btn.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
                    }
                    """
                ], capture_output=True, timeout=5)
            except: pass
            time.sleep(2)
    threading.Thread(target=cerrar_crash_dialog, daemon=True).start()

    print("  Esperando que el emulador aparezca en ADB...")
    for _ in range(60):
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=10)
        if "emulator-5554" in result.stdout:
            break
        time.sleep(2)
    else:
        raise RuntimeError("❌ El emulador no apareció en ADB después de 2 minutos")

    print("  Esperando boot completo...")
    for _ in range(180):
        result = subprocess.run(
            ["adb", "-s", "emulator-5554", "shell", "getprop", "sys.boot_completed"],
            capture_output=True, text=True, timeout=10
        )
        if result.stdout.strip() == "1":
            print("✔ Emulador listo.")
            time.sleep(3)
            return
        time.sleep(2)

    raise RuntimeError("❌ El emulador no terminó de bootear después de 6 minutos")


def iniciar_appium_si_necesario():
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    resultado = sock.connect_ex(("127.0.0.1", 4723))
    sock.close()

    if resultado == 0:
        print("✔ Appium Server ya está corriendo.")
        return

    print("Iniciando Appium Server...")
    subprocess.Popen(
        [NODE_PATH, APPIUM_CLI],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    print("  Esperando que Appium esté listo...")
    for _ in range(30):
        time.sleep(2)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        resultado = sock.connect_ex(("127.0.0.1", 4723))
        sock.close()
        if resultado == 0:
            print("✔ Appium Server listo.")
            time.sleep(2)
            return

    raise RuntimeError("❌ Appium Server no respondió después de 60 segundos")


def click_day_robust_native(driver, day):
    driver.switch_to.context("NATIVE_APP")
    strategies = [
        (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{day}").className("android.view.View")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{day}")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{day:02d}")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().descriptionContains("{day}")'),
        (AppiumBy.XPATH, f'//*[@text="{day}"]'),
        (AppiumBy.XPATH, f'//*[@text="{day:02d}"]'),
        (AppiumBy.XPATH, f'//*[contains(@content-desc,"{day}")]'),
    ]
    for by, value in strategies:
        try:
            driver.find_element(by, value).click()
            print(f"✔ Día {day} clickeado (NATIVE) con: {value}")
            return True
        except:
            continue
    return False


def click_day_robust_webview(driver, day, webview_ctx):
    try:
        driver.switch_to.context(webview_ctx)
        time.sleep(1)

        strategies = [
            # Más específicas primero: dentro del picker, solo celdas de día habilitadas
            (By.CSS_SELECTOR, f'.picker__day:not(.picker__day--disabled):not(.picker__day--outfocus)'),
            (By.XPATH, f'//div[contains(@class,"picker")]//td[normalize-space(text())="{day}"]'),
            (By.XPATH, f'//div[contains(@class,"picker")]//*[normalize-space(text())="{day}" and not(contains(@class,"disabled"))]'),
            (By.XPATH, f'//table//td[normalize-space(text())="{day}" and not(contains(@class,"disabled"))]'),
            (By.XPATH, f'//table//td[normalize-space(text())="{day:02d}" and not(contains(@class,"disabled"))]'),
        ]

        for by, value in strategies:
            try:
                if by == By.CSS_SELECTOR:
                    # Para CSS buscamos todos y filtramos por texto
                    els = driver.find_elements(by, value)
                    for el in els:6
                        if el.text.strip() in (str(day), f"{day:02d}"):
                            driver.execute_script("arguments[0].click();", el)
                            print(f"✔ Día {day} clickeado (WEBVIEW CSS picker) text='{el.text}'")
                            return True
                else:
                    el = driver.find_element(by, value)
                    driver.execute_script("arguments[0].click();", el)
                    print(f"✔ Día {day} clickeado (WEBVIEW) con: {value}")
                    return True
            except:
                continue

        # Si todo falló, guardar HTML para debug
        try:
            html = driver.execute_script("return document.documentElement.outerHTML;")
            with open("webview_calendar.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("✔ HTML del WebView guardado → webview_calendar.html")
        except Exception as e:
            print(f"No se pudo guardar HTML: {e}")

    except Exception as e:
        print(f"Error en WebView: {e}")
    finally:
        driver.switch_to.context("NATIVE_APP")
    return False


# =======================================================
# CLASE
# =======================================================

class ReservaBot:

    def __init__(self, usuario: dict):
        self.email     = usuario["email"]
        self.password  = usuario["password"]
        self.dias      = usuario["dias"]
        self.recorrido = usuario["recorrido"]
        self.horario   = usuario["horario"]
        self.parada    = usuario["parada"]
        self.pago      = usuario["pago"]

    def correr(self, dia_objetivo):
        print(f"\n{'='*50}")
        print(f"Usuario : {self.email}")
        print(f"Días    : {self.dias}  |  Recorrido: {self.recorrido}  |  Horario: {self.horario}  |  Parada: {self.parada}  |  Pago: {self.pago}")
        print(f"{'='*50}")

        MAX_INTENTOS = 3
        for intento in range(1, MAX_INTENTOS + 1):
            try:
                resultado = self._reservar_dia(dia_objetivo)
                if resultado:
                    break
                else:
                    print(f"  ⚠ Intento {intento}/{MAX_INTENTOS} falló, reintentando en 10s...")
                    time.sleep(10)
            except Exception as e:
                print(f"  ⚠ Intento {intento}/{MAX_INTENTOS} - Excepción: {e}")
                if intento < MAX_INTENTOS:
                    print(f"  Reintentando en 10s...")
                    time.sleep(10)
                else:
                    print(f"  ❌ Se agotaron los {MAX_INTENTOS} intentos para día {dia_objetivo}")

    def _reservar_dia(self, target_weekday):
        hoy = date.today()
        dias_hasta = (target_weekday - hoy.weekday()) % 7 or 7
        prox_dia   = hoy + timedelta(days=dias_hasta)
        day        = prox_dia.day

        # -------------------------------------------------------
        # INICIAR EMULADOR Y APPIUM SI NO ESTÁN CORRIENDO
        # -------------------------------------------------------
        iniciar_appium_si_necesario()
        iniciar_emulador_si_necesario()

        # -------------------------------------------------------
        # LIMPIAR CACHE
        # -------------------------------------------------------
        print("Limpiando cache de la app...")
        try:
            subprocess.run(
                ["adb", "-s", "emulator-5554", "shell", "pm", "clear", PKG],
                capture_output=True, text=True, timeout=30
            )
            print("✔ Cache limpiado.")
        except Exception as e:
            print(f"⚠ No se pudo limpiar cache: {e}")

        # -------------------------------------------------------
        # INICIAR DRIVER
        # -------------------------------------------------------
        caps = {
            "platformName": "Android",
            "deviceName": "emulator-5554",
            "automationName": "UiAutomator2",
            "appPackage": PKG,
            "appActivity": "com.app.reservacombi.expresocastelar.MainActivity",
            "autoGrantPermissions": True,
            "noReset": True,
            "chromedriverExecutable": CHROMEDRIVER,
            "adbExecTimeout": 60000,
        }
        options = UiAutomator2Options()
        options.load_capabilities(caps)
        driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
        driver.implicitly_wait(IMPLICIT_WAIT)
        WAIT = WebDriverWait(driver, WAIT_TIMEOUT)

        try:
            # -------------------------------------------------------
            # PERMISOS
            # -------------------------------------------------------
            print("Revisando popups de permisos...")
            for i in range(PERMISSION_CHECK_LOOPS):
                try:
                    botones = driver.find_elements(By.XPATH,
                        "//*[@text='Allow' or @text='ALLOW' or @text='Permitir' or @text='PERMITIR']")
                    if botones:
                        print("  → Popup permiso (texto) clicado")
                        botones[0].click()
                except: pass
                try:
                    botones2 = driver.find_elements(By.ID,
                        "com.android.permissioncontroller:id/permission_allow_button")
                    if botones2:
                        print("  → Popup permiso (id) clicado")
                        botones2[0].click()
                except: pass
                time.sleep(0.7)

            # -------------------------------------------------------
            # LOGIN
            # -------------------------------------------------------
            print("Esperando campos de login...")
            campos = []
            for i in range(LOGIN_MAX_WAIT):
                campos = driver.find_elements(By.CLASS_NAME, "android.widget.EditText")
                print(f"  Segundo {i+1}: encontrados {len(campos)} EditText")
                if len(campos) >= 2:
                    break
                time.sleep(1)

            if len(campos) < 2:
                print("❌ No encontré los campos de login")
                return False

            print("Haciendo login...")
            campos[0].send_keys(self.email)
            campos[1].send_keys(self.password)
            driver.find_element(By.XPATH, "//android.widget.Button[@text='INGRESAR']").click()
            WAIT.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@text,'Dónde viajas')]")))
            print("✔ Pantalla principal cargada.")

            # -------------------------------------------------------
            # ABRIR CALENDARIO
            # -------------------------------------------------------
            print("Abriendo calendario...")
            driver.switch_to.context("NATIVE_APP")
            time.sleep(1)

            try:
                driver.find_element(By.XPATH, '//*[@resource-id="txt_fecha_viaje_consulta"]').click()
                print("✔ Campo fecha clickeado por resource-id")
            except:
                tap_xy_native(driver, 540, 890)
                print("✔ Campo fecha clickeado por coordenadas")

            print("Esperando que cargue el calendario...")
            time.sleep(3)

            # -------------------------------------------------------
            # NAVEGAR AL MES SIGUIENTE SI ES NECESARIO
            # -------------------------------------------------------
            if prox_dia.month != hoy.month or prox_dia.year != hoy.year:
                print(f"  El día objetivo ({prox_dia}) está en el mes siguiente, navegando...")
                webview_ctx = get_webview_context(driver)
                if webview_ctx:
                    try:
                        driver.switch_to.context(webview_ctx)
                        time.sleep(1)
                        # pickadate.js siempre usa esta clase para el botón de mes siguiente
                        next_btn = driver.find_element(By.CSS_SELECTOR, ".picker__nav--next")
                        next_btn.click()
                        print("  ✔ Navegado al mes siguiente.")
                        time.sleep(1.5)
                    except Exception as e:
                        print(f"  ⚠ No pude navegar al mes siguiente: {e}")
                        # Guardar HTML para debug si falla
                        try:
                            html = driver.execute_script("return document.documentElement.outerHTML;")
                            with open("calendar_nav_debug.html", "w", encoding="utf-8") as f:
                                f.write(html)
                            print("  HTML guardado → calendar_nav_debug.html")
                        except: pass
                    finally:
                        driver.switch_to.context("NATIVE_APP")
                else:
                    print("  ⚠ No se encontró WebView para navegar el mes")

            # -------------------------------------------------------
            # CLICK EN EL DÍA
            # -------------------------------------------------------
            print(f"✔ Día objetivo: {prox_dia} → día {day}")
            print(f"Buscando día {day} en el calendario...")

            clicked = click_day_robust_native(driver, day)
            if not clicked:
                print("NATIVE no funcionó, intentando WebView...")
                webview_ctx = get_webview_context(driver)
                if webview_ctx:
                    clicked = click_day_robust_webview(driver, day, webview_ctx)
                else:
                    print("❌ No se encontró contexto WebView")

            if not clicked:
                print(f"❌ No pude clickear el día {day}")
                driver.switch_to.context("NATIVE_APP")
                with open("calendar_dump_final.xml", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("Dump guardado → calendar_dump_final.xml")
                return False

            print("✔ Día seleccionado correctamente.")
            time.sleep(2)

            # -------------------------------------------------------
            # SELECCIONAR RECORRIDO
            # -------------------------------------------------------
            print("Abriendo selector de recorrido...")
            driver.switch_to.context("NATIVE_APP")
            try:
                driver.find_element(By.XPATH, '//*[@resource-id="txt_recorrido"]').click()
                print("✔ Campo recorrido clickeado")
            except:
                tap_xy_native(driver, 540, 590)
                print("✔ Campo recorrido clickeado por coordenadas")

            time.sleep(2)

            print(f"Seleccionando {self.recorrido}...")
            webview_ctx = get_webview_context(driver)
            if webview_ctx:
                try:
                    driver.switch_to.context(webview_ctx)
                    castelar_strategies = [
                        (By.XPATH, f'//*[contains(text(),"{self.recorrido}")]'),
                        (By.CSS_SELECTOR, 'li'),
                    ]
                    clicked_recorrido = False
                    for by, value in castelar_strategies:
                        try:
                            if by == By.CSS_SELECTOR:
                                for el in driver.find_elements(by, value):
                                    if self.recorrido.upper() in el.text.upper():
                                        el.click()
                                        print(f"✔ Recorrido clickeado: {el.text}")
                                        clicked_recorrido = True
                                        break
                            else:
                                driver.find_element(by, value).click()
                                print(f"✔ {self.recorrido} seleccionado.")
                                clicked_recorrido = True
                                break
                        except:
                            continue

                    if not clicked_recorrido:
                        print(f"❌ No encontré {self.recorrido}, guardando HTML...")
                        html = driver.execute_script("return document.documentElement.outerHTML;")
                        with open("recorrido_dump.html", "w", encoding="utf-8") as f:
                            f.write(html)
                        print("HTML guardado → recorrido_dump.html")
                        return False

                except Exception as e:
                    print(f"Error seleccionando recorrido: {e}")
                finally:
                    driver.switch_to.context("NATIVE_APP")

            time.sleep(2)

            # -------------------------------------------------------
            # SELECCIONAR HORARIO
            # -------------------------------------------------------
            print(f"Buscando horario {self.horario}...")
            driver.switch_to.context("NATIVE_APP")
            webview_ctx = get_webview_context(driver)
            if webview_ctx:
                try:
                    driver.switch_to.context(webview_ctx)
                    time.sleep(1)

                    clicked_horario = False
                    for xpath in [
                        f'//b[contains(text(),"{self.horario}")]/ancestor::div[contains(@class,"card__content")]'
                        f'//button[contains(@class,"toolbar-button--outline--3") and not(contains(@class,"ng-hide"))]',
                        f'//b[contains(text(),"{self.horario}")]/ancestor::div[contains(@class,"card__content")]'
                        f'//button[contains(@class,"toolbar-button--listaespera")]',
                    ]:
                        try:
                            el = driver.find_element(By.XPATH, xpath)
                            el.click()
                            print(f"✔ Botón {self.horario} clickeado: '{el.text.strip()}'")
                            clicked_horario = True
                            break
                        except:
                            continue

                    if not clicked_horario:
                        print(f"❌ No encontré botón para {self.horario}")
                        return False

                except Exception as e:
                    print(f"Error seleccionando horario: {e}")
                finally:
                    driver.switch_to.context("NATIVE_APP")

            time.sleep(2)

            # -------------------------------------------------------
            # SELECCIONAR PARADA
            # -------------------------------------------------------
            print(f"Seleccionando parada: {self.parada}...")
            driver.switch_to.context("NATIVE_APP")
            webview_ctx = None
            for _ in range(10):
                webview_ctx = get_webview_context(driver)
                if webview_ctx:
                    break
                time.sleep(1)
            if not webview_ctx:
                print("  ❌ No se encontró WebView para parada")
                return False
            if webview_ctx:
                try:
                    driver.switch_to.context(webview_ctx)

                    print("  Esperando pantalla Nueva Reserva...")
                    for _ in range(10):
                        try:
                            driver.find_element(By.XPATH, '//*[@id="txtComentariosSubida"]')
                            print("  ✔ Pantalla Nueva Reserva cargada.")
                            break
                        except:
                            time.sleep(1)

                    driver.find_element(By.XPATH, '//*[@id="txtComentariosSubida"]').click()
                    print("  ✔ Campo parada clickeado, esperando lista...")
                    time.sleep(2)

                    clicked_parada = False
                    for xpath in [
                        f'//*[contains(text(),"{self.parada}")]',
                        f'//*[contains(text(),"{self.parada.upper()}")]',
                    ]:
                        try:
                            el = driver.find_element(By.XPATH, xpath)
                            el.click()
                            print(f"  ✔ Parada clickeada: '{el.text.strip()}'")
                            clicked_parada = True
                            break
                        except:
                            continue

                    if not clicked_parada:
                        print(f"  ❌ No encontré la parada '{self.parada}', guardando HTML...")
                        html = driver.execute_script("return document.documentElement.outerHTML;")
                        with open("parada_dump.html", "w", encoding="utf-8") as f:
                            f.write(html)
                        print("  HTML guardado → parada_dump.html")
                        return False

                except Exception as e:
                    print(f"  Error seleccionando parada: {e}")
                finally:
                    driver.switch_to.context("NATIVE_APP")

            time.sleep(2)

            # -------------------------------------------------------
            # SELECCIONAR FORMA DE PAGO Y RESERVAR
            # -------------------------------------------------------
            print(f"Seleccionando forma de pago: {self.pago}...")
            driver.switch_to.context("NATIVE_APP")
            webview_ctx = None
            for _ in range(10):
                webview_ctx = get_webview_context(driver)
                if webview_ctx:
                    break
                time.sleep(1)
            if not webview_ctx:
                print("  ❌ No se encontró WebView para pago/reserva")
            else:
                try:
                    driver.switch_to.context(webview_ctx)
                    time.sleep(2)

                    for xpath in [
                        f'//*[contains(text(),"{self.pago}")]/preceding-sibling::input[@type="radio"]',
                        f'//*[contains(text(),"{self.pago}")]/..//input[@type="radio"]',
                        f'//*[contains(text(),"{self.pago}")]',
                    ]:
                        try:
                            el = driver.find_element(By.XPATH, xpath)
                            el.click()
                            print(f"  ✔ {self.pago} seleccionado.")
                            break
                        except:
                            continue

                    time.sleep(1)

                    clicked_reservar = False
                    for xpath in [
                        '//button[contains(text(),"RESERVAR")]',
                        '//button[contains(text(),"Reservar")]',
                        '//button[contains(translate(text(),"abcdefghijklmnopqrstuvwxyz","ABCDEFGHIJKLMNOPQRSTUVWXYZ"),"RESERVAR")]',
                    ]:
                        try:
                            els = driver.find_elements(By.XPATH, xpath)
                            for el in els:
                                txt = el.text.strip()
                                if txt:
                                    el.click()
                                    print(f"  ✔ Botón clickeado: '{txt}'")
                                    clicked_reservar = True
                                    break
                            if clicked_reservar:
                                break
                        except:
                            continue

                    if not clicked_reservar:
                        print("  ❌ No encontré botón RESERVAR, guardando HTML...")
                        html = driver.execute_script("return document.documentElement.outerHTML;")
                        with open("reservar_dump.html", "w", encoding="utf-8") as f:
                            f.write(html)
                        print("  HTML guardado → reservar_dump.html")

                except Exception as e:
                    print(f"  Error en pago/reserva: {e}")
                finally:
                    driver.switch_to.context("NATIVE_APP")

            time.sleep(2)
            print(f"✔ Reserva completada para {self.email} el {prox_dia}.")
            return True

        finally:
            try:
                driver.switch_to.context("NATIVE_APP")
            except: pass
            try:
                driver.quit()
            except: pass


# =======================================================
# MAIN
# =======================================================

if __name__ == "__main__":
    configurar_log()

    if os.path.exists(LOCK_FILE):
        print("⚠ Ya hay una instancia corriendo (lock encontrado). Saliendo.")
        sys.exit(0)
    try:
        open(LOCK_FILE, "w").write(str(os.getpid()))
    except: pass

    try:
        with open(USUARIOS_JSON, "r", encoding="utf-8") as f:
            usuarios = json.load(f)

        print(f"Cargados {len(usuarios)} usuario(s).")

        hoy = date.today()
        dia_a_reservar = (hoy.weekday() + 6) % 7
        NOMBRES_DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        print(f"Hoy es {NOMBRES_DIAS[hoy.weekday()]}. Se reserva para el próximo {NOMBRES_DIAS[dia_a_reservar]}.")

        usuarios_hoy = [u for u in usuarios if dia_a_reservar in u["dias"]]
        print(f"{len(usuarios_hoy)} usuario(s) tienen reserva para el {NOMBRES_DIAS[dia_a_reservar]}.")

        if not usuarios_hoy:
            print("No hay reservas para procesar hoy.")
        else:
            for i, u in enumerate(usuarios_hoy):
                ReservaBot(u).correr(dia_a_reservar)
                if i < len(usuarios_hoy) - 1:
                    print("\nEsperando 15 segundos antes del siguiente usuario...")
                    time.sleep(15)

        print("\n✔ Proceso finalizado.")

    finally:
        try:
            os.remove(LOCK_FILE)
        except: pass

    if APAGAR_AL_TERMINAR:
        print("Apagando la PC en 60 segundos... (ejecutá 'shutdown /a' para cancelar)")
        subprocess.run(["shutdown", "/s", "/t", "60"])