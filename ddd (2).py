
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import sqlite3
import math
import pandas as pd


# =========================
# SETTINGS
# =========================

DB_PATH = Path(__file__).with_name("weather_data.db")

REQUIRED_COLUMNS = [
    "observation_time",
    "air_temperature",
    "relative_humidity",
    "station_pressure",
    "wind_speed",
    "wind_direction",
    "precipitation_type",
    "precipitation",
    "snow_depth",
    "solar_irradiance",
    "sunshine_duration",
    "cloud_cover",
    "visibility"
]

ERROR_COLUMNS = [
    "Row",
    "Column",
    "Value",
    "Error Type",
    "Description"
]

selected_file = None
weather_data = None

placeholder_active = {}


# =========================
# MAIN WINDOW
# =========================

root = tk.Tk()
root.title("Weather Data Management System")
root.geometry("1150x720")
root.minsize(950, 600)
root.configure(bg="#f2f2f2")


# =========================
# FUNCTIONS
# =========================

def get_entry_value(entry):
    if placeholder_active.get(entry, False):
        return ""

    return entry.get().strip()


def update_confirm_style():

    station = get_entry_value(station_entry)
    longitude = get_entry_value(longitude_entry)
    latitude = get_entry_value(latitude_entry)

    ready = (
        selected_file is not None
        and station != ""
        and longitude != ""
        and latitude != ""
    )

    if ready:
        confirm_button.config(
            state="normal",
            bg="#198754",
            activebackground="#157347",
            fg="white"
        )
    else:
        confirm_button.config(
            state="disabled",
            bg="#999999",
            activebackground="#999999",
            fg="white"
        )


# =========================
# PLACEHOLDER SYSTEM
# =========================

def add_placeholder(entry, placeholder):

    placeholder_active[entry] = True

    entry.config(state="normal")
    entry.delete(0, tk.END)
    entry.insert(0, placeholder)
    entry.config(fg="#888888")

    entry.config(state="disabled")

    def on_focus_in(event):

        if selected_file is None:
            return

        entry.config(state="normal")

        if placeholder_active.get(entry, False):
            entry.delete(0, tk.END)
            entry.config(fg="#222222")
            placeholder_active[entry] = False

        update_confirm_style()

    def on_focus_out(event):

        if entry.get().strip() == "":
            entry.delete(0, tk.END)
            entry.insert(0, placeholder)
            entry.config(fg="#888888")
            placeholder_active[entry] = True

        update_confirm_style()

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)
    entry.bind("<KeyRelease>", lambda event: update_confirm_style())


def set_station_fields_enabled(enabled):

    entries = (
        station_entry,
        longitude_entry,
        latitude_entry
    )

    for entry in entries:

        if enabled:

            entry.config(state="normal")

            if placeholder_active.get(entry, False):
                entry.config(fg="#888888")
            else:
                entry.config(fg="#222222")

        else:

            entry.config(state="normal")

            # Restore placeholder if the field is empty
            if entry.get().strip() == "":
                entry.delete(0, tk.END)

                if entry == station_entry:
                    placeholder = "Station Name"
                elif entry == longitude_entry:
                    placeholder = "Longitude"
                else:
                    placeholder = "Latitude"

                entry.insert(0, placeholder)
                placeholder_active[entry] = True

            entry.config(
                fg="#888888" if placeholder_active.get(entry, False) else "#222222",
                disabledforeground="#888888",
                state="disabled"
            )

    update_confirm_style()


# =========================
# CSV PREVIEW
# =========================

def show_preview(data):

    for item in preview_tree.get_children():
        preview_tree.delete(item)

    columns = list(data.columns)

    preview_tree["columns"] = columns
    preview_tree["show"] = "headings"

    for column in columns:

        preview_tree.heading(
            column,
            text=column
        )

        preview_tree.column(
            column,
            width=130,
            minwidth=100,
            anchor="center"
        )

    for _, row in data.head(100).iterrows():

        values = [
            "" if pd.isna(value) else str(value)
            for value in row
        ]

        preview_tree.insert(
            "",
            tk.END,
            values=values
        )


