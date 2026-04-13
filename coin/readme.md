# Photobooth Münzprüfer Setup (Pico W & HX-916)

Diese Dokumentation beschreibt die Einrichtung des Raspberry Pi Pico W als Steuerungs-Einheit für ein Münzzahlsystem in einer Photobooth, inklusive der Anbindung an einen Proxy-Server.

## 1. Programmierung des Münzprüfers (HX-916)

Der Münzprüfer muss im Impuls-Modus konfiguriert werden. 
**Standard: 1 Impuls = 0,50 €**

### Vorbereitung
1. Halte die Tasten `+` und `-` gleichzeitig gedrückt, bis **"A"** im Display erscheint.
2. Drücke `SET`.

### Parameter-Tabelle
| Parameter | Wert | Bedeutung |
| :--- | :--- | :--- |
| **E** | **3** | Anzahl der Münzsorten (0.50€, 1.00€, 2.00€) |
| **H1** | **20** | Lern-Münzen für 0.50€ (20 Stück einwerfen) |
| **P1** | **1** | **1 Impuls** für 0.50€ |
| **F1** | **8** | Genauigkeit (Standardwert) |
| **H2** | **20** | Lern-Münzen für 1.00€ |
| **P2** | **2** | **2 Impulse** für 1.00€ |
| **F2** | **8** | Genauigkeit |
| **H3** | **20** | Lern-Münzen für 2.00€ |
| **P3** | **4** | **4 Impulse** für 2.00€ |
| **F3** | **8** | Genauigkeit |

**Wichtig:** Nach der Programmierung erscheint im Display nacheinander **A1, A2, A3**. In dieser Phase müssen jeweils die 20 echten Referenzmünzen eingeworfen werden, um die Profile zu speichern.

---

## 2. Benötigte Hardware

* **Raspberry Pi Pico W**
* **HX-916 Münzprüfer** (12V Betrieb)
* **LAOMAO DM004X6 DC-DC Step-Down Converter** (12V -> 5V)
* **DST-1R4P-N Optokoppler** (Signaltrennung 12V / 3.3V)
* **Freenove I2C LCD 1602 Modul** (Display)
* **Momentary Push Button** (Taster)
* **12V Netzteil** (Zentrale Versorgung)

---

## 3. Vollständiger Verkabelungsplan

### A. Stromversorgung (12V zu 5V)
* **12V Netzteil (+)** an Münzprüfer (12V Rot) **UND** Step-Down Converter **IN+** **UND** Optokoppler Eingang **1+**.
* **12V Netzteil (-)** an Münzprüfer (Schwarz) **UND** Step-Down Converter **IN-**.
* **Step-Down OUT+** an Pico **VSYS (Pin 39)**. *(Zuvor stabil auf 5.0V einstellen!)*
* **Step-Down OUT-** an Pico **GND**.

### B. Optokoppler (DST-1R4P-N)
**Eingangsseite (12V):**
* **12V Netzteil (+)** an Eingang **1+** des Optokopplers.
* **COIN-Kabel (Weiß)** vom HX-916 an den Eingang **1-** des Optokopplers.

**Ausgangsseite (3.3V zum Pico):**
* **VCC** am Optokoppler an Pico **3.3V (Pin 36)**.
* **GND** am Optokoppler an Pico **GND**.
* **OUT (O1)** am Optokoppler an Pico **GP22 (Pin 29)**.

### C. I2C LCD Display (Freenove)
* **VCC** an Pico **VBUS (Pin 40)** (leitet 5V vom Converter weiter).
* **GND** an Pico **GND**.
* **SDA** an Pico **GP0 (Pin 1)**.
* **SCL** an Pico **GP1 (Pin 2)**.

### D. Push Button (Taster)
* **Pin 1** an Pico **GP21 (Pin 27)**.
* **Pin 2** an Pico **GND**.

---

## 4. Wichtige Sicherheitshinweise

1.  **GND-Sternpunkt:** Alle Massen (Netzteil, Step-Down, Pico, LCD, Taster, Optokoppler-Ausgang) müssen zwingend miteinander verbunden sein.
2.  **Spannungsprüfung:** Die Ausgangsspannung des Step-Down Converters muss mit einem Multimeter geprüft werden, **bevor** er an den Pico angeschlossen wird (exakt 5.0V).
3.  **3.3V Schutz:** Verbinde niemals das weiße COIN-Kabel des Münzprüfers direkt mit dem Pico. Der Pico verträgt an seinen Pins nur 3.3V. Der Optokoppler schützt den Controller vor den 12V-Signalen.

## 5. Code.py

Der enthaltene Code für den Pico W basiert auf Adafruit Circuit Python. Dieses muss zunächst installiert werden: 

```bash
https://circuitpython.org/board/raspberry_pi_pico_w/
```

Anschließend den kompletten Inhalt aus dem Ordner picow auf das CIRCUITPY-Laufwerk kopieren. 
Die settings.toml anpassen!!!


