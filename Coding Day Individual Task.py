import flet as ft
import threading
import random
import time
from datetime import datetime
from typing import Any, Dict

# ---------------------------------------------------------------------
# 1–2. DEVICE DICTIONARY + ALAP ADATOK
# ---------------------------------------------------------------------

devices: Dict[str, Dict[str, Any]] = {
    "light1": {
        "name": "Living Room Light",
        "type": "light",
        "state": False,
        "power_w": 60,
        "recent_actions": [],
    },
    "door1": {
        "name": "Front Door",
        "type": "door",
        "state": True,    # True = LOCKED
        "power_w": 0,
        "recent_actions": [],
    },
    "thermo1": {
        "name": "Thermostat",
        "type": "thermo",
        "temp": 22.0,
        "power_w": 120,
        "recent_actions": [],
    },
    "fan1": {
        "name": "Ceiling Fan",
        "type": "fan",
        "speed": 0,
        "power_w": 50,
        "recent_actions": [],
    },
}

event_log: list[dict] = []

# ---------------------------------------------------------------------
# 6. EGYSZERŰ PUB/SUB RENDSZER
# ---------------------------------------------------------------------

class PubSub:
    def __init__(self):
        self.listeners = []

    def subscribe(self, callback):
        self.listeners.append(callback)

    def publish(self, data: dict):
        for fn in self.listeners:
            fn(data)

global_pubsub = PubSub()


# ---------------------------------------------------------------------
# 9. ASYNC ESZKÖZ / POWER SZIMULÁTOR (HÁTTÉRTASKOK)
# ---------------------------------------------------------------------

def simulate_power():
    """Háttérben fut: időnként 'mért' teljesítményt küld (5 mp-enként)."""
    while True:
        simulated_value = random.randint(80, 160)
        global_pubsub.publish({"type": "power", "value": simulated_value})
        time.sleep(5) 


def simulate_device_changes(page: ft.Page):
    """
    Háttértask: Véletlenszerűen változtatja a termosztát és a ventilátor
    értékeit 5 másodpercenként.
    """
    while True:
        time.sleep(5) 
        
        # --- Termosztát ---
        thermo = devices["thermo1"]
        current_temp = thermo["temp"]
        change = random.choice([-0.5, 0.0, 0.5])
        new_temp = round(current_temp + change, 1)
        new_temp = max(16.0, min(30.0, new_temp))
        
        if new_temp != current_temp:
             add_log("thermo1", "Auto Change", f"Temp changed to {new_temp:.1f} °C")
             thermo["temp"] = new_temp
             
        # --- Ventilátor ---
        fan = devices["fan1"]
        current_speed = fan["speed"]
        change = random.choice([-1, 0, 1])
        new_speed = current_speed + change
        new_speed = max(0, min(3, new_speed))
        
        if new_speed != current_speed:
            add_log("fan1", "Auto Change", f"Speed changed to {new_speed}")
            fan["speed"] = new_speed
            
        if page.route == "/" or page.route.startswith("/details/"):
             page.update()


def start_simulator(page: ft.Page):
    """Elindítja a teljesítmény- és az eszközváltozás szimulátorokat."""
    t_power = threading.Thread(target=simulate_power, daemon=True)
    t_power.start()
    
    t_device = threading.Thread(target=simulate_device_changes, args=(page,), daemon=True)
    t_device.start()


# ---------------------------------------------------------------------
# 10. VALÓS IDEJŰ POWER LINE CHART
# ---------------------------------------------------------------------

class PowerChart(ft.LineChart):
    """Egyszerű power history line chart. Címkék nélkül a zsúfoltság elkerüléséért."""

    def __init__(self, width: int = 900, height: int = 300):
        super().__init__(
            data_series=[],
            width=width,
            height=height,
            animate=True,
            tooltip_bgcolor=ft.Colors.BLUE_GREY_100, 
            
            # --- TENGELYEK: Címkék kikapcsolva a 0-probléma elkerülése érdekében ---
            left_axis=ft.ChartAxis(
                show_labels=False, 
                labels_size=0,
            ),
            bottom_axis=ft.ChartAxis(
                show_labels=False,
            ),
            
            horizontal_grid_lines=ft.ChartGridLines(
                interval=25, 
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                width=1,
            ),
            
            min_y=70,  
            max_y=170, 
        )
        self.values: list[float] = []

    def add_value(self, v: float):
        self.values.append(v)
        # Futószalag effektus: Max 40 adatpont
        if len(self.values) > 40:
            self.values.pop(0)
        
        self.data_series = [
            ft.LineChartData(
                data_points=[
                    ft.LineChartDataPoint(i, val) for i, val in enumerate(self.values)
                ],
                color=ft.Colors.BLUE,
                stroke_width=2,
            )
        ]


