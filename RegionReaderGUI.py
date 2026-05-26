import os
import ctypes
import tkinter as tk
from PIL import ImageGrab

from ReadText import read_highlighted_substats
from ScoreText import calculate_strength_from_lines


# Fix Windows DPI scaling issue
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


TRANSPARENT_COLOUR = "#ff00ff"
MIN_WIDTH = 200
MIN_HEIGHT = 300
OUTPUT_FOLDER = "Cropped"
OUTPUT_IMAGE = "stat_panel.png"


class RegionReaderGUI:
    def __init__(self):
        self.root = tk.Tk()

        self.root.title("WuWa Echo Reader")

        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"360x400+{screen_width - 500}+100")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.resizable(True, True)
        self.root.attributes("-topmost", True)

        # True transparent centre colour
        self.root.attributes("-transparentcolor", TRANSPARENT_COLOUR)

        self.root.configure(bg="white")

        self.build_ui()

    def build_ui(self):
        self.main_frame = tk.Frame(
            self.root,
            bg="white",
            bd=0
        )
        self.main_frame.pack(fill="both", expand=True)

        # Black border around reading area
        self.read_area_border = tk.Frame(
            self.main_frame,
            bg="black",
            bd=0
        )
        self.read_area_border.pack(
            fill="both",
            expand=True,
            padx=6,
            pady=(6, 4)
        )

        # True transparent reading area
        self.read_area = tk.Frame(
            self.read_area_border,
            bg=TRANSPARENT_COLOUR,
            bd=0
        )
        self.read_area.pack(
            fill="both",
            expand=True,
            padx=2,
            pady=2
        )

        # Bottom control bar
        self.bottom_bar = tk.Frame(
            self.main_frame,
            bg="white",
            height=40
        )
        self.bottom_bar.pack(
            fill="x",
            side="bottom",
            padx=6,
            pady=(0, 6)
        )

        self.scan_button = tk.Button(
            self.bottom_bar,
            text="Scan",
            command=self.scan_echo,
            font=("Segoe UI", 12, "bold"),
            width=12,
            height=1,
            bg="#e8f0ff",
            fg="black",
            activebackground="#cfe0ff",
            activeforeground="black",
            relief="raised",
            bd=1,
            cursor="hand2"
        )
        self.scan_button.pack(
            side="left",
            padx=(0, 10),
            pady=4
        )

        self.value_label = tk.Label(
            self.bottom_bar,
            text="Value:",
            bg="white",
            fg="black",
            font=("Segoe UI", 10)
        )
        self.value_label.pack(
            side="left",
            pady=4
        )

        self.value_box = tk.Label(
            self.bottom_bar,
            text="--%",
            bg="white",
            fg="black",
            font=("Segoe UI", 12),
            width=12,
            relief="solid",
            bd=1,
            anchor="center"
        )
        self.value_box.pack(
            side="left",
            padx=(6, 0),
            pady=4
        )

    def get_read_area_bbox(self):
        self.root.update_idletasks()

        left = self.read_area.winfo_rootx()
        top = self.read_area.winfo_rooty()
        right = left + self.read_area.winfo_width()
        bottom = top + self.read_area.winfo_height()

        return left, top, right, bottom

    def capture_read_area(self):
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)

        bbox = self.get_read_area_bbox()
        screenshot = ImageGrab.grab(bbox=bbox)

        output_path = os.path.join(OUTPUT_FOLDER, OUTPUT_IMAGE)
        screenshot.save(output_path)

        return output_path

    def scan_echo(self):
        try:
            self.value_box.config(text="Reading...")
            self.root.update_idletasks()

            image_path = self.capture_read_area()

            ocr_lines = read_highlighted_substats(image_path)

            strength_percent = calculate_strength_from_lines(ocr_lines)

            self.value_box.config(text=f"{strength_percent:.2f}%")

            print("\nOCR lines:")
            for line in ocr_lines:
                print(line)

            print(f"\nStrength: {strength_percent:.2f}%")

        except Exception as error:
            self.value_box.config(text="Error")
            print("Scan failed:")
            print(error)

    def run(self):
        self.root.mainloop()