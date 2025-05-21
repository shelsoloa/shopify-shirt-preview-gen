import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
from datetime import datetime


class ImageOverlayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Overlay Tool")
        self.root.geometry("1000x600")

        # Create menu bar
        self.create_menu_bar()

        # Variables to store file paths and coordinates
        self.graphic_path = tk.StringVar()
        self.base_path = tk.StringVar()
        self.x_coord = tk.IntVar(value=0)
        self.y_coord = tk.IntVar(value=0)
        self.scale_x = tk.IntVar(value=100)  # Scale X in percentage
        self.scale_y = tk.IntVar(value=100)  # Scale Y in percentage

        # Store image objects
        self.graphic_image = None
        self.base_image = None
        self.preview_image = None
        self.current_composite = None  # Store the current composite image for export

        # Create main frames
        self.create_layout()

        # Bind variables to update preview
        self.graphic_path.trace_add("write", self.update_preview)
        self.base_path.trace_add("write", self.update_preview)
        self.x_coord.trace_add("write", self.update_preview)
        self.y_coord.trace_add("write", self.update_preview)
        self.scale_x.trace_add("write", self.update_preview)
        self.scale_y.trace_add("write", self.update_preview)

        # Schedule an initial canvas size update after UI is fully loaded
        self.root.after(100, self.update_preview)

    def create_menu_bar(self):
        # Create the menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Create File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)

        # Add menu items
        file_menu.add_command(
            label="Save", command=self.export_image, accelerator="Command+S"
        )
        file_menu.add_command(
            label="Save As...", command=self.save_as, accelerator="Shift+Command+S"
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Exit", command=self.root.quit, accelerator="Command+W"
        )

        # Bind keyboard shortcuts
        self.root.bind("<Command-s>", lambda e: self.export_image())
        self.root.bind("<Shift-Command-s>", lambda e: self.save_as())
        self.root.bind("<Command-w>", lambda e: self.root.quit())

    def create_layout(self):
        # Main layout: left and right frames
        left_frame = tk.Frame(self.root, width=300, height=600)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        left_frame.pack_propagate(False)

        right_frame = tk.Frame(self.root, width=700, height=600, bg="#f0f0f0")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        right_frame.pack_propagate(False)

        # Split left frame into base and graphic sections
        base_frame = tk.LabelFrame(left_frame, text="Base", height=150)
        base_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 5))

        graphic_frame = tk.LabelFrame(left_frame, text="Graphic", height=450)
        graphic_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # Create preview frame on right
        preview_frame = tk.LabelFrame(right_frame, text="Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True)

        # Fill the Base frame
        self.create_base_section(base_frame)

        # Fill the Graphic frame
        self.create_graphic_section(graphic_frame)

        # Fill the Preview frame
        self.create_preview_section(preview_frame)

    def create_base_section(self, parent):
        # Base image selection
        base_frame = tk.Frame(parent)
        base_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(base_frame, text="Image:").pack(side=tk.LEFT, padx=(0, 10))

        base_entry = tk.Entry(base_frame, textvariable=self.base_path, width=20)
        base_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        base_button = tk.Button(base_frame, text="Browse...", command=self.select_base)
        base_button.pack(side=tk.RIGHT, padx=(5, 0))

    def create_graphic_section(self, parent):
        # Graphic image selection
        graphic_frame = tk.Frame(parent)
        graphic_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(graphic_frame, text="Image:").pack(side=tk.LEFT, padx=(0, 10))

        graphic_entry = tk.Entry(
            graphic_frame, textvariable=self.graphic_path, width=20
        )
        graphic_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        graphic_button = tk.Button(
            graphic_frame, text="Browse...", command=self.select_graphic
        )
        graphic_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Position controls
        position_frame = tk.LabelFrame(parent, text="Position")
        position_frame.pack(fill=tk.X, padx=10, pady=5)

        # X coordinate
        x_frame = tk.Frame(position_frame)
        x_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(x_frame, text="X:").pack(side=tk.LEFT, padx=(0, 10))

        x_spinbox = ttk.Spinbox(
            x_frame,
            from_=-1000,
            to=1000,
            textvariable=self.x_coord,
            width=10,
            increment=1,
        )
        x_spinbox.pack(side=tk.LEFT)

        # Y coordinate
        y_frame = tk.Frame(position_frame)
        y_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(y_frame, text="Y:").pack(side=tk.LEFT, padx=(0, 10))

        y_spinbox = ttk.Spinbox(
            y_frame,
            from_=-1000,
            to=1000,
            textvariable=self.y_coord,
            width=10,
            increment=1,
        )
        y_spinbox.pack(side=tk.LEFT)

        # Scale controls
        scale_frame = tk.LabelFrame(parent, text="Scale")
        scale_frame.pack(fill=tk.X, padx=10, pady=5)

        # Scale X
        scale_x_frame = tk.Frame(scale_frame)
        scale_x_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(scale_x_frame, text="X (%):").pack(side=tk.LEFT, padx=(0, 10))

        scale_x_spinbox = ttk.Spinbox(
            scale_x_frame,
            from_=10,
            to=500,
            textvariable=self.scale_x,
            width=10,
            increment=5,
        )
        scale_x_spinbox.pack(side=tk.LEFT)

        # Scale Y
        scale_y_frame = tk.Frame(scale_frame)
        scale_y_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(scale_y_frame, text="Y (%):").pack(side=tk.LEFT, padx=(0, 10))

        scale_y_spinbox = ttk.Spinbox(
            scale_y_frame,
            from_=10,
            to=500,
            textvariable=self.scale_y,
            width=10,
            increment=5,
        )
        scale_y_spinbox.pack(side=tk.LEFT)

    def create_preview_section(self, parent):
        # Create canvas for preview
        self.preview_canvas = tk.Canvas(parent, bg="white")
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Bind canvas resize event
        self.preview_canvas.bind("<Configure>", self.on_canvas_resize)

    def on_canvas_resize(self, event):
        # Update preview when canvas is resized
        self.update_preview()

    def select_graphic(self):
        filepath = filedialog.askopenfilename(
            title="Select Graphic Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")],
        )
        if filepath:
            self.graphic_path.set(filepath)

    def select_base(self):
        filepath = filedialog.askopenfilename(
            title="Select Base Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")],
        )
        if filepath:
            self.base_path.set(filepath)

    def update_preview(self, *args):
        # Clear current preview
        self.preview_canvas.delete("all")

        # Check if we have both images
        if not self.base_path.get() or not self.graphic_path.get():
            return

        try:
            # Load the base image
            base_img = Image.open(self.base_path.get())

            # Load the graphic image
            graphic_img = Image.open(self.graphic_path.get())

            # Get canvas dimensions
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()

            # If canvas is not visible yet, set minimum dimensions
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 400
                canvas_height = 400

            # Resize the base image to fit the canvas (maintaining aspect ratio)
            base_width, base_height = base_img.size
            base_ratio = min(canvas_width / base_width, canvas_height / base_height)
            new_width = int(base_width * base_ratio)
            new_height = int(base_height * base_ratio)

            resized_base = base_img.resize(
                (new_width, new_height), Image.Resampling.LANCZOS
            )

            # Create a composite image by pasting the graphic onto the base
            composite = resized_base.copy()

            # Calculate scaled position based on original base image dimensions
            x_scale = new_width / base_width
            y_scale = new_height / base_height

            x_pos = int(self.x_coord.get() * x_scale)
            y_pos = int(self.y_coord.get() * y_scale)

            # Determine the center position on the base image
            center_x = new_width // 2
            center_y = new_height // 2

            # Resize graphic while maintaining aspect ratio
            graphic_width = int(graphic_img.width * base_ratio)
            graphic_height = int(graphic_img.height * base_ratio)

            # Apply X and Y scaling
            scale_x_factor = self.scale_x.get() / 100.0
            scale_y_factor = self.scale_y.get() / 100.0
            graphic_width = int(graphic_width * scale_x_factor)
            graphic_height = int(graphic_height * scale_y_factor)

            graphic_resized = graphic_img.resize(
                (graphic_width, graphic_height), Image.Resampling.LANCZOS
            )

            # Calculate top-left position for the graphic image, accounting for its size
            paste_x = center_x + x_pos - (graphic_resized.width // 2)
            paste_y = center_y + y_pos - (graphic_resized.height // 2)

            # Paste the graphic onto the composite image
            if graphic_resized.mode == "RGBA":
                # Use alpha channel for transparent images
                composite.paste(graphic_resized, (paste_x, paste_y), graphic_resized)
            else:
                composite.paste(graphic_resized, (paste_x, paste_y))

            # Store the current composite for export
            self.current_composite = composite

            # Create a PhotoImage object from the composite image
            self.preview_image = ImageTk.PhotoImage(composite)

            # Display the composite image on the canvas
            canvas_center_x = canvas_width // 2
            canvas_center_y = canvas_height // 2

            self.preview_canvas.create_image(
                canvas_center_x,
                canvas_center_y,
                image=self.preview_image,
                anchor="center",
            )

        except Exception as e:
            messagebox.showerror("Error", f"Error updating preview: {e}")
            print(f"Error updating preview: {e}")

    def export_image(self):
        if not self.current_composite:
            messagebox.showerror(
                "Error",
                "No image to export. Please load both base and graphic images first.",
            )
            return

        # Generate filename with current timestamp
        timestamp = (
            datetime.now().isoformat().replace(":", "-").split(".")[0]
        )  # Remove milliseconds and replace colons
        filename = f"export_{timestamp}.png"

        try:
            # Save the image
            self.current_composite.save(filename, "PNG")
            messagebox.showinfo("Success", f"Image exported successfully as {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export image: {e}")

    def save_as(self):
        if not self.current_composite:
            messagebox.showerror(
                "Error",
                "No image to save. Please load both base and graphic images first.",
            )
            return

        # Generate default filename with current timestamp
        timestamp = datetime.now().isoformat().replace(":", "-").split(".")[0]
        default_name = f"export_{timestamp}.png"

        # Open save file dialog
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=default_name,
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg;*.jpeg"),
                ("All files", "*.*"),
            ],
        )

        if filepath:  # If user didn't cancel
            try:
                # Save the image
                self.current_composite.save(filepath)
                messagebox.showinfo(
                    "Success", f"Image saved successfully as {filepath}"
                )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageOverlayApp(root)
    root.mainloop()