# =========================
# SELECT CSV
# =========================

def select_csv():

    global selected_file, weather_data

    file_path = filedialog.askopenfilename(
        title="Select Weather CSV File",
        filetypes=[
            ("CSV Files", "*.csv"),
            ("All Files", "*.*")
        ]
    )

    if not file_path:
        return

    try:

        data = pd.read_csv(file_path)

        if data.empty:
            messagebox.showerror(
                "Error",
                "The selected CSV file is empty."
            )
            return

        missing_columns = [
            column
            for column in REQUIRED_COLUMNS
            if column not in data.columns
        ]

        if missing_columns:

            messagebox.showerror(
                "Missing Columns",
                "The following columns are missing:\n\n"
                + "\n".join(missing_columns)
            )

            return

        selected_file = file_path
        weather_data = data

        file_label.config(
            text=Path(file_path).name,
            fg="#198754"
        )

        set_station_fields_enabled(True)

        show_preview(data)

        update_confirm_style()

    except Exception as error:

        messagebox.showerror(
            "CSV Error",
            str(error)
       
  
        )


# =========================
# NUMBER CONVERSION
# =========================

def get_number(value):

    if pd.isna(value):
        return None

    try:

        number = float(value)

        if not math.isfinite(number):
            return None

        return number

    except (ValueError, TypeError):
        return None


# =========================
# VALIDATION
# =========================

