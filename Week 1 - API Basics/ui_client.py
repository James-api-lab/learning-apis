# ui_client.py
import threading
import requests
import tkinter as tk
from tkinter import ttk, messagebox

BASE = "http://127.0.0.1:8000"  # your FastAPI server

def fetch_weather(city: str, units: str, use_ai: bool, set_status, set_result, btn):
    try:
        btn.config(state="disabled")
        set_status("Fetching…")
        endpoint = "/weather/summary/by-city" if use_ai else "/weather/by-city"
        r = requests.get(f"{BASE}{endpoint}", params={"city": city, "units": units}, timeout=30)
        r.raise_for_status()
        data = r.json()
        # Prefer AI summary if present; else fallback to local summary
        text = data.get("summary") or f"{data}"
        set_result(text)
        set_status("Done")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Request Error", str(e))
        set_status("Error")
    finally:
        btn.config(state="normal")

def on_get_weather():
    city = city_var.get().strip()
    if not city:
        messagebox.showwarning("Missing city", "Please type a city name.")
        return
    units = units_var.get()
    use_ai = ai_var.get() == 1

    # run network call in a thread so the UI doesn’t freeze
    threading.Thread(
        target=fetch_weather,
        args=(city, units, use_ai, status_var.set, result_var.set, get_btn),
        daemon=True
    ).start()

# ---- UI ----
root = tk.Tk()
root.title("Local Weather Client")

main = ttk.Frame(root, padding=14)
main.grid(sticky="nsew")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

city_var = tk.StringVar(value="Seattle")
units_var = tk.StringVar(value="imperial")
ai_var = tk.IntVar(value=1)  # 1 = use AI summary

ttk.Label(main, text="City").grid(row=0, column=0, sticky="w")
city_entry = ttk.Entry(main, textvariable=city_var, width=28)
city_entry.grid(row=0, column=1, columnspan=2, sticky="ew", padx=(6,0))

ttk.Label(main, text="Units").grid(row=1, column=0, sticky="w", pady=(8,0))
units_menu = ttk.OptionMenu(main, units_var, "imperial", "imperial", "metric")
units_menu.grid(row=1, column=1, sticky="w", pady=(8,0))

ai_chk = ttk.Checkbutton(main, text="AI-polished summary", variable=ai_var)
ai_chk.grid(row=1, column=2, sticky="w", pady=(8,0))

result_var = tk.StringVar(value="Result will appear here.")
result_label = ttk.Label(main, textvariable=result_var, wraplength=420, justify="left")
result_label.grid(row=3, column=0, columnspan=3, sticky="w", pady=(10,0))

status_var = tk.StringVar(value="Idle")
status_label = ttk.Label(main, textvariable=status_var, foreground="gray")
status_label.grid(row=4, column=0, columnspan=3, sticky="w", pady=(6,0))

get_btn = ttk.Button(main, text="Get Weather", command=on_get_weather)
get_btn.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10,0))

for i in range(3):
    main.columnconfigure(i, weight=1)

# Start the app
if __name__ == "__main__":
    root.mainloop()
