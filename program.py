from datetime import datetime
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from functools import wraps
from PIL import Image, ImageTk


def debounce(wait):
    """Decorator that will postpone a function's execution until after `wait` seconds
    have elapsed since the last time it was invoked."""

    def decorator(fn):
        timer = None

        @wraps(fn)
        def debounced(*args, **kwargs):
            nonlocal timer

            def call_function():
                fn(*args, **kwargs)

            # Cancel previous timer if it exists
            if timer is not None:
                args[0].root.after_cancel(timer)

            # Schedule new timer
            timer = args[0].root.after(int(wait * 1000), call_function)

        return debounced

    return decorator


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
        self.reference_path = tk.StringVar()
        self.x_coord = tk.IntVar(value=0)
        self.y_coord = tk.IntVar(value=0)
        self.scale_x = tk.IntVar(value=100)  # Scale X in percentage
        self.scale_y = tk.IntVar(value=100)  # Scale Y in percentage
        self.show_reference = tk.BooleanVar(value=True)  # Toggle for reference image
        self.reference_opacity = tk.IntVar(
            value=30
        )  # Opacity for reference image (0-100)
        self.reference_x = tk.IntVar(value=0)  # Reference X position
        self.reference_y = tk.IntVar(value=0)  # Reference Y position
        self.reference_scale_x = tk.IntVar(value=100)  # Reference X scale percentage
        self.reference_scale_y = tk.IntVar(value=100)  # Reference Y scale percentage
        self.apply_background = tk.BooleanVar(value=False)  # Toggle for background

        # Cache for processed images
        self.cache = {
            "base_img": None,
            "graphic_img": None,
            "reference_img": None,
            "base_path": None,
            "graphic_path": None,
            "reference_path": None,
            "resized_base": None,
            "resized_graphic": None,
            "resized_reference": None,
            "last_canvas_size": (0, 0),
            "last_scale": (100, 100),
            "last_ref_scale": (100, 100),
            "last_opacity": 30,
        }

        # Store image objects
        self.graphic_image = None
        self.base_image = None
        self.preview_image = None
        self.reference_image = None
        self.current_composite = None  # Store the current composite image for export

        # Create main frames
        self.create_layout()

        # Bind variables to update preview with debounce
        for var in [
            self.graphic_path,
            self.base_path,
            self.reference_path,
            self.x_coord,
            self.y_coord,
            self.scale_x,
            self.scale_y,
            self.show_reference,
            self.reference_opacity,
            self.reference_x,
            self.reference_y,
            self.reference_scale_x,
            self.reference_scale_y,
            self.apply_background,
        ]:
            var.trace_add("write", self.trigger_update_preview)

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

        reference_frame = tk.LabelFrame(left_frame, text="Reference", height=150)
        reference_frame.pack(fill=tk.BOTH, expand=False, pady=(5, 0))

        # Create preview frame on right
        preview_frame = tk.LabelFrame(right_frame, text="Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True)

        # Fill the Base frame
        self.create_base_section(base_frame)

        # Fill the Graphic frame
        self.create_graphic_section(graphic_frame)

        # Fill the Reference frame
        self.create_reference_section(reference_frame)

        # Fill the Preview frame
        self.create_preview_section(preview_frame)

    def create_base_section(self, parent):
        # Base image selection
        base_frame = tk.Frame(parent)
        base_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(base_frame, text="Image:").pack(side=tk.LEFT, padx=(0, 10))

        base_entry = tk.Entry(base_frame, textvariable=self.base_path, width=20)
        base_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        base_button = tk.Button(base_frame, text="📂", command=self.select_base)
        base_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Background toggle
        bg_frame = tk.Frame(parent)
        bg_frame.pack(fill=tk.X, padx=10, pady=5)

        bg_toggle = tk.Checkbutton(
            bg_frame,
            text="Apply Background",
            variable=self.apply_background,
            onvalue=True,
            offvalue=False,
        )
        bg_toggle.pack(side=tk.LEFT)

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
            graphic_frame, text="📂", command=self.select_graphic
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

    def create_reference_section(self, parent):
        # Reference image selection
        ref_frame = tk.Frame(parent)
        ref_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(ref_frame, text="Image:").pack(side=tk.LEFT, padx=(0, 10))

        ref_entry = tk.Entry(ref_frame, textvariable=self.reference_path, width=20)
        ref_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ref_button = tk.Button(ref_frame, text="📂", command=self.select_reference)
        ref_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Controls frame for toggle and opacity
        controls_frame = tk.Frame(parent)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)

        # Toggle visibility
        toggle_button = tk.Checkbutton(
            controls_frame,
            text="Show Reference",
            variable=self.show_reference,
            onvalue=True,
            offvalue=False,
        )
        toggle_button.pack(side=tk.LEFT)

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
            textvariable=self.reference_x,
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
            textvariable=self.reference_y,
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
            textvariable=self.reference_scale_x,
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
            textvariable=self.reference_scale_y,
            width=10,
            increment=5,
        )
        scale_y_spinbox.pack(side=tk.LEFT)

        # Opacity control
        opacity_frame = tk.LabelFrame(parent, text="Opacity")
        opacity_frame.pack(fill=tk.X, padx=10, pady=5)

        opacity_scale = ttk.Scale(
            opacity_frame,
            from_=0,
            to=100,
            variable=self.reference_opacity,
            orient=tk.HORIZONTAL,
        )
        opacity_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=5)

        # Opacity percentage label
        opacity_label = tk.Label(opacity_frame, text="30%", width=4)
        opacity_label.pack(side=tk.LEFT, padx=(0, 10), pady=5)

        # Update opacity label when slider moves
        def update_opacity_label(*args):
            opacity_label.config(text=f"{self.reference_opacity.get()}%")

        self.reference_opacity.trace_add("write", update_opacity_label)

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

    def select_reference(self):
        filepath = filedialog.askopenfilename(
            title="Select Reference Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")],
        )
        if filepath:
            self.reference_path.set(filepath)

    def update_preview(self, *args):
        # Clear current preview
        self.preview_canvas.delete("all")

        # Get canvas dimensions
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()

        # If canvas is not visible yet, set minimum dimensions
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 400
            canvas_height = 400

        # Set canvas background color if background is enabled
        if self.apply_background.get():
            self.preview_canvas.configure(bg="#b4b4b4")
        else:
            self.preview_canvas.configure(bg="white")

        canvas_size = (canvas_width, canvas_height)
        current_scale = (self.scale_x.get(), self.scale_y.get())

        # Check if we have both images for the composite
        if self.base_path.get() and self.graphic_path.get():
            try:
                # Load or get from cache the base image
                if (
                    self.cache["base_path"] != self.base_path.get()
                    or self.cache["base_img"] is None
                ):
                    self.cache["base_img"] = Image.open(self.base_path.get())
                    self.cache["base_path"] = self.base_path.get()

                base_img = self.cache["base_img"]

                # Load or get from cache the graphic image
                if (
                    self.cache["graphic_path"] != self.graphic_path.get()
                    or self.cache["graphic_img"] is None
                ):
                    self.cache["graphic_img"] = Image.open(self.graphic_path.get())
                    self.cache["graphic_path"] = self.graphic_path.get()

                graphic_img = self.cache["graphic_img"]

                # Only resize base image if canvas size changed
                if (
                    self.cache["last_canvas_size"] != canvas_size
                    or self.cache["resized_base"] is None
                ):
                    # Resize the base image to fit the canvas (maintaining aspect ratio)
                    base_width, base_height = base_img.size
                    base_ratio = min(
                        canvas_width / base_width, canvas_height / base_height
                    )
                    new_width = int(base_width * base_ratio)
                    new_height = int(base_height * base_ratio)

                    self.cache["resized_base"] = base_img.resize(
                        (new_width, new_height), Image.Resampling.LANCZOS
                    )
                    self.cache["last_canvas_size"] = canvas_size

                resized_base = self.cache["resized_base"]
                composite = resized_base.copy()

                # Calculate scaled position based on original base image dimensions
                base_width, base_height = base_img.size
                x_scale = resized_base.width / base_width
                y_scale = resized_base.height / base_height

                x_pos = int(self.x_coord.get() * x_scale)
                y_pos = int(self.y_coord.get() * y_scale)

                # Determine the center position on the base image
                center_x = resized_base.width // 2
                center_y = resized_base.height // 2

                # Only resize graphic if scale changed
                if (
                    self.cache["last_scale"] != current_scale
                    or self.cache["resized_graphic"] is None
                ):
                    # Calculate scaled dimensions for graphic
                    base_ratio = min(
                        canvas_width / base_width, canvas_height / base_height
                    )
                    graphic_width = int(graphic_img.width * base_ratio)
                    graphic_height = int(graphic_img.height * base_ratio)

                    # Apply X and Y scaling
                    scale_x_factor = self.scale_x.get() / 100.0
                    scale_y_factor = self.scale_y.get() / 100.0
                    graphic_width = int(graphic_width * scale_x_factor)
                    graphic_height = int(graphic_height * scale_y_factor)

                    self.cache["resized_graphic"] = graphic_img.resize(
                        (graphic_width, graphic_height), Image.Resampling.LANCZOS
                    )
                    self.cache["last_scale"] = current_scale

                graphic_resized = self.cache["resized_graphic"]

                # Calculate top-left position for the graphic image
                paste_x = center_x + x_pos - (graphic_resized.width // 2)
                paste_y = center_y + y_pos - (graphic_resized.height // 2)

                # Paste the graphic onto the composite image
                if graphic_resized.mode == "RGBA":
                    composite.paste(
                        graphic_resized, (paste_x, paste_y), graphic_resized
                    )
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
                    tags="composite",
                )

            except Exception as e:
                messagebox.showerror("Error", f"Error updating preview: {e}")
                print(f"Error updating preview: {e}")

        # Handle reference image
        if self.reference_path.get() and self.show_reference.get():
            try:
                # Load or get from cache the reference image
                if (
                    self.cache["reference_path"] != self.reference_path.get()
                    or self.cache["reference_img"] is None
                ):
                    self.cache["reference_img"] = Image.open(self.reference_path.get())
                    self.cache["reference_path"] = self.reference_path.get()

                reference_img = self.cache["reference_img"]
                current_ref_scale = (
                    self.reference_scale_x.get(),
                    self.reference_scale_y.get(),
                )

                # Only resize reference if scale or opacity changed
                if (
                    self.cache["last_ref_scale"] != current_ref_scale
                    or self.cache["last_opacity"] != self.reference_opacity.get()
                    or self.cache["resized_reference"] is None
                ):
                    # Calculate base size (before user scaling)
                    ref_width, ref_height = reference_img.size
                    ref_ratio = min(
                        canvas_width / ref_width, canvas_height / ref_height
                    )
                    base_width = int(ref_width * ref_ratio)
                    base_height = int(ref_height * ref_ratio)

                    # Apply user scaling
                    scale_x_factor = self.reference_scale_x.get() / 100.0
                    scale_y_factor = self.reference_scale_y.get() / 100.0
                    new_width = int(base_width * scale_x_factor)
                    new_height = int(base_height * scale_y_factor)

                    resized_reference = reference_img.resize(
                        (new_width, new_height), Image.Resampling.LANCZOS
                    )

                    # Convert to RGBA and apply opacity
                    if resized_reference.mode != "RGBA":
                        resized_reference = resized_reference.convert("RGBA")

                    opacity = self.reference_opacity.get() / 100.0
                    alpha = int(255 * opacity)

                    # Optimize opacity application using point()
                    bands = list(resized_reference.split())
                    if len(bands) == 4:
                        bands[3] = bands[3].point(lambda x: int(x * opacity))
                        resized_reference = Image.merge("RGBA", bands)

                    self.cache["resized_reference"] = resized_reference
                    self.cache["last_ref_scale"] = current_ref_scale
                    self.cache["last_opacity"] = self.reference_opacity.get()

                resized_reference = self.cache["resized_reference"]

                # Create a PhotoImage object from the reference image
                self.reference_image = ImageTk.PhotoImage(resized_reference)

                # Calculate position with offset
                canvas_center_x = canvas_width // 2
                canvas_center_y = canvas_height // 2
                x_pos = canvas_center_x + self.reference_x.get()
                y_pos = canvas_center_y + self.reference_y.get()

                # Display the reference image on the canvas
                self.preview_canvas.create_image(
                    x_pos,
                    y_pos,
                    image=self.reference_image,
                    anchor="center",
                    tags="reference",
                )
            except Exception as e:
                messagebox.showerror("Error", f"Error loading reference image: {e}")

    def export_image(self):
        if not self.current_composite:
            messagebox.showerror(
                "Error",
                "No image to export. Please load both base and graphic images first.",
            )
            return

        # If background is enabled, create a new image with padding
        if self.apply_background.get():
            # Calculate padding (10% of the original dimensions)
            padding_x = int(self.current_composite.width * 0.1)
            padding_y = int(self.current_composite.height * 0.1)

            # Create new image with background color and padding
            new_width = self.current_composite.width + (padding_x * 2)
            new_height = self.current_composite.height + (padding_y * 2)

            # Create background image
            background = Image.new("RGB", (new_width, new_height), "#b4b4b4")

            # Paste the composite onto the background
            if self.current_composite.mode == "RGBA":
                background.paste(
                    self.current_composite,
                    (padding_x, padding_y),
                    self.current_composite,
                )
            else:
                background.paste(self.current_composite, (padding_x, padding_y))

            export_image = background
        else:
            export_image = self.current_composite

        # Generate filename with current timestamp
        timestamp = datetime.now().isoformat().replace(":", "-").split(".")[0]
        filename = f"export_{timestamp}.png"

        try:
            # Save the image
            export_image.save(filename, "PNG")
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
                # If background is enabled, create a new image with padding
                if self.apply_background.get():
                    # Calculate padding (10% of the original dimensions)
                    padding_x = int(self.current_composite.width * 0.1)
                    padding_y = int(self.current_composite.height * 0.1)

                    # Create new image with background color and padding
                    new_width = self.current_composite.width + (padding_x * 2)
                    new_height = self.current_composite.height + (padding_y * 2)

                    # Create background image
                    background = Image.new("RGB", (new_width, new_height), "#b4b4b4")

                    # Paste the composite onto the background
                    if self.current_composite.mode == "RGBA":
                        background.paste(
                            self.current_composite,
                            (padding_x, padding_y),
                            self.current_composite,
                        )
                    else:
                        background.paste(self.current_composite, (padding_x, padding_y))

                    export_image = background
                else:
                    export_image = self.current_composite

                # Save the image
                export_image.save(filepath)
                messagebox.showinfo(
                    "Success", f"Image saved successfully as {filepath}"
                )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {e}")

    def trigger_update_preview(self, *args):
        self.debounced_update_preview()

    @debounce(0.1)  # 100ms debounce
    def debounced_update_preview(self):
        self.update_preview()


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageOverlayApp(root)
    root.mainloop()