def validate_weather_data(data):

    critical_errors = []
    suspicious_errors = []

    critical_rows = set()
    suspicious_rows = set()
    clean_rows = set()

    for index, row in data.iterrows():

        row_number = index + 2

        row_has_critical = False
        row_has_suspicious = False

        def add_error(column, value, error_type, description):

            nonlocal row_has_critical, row_has_suspicious

            error = {
                "Row": row_number,
                "Column": column,
                "Value": value,
                "Error Type": error_type,
                "Description": description
            }

            if error_type == "Critical":
                critical_errors.append(error)
                row_has_critical = True

            else:
                suspicious_errors.append(error)
                row_has_suspicious = True

        def check_number(column):

            value = row[column]
            number = get_number(value)

            if number is None:

                add_error(
                    column,
                    value,
                    "Critical",
                    "Value must be a valid number."
                )

            return number

        # Air temperature
        temperature = check_number("air_temperature")

        if temperature is not None:

            if temperature < -90 or temperature > 70:

                add_error(
                    "air_temperature",
                    temperature,
                    "Suspicious",
                    "Air temperature is outside the expected range (-90 to 70)."
                )

        # Relative humidity
        humidity = check_number("relative_humidity")

        if humidity is not None:

            if humidity < 0 or humidity > 100:

                add_error(
                    "relative_humidity",
                    humidity,
                    "Suspicious",
                    "Relative humidity must be between 0 and 100."
                )

        # Station pressure
        pressure = check_number("station_pressure")

        if pressure is not None:

            if pressure < 500 or pressure > 1080:

                add_error(
                    "station_pressure",
                    pressure,
                    "Suspicious",
                    "Station pressure is outside the expected range (500 to 1080)."
                )

        # Wind speed
        wind_speed = check_number("wind_speed")

        if wind_speed is not None:

            if wind_speed < 0:

                add_error(
                    "wind_speed",
                    wind_speed,
                    "Critical",
                    "Wind speed cannot be negative."
                )

            elif wind_speed > 113:

                add_error(
                    "wind_speed",
                    wind_speed,
                    "Suspicious",
                    "Wind speed is above 113."
                )

        # Wind direction
        wind_direction = check_number("wind_direction")

        if wind_direction is not None:

            if wind_direction < 0:

                add_error(
                    "wind_direction",
                    wind_direction,
                    "Critical",
                    "Wind direction cannot be negative."
                )

            elif wind_direction > 360:

                add_error(
                    "wind_direction",
                    wind_direction,
                    "Suspicious",
                    "Wind direction cannot exceed 360."
                )

        # Precipitation type
        precipitation_type = row["precipitation_type"]

        if pd.isna(precipitation_type) or str(precipitation_type).strip() == "":

            precipitation_type = ""

            add_error(
                "precipitation_type",
                precipitation_type,
                "Critical",
                "Precipitation type cannot be empty."
            )

        else:

            precipitation_type = str(
                precipitation_type
            ).strip().lower()

            valid_types = [
                "none",
                "rain",
                "snow",
                "sleet",
                "hail",
                "freezing_rain"
            ]

            if precipitation_type not in valid_types:

                add_error(
                    "precipitation_type",
                    precipitation_type,
                    "Suspicious",
                    "Invalid precipitation type."
                )

        # Precipitation amount
        precipitation = check_number("precipitation")

        if precipitation is not None:

            if precipitation < 0:

                add_error(
                    "precipitation",
                    precipitation,
                    "Critical",
                    "Precipitation cannot be negative."
                )

            elif precipitation_type == "none" and precipitation != 0:

                add_error(
                    "precipitation",
                    precipitation,
                    "Critical",
                    "Precipitation must be zero when precipitation type is none."
                )

            elif precipitation_type in [
                "rain",
                "sleet",
                "hail",
                "freezing_rain"
            ] and precipitation > 305:

                add_error(
                    "precipitation",
                    precipitation,
                    "Suspicious",
                    "Precipitation amount is above 305."
                )

            elif precipitation_type == "snow" and precipitation > 100:

                add_error(
                    "precipitation",
                    precipitation,
                    "Suspicious",
                    "Snow precipitation amount is above 100."
                )

        # Snow depth
        snow_depth = check_number("snow_depth")

        if snow_depth is not None:

            if snow_depth < 0:

                add_error(
                    "snow_depth",
                    snow_depth,
                    "Critical",
                    "Snow depth cannot be negative."
                )

            elif not snow_depth.is_integer():

                add_error(
                    "snow_depth",
                    snow_depth,
                    "Critical",
                    "Snow depth must be an integer."
                )

            elif snow_depth > 996:

                add_error(
                    "snow_depth",
                    snow_depth,
                    "Suspicious",
                    "Snow depth is above 996."
                )

        # Solar irradiance
        solar = check_number("solar_irradiance")

        if solar is not None:

            if solar < 0:

                add_error(
                    "solar_irradiance",
                    solar,
                    "Critical",
                    "Solar irradiance cannot be negative."
                )

            elif solar > 2000:

                add_error(
                    "solar_irradiance",
                    solar,
                    "Suspicious",
                    "Solar irradiance is above 2000."
                )

        # Sunshine duration
        sunshine = check_number("sunshine_duration")

        if sunshine is not None:

            if sunshine < 0 or sunshine > 60:

                add_error(
                    "sunshine_duration",
                    sunshine,
                    "Critical",
                    "Sunshine duration must be between 0 and 60."
                )

        # Cloud cover
        cloud_cover = check_number("cloud_cover")

        if cloud_cover is not None:

            if cloud_cover < 0 or cloud_cover > 100:

                add_error(
                    "cloud_cover",
                    cloud_cover,
                    "Critical",
                    "Cloud cover must be between 0 and 100."
                )

        # Visibility
        visibility = check_number("visibility")

        if visibility is not None:

            if visibility < 0:

                add_error(
                    "visibility",
                    visibility,
                    "Critical",
                    "Visibility cannot be negative."
                )

            elif visibility > 100000:

                add_error(
                    "visibility",
                    visibility,
                    "Suspicious",
                    "Visibility is above 100000."
                )

        # Classify row
        if row_has_critical:

            critical_rows.add(index)

        elif row_has_suspicious:

            suspicious_rows.add(index)

        else:

            clean_rows.add(index)

    return (
        critical_errors,
        suspicious_errors,
        critical_rows,
        suspicious_rows,
        clean_rows
    )


# =========================
# DATABASE
# =========================

def save_to_database(
    data,
    station_info,
    critical_errors,
    suspicious_errors,
    critical_rows,
    suspicious_rows,
    clean_rows
):

    try:

        suspicious_indexes = sorted(suspicious_rows)

        if suspicious_indexes:

            answer = messagebox.askyesno(
                "Suspicious Data",
                f"{len(suspicious_indexes)} rows have suspicious values.\n\n"
                "Do you want to include these rows in Main Data?"
            )

            if answer:
                accepted_suspicious = suspicious_indexes
            else:
                accepted_suspicious = []

        else:

            accepted_suspicious = []

        accepted_indexes = (
            sorted(clean_rows)
            + accepted_suspicious
        )

        main_data = data.loc[accepted_indexes].copy()

        critical_df = pd.DataFrame(
            critical_errors,
            columns=ERROR_COLUMNS
        )

        suspicious_df = pd.DataFrame(
            suspicious_errors,
            columns=ERROR_COLUMNS
        )

        station_df = pd.DataFrame(
            [station_info]
        )

        with sqlite3.connect(DB_PATH) as connection:

            main_data.to_sql(
                "Main Data",
                connection,
                if_exists="replace",
                index=False
            )

            station_df.to_sql(
                "Station Info",
                connection,
                if_exists="replace",
                index=False
            )

            critical_df.to_sql(
                "Critical Errors",
                connection,
                if_exists="replace",
                index=False
            )

            suspicious_df.to_sql(
                "Suspicious Errors",
                connection,
                if_exists="replace",
                index=False
            )

        messagebox.showinfo(
            "Success",
            "Database created successfully!\n\n"
            f"Main Data: {len(main_data)} rows\n"
            f"Critical Errors: {len(critical_errors)}\n"
            f"Suspicious Errors: {len(suspicious_errors)}\n\n"
            f"Database location:\n{DB_PATH}"
        )

    except Exception as error:

        messagebox.showerror(
            "Database Error",
            str(error)
        )


# =========================
# CONFIRM
# =========================

def confirm_data():

    if selected_file is None or weather_data is None:
        messagebox.showwarning(
            "Warning",
            "Please select a CSV file first."
        )
        return

    station_name = get_entry_value(station_entry)
    longitude_text = get_entry_value(longitude_entry)
    latitude_text = get_entry_value(latitude_entry)

    if not station_name or not longitude_text or not latitude_text:

        messagebox.showwarning(
            "Missing Information",
            "Please complete all station information fields."
        )
        return

    try:

        longitude = float(longitude_text)
        latitude = float(latitude_text)

        if not math.isfinite(longitude) or not -180 <= longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180.")

        if not math.isfinite(latitude) or not -90 <= latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90.")

    except ValueError as error:

        messagebox.showerror(
            "Invalid Station Information",
            str(error)
        )
        return

    station_info = {
        "Station Name": station_name,
        "Longitude": longitude,
        "Latitude": latitude
    }

    try:

        (
            critical_errors,
            suspicious_errors,
            critical_rows,
            suspicious_rows,
            clean_rows
        ) = validate_weather_data(weather_data)

        save_to_database(
            weather_data,
            station_info,
            critical_errors,
            suspicious_errors,
            critical_rows,
            suspicious_rows,
            clean_rows
        )

    except Exception as error:

        messagebox.showerror(
            "Error",
            str(error)
        )


# =========================
# GUI
# =========================

main_frame = tk.Frame(
    root,
    bg="#f2f2f2",
    padx=20,
    pady=15
)

main_frame.pack(
    fill="both",
    expand=True
)


