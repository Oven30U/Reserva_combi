from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

PKG = "com.app.reservacombi.expresocastelar"

caps = {
    "platformName": "Android",
    "deviceName": "emulator",
    "automationName": "UiAutomator2",
    "appPackage": PKG,
    "appActivity": "com.app.reservacombi.expresocastelar.MainActivity",
    "autoGrantPermissions": True,
    "noReset": False,
}

options = UiAutomator2Options()
options.load_capabilities(caps)
driver = webdriver.Remote("http://127.0.0.1:4723/wd/hub", options=options)
driver.implicitly_wait(4)
WAIT = WebDriverWait(driver, 15)

# Login rápido
time.sleep(3)
campos = driver.find_elements(By.CLASS_NAME, "android.widget.EditText")
campos[0].send_keys("ovenpereyra@gmail.com")
campos[1].send_keys("Lengay10")
driver.find_element(By.XPATH, "//android.widget.Button[@text='INGRESAR']").click()
time.sleep(4)

# Abrir calendario (tap genérico en zona media)
driver.tap([(540, 900)])
time.sleep(3)

# === DIAGNÓSTICO ===
print("CONTEXTOS:", driver.contexts)

with open("calendar_dump.xml", "w", encoding="utf-8") as f:
    f.write(driver.page_source)
print("Guardado calendar_dump.xml")

views = driver.find_elements(AppiumBy.CLASS_NAME, "android.view.View")
for v in views:
    try:
        print(f"bounds={v.get_attribute('bounds')} | text='{v.get_attribute('text') or ''}' | desc='{v.get_attribute('content-desc') or ''}'")
    except:
        pass

driver.quit()