# ---------------------------------------------------------------------
# KÖZÖS SEGÉDFÜGGVÉNYEK (LOG, IDŐ, STB.)
# ---------------------------------------------------------------------

def add_log(device_id: str, action: str, details: str = ""):
    """Hozzáad egy eseményt a globális eseménynaplóhoz."""
    dev = devices.get(device_id)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "time": ts,
        "device_id": device_id,
        "device_name": dev["name"] if dev else device_id,
        "action": action,
        "details": details,
    }
    event_log.append(entry)
    
    if dev and "recent_actions" in dev:
        dev["recent_actions"].append(f"[{ts}] {action}: {details}")


# ---------------------------------------------------------------------
# 7. MAIN APP – ROUTING, OLDALAK, LOGIKA
# ---------------------------------------------------------------------

def main(page: ft.Page):
    page.title = "Smart Home Monitoring System"
    page.theme_mode = "light"
    page.window_width = 1000
    page.window_height = 720
    page.padding = 0
    page.bgcolor = ft.Colors.GREY_100
    page.scroll = True 

    power_chart = PowerChart(width=None, height=300)

    def on_pubsub_event(ev: dict):
        if ev.get("type") == "power":
            power_chart.add_value(ev["value"])
            if power_chart.page and page.route == "/statistics":
                 page.update() 

    global_pubsub.subscribe(on_pubsub_event)

    start_simulator(page)

    # -----------------------------------------------------------------
    # 3–5. MAIN PAGE (OVERVIEW) – DEVICE CARDOK + LOGIKA
    # -----------------------------------------------------------------

    def build_overview_view() -> ft.View:
        onoff_cards: list[ft.Control] = []
        slider_cards: list[ft.Control] = []

        for dev_id, dev in devices.items():
            if dev["type"] in ("light", "door"):

                def make_toggle_handler(did: str):
                    def handler(e):
                        d = devices[did]
                        d["state"] = not d["state"]
                        
                        if d["type"] == "light":
                            state_txt = "ON" if d["state"] else "OFF"
                            add_log(did, "Toggle", f"Light turned {state_txt}")
                        else:
                            state_txt = "LOCKED" if d["state"] else "UNLOCKED"
                            add_log(did, "Toggle", f"Door {state_txt}")
                            
                        page.update() 
                    return handler

                icon = (
                    ft.Icons.LIGHTBULB_ROUNDED
                    if dev["type"] == "light"
                    else ft.Icons.DOOR_SLIDING
                )
                status = (
                    "ON" if dev["state"] else "OFF"
                    if dev["type"] == "light"
                    else ("LOCKED" if dev["state"] else "UNLOCKED")
                )
                
                card = ft.Container(
                    ft.Card(
                        content=ft.Container(
                            bgcolor=ft.Colors.AMBER_50
                            if dev["type"] == "light"
                            else ft.Colors.BLUE_50,
                            padding=20,
                            border_radius=15,
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Icon(icon),
                                            ft.Text(dev["name"], size=18, weight="bold"),
                                        ]
                                    ),
                                    ft.Text(f"Status: {status}"),
                                    ft.Text(f"Power: {dev['power_w']} W"),
                                    ft.Row(
                                        [
                                            ft.ElevatedButton(
                                                "Toggle",
                                                on_click=make_toggle_handler(dev_id),
                                            ),
                                            ft.TextButton(
                                                "Details",
                                                on_click=lambda e, d_id=dev_id: page.go(
                                                    f"/details/{d_id}"
                                                ),
                                            ),
                                        ]
                                    ),
                                ],
                                spacing=8,
                                alignment=ft.MainAxisAlignment.START,
                            ),
                        ),
                    ),
                    width=450, 
                    expand=False 
                )
                onoff_cards.append(card)

        # Slider-es eszközök (Dinamikus frissítés bevezetve a sliderhez)
        for dev_id, dev in devices.items():
            if dev["type"] in ("thermo", "fan"):

                # Dinamikus szöveges vezérlő létrehozása a csúszka értékének
                label_text = ft.Text(
                    f"Temp: {dev['temp']:.1f} °C"
                    if dev["type"] == "thermo"
                    else f"Speed: {dev['speed']}"
                )

                def make_slider_handler(did: str, text_control: ft.Text):
                    def handler(e: ft.ControlEvent):
                        d = devices[did]
                        
                        # Eszköz adatainak frissítése
                        if d["type"] == "thermo":
                            new_value = round(e.control.value, 1)
                            d["temp"] = new_value
                            add_log(
                                did,
                                "Set temperature",
                                f"New setpoint: {d['temp']:.1f} °C",
                            )
                            # VALÓS IDEJŰ FRISSÍTÉS: Frissítjük a Text vezérlő értékét
                            text_control.value = f"Temp: {d['temp']:.1f} °C"
                        else:
                            new_value = int(e.control.value)
                            d["speed"] = new_value
                            add_log(
                                did,
                                "Set speed",
                                f"New fan speed: {d['speed']}",
                            )
                            # VALÓS IDEJŰ FRISSÍTÉS: Frissítjük a Text vezérlő értékét
                            text_control.value = f"Speed: {d['speed']}"
                        
                        # VALÓS IDEJŰ FRISSÍTÉS: Frissítjük a Text vezérlőt
                        text_control.update() 
                        
                    return handler

                card = ft.Container(
                    ft.Card(
                        content=ft.Container(
                            bgcolor=ft.Colors.RED_50
                            if dev["type"] == "thermo"
                            else ft.Colors.CYAN_50,
                            padding=20,
                            border_radius=15,
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Icon(
                                                ft.Icons.DEVICE_THERMOSTAT
                                                if dev["type"] == "thermo"
                                                else ft.Icons.AIR 
                                            ),
                                            ft.Text(dev["name"], size=18, weight="bold"),
                                        ]
                                    ),
                                    label_text, # Dinamikus Text vezérlő
                                    ft.Slider(
                                        min=16 if dev["type"] == "thermo" else 0,
                                        max=30 if dev["type"] == "thermo" else 3,
                                        divisions=14 if dev["type"] == "thermo" else 3,
                                        value=dev["temp"]
                                        if dev["type"] == "thermo"
                                        else dev["speed"],
                                        on_change=make_slider_handler(dev_id, label_text),
                                    ),
                                    ft.TextButton(
                                        "Details",
                                        on_click=lambda e, d_id=dev_id: page.go(
                                            f"/details/{d_id}"
                                        ),
                                    ),
                                ],
                                spacing=8,
                            ),
                        ),
                    ),
                    width=450, 
                    expand=False
                )
                slider_cards.append(card)

        return ft.View(
            route="/",
            controls=[
                ft.AppBar(
                    title=ft.Text("Smart Home Overview 🏠"),
                    bgcolor=ft.Colors.WHITE,
                    actions=[
                        ft.TextButton(
                            "Overview", on_click=lambda e: page.go("/")
                        ),
                        ft.TextButton(
                            "Statistics",
                            on_click=lambda e: page.go("/statistics"),
                        ),
                    ],
                ),
                ft.Container(
                    padding=20,
                    content=ft.Column(
                        [
                            ft.Text("On/Off Devices 💡🚪", size=22, weight="bold"),
                            ft.Row(onoff_cards, wrap=True, spacing=20, run_spacing=20), 
                            ft.Divider(),
                            ft.Text(
                                "Slider Controlled Devices 🌡️💨",
                                size=22,
                                weight="bold",
                            ),
                            ft.Row(slider_cards, wrap=True, spacing=20, run_spacing=20), 
                        ],
                        spacing=20,
                        expand=True 
                    ),
                ),
            ],
            scroll=ft.ScrollMode.ADAPTIVE 
        )

    # -----------------------------------------------------------------
    # 8. STATISTICS PAGE (LOG TABLE + 10. POWER LINE CHART)
    # -----------------------------------------------------------------

    def build_statistics_view() -> ft.View:
        columns = [
            ft.DataColumn(ft.Text("Time")),
            ft.DataColumn(ft.Text("Device")),
            ft.DataColumn(ft.Text("Action")),
            ft.DataColumn(ft.Text("Details")),
        ]

        rows: list[ft.DataRow] = []
        for entry in reversed(event_log[-100:]):
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(entry["time"])),
                        ft.DataCell(ft.Text(entry["device_name"])),
                        ft.DataCell(ft.Text(entry["action"])),
                        ft.DataCell(ft.Text(entry["details"])),
                    ]
                )
            )

        log_table = ft.DataTable(
            columns=columns,
            rows=rows,
            column_spacing=10,
            expand=True 
        )

        return ft.View(
            route="/statistics",
            controls=[
                ft.AppBar(
                    title=ft.Text("Smart Home Statistics 📊"),
                    bgcolor=ft.Colors.WHITE,
                    actions=[
                        ft.TextButton(
                            "Overview", on_click=lambda e: page.go("/")
                        ),
                        ft.TextButton(
                            "Statistics",
                            on_click=lambda e: page.go("/statistics"),
                        ),
                    ],
                ),
                ft.Container(
                    padding=20,
                    content=ft.Column(
                        [
                            ft.Text(
                                "Event Log 📝 (Last 100 entries)", 
                                size=22, 
                                weight="bold"
                            ),
                            ft.Container(
                                height=250, 
                                content=ft.ListView(
                                    [log_table], 
                                    expand=True 
                                ),
                                expand=True 
                            ),
                            ft.Divider(),
                            ft.Text(
                                "Real-Time Power Consumption ⚡",
                                size=22,
                                weight="bold",
                            ),
                            ft.Container(
                                content=power_chart,
                                expand=True 
                            ),
                        ],
                        spacing=20,
                    ),
                ),
            ],
             scroll=ft.ScrollMode.ADAPTIVE 
        )

    # -----------------------------------------------------------------
    # 3. DETAILS PAGE (ESZKÖZ RÉSZLETEK)
    # -----------------------------------------------------------------

    def build_details_view(device_id: str) -> ft.View:
        dev = devices.get(device_id)
        if not dev:
            body = ft.Text("Unknown device.", size=18)
            title = "Device Not Found 🚫"
        else:
            title = dev["name"]
            details_controls: list[ft.Control] = [
                ft.Text(f"ID: {device_id}", size=16),
                ft.Text(f"Type: {dev['type']}", size=16),
            ]

            if dev["type"] == "light":
                details_controls.append(ft.Text(f"State: {'ON' if dev['state'] else 'OFF'}", size=16))
            elif dev["type"] == "door":
                details_controls.append(ft.Text(f"State: {'LOCKED' if dev['state'] else 'UNLOCKED'}", size=16))
            elif dev["type"] == "thermo":
                details_controls.append(ft.Text(f"Setpoint: {dev['temp']:.1f} °C", size=16))
            elif dev["type"] == "fan":
                details_controls.append(ft.Text(f"Speed: {dev['speed']}", size=16))

            details_controls.append(ft.Text(f"Power: {dev['power_w']} W", size=16))
            details_controls.append(ft.Divider())
            details_controls.append(ft.Text("Recent actions: 📋", size=18, weight="bold"))
            
            recent = dev["recent_actions"][-10:]
            if not recent:
                details_controls.append(ft.Text("No actions yet."))
            else:
                for a in reversed(recent):
                    details_controls.append(ft.Text(f"• {a}"))

            body = ft.Column(details_controls, spacing=8)

        return ft.View(
            route=f"/details/{device_id}",
            controls=[
                ft.AppBar(
                    title=ft.Text(f"Details: {title}"),
                    bgcolor=ft.Colors.WHITE,
                    actions=[
                        ft.TextButton(
                            "Overview", on_click=lambda e: page.go("/")
                        ),
                        ft.TextButton(
                            "Statistics",
                            on_click=lambda e: page.go("/statistics"),
                        ),
                    ],
                ),
                ft.Container(
                    padding=20,
                    content=ft.Column(
                        [
                            ft.Text(title, size=26, weight="bold"),
                            ft.Divider(),
                            body,
                            ft.ElevatedButton(
                                "Back to Overview",
                                on_click=lambda e: page.go("/"),
                            ),
                        ],
                        spacing=16,
                    ),
                ),
            ],
            scroll=ft.ScrollMode.ADAPTIVE
        )

    # -----------------------------------------------------------------
    # 7. NAVIGATION & ROUTING
    # -----------------------------------------------------------------

    def route_change(e: ft.RouteChangeEvent):
        page.views.clear()

        if page.route == "/":
            page.views.append(build_overview_view())
        elif page.route == "/statistics":
            page.views.append(build_statistics_view())
        elif page.route.startswith("/details/"):
            dev_id = page.route.split("/")[-1]
            page.views.append(build_details_view(dev_id))
        else:
            page.views.append(build_overview_view())

        page.update()

    page.on_route_change = route_change

    page.go("/")


if __name__ == "__main__":
    ft.app(target=main)