# Version: 2024-10-12
import tkinter as tk
from tkinter import filedialog, colorchooser, simpledialog, messagebox
import webbrowser
import svgwrite
import xml.etree.ElementTree as ET
import os
import sys
import requests
import re

class VectorLineDrawer:
    def __init__(self, master, loaded_file=None):
        self.master = master
        self.master.title("Vector Line Drawing Program")
        
        self.canvas = tk.Canvas(self.master, bg='white', width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.paths = []
        self.current_path = []
        self.undo_stack = []
        self.redo_stack = []
        self.pen_color = 'black'
        self.pen_width = 1
        self.loaded_file = loaded_file
        self.documentation_url = "https://github.com/OpenAnimationLibrary/extrastuff/blob/master/tools%20and%20utilities/drawing/vector/readme.md"
        self.update_url = "https://raw.githubusercontent.com/OpenAnimationLibrary/extrastuff/master/tools%20and%20utilities/drawing/vector/vectordraw.py"
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        self.create_menu()
        self.bind_shortcuts()
        self.create_widgets()
        
        if self.loaded_file:
            self.load_svg(self.loaded_file)

    def create_menu(self):
        menu_bar = tk.Menu(self.master)
        self.master.config(menu=menu_bar)
        
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_canvas)
        file_menu.add_command(label="Save as SVG", command=self.save_as_svg)
        file_menu.add_command(label="Load SVG", command=self.load_svg_dialog)
        file_menu.add_command(label="Restart", command=self.restart_program)
        file_menu.add_command(label="Exit", command=self.master.quit)
        
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo)
        edit_menu.add_command(label="Redo", command=self.redo)
        
        options_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Options", menu=options_menu)
        options_menu.add_command(label="Select Pen Color", command=self.select_pen_color)
        
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Open Documentation", command=self.open_documentation)
        help_menu.add_command(label="Edit Documentation URL", command=self.edit_documentation_url)
        help_menu.add_command(label="Check for Updates", command=self.check_for_updates)

    def bind_shortcuts(self):
        self.master.bind("<Control-z>", lambda event: self.undo())
        self.master.bind("<Control-y>", lambda event: self.redo())
        self.master.bind("<Control-s>", lambda event: self.save_as_svg())

    def create_widgets(self):
        self.brush_size_label = tk.Label(self.master, text="Brush Size:")
        self.brush_size_label.pack(side=tk.LEFT, padx=5)
        
        self.brush_size_slider = tk.Scale(self.master, from_=0, to=100, orient=tk.HORIZONTAL, command=self.update_brush_size)
        self.brush_size_slider.set(self.pen_width)
        self.brush_size_slider.pack(side=tk.LEFT)

    def update_brush_size(self, value):
        self.pen_width = int(value)

    def select_pen_color(self):
        color_code = colorchooser.askcolor(title="Choose Pen Color")[1]
        if color_code:
            self.pen_color = color_code

    def on_press(self, event):
        self.current_path = [(event.x, event.y)]

    def on_drag(self, event):
        if self.current_path is not None:
            self.current_path.append((event.x, event.y))
            self.canvas.delete("current_line")  # Delete the previous line to create a smooth effect
            self.canvas.create_line(self.current_path, fill=self.pen_color, width=self.pen_width, tags="current_line", smooth=True, capstyle=tk.ROUND)

    def on_release(self, event):
        if self.current_path:
            self.canvas.delete("current_line")  # Remove the temporary line
            self.paths.append((self.current_path, self.pen_color, self.pen_width))
            self.undo_stack.append((self.current_path, self.pen_color, self.pen_width))
            self.current_path = None
            self.redo_stack.clear()
            self.redraw_canvas()

    def undo(self):
        if self.paths:
            path = self.paths.pop()
            self.undo_stack.append(path)
            self.redraw_canvas()

    def redo(self):
        if self.undo_stack:
            path = self.undo_stack.pop()
            self.paths.append(path)
            self.redraw_canvas()

    def redraw_canvas(self):
        self.canvas.delete("all")
        for path, color, width in self.paths:
            self.canvas.create_line(path, fill=color, width=width, smooth=True, capstyle=tk.ROUND)

    def save_as_svg(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".svg", filetypes=[("SVG files", "*.svg")])
        if not file_path:
            return
        
        dwg = svgwrite.Drawing(file_path, profile='tiny', size=(800, 600))
        for path, color, width in self.paths:
            for i in range(1, len(path)):
                start_x, start_y = path[i - 1]
                end_x, end_y = path[i]
                dwg.add(dwg.line(start=(start_x, start_y), end=(end_x, end_y), stroke=color, stroke_width=width, stroke_linecap='round'))
        dwg.save()

    def load_svg_dialog(self):
        file_path = filedialog.askopenfilename(filetypes=[("SVG files", "*.svg")])
        if not file_path:
            return
        self.loaded_file = file_path
        self.load_svg(file_path)

    def load_svg(self, file_path):
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        self.paths.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        
        for element in root.findall(".//{http://www.w3.org/2000/svg}line"):
            start_x = float(element.get("x1"))
            start_y = float(element.get("y1"))
            end_x = float(element.get("x2"))
            end_y = float(element.get("y2"))
            color = element.get("stroke", "black")
            if color.startswith("rgb"):
                color = "black"  # Fallback for unsupported color formats
            width = float(element.get("stroke-width", 1))
            self.paths.append(([(start_x, start_y), (end_x, end_y)], color, width))
        
        self.redraw_canvas()

    def new_canvas(self):
        self.paths.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.redraw_canvas()

    def restart_program(self):
        self.master.destroy()
        python = sys.executable
        os.execl(python, python, *sys.argv, self.loaded_file if self.loaded_file else "")

    def open_documentation(self):
        webbrowser.open(self.documentation_url)

    def edit_documentation_url(self):
        new_url = simpledialog.askstring("Edit Documentation URL", "Enter the new documentation URL:", initialvalue=self.documentation_url)
        if new_url:
            self.documentation_url = new_url

    def check_for_updates(self):
        try:
            response = requests.get(self.update_url)
            if response.status_code == 200:
                online_content = response.text
                local_version = self.get_version_from_content(self.get_local_content())
                online_version = self.get_version_from_content(online_content)
                if online_version > local_version:
                    local_file_path = os.path.abspath(__file__)
                    with open(local_file_path, 'w', encoding='utf-8') as file:
                        file.write(online_content)
                    messagebox.showinfo("Update", "The application has been updated. Please restart the program.")
                else:
                    messagebox.showinfo("Update", "You already have the latest version.")
            else:
                messagebox.showerror("Update", "Failed to check for updates. Status code: {}".format(response.status_code))
        except Exception as e:
            messagebox.showerror("Update", "An error occurred while checking for updates: {}".format(e))

    def get_version_from_content(self, content):
        version_match = re.search(r"# Version: (\d{4}-\d{2}-\d{2})", content)
        if version_match:
            return datetime.strptime(version_match.group(1), "%Y-%m-%d")
        return datetime.min

    def get_local_content(self):
        local_file_path = os.path.abspath(__file__)
        with open(local_file_path, 'r', encoding='utf-8') as file:
            return file.read()

if __name__ == "__main__":
    loaded_file = sys.argv[1] if len(sys.argv) > 1 else None
    root = tk.Tk()
    app = VectorLineDrawer(master=root, loaded_file=loaded_file)
    root.mainloop()