# Title
title_label = tk.Label(
    main_frame,
    text="Weather Data Management System",
    font=("Arial", 19, "bold"),
    bg="#f2f2f2",
    fg="#222222"
)

title_label.pack(pady=(0, 20))


# File section
file_frame = tk.LabelFrame(
    main_frame,
    text="CSV File",
    font=("Arial", 11, "bold"),
    bg="#f2f2f2",
    padx=12,
    pady=12
)

file_frame.pack(
    fill="x",
    pady=5
)

upload_button = tk.Button(
    file_frame,
    text="Select CSV File",
    font=("Arial", 10, "bold"),
    bg="#0d6efd",
    fg="white",
    activebackground="#0b5ed7",
    relief="flat",
    padx=15,
    pady=7,
    command=select_csv
)

upload_button.pack(side="left")

file_label = tk.Label(
    file_frame,
    text="No file selected",
    font=("Arial", 10),
    bg="#f2f2f2",
    fg="#666666"
)

file_label.pack(
    side="left",
    padx=15
)


# Station information
station_frame = tk.LabelFrame(
    main_frame,
    text="Station Information",
    font=("Arial", 11, "bold"),
    bg="#f2f2f2",
    padx=12,
    pady=12
)

station_frame.pack(
    fill="x",
    pady=10
)

station_entry = tk.Entry(
    station_frame,
    font=("Arial", 11),
    width=25,
    relief="solid",
    bd=1
)

longitude_entry = tk.Entry(
    station_frame,
    font=("Arial", 11),
    width=25,
    relief="solid",
    bd=1
)

latitude_entry = tk.Entry(
    station_frame,
    font=("Arial", 11),
    width=25,
    relief="solid",
    bd=1
)

station_entry.grid(
    row=0,
    column=0,
    padx=8,
    pady=8
)

longitude_entry.grid(
    row=0,
    column=1,
    padx=8,
    pady=8
)

latitude_entry.grid(
    row=0,
    column=2,
    padx=8,
    pady=8
)


# Add placeholders
add_placeholder(
    station_entry,
    "Station Name"
)

add_placeholder(
    longitude_entry,
    "Longitude"
)

add_placeholder(
    latitude_entry,
    "Latitude"
)


# Preview section
preview_frame = tk.LabelFrame(
    main_frame,
    text="CSV Preview",
    font=("Arial", 11, "bold"),
    bg="#f2f2f2",
    padx=10,
    pady=10
)

preview_frame.pack(
    fill="both",
    expand=True,
    pady=5
)

tree_container = tk.Frame(
    preview_frame,
    bg="#f2f2f2"
)

tree_container.pack(
    fill="both",
    expand=True
)

preview_tree = ttk.Treeview(
    tree_container,
    show="headings"
)

vertical_scrollbar = ttk.Scrollbar(
    tree_container,
    orient="vertical",
    command=preview_tree.yview
)

horizontal_scrollbar = ttk.Scrollbar(
    tree_container,
    orient="horizontal",
    command=preview_tree.xview
)

preview_tree.configure(
    yscrollcommand=vertical_scrollbar.set,
    xscrollcommand=horizontal_scrollbar.set
)

preview_tree.grid(
    row=0,
    column=0,
    sticky="nsew"
)

vertical_scrollbar.grid(
    row=0,
    column=1,
    sticky="ns"
)

horizontal_scrollbar.grid(
    row=1,
    column=0,
    sticky="ew"
)

tree_container.grid_rowconfigure(0, weight=1)
tree_container.grid_columnconfigure(0, weight=1)


# Confirm button
confirm_button = tk.Button(
    main_frame,
    text="Confirm",
    font=("Arial", 11, "bold"),
    bg="#999999",
    fg="white",
    activebackground="#157347",
    relief="flat",
    padx=35,
    pady=10,
    state="disabled",
    command=confirm_data
)

confirm_button.pack(
    pady=12
)


# Initial state
set_station_fields_enabled(False)


# =========================
# RUN
# =========================

root.mainloop()
