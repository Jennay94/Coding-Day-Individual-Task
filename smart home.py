import flet as ft
from datetime import datetime

def main(page: ft.Page):
    page.title = "Smart Home Controller"
    page.window_width = 900
    page.window_height = 700
    page.padding = 20
    page.bgcolor = ft.Colors.GREY_100
    
    # Device states
    light_on = ft.Ref[bool]()
    light_on.current = False
    
    door_locked = ft.Ref[bool]()
    door_locked.current = True
    
    temperature = ft.Ref[float]()
    temperature.current = 22.0
    
    fan_speed = ft.Ref[int]()
    fan_speed.current = 0
    
    # Action log list
    action_log = []
    
    # Create pie chart
    pie_chart = ft.PieChart(
        sections=[],
        center_space_radius=0,
    )
    
    # Create action log table
    action_log_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Time", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Device", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Action", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("User", weight=ft.FontWeight.BOLD)),
        ],
        rows=[],
    )
    
    # Update pie chart
    def update_pie_chart():
        light_power = 60 if light_on.current else 0
        fan_power = fan_speed.current * 20
        
        pie_chart.sections.clear()
        pie_chart.sections.append(
            ft.PieChartSection(
                value=light_power if light_power > 0 else 1,
                title="Light",
                title_style=ft.TextStyle(color=ft.Colors.WHITE, size=12),
                color=ft.Colors.YELLOW,
            )
        )
        pie_chart.sections.append(
            ft.PieChartSection(
                value=5,
                title="Door",
                title_style=ft.TextStyle(color=ft.Colors.WHITE, size=12),
                color=ft.Colors.BLUE,
            )
        )
        pie_chart.sections.append(
            ft.PieChartSection(
                value=15,
                title="Thermostat",
                title_style=ft.TextStyle(color=ft.Colors.WHITE, size=12),
                color=ft.Colors.RED,
            )
        )
        pie_chart.sections.append(
            ft.PieChartSection(
                value=fan_power if fan_power > 0 else 1,
                title="Fan",
                title_style=ft.TextStyle(color=ft.Colors.WHITE, size=12),
                color=ft.Colors.CYAN,
            )
        )
        page.update()
    
    # Function to add action to log
    def add_action(device, action):
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        action_log.insert(0, {
            "time": time_str,
            "device": device,
            "action": action,
            "user": "User"
        })
        update_action_log_table()
        update_pie_chart()
    
    def update_action_log_table():
        action_log_table.rows.clear()
        for log in action_log[:10]:  # Show last 10 actions
            action_log_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(log["time"])),
                        ft.DataCell(ft.Text(log["device"])),
                        ft.DataCell(ft.Text(log["action"])),
                        ft.DataCell(ft.Text(log["user"])),
                    ]
                )
            )
        page.update()
    
    # Light status text
    light_status = ft.Text("Status: OFF", size=14, color=ft.Colors.GREY_700)
    light_button = ft.ElevatedButton("Turn ON", bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE)
    
    # Door status text
    door_status = ft.Text("Door: LOCKED", size=14, color=ft.Colors.GREY_700)
    door_button = ft.ElevatedButton("Unlock", bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE)
    
    # Temperature display
    temp_display = ft.Text(f"Set point: {temperature.current:.1f} °C", size=14, color=ft.Colors.GREY_700)
    temp_slider = ft.Slider(min=15, max=30, value=22, divisions=30, label="{value}°C")
    
    # Fan speed display
    fan_display = ft.Text(f"Fan speed: {fan_speed.current}", size=14, color=ft.Colors.GREY_700)
    fan_slider = ft.Slider(min=0, max=3, value=0, divisions=3, label="{value}")
    
    # Toggle light function
    def toggle_light(e):
        light_on.current = not light_on.current
        if light_on.current:
            light_status.value = "Status: ON"
            light_button.text = "Turn OFF"
            add_action("light1", "Turn ON")
        else:
            light_status.value = "Status: OFF"
            light_button.text = "Turn ON"
            add_action("light1", "Turn OFF")
        update_pie_chart()
        page.update()
    
    # Toggle door function
    def toggle_door(e):
        door_locked.current = not door_locked.current
        if door_locked.current:
            door_status.value = "Door: LOCKED"
            door_button.text = "Unlock"
            add_action("door1", "Lock")
        else:
            door_status.value = "Door: UNLOCKED"
            door_button.text = "Lock"
            add_action("door1", "Unlock")
        page.update()
    
    # Change temperature function
    def change_temperature(e):
        temperature.current = e.control.value
        temp_display.value = f"Set point: {temperature.current:.1f} °C"
        add_action("thermostat", f"Set to {temperature.current:.1f}°C")
        page.update()
    
    # Change fan speed function
    def change_fan_speed(e):
        fan_speed.current = int(e.control.value)
        fan_display.value = f"Fan speed: {fan_speed.current}"
        add_action("fan", f"Speed set to {fan_speed.current}")
        update_pie_chart()
        page.update()
    
    # Show device details
    def show_light_details(e):
        page.controls.clear()
        
        # Get light actions
        light_actions = [log for log in action_log if log["device"] == "light1"]
        
        # Create recent actions list
        actions_column = ft.Column()
        if light_actions:
            for log in light_actions[:5]:
                actions_column.controls.append(
                    ft.Text(f"{log['time']} - {log['action']} ({log['user']})", size=14)
                )
        else:
            actions_column.controls.append(ft.Text("No recent actions", color=ft.Colors.GREY_500))
        
        details_view = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ARROW_BACK, color=ft.Colors.PINK),
                    ft.Text("Smart Home Controller + Simulator", size=16, color=ft.Colors.GREY_600)
                ], spacing=10),
                ft.Text("Smart Home Controller", size=32, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Living Room Light details", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text(f"ID: light1", size=14),
                        ft.Text(f"Type: light", size=14),
                        ft.Text(f"State: {'ON' if light_on.current else 'OFF'}", size=14),
                        ft.Divider(height=20),
                        ft.Text("Recent actions", size=20, weight=ft.FontWeight.BOLD),
                        actions_column,
                        ft.Container(height=20),
                        ft.ElevatedButton(
                            "Back to overview",
                            bgcolor=ft.Colors.BLUE,
                            color=ft.Colors.WHITE,
                            on_click=lambda e: show_overview(e)
                        ),
                    ]),
                    bgcolor=ft.Colors.GREY_100,
                    padding=20,
                    border_radius=10,
                ),
            ]),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
        )
        page.add(details_view)
        page.update()
    
    # Assign button click handlers
    light_button.on_click = toggle_light
    door_button.on_click = toggle_door
    temp_slider.on_change = change_temperature
    fan_slider.on_change = change_fan_speed
    
    # Navigation functions
    def show_overview(e):
        page.controls.clear()
        page.add(overview_view)
        page.update()
    
    def show_statistics(e):
        page.controls.clear()
        page.add(statistics_view)
        page.update()
    
    # Overview View
    overview_view = ft.Container(
        content=ft.Column([
            # Header
            ft.Row([
                ft.Icon(ft.Icons.HOME, color=ft.Colors.PINK),
                ft.Text("Smart Home Controller", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.TextButton("Overview", on_click=show_overview, style=ft.ButtonStyle(color=ft.Colors.BLUE)),
                ft.TextButton("Statistics", on_click=show_statistics, style=ft.ButtonStyle(color=ft.Colors.GREY_700)),
            ], alignment=ft.MainAxisAlignment.START),
            
            ft.Divider(),
            
            # On/Off Devices
            ft.Text("On/Off devices", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([
                # Living Room Light
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.LIGHTBULB, color=ft.Colors.YELLOW if light_on.current else ft.Colors.GREY),
                            ft.Text("Living Room Light", weight=ft.FontWeight.BOLD),
                        ]),
                        light_status,
                        ft.Text("Tap to switch the light.", size=12, color=ft.Colors.GREY_500),
                        ft.Row([
                            ft.TextButton("Details", on_click=show_light_details),
                            light_button,
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ]),
                    bgcolor=ft.Colors.YELLOW_100,
                    padding=15,
                    border_radius=10,
                    expand=True,
                ),
                
                # Front Door
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.DOOR_BACK_DOOR, color=ft.Colors.BLUE),
                            ft.Text("Front Door", weight=ft.FontWeight.BOLD),
                        ]),
                        door_status,
                        ft.Text("Tap to lock / unlock the door.", size=12, color=ft.Colors.GREY_500),
                        ft.Row([
                            ft.TextButton("Details"),
                            door_button,
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ]),
                    bgcolor=ft.Colors.BLUE_100,
                    padding=15,
                    border_radius=10,
                    expand=True,
                ),
            ], spacing=10),
            
            # Slider Controlled Devices
            ft.Text("Slider controlled devices", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([
                # Thermostat
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.THERMOSTAT, color=ft.Colors.RED),
                            ft.Text("Thermostat", weight=ft.FontWeight.BOLD),
                        ]),
                        temp_display,
                        ft.Text("Use slider to change temperature.", size=12, color=ft.Colors.GREY_500),
                        temp_slider,
                        ft.TextButton("Details"),
                    ]),
                    bgcolor=ft.Colors.PINK_100,
                    padding=15,
                    border_radius=10,
                    expand=True,
                ),
                
                # Ceiling Fan
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.AIR, color=ft.Colors.CYAN),
                            ft.Text("Ceiling Fan", weight=ft.FontWeight.BOLD),
                        ]),
                        fan_display,
                        ft.Text("0 = OFF, 3 = MAX.", size=12, color=ft.Colors.GREY_500),
                        fan_slider,
                        ft.TextButton("Details"),
                    ]),
                    bgcolor=ft.Colors.CYAN_100,
                    padding=15,
                    border_radius=10,
                    expand=True,
                ),
            ], spacing=10),
        ], scroll=ft.ScrollMode.AUTO),
        padding=20,
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
    )
    
    # Statistics View
    statistics_view = ft.Container(
        content=ft.Column([
            # Header
            ft.Row([
                ft.Icon(ft.Icons.HOME, color=ft.Colors.PINK),
                ft.Text("Smart Home Controller", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.TextButton("Overview", on_click=show_overview, style=ft.ButtonStyle(color=ft.Colors.GREY_700)),
                ft.TextButton("Statistics", on_click=show_statistics, style=ft.ButtonStyle(color=ft.Colors.BLUE)),
            ], alignment=ft.MainAxisAlignment.START),
            
            ft.Divider(),
            
            # Power Consumption
            ft.Text("Power consumption (simulated)", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=pie_chart,
                height=300,
                bgcolor=ft.Colors.GREY_50,
                border=ft.border.all(2, ft.Colors.CYAN),
                border_radius=10,
                padding=20,
            ),
            
            # Action Log
            ft.Text("Action log", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=action_log_table,
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=10,
                padding=10,
            ),
        ], scroll=ft.ScrollMode.AUTO),
        padding=20,
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
    )
    
    # Initialize with sample data
    add_action("light1", "Turn ON")
    add_action("door1", "Unlock")
    add_action("thermostat", "Set to 24.0°C")
    add_action("fan", "Speed set to 2")
    add_action("light1", "Turn OFF")
 
 
    page.add(overview_view)

# Run the app
ft.app(target=main)