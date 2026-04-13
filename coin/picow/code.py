import os
import time
import json
import wifi
import socketpool
import board
import bitbangio
import digitalio
import adafruit_requests

from pcf8574_lcd import PCF8574_LCD
from adafruit_httpserver import Server, Request, Response, POST

print("Start Pico")

WIFI_SSID = os.getenv("CIRCUITPY_WIFI_SSID")
WIFI_PASSWORD = os.getenv("CIRCUITPY_WIFI_PASSWORD")
COIN_PROXY_URL = os.getenv("COIN_PROXY_URL")
CANCEL_PAYMENT_URL = os.getenv("CANCEL_PAYMENT_URL")
COIN_SECRET = os.getenv("COIN_SECRET", "")

# --- KONFIG ---
IMPULS_WERT = 50          # 1 Impuls = 50 Cent
IMPULS_PAUSE = 0.3        # ab wann eine Impulsserie ausgewertet wird
DEFAULT_ANZEIGE_TIMEOUT = 120  # Fallback, wenn nichts vom Admin kommt

# --- STATUS ---
PREIS_CENTS = 0
PAYMENT_ACTIVE = False
PAYMENT_STARTED_AT = 0.0
PAYMENT_MESSAGE = "Bitte einwerfen"
ANZEIGE_TIMEOUT = DEFAULT_ANZEIGE_TIMEOUT

AKTUELLES_GUTHABEN_CENTS = 0
LETZTER_IMPULS_ZEITPUNKT = 0.0
GESAMMELTE_IMPULSE = 0
LAST_COIN_STATE = True

# --- LCD ---
i2c = bitbangio.I2C(board.GP0, board.GP1, frequency=10000)
lcd = PCF8574_LCD(i2c, address=0x27, cols=16, rows=2)
lcd.backlight_on()

# --- MUENZPRUEFER ---
coin_pin = digitalio.DigitalInOut(board.GP22)
coin_pin.direction = digitalio.Direction.INPUT
coin_pin.pull = digitalio.Pull.UP

# --- CANCEL BUTTON ---
cancel_pin = digitalio.DigitalInOut(board.GP21)
cancel_pin.direction = digitalio.Direction.INPUT
cancel_pin.pull = digitalio.Pull.UP
LAST_CANCEL_STATE = True
LAST_CANCEL_AT = 0.0


def zeige_text(zeile1="", zeile2=""):
    lcd.clear()
    lcd.set_cursor(0, 0)
    lcd.message(f"{zeile1[:16]:<16}")
    lcd.set_cursor(0, 1)
    lcd.message(f"{zeile2[:16]:<16}")


def update_display():
    if not PAYMENT_ACTIVE:
        zeige_text("Fotobox bereit", "Bitte einwerfen")
        return

    noch = max(0, PREIS_CENTS - AKTUELLES_GUTHABEN_CENTS)
    zeile1 = f"Geld:{AKTUELLES_GUTHABEN_CENTS/100:>5.2f}E"
    zeile2 = f"Noch:{noch/100:>5.2f}E"
    zeige_text(zeile1, zeile2)


def reset_payment():
    global PREIS_CENTS
    global PAYMENT_ACTIVE
    global PAYMENT_STARTED_AT
    global PAYMENT_MESSAGE
    global AKTUELLES_GUTHABEN_CENTS
    global LETZTER_IMPULS_ZEITPUNKT
    global GESAMMELTE_IMPULSE
    global ANZEIGE_TIMEOUT

    PREIS_CENTS = 0
    PAYMENT_ACTIVE = False
    PAYMENT_STARTED_AT = 0.0
    PAYMENT_MESSAGE = "Bitte einwerfen"
    AKTUELLES_GUTHABEN_CENTS = 0
    LETZTER_IMPULS_ZEITPUNKT = 0.0
    GESAMMELTE_IMPULSE = 0
    ANZEIGE_TIMEOUT = DEFAULT_ANZEIGE_TIMEOUT
    update_display()


def melde_bezahlt():
    if not COIN_PROXY_URL:
        print("COIN_PROXY_URL fehlt")
        return False

    payload = {
        "secret": COIN_SECRET,
        "amount_cents_received": AKTUELLES_GUTHABEN_CENTS,
    }

    try:
        response = requests.post(COIN_PROXY_URL, json=payload, timeout=10)
        print("coin-paid status:", response.status_code)
        try:
            print("coin-paid body:", response.text)
        except Exception:
            pass
        return 200 <= response.status_code < 300
    except Exception as exc:
        print("coin-paid FEHLER:", exc)
        return False


def melde_abbruch():
    if not CANCEL_PAYMENT_URL:
        print("CANCEL_PAYMENT_URL fehlt")
        return False

    try:
        response = requests.post(CANCEL_PAYMENT_URL, json={"source": "pico_button"}, timeout=10)
        print("cancel-payment status:", response.status_code)
        try:
            print("cancel-payment body:", response.text)
        except Exception:
            pass
        return 200 <= response.status_code < 300
    except Exception as exc:
        print("cancel-payment FEHLER:", exc)
        return False


print("Verbinde WLAN...")
wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD)
print("IP:", wifi.radio.ipv4_address)

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool)
server = Server(pool, debug=True)


@server.route("/health")
def health(request: Request):
    return Response(
        request,
        json.dumps(
            {
                "status": "ok",
                "payment_active": PAYMENT_ACTIVE,
                "preis_cents": PREIS_CENTS,
                "guthaben_cents": AKTUELLES_GUTHABEN_CENTS,
                "anzeige_timeout": ANZEIGE_TIMEOUT,
            }
        ),
        content_type="application/json",
    )


@server.route("/start-payment", [POST])
def start_payment(request: Request):
    global PREIS_CENTS
    global PAYMENT_ACTIVE
    global PAYMENT_STARTED_AT
    global PAYMENT_MESSAGE
    global AKTUELLES_GUTHABEN_CENTS
    global LETZTER_IMPULS_ZEITPUNKT
    global GESAMMELTE_IMPULSE
    global ANZEIGE_TIMEOUT

    try:
        data = request.json()
    except Exception:
        return Response(
            request,
            json.dumps({"status": "invalid_json"}),
            content_type="application/json",
        )

    PREIS_CENTS = int(data.get("amount_cents", 0))
    PAYMENT_MESSAGE = str(data.get("message", "")) or "Bitte einwerfen"

    timeout_value = data.get("timeout", DEFAULT_ANZEIGE_TIMEOUT)
    try:
        timeout_value = int(timeout_value)
    except Exception:
        timeout_value = DEFAULT_ANZEIGE_TIMEOUT

    if timeout_value <= 0:
        timeout_value = DEFAULT_ANZEIGE_TIMEOUT

    ANZEIGE_TIMEOUT = timeout_value

    AKTUELLES_GUTHABEN_CENTS = 0
    LETZTER_IMPULS_ZEITPUNKT = 0.0
    GESAMMELTE_IMPULSE = 0
    PAYMENT_ACTIVE = PREIS_CENTS > 0
    PAYMENT_STARTED_AT = time.monotonic()

    print("Neuer Payment-Start:", PREIS_CENTS, "Cent")
    print("Timeout vom Admin/PHP:", ANZEIGE_TIMEOUT, "Sekunden")
    update_display()

    return Response(
        request,
        json.dumps(
            {
                "status": "started",
                "amount_cents": PREIS_CENTS,
                "payment_active": PAYMENT_ACTIVE,
                "timeout": ANZEIGE_TIMEOUT,
            }
        ),
        content_type="application/json",
    )


print("Starte HTTP...")
server.start(str(wifi.radio.ipv4_address), port=80)
print("HTTP ready")

update_display()

while True:
    try:
        server.poll()
    except Exception as e:
        print("poll error:", e)

    jetzt = time.monotonic()
    current_state = coin_pin.value

    # HIGH -> LOW Flanke = Impuls
    if PAYMENT_ACTIVE and LAST_COIN_STATE and not current_state:
        GESAMMELTE_IMPULSE += 1
        LETZTER_IMPULS_ZEITPUNKT = jetzt
        print("Impuls registriert")

    LAST_COIN_STATE = current_state

    # Impulsserie auswerten
    if PAYMENT_ACTIVE and GESAMMELTE_IMPULSE > 0 and (jetzt - LETZTER_IMPULS_ZEITPUNKT) > IMPULS_PAUSE:
        neuer_betrag = GESAMMELTE_IMPULSE * IMPULS_WERT
        AKTUELLES_GUTHABEN_CENTS += neuer_betrag
        print("Impulse:", GESAMMELTE_IMPULSE, "=>", neuer_betrag, "Cent")
        print("Guthaben:", AKTUELLES_GUTHABEN_CENTS, "Cent")
        GESAMMELTE_IMPULSE = 0
        update_display()

    # Genug Guthaben
    if PAYMENT_ACTIVE and PREIS_CENTS > 0 and AKTUELLES_GUTHABEN_CENTS >= PREIS_CENTS:
        zeige_text("   BEZAHLT!   ", "Druck startet")
        if melde_bezahlt():
            time.sleep(2)
            reset_payment()
        else:
            zeige_text("Proxy Fehler", "Bitte warten")
            time.sleep(3)
            update_display()

    # Cancel-Button (kurzer Druck gegen GND)
    cancel_state = cancel_pin.value
    if PAYMENT_ACTIVE and LAST_CANCEL_STATE and not cancel_state and (jetzt - LAST_CANCEL_AT) > 0.3:
        LAST_CANCEL_AT = jetzt
        print("Cancel-Button gedrückt")
        zeige_text("Abbruch...", "Bitte warten")
        melde_abbruch()
        time.sleep(1)
        reset_payment()

    LAST_CANCEL_STATE = cancel_state

    # Timeout
    if PAYMENT_ACTIVE and PAYMENT_STARTED_AT > 0 and (jetzt - PAYMENT_STARTED_AT) > ANZEIGE_TIMEOUT:
        zeige_text("Zeit abgelaufen", "Neustart...")
        time.sleep(2)
        reset_payment()

    time.sleep(0.001)
