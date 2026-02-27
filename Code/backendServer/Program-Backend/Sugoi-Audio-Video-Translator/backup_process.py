import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import os
import subprocess
import sys
from SubtitleProcessor import SubtitleProcessor # Assuming SubtitleProcessor.py is in the same directory

class SubtitleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ Subtitle Processor")
        self.root.geometry("600x500")
        self.root.minsize(500, 400)
        
        self.colors = {
            'bg': '#1e1e2e',
            'fg': '#cdd6f4',
            'primary': '#89b4fa',
            'secondary': '#f38ba8',
            'surface': '#313244',
            'surface_light': '#45475a',
            'border': '#585b70',
            'accent': '#b4befe'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # --- Style Configuration ---
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure("TFrame", background=self.colors['bg'])
        style.configure("TButton",
                        background=self.colors['primary'],
                        foreground=self.colors['bg'],
                        borderwidth=0,
                        font=('Segoe UI', 10, 'bold'),
                        padding=(15, 10))
        style.map("TButton", background=[("active", self.colors['accent'])])
        style.configure("Secondary.TButton",
                        background=self.colors['surface_light'],
                        foreground=self.colors['fg'])
        style.map("Secondary.TButton", background=[("active", self.colors['border'])])
        style.configure("TLabel",
                        background=self.colors['bg'],
                        foreground=self.colors['fg'],
                        font=('Segoe UI', 10))
        style.configure("Title.TLabel",
                        foreground=self.colors['primary'],
                        font=('Segoe UI', 14, 'bold'))

        # --- Main Layout ---
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)

        # --- Header ---
        ttk.Label(self.main_frame, text="✨ Subtitle Processor", style="Title.TLabel").grid(row=0, column=0, sticky=tk.W, pady=(0, 20))
        
        # --- Controls Card ---
        controls_card = ttk.Frame(self.main_frame, style="Card.TFrame", padding=15)
        controls_card.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        controls_card.columnconfigure(0, weight=1)

        # --- Folder Buttons ---
        folder_frame = ttk.Frame(controls_card, style="Card.TFrame")
        folder_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        folder_frame.columnconfigure(0, weight=1)
        folder_frame.columnconfigure(1, weight=1)

        self.input_button = ttk.Button(folder_frame, text="Open INPUT Folder", command=lambda: self.open_folder("INPUT"), style="Secondary.TButton")
        self.input_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.output_button = ttk.Button(folder_frame, text="Open OUTPUT Folder", command=lambda: self.open_folder("OUTPUT"), style="Secondary.TButton")
        self.output_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        
        self.start_button = ttk.Button(controls_card, text="Start Batch Process", command=self.start_processing_thread)
        self.start_button.grid(row=1, column=0, columnspan=2, sticky="ew", pady=10)
        
        # --- Status/Output Card ---
        output_card = ttk.Frame(self.main_frame, style="Card.TFrame", padding=15)
        output_card.grid(row=2, column=0, sticky="nsew")
        output_card.columnconfigure(0, weight=1)
        output_card.rowconfigure(1, weight=1)

        style.configure("Card.TFrame", background=self.colors['surface'], relief='flat', borderwidth=0)
        
        self.status_label = ttk.Label(output_card, text="Status:", foreground=self.colors['accent'], background=self.colors['surface'], font=('Segoe UI', 11, 'bold'))
        self.status_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        self.status_text = scrolledtext.ScrolledText(
            output_card,
            wrap=tk.WORD,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            borderwidth=0,
            padx=10,
            pady=10,
            font=('Consolas', 10)
        )
        self.status_text.grid(row=1, column=0, sticky="nsew")

        self.subtitle_processor = SubtitleProcessor()
        # Monkey patch the setProgressStatus to update the GUI
        self.subtitle_processor.setProgressStatus = self.update_status

    def open_folder(self, folder_name):
        """Opens the specified folder in the file explorer."""
        path = os.path.abspath(folder_name)
        if not os.path.exists(path):
            os.makedirs(path)
        
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            self.update_status(f"Error opening folder {folder_name}: {e}")

    def update_status(self, status):
        """Updates the status text area in a thread-safe way."""
        self.status_text.insert(tk.END, status + "\n")
        self.status_text.see(tk.END)
        print(status)

    def start_processing_thread(self):
        """Starts the batch processing in a separate thread to keep the GUI responsive."""
        self.start_button.config(state=tk.DISABLED)
        self.status_text.delete(1.0, tk.END)
        self.update_status("Starting batch process...")
        
        thread = threading.Thread(target=self.run_batch_process)
        thread.daemon = True
        thread.start()

    def run_batch_process(self):
        """Runs the subtitle processor's batch process and handles completion."""
        try:
            self.subtitle_processor.batch_process()
            self.update_status("All files are done")
        except Exception as e:
            self.update_status(f"An error occurred: {e}")
        finally:
            self.root.after(0, self.on_processing_complete)

    def on_processing_complete(self):
        """Re-enables the start button when processing is complete."""
        self.start_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = SubtitleApp(root)
    root.mainloop()