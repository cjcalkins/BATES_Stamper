import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import fitz  # PyMuPDF
from pathlib import Path
from PIL import Image, ImageTk
import sv_ttk  # Sun Valley ttk theme
import sys

class PDFStamperApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PDF Combiner & Stamper")
        
        # Launch maximized
        try:
            self.root.state('zoomed')
        except tk.TclError:
            self.root.attributes('-zoomed', True)
        
        self.root.minsize(1100, 850)
        
        sv_ttk.set_theme("light")
        self.root.option_add('*Font', 'Georgia 10')
        
        self.files_data = []
        self.current_selected_idx = None
        self.large_preview = None
        
        # Global font selector
        self.stamp_font_var = tk.StringVar(value="Helvetica-Bold")
        
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.combine_tab = ttk.Frame(notebook)
        notebook.add(self.combine_tab, text="Combine & Stamp")
        self.build_combine_tab()
        
        self.remove_tab = ttk.Frame(notebook)
        notebook.add(self.remove_tab, text="Remove Stamp")
        self.build_remove_tab()
        
        self.view_tab = ttk.Frame(notebook)
        notebook.add(self.view_tab, text="View & Export Pages")
        self.build_view_tab()
        
    def build_combine_tab(self):
        frame = self.combine_tab
        
        tk.Label(frame, text="Selected Files (click row to select for move):", 
                 font=("Georgia", 10, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
        
        list_container = tk.Frame(frame)
        list_container.pack(fill='both', expand=True, padx=15, pady=5)
        
        self.canvas = tk.Canvas(list_container, height=340, bg="#f9f9f9")
        scrollbar = tk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f9f9f9")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="Add Files", command=self.select_files, width=15).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Move Up", command=self.move_up, width=12).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Move Down", command=self.move_down, width=12).pack(side="left", padx=5)
        
        settings = ttk.LabelFrame(frame, text="Stamp Settings", padding=12)
        settings.pack(fill="x", padx=15, pady=12)
        
        row = 0
        tk.Label(settings, text="Prefix:").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        self.prefix_var = tk.StringVar(value="EXH")
        tk.Entry(settings, textvariable=self.prefix_var, width=20).grid(row=row, column=1, padx=8, pady=6, sticky="w")
        
        row += 1
        tk.Label(settings, text="Starting Number:").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        self.start_num_var = tk.StringVar(value="1")
        tk.Entry(settings, textvariable=self.start_num_var, width=10).grid(row=row, column=1, padx=8, pady=6, sticky="w")
        
        # Suffix moved up here (above font controls)
        row += 1
        tk.Label(settings, text="Suffix (optional):").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        self.suffix_var = tk.StringVar()
        tk.Entry(settings, textvariable=self.suffix_var, width=25).grid(row=row, column=1, padx=8, pady=6, sticky="w")
        
        row += 1
        tk.Label(settings, text="Font Size:").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        self.font_size_var = tk.StringVar(value="14")
        font_combo = ttk.Combobox(settings, textvariable=self.font_size_var, 
                                  values=["10", "12", "14", "16", "18", "20"], 
                                  state="readonly", width=8)
        font_combo.grid(row=row, column=1, padx=8, pady=6, sticky="w")
        
        # Font selector
        row += 1
        tk.Label(settings, text="Font:").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        font_options = ["Helvetica-Bold", "Helvetica", "Times-Bold", "Times-Roman", "Courier-Bold", "Courier"]
        font_selector = ttk.Combobox(settings, textvariable=self.stamp_font_var, 
                                     values=font_options, state="readonly", width=15)
        font_selector.grid(row=row, column=1, padx=8, pady=6, sticky="w")
        
        out_frame = ttk.LabelFrame(frame, text="Output PDF", padding=12)
        out_frame.pack(fill="x", padx=15, pady=12)
        tk.Label(out_frame, text="Save as:").pack(anchor="w", padx=8)
        self.output_var = tk.StringVar()
        tk.Entry(out_frame, textvariable=self.output_var, width=80).pack(fill="x", padx=8, pady=5)
        tk.Button(out_frame, text="Browse...", command=self.browse_output).pack(anchor="e", padx=8)
        
        self.auto_open_var = tk.BooleanVar(value=False)
        tk.Checkbutton(out_frame, text="Open in View & Export after saving", 
                       variable=self.auto_open_var).pack(anchor="w", padx=8, pady=8)
        
        tk.Button(frame, text="COMBINE PDFs & APPLY STAMPS", bg="#28a745", fg="white",
                  font=("Georgia", 11, "bold"), height=2, command=self.process_combine).pack(pady=20)
        
    def build_remove_tab(self):
        frame = self.remove_tab
        tk.Label(frame, text="Remove stamps from a PDF previously created by this tool", 
                 font=("Georgia", 11, "bold")).pack(pady=30)
        
        tk.Label(frame, text="Input (stamped) PDF:").pack(anchor="w", padx=40, pady=(20,5))
        self.remove_input_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.remove_input_var, width=80).pack(fill="x", padx=40, pady=5)
        tk.Button(frame, text="Browse Input", command=self.browse_remove_input).pack(pady=8)
        
        tk.Label(frame, text="Output (clean) PDF:").pack(anchor="w", padx=40, pady=(20,5))
        self.remove_output_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.remove_output_var, width=80).pack(fill="x", padx=40, pady=5)
        tk.Button(frame, text="Browse Output", command=self.browse_remove_output).pack(pady=8)
        
        tk.Button(frame, text="REMOVE STAMPS", bg="#dc3545", fg="white",
                  font=("Georgia", 11, "bold"), height=2, command=self.process_remove).pack(pady=50)
        
    def build_view_tab(self):
        frame = self.view_tab
        tk.Label(frame, text="PDF Viewer & Page Extractor", 
                 font=("Georgia", 12, "bold")).pack(pady=30)
        
        tk.Label(frame, text="Open a PDF to view pages as tiles or in full detail,\n"
                             "select pages, and export them as a new PDF.",
                 font=("Georgia", 10), justify="center").pack(pady=10)
        
        tk.Button(frame, text="Open PDF for Viewing", 
                  font=("Georgia", 11, "bold"), bg="#007bff", fg="white",
                  width=30, height=2, command=self.open_pdf_viewer).pack(pady=40)
        
    def open_pdf_viewer(self, path=None):
        if path is None:
            path = filedialog.askopenfilename(
                title="Select PDF to view",
                filetypes=[("PDF files", "*.pdf")]
            )
        if not path:
            return
        PDFViewerWindow(self.root, path)
    
    def _generate_small_thumbnail(self, filepath):
        try:
            if str(filepath).lower().endswith('.pdf'):
                doc = fitz.open(filepath)
                page = doc[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(0.12, 0.12))
                doc.close()
                pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            else:
                pil_img = Image.open(filepath)
            
            pil_img.thumbnail((60, 80), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(pil_img)
        except Exception:
            placeholder = Image.new("RGB", (60, 80), "#cccccc")
            return ImageTk.PhotoImage(placeholder)
    
    def _open_file_as_document(self, filepath):
        path_str = str(filepath).lower()
        if path_str.endswith('.pdf'):
            return fitz.open(filepath)
        
        doc = fitz.open()
        img = Image.open(filepath)
        w, h = img.size
        page = doc.new_page(width=w, height=h)
        page.insert_image(page.rect, filename=filepath)
        return doc
    
    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Select PDF or Image files",
            filetypes=[
                ("PDF and Image files", "*.pdf *.jpg *.jpeg *.png *.bmp *.tiff *.gif *.webp"),
                ("PDF files", "*.pdf"),
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.gif *.webp")
            ]
        )
        if not files:
            return
        
        progress_win = tk.Toplevel(self.root)
        progress_win.title("Adding Files...")
        progress_win.geometry("420x140")
        progress_win.transient(self.root)
        progress_win.grab_set()
        progress_win.resizable(False, False)
        
        tk.Label(progress_win, text="Adding selected files...",
                 font=("Georgia", 10)).pack(pady=10)
        
        status_var = tk.StringVar(value="Preparing...")
        status_label = tk.Label(progress_win, textvariable=status_var, font=("Georgia", 9))
        status_label.pack(pady=5)
        
        progress_bar = ttk.Progressbar(progress_win, orient="horizontal", length=380, mode="determinate")
        progress_bar.pack(pady=10, padx=20)
        
        total_files = len(files)
        progress_bar['maximum'] = total_files
        progress_bar['value'] = 0
        
        added = False
        for i, f in enumerate(files):
            status_var.set(f"Adding file {i+1} of {total_files}...")
            progress_bar['value'] = i
            progress_win.update_idletasks()
            
            if not any(d['path'] == f for d in self.files_data):
                thumbnail = self._generate_small_thumbnail(f)
                self.files_data.append({
                    'path': f,
                    'name': Path(f).name,
                    'color': (0.0, 0.0, 0.0),
                    'page_colors': {},
                    'manual': False,
                    'manual_positions': {},
                    'thumbnail': thumbnail
                })
                added = True
        
        status_var.set(f"Added {total_files} file(s)")
        progress_bar['value'] = total_files
        progress_win.update_idletasks()
        progress_win.destroy()
        
        if added:
            self.refresh_file_list()
    
    def refresh_file_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        for i, item in enumerate(self.files_data):
            row_frame = tk.Frame(self.scrollable_frame, bg="#f9f9f9")
            row_frame.pack(fill="x", padx=8, pady=3)
            
            if i == self.current_selected_idx:
                row_frame.configure(bg="#e0f0ff")
            
            thumb_label = tk.Label(row_frame, image=item['thumbnail'], bg=row_frame['bg'])
            thumb_label.pack(side="left", padx=(5, 8))
            thumb_label.bind("<Enter>", lambda e, fp=item['path']: self.show_large_preview(e, fp))
            thumb_label.bind("<Leave>", self.hide_large_preview)
            
            name_label = tk.Label(row_frame, text=item['name'], anchor="w", width=38, bg=row_frame['bg'])
            name_label.pack(side="left", padx=(0, 8))
            
            manual_var = tk.BooleanVar(value=item.get('manual', False))
            chk = tk.Checkbutton(row_frame, text="Manual Placement", variable=manual_var,
                                 command=lambda idx=i, v=manual_var: self.toggle_manual(idx, v))
            chk.pack(side="left", padx=8)
            
            if item.get('manual', False):
                set_btn = tk.Button(row_frame, text="Set Position", bg="#007bff", fg="white",
                                    command=lambda idx=i: self.open_placement_editor(idx))
                set_btn.pack(side="left", padx=5)
            
            default_color = item.get('page_colors', {}).get(0, item['color'])
            hex_color = f"#{int(default_color[0]*255):02x}{int(default_color[1]*255):02x}{int(default_color[2]*255):02x}"
            swatch = tk.Canvas(row_frame, width=24, height=24, bg=hex_color, highlightthickness=1, highlightbackground="#666")
            swatch.pack(side="left", padx=(8, 4))
            
            color_btn = tk.Button(row_frame, text="Choose Color", bg="#f0f0f0",
                                  command=lambda idx=i: self.choose_color(idx))
            color_btn.pack(side="left", padx=4)
            
            remove_btn = tk.Button(row_frame, text="Remove", fg="red", command=lambda idx=i: self.remove_file(idx))
            remove_btn.pack(side="right", padx=5)
            
            for widget in (row_frame, name_label):
                widget.bind("<Button-1>", lambda e, idx=i: self.select_row(idx))
    
    def show_large_preview(self, event, filepath):
        if self.large_preview is not None:
            self.large_preview.destroy()
        
        self.large_preview = tk.Toplevel(self.root)
        self.large_preview.overrideredirect(True)
        self.large_preview.attributes("-topmost", True)
        
        try:
            if str(filepath).lower().endswith('.pdf'):
                doc = fitz.open(filepath)
                page = doc[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(0.45, 0.45))
                doc.close()
                pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            else:
                pil_img = Image.open(filepath)
                pil_img.thumbnail((450, 650), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(pil_img)
            label = tk.Label(self.large_preview, image=photo, bg="#222222")
            label.image = photo
            label.pack()
        except Exception:
            tk.Label(self.large_preview, text="Preview unavailable", bg="#222222", fg="white").pack(pady=20)
        
        x = self.root.winfo_pointerx() + 15
        y = self.root.winfo_pointery() + 15
        self.large_preview.geometry(f"+{x}+{y}")
    
    def hide_large_preview(self, event=None):
        if self.large_preview is not None:
            self.large_preview.destroy()
            self.large_preview = None
    
    def choose_color(self, idx):
        if not (0 <= idx < len(self.files_data)):
            return
        item = self.files_data[idx]
        current_rgb255 = tuple(int(c * 255) for c in item['color'])
        result = colorchooser.askcolor(initialcolor=current_rgb255, title=f"Choose default stamp color for {item['name']}")
        
        if result[1] is not None:
            r, g, b = result[0]
            item['color'] = (r/255.0, g/255.0, b/255.0)
            self.refresh_file_list()
    
    def toggle_manual(self, idx, var):
        if 0 <= idx < len(self.files_data):
            self.files_data[idx]['manual'] = var.get()
            self.refresh_file_list()
    
    def remove_file(self, idx):
        if 0 <= idx < len(self.files_data):
            del self.files_data[idx]
            if self.current_selected_idx == idx:
                self.current_selected_idx = None
            elif self.current_selected_idx is not None and self.current_selected_idx > idx:
                self.current_selected_idx -= 1
            self.refresh_file_list()
    
    def move_up(self):
        if self.current_selected_idx is None or self.current_selected_idx <= 0:
            return
        i = self.current_selected_idx
        self.files_data[i], self.files_data[i-1] = self.files_data[i-1], self.files_data[i]
        self.current_selected_idx = i - 1
        self.refresh_file_list()
    
    def move_down(self):
        if self.current_selected_idx is None or self.current_selected_idx >= len(self.files_data)-1:
            return
        i = self.current_selected_idx
        self.files_data[i], self.files_data[i+1] = self.files_data[i+1], self.files_data[i]
        self.current_selected_idx = i + 1
        self.refresh_file_list()
    
    def select_row(self, idx):
        self.current_selected_idx = idx
        self.refresh_file_list()
    
    def open_placement_editor(self, idx):
        file_item = self.files_data[idx]
        PlacementEditor(self.root, file_item['path'], file_item, lambda: self.refresh_file_list(), 
                        self.font_size_var, self.stamp_font_var.get())
    
    def browse_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if path:
            self.output_var.set(path)
    
    def browse_remove_input(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.remove_input_var.set(path)
            if not self.remove_output_var.get():
                p = Path(path)
                self.remove_output_var.set(str(p.with_name(p.stem + "_clean" + p.suffix)))
    
    def browse_remove_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if path:
            self.remove_output_var.set(path)
    
    def process_combine(self):
        if not self.files_data:
            messagebox.showerror("Error", "No files selected.")
            return
        
        try:
            start_num = int(self.start_num_var.get())
            font_size = int(self.font_size_var.get())
        except ValueError:
            messagebox.showerror("Error", "Starting Number and Font Size must be valid integers.")
            return
        
        prefix = self.prefix_var.get().strip()
        suffix = self.suffix_var.get().strip()
        output_path = self.output_var.get().strip()
        font_name = self.stamp_font_var.get()
        
        if not prefix:
            messagebox.showerror("Error", "Prefix is required.")
            return
        
        if not output_path:
            num_str = f"{start_num:06d}"
            if suffix:
                filename = f"{prefix}.{num_str}-{suffix}.pdf"
            else:
                filename = f"{prefix}.{num_str}.pdf"
            
            if getattr(sys, 'frozen', False):
                exe_dir = Path(sys.executable).parent
            else:
                exe_dir = Path(__file__).parent
            output_path = str(exe_dir / filename)
            self.output_var.set(output_path)
        
        progress_win = tk.Toplevel(self.root)
        progress_win.title("Combining & Stamping Files...")
        progress_win.geometry("420x140")
        progress_win.transient(self.root)
        progress_win.grab_set()
        progress_win.resizable(False, False)
        
        tk.Label(progress_win, text="Please wait while files are combined and stamped...",
                 font=("Georgia", 10)).pack(pady=10)
        
        status_var = tk.StringVar(value="Preparing...")
        status_label = tk.Label(progress_win, textvariable=status_var, font=("Georgia", 9))
        status_label.pack(pady=5)
        
        progress_bar = ttk.Progressbar(progress_win, orient="horizontal", length=380, mode="determinate")
        progress_bar.pack(pady=10, padx=20)
        
        total_files = len(self.files_data)
        progress_bar['maximum'] = total_files
        progress_bar['value'] = 0
        
        try:
            doc = fitz.open()
            current_num = start_num
            
            for file_idx, file_item in enumerate(self.files_data):
                status_var.set(f"Processing file {file_idx + 1} of {total_files}...")
                progress_bar['value'] = file_idx
                progress_win.update_idletasks()
                
                color_default = file_item['color']
                page_colors = file_item.get('page_colors', {})
                src = self._open_file_as_document(file_item['path'])
                
                manual_positions = file_item.get('manual_positions', {})
                
                for page_idx, page in enumerate(src):
                    num_str = f"{current_num:06d}"
                    stamp_text = f"{prefix}.{num_str}"
                    if suffix:
                        stamp_text += f" {suffix}"
                    
                    color = page_colors.get(page_idx, color_default)
                    
                    pos = manual_positions.get(page_idx)
                    r = page.rect
                    
                    if pos and pos.get('top') and pos.get('bottom'):
                        page.insert_textbox(pos['top'], stamp_text, fontsize=font_size,
                                            align=fitz.TEXT_ALIGN_RIGHT,
                                            fontname=font_name, color=color)
                        page.insert_textbox(pos['bottom'], stamp_text, fontsize=font_size,
                                            align=fitz.TEXT_ALIGN_RIGHT,
                                            fontname=font_name, color=color)
                    else:
                        page.insert_textbox(fitz.Rect(r.x1 - 300, 22, r.x1 - 20, 80),
                                            stamp_text, fontsize=font_size,
                                            align=fitz.TEXT_ALIGN_RIGHT,
                                            fontname=font_name, color=color)
                        page.insert_textbox(fitz.Rect(r.x1 - 300, r.y1 - 85, r.x1 - 20, r.y1 - 27),
                                            stamp_text, fontsize=font_size,
                                            align=fitz.TEXT_ALIGN_RIGHT,
                                            fontname=font_name, color=color)
                    
                    current_num += 1
                
                doc.insert_pdf(src)
                src.close()
            
            status_var.set(f"Processing file {total_files} of {total_files}... Done!")
            progress_bar['value'] = total_files
            progress_win.update_idletasks()
            
            doc.save(output_path, garbage=1, deflate=True, clean=True)
            doc.close()
            
            progress_win.destroy()
            
            messagebox.showinfo("Success", f"Stamped PDF saved successfully:\n{output_path}")
            
            if self.auto_open_var.get():
                self.open_pdf_viewer(output_path)
        
        except Exception as e:
            if 'progress_win' in locals():
                progress_win.destroy()
            messagebox.showerror("Error", f"Failed to process:\n{str(e)}")
    
    def process_remove(self):
        input_path = self.remove_input_var.get().strip()
        output_path = self.remove_output_var.get().strip()
        
        if not input_path or not output_path:
            messagebox.showerror("Error", "Please select both input and output files.")
            return
        
        try:
            doc = fitz.open(input_path)
            for page in doc:
                page.add_redact_annot(page.rect, fill=(1, 1, 1))
            for page in doc:
                page.apply_redactions()
            doc.save(output_path, garbage=1, deflate=True, clean=True)
            doc.close()
            messagebox.showinfo("Success", f"Stamps removed and saved to:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove stamps:\n{str(e)}")
    
    def run(self):
        self.root.mainloop()


class PlacementEditor(tk.Toplevel):
    def __init__(self, parent, pdf_path, file_item, refresh_callback, font_size_var, font_name):
        super().__init__(parent)
        self.title(f"Manual Stamp Placement – {Path(pdf_path).name}")
        self.geometry("1200x800")
        
        try:
            self.state('zoomed')
        except tk.TclError:
            self.attributes('-zoomed', True)
        
        self.pdf_path = pdf_path
        self.file_item = file_item
        self.refresh_callback = refresh_callback
        self.font_size = int(font_size_var.get())
        self.font_name = font_name
        
        self.default_color = file_item['color']
        self.page_colors = file_item.setdefault('page_colors', {})
        
        self.pdf_doc = fitz.open(pdf_path)
        self.num_pages = len(self.pdf_doc)
        self.current_page = 0
        
        if 'manual_positions' not in self.file_item:
            self.file_item['manual_positions'] = {}
        
        self.build_ui()
    
    def build_ui(self):
        toolbar = tk.Frame(self, bg="#f0f0f0")
        toolbar.pack(fill="x")
        
        tk.Button(toolbar, text="← Previous Page", command=self.prev_page).pack(side="left", padx=10, pady=8)
        
        self.page_label = tk.Label(toolbar, text=f"Page {self.current_page + 1} of {self.num_pages}", 
                                   font=("Georgia", 11, "bold"))
        self.page_label.pack(side="left", expand=True)
        
        tk.Button(toolbar, text="Next Page →", command=self.next_page).pack(side="left", padx=10, pady=8)
        
        self.color_swatch = tk.Canvas(toolbar, width=28, height=28, highlightthickness=2, highlightbackground="#333")
        self.color_swatch.pack(side="left", padx=(20, 5))
        tk.Button(toolbar, text="Choose Color for This Page", bg="#f0f0f0",
                  command=self.choose_color_for_current_page).pack(side="left", padx=5)
        
        tk.Button(toolbar, text="Save All Positions", bg="#28a745", fg="white",
                  command=self.save_all_positions).pack(side="right", padx=10, pady=8)
        tk.Button(toolbar, text="Cancel", command=self.destroy).pack(side="right", padx=10, pady=8)
        
        self.canvas = tk.Canvas(self, bg="#f0f0f0")
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.load_current_page()
    
    def get_current_page_color_hex(self):
        color = self.page_colors.get(self.current_page, self.default_color)
        return f"#{int(color[0]*255):02x}{int(color[1]*255):02x}{int(color[2]*255):02x}"
    
    def choose_color_for_current_page(self):
        current_rgb255 = tuple(int(c * 255) for c in self.page_colors.get(self.current_page, self.default_color))
        result = colorchooser.askcolor(initialcolor=current_rgb255, 
                                       title=f"Choose color for page {self.current_page + 1}")
        if result[1] is not None:
            r, g, b = result[0]
            self.page_colors[self.current_page] = (r/255.0, g/255.0, b/255.0)
            self.color_swatch.config(bg=self.get_current_page_color_hex())
            self.load_current_page()
    
    def load_current_page(self):
        for widget in self.canvas.winfo_children():
            widget.destroy()
        
        page = self.pdf_doc[self.current_page]
        pix = page.get_pixmap(matrix=fitz.Matrix(0.8, 0.8))
        pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.photo = ImageTk.PhotoImage(pil_img)
        
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        
        self.color_swatch.config(bg=self.get_current_page_color_hex())
        
        pos = self.file_item['manual_positions'].get(self.current_page, {})
        
        if 'top' in pos and pos['top']:
            top_rect = pos['top']
        else:
            r = page.rect
            top_rect = fitz.Rect(r.x1 - 240, 40, r.x1 - 20, 90)
        
        if 'bottom' in pos and pos['bottom']:
            bottom_rect = pos['bottom']
        else:
            r = page.rect
            bottom_rect = fitz.Rect(r.x1 - 240, r.y1 - 80, r.x1 - 20, r.y1 - 30)
        
        scale = 0.8
        self.top_rect = fitz.Rect(top_rect.x0 * scale, top_rect.y0 * scale,
                                  top_rect.x1 * scale, top_rect.y1 * scale)
        self.bottom_rect = fitz.Rect(bottom_rect.x0 * scale, bottom_rect.y0 * scale,
                                     bottom_rect.x1 * scale, bottom_rect.y1 * scale)
        
        page_color_hex = self.get_current_page_color_hex()
        
        self.top_text = self.canvas.create_text(
            self.top_rect.x1 - 10, self.top_rect.y0 + 25,
            text="TOP STAMP", anchor="e", 
            font=(self.font_name, self.font_size, "bold"), fill=page_color_hex
        )
        self.bottom_text = self.canvas.create_text(
            self.bottom_rect.x1 - 10, self.bottom_rect.y0 + 25,
            text="BOTTOM STAMP", anchor="e", 
            font=(self.font_name, self.font_size, "bold"), fill=page_color_hex
        )
        
        self.dragging = None
        self.offset_x = 0
        self.offset_y = 0
        
        self.canvas.tag_bind(self.top_text, "<Button-1>", lambda e: self.start_drag(e, "top"))
        self.canvas.tag_bind(self.top_text, "<B1-Motion>", self.do_drag)
        self.canvas.tag_bind(self.top_text, "<ButtonRelease-1>", self.stop_drag)
        
        self.canvas.tag_bind(self.bottom_text, "<Button-1>", lambda e: self.start_drag(e, "bottom"))
        self.canvas.tag_bind(self.bottom_text, "<B1-Motion>", self.do_drag)
        self.canvas.tag_bind(self.bottom_text, "<ButtonRelease-1>", self.stop_drag)
        
        self.page_label.config(text=f"Page {self.current_page + 1} of {self.num_pages}")
    
    def start_drag(self, event, which):
        self.dragging = which
        self.offset_x = event.x
        self.offset_y = event.y
    
    def do_drag(self, event):
        if not self.dragging:
            return
        dx = event.x - self.offset_x
        dy = event.y - self.offset_y
        self.offset_x = event.x
        self.offset_y = event.y
        
        if self.dragging == "top":
            self.canvas.move(self.top_text, dx, dy)
        else:
            self.canvas.move(self.bottom_text, dx, dy)
    
    def stop_drag(self, event):
        self.dragging = None
    
    def prev_page(self):
        self.save_current_page_positions()
        if self.current_page > 0:
            self.current_page -= 1
            self.load_current_page()
    
    def next_page(self):
        self.save_current_page_positions()
        if self.current_page < self.num_pages - 1:
            self.current_page += 1
            self.load_current_page()
    
    def save_current_page_positions(self):
        scale = 0.8
        inv_scale = 1 / scale
        
        coords = self.canvas.coords(self.top_text)
        x = coords[0]
        y = coords[1] - 25
        top_rect = fitz.Rect((x - 220) * inv_scale, y * inv_scale,
                             x * inv_scale, (y + 48) * inv_scale)
        
        coords = self.canvas.coords(self.bottom_text)
        x = coords[0]
        y = coords[1] - 25
        bottom_rect = fitz.Rect((x - 220) * inv_scale, y * inv_scale,
                                x * inv_scale, (y + 48) * inv_scale)
        
        self.file_item['manual_positions'][self.current_page] = {
            'top': top_rect,
            'bottom': bottom_rect
        }
    
    def save_all_positions(self):
        self.save_current_page_positions()
        messagebox.showinfo("Saved", "Stamp positions and per-page colors saved for all pages.")
        self.refresh_callback()
        self.destroy()
    
    def destroy(self):
        if hasattr(self, 'pdf_doc'):
            self.pdf_doc.close()
        super().destroy()


class PDFViewerWindow(tk.Toplevel):
    def __init__(self, parent, pdf_path):
        super().__init__(parent)
        self.title(f"PDF Viewer - {Path(pdf_path).name}")
        self.geometry("1400x900")
        
        try:
            self.state('zoomed')
        except tk.TclError:
            self.attributes('-zoomed', True)
        
        self.pdf_path = pdf_path
        self.pdf_doc = fitz.open(pdf_path)
        self.num_pages = len(self.pdf_doc)
        
        self.selected_pages = set()
        self.exported_pages = set()
        
        self.current_page = 0
        self.view_mode = "tile"
        self.zoom = 1.0
        
        self.thumbnails = []
        
        self.build_ui()
        self.load_thumbnails_with_progress()
    
    def load_thumbnails_with_progress(self):
        progress_win = tk.Toplevel(self)
        progress_win.title("Loading PDF Thumbnails...")
        progress_win.geometry("420x140")
        progress_win.transient(self)
        progress_win.grab_set()
        progress_win.resizable(False, False)
        
        tk.Label(progress_win, text="Generating thumbnails for large PDF...\nThis may take a moment.",
                 font=("Georgia", 10)).pack(pady=10)
        
        status_var = tk.StringVar(value="Preparing...")
        status_label = tk.Label(progress_win, textvariable=status_var, font=("Georgia", 9))
        status_label.pack(pady=5)
        
        progress_bar = ttk.Progressbar(progress_win, orient="horizontal", length=380, mode="determinate")
        progress_bar.pack(pady=10, padx=20)
        
        total = self.num_pages
        progress_bar['maximum'] = total
        progress_bar['value'] = 0
        
        self.thumbnails.clear()
        
        for i in range(total):
            status_var.set(f"Generating thumbnail for page {i+1} of {total}...")
            progress_bar['value'] = i
            progress_win.update_idletasks()
            
            page = self.pdf_doc[i]
            pix = page.get_pixmap(matrix=fitz.Matrix(0.18, 0.18))
            pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            pil_img = pil_img.resize((160, 220), Image.Resampling.LANCZOS)
            self.thumbnails.append(ImageTk.PhotoImage(pil_img))
        
        status_var.set("Thumbnail generation complete!")
        progress_bar['value'] = total
        progress_win.update_idletasks()
        progress_win.destroy()
        
        self.show_tile_canvas_view()
    
    def build_ui(self):
        toolbar = tk.Frame(self, bg="#f0f0f0", height=50)
        toolbar.pack(fill="x", side="top")
        toolbar.pack_propagate(False)
        
        tk.Button(toolbar, text="Tile View", command=lambda: self.switch_view("tile")).pack(side="left", padx=10, pady=8)
        tk.Button(toolbar, text="Full View", command=lambda: self.switch_view("full")).pack(side="left", padx=10, pady=8)
        
        self.page_label = tk.Label(toolbar, text=f"Page {self.current_page + 1} of {self.num_pages}", 
                                   font=("Georgia", 11))
        self.page_label.pack(side="left", padx=30)
        
        self.selected_count_label = tk.Label(toolbar, text="Selected: 0 pages", font=("Georgia", 10), fg="#28a745")
        self.selected_count_label.pack(side="left", padx=20)
        
        tk.Button(toolbar, text="Export Selected Pages", bg="#28a745", fg="white",
                  command=self.export_selected).pack(side="right", padx=10, pady=8)
        tk.Button(toolbar, text="Close Viewer", command=self.destroy).pack(side="right", padx=10, pady=8)
        
        self.content_frame = tk.Frame(self)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.bind("<Left>", lambda e: self.prev_page())
        self.bind("<Right>", lambda e: self.next_page())
    
    def show_tile_canvas_view(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        canvas = tk.Canvas(self.content_frame, bg="#f9f9f9", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        
        scroll_frame = tk.Frame(canvas, bg="#f9f9f9")
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        canvas.bind("<MouseWheel>", self._on_mousewheel)
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        
        self.tile_canvas = canvas
        self.tile_scroll_frame = scroll_frame
        
        cols = 5
        thumb_w = 160
        thumb_h = 220
        padding = 20
        x_start = padding
        y = padding
        
        for i in range(self.num_pages):
            col = i % cols
            row = i // cols
            
            x = x_start + col * (thumb_w + padding * 2)
            y_pos = y + row * (thumb_h + padding * 2 + 60)
            
            bg_tag = f"bg_{i}"
            canvas.create_rectangle(x, y_pos, x+thumb_w, y_pos+thumb_h, 
                                    fill="#ffffff", outline="#ddd", tags=bg_tag)
            
            img_tag = f"thumb_{i}"
            canvas.create_image(x, y_pos, anchor="nw", image=self.thumbnails[i], tags=img_tag)
            
            canvas.create_text(x + thumb_w//2, y_pos + thumb_h + 10,
                               text=f"Page {i+1}", font=("Georgia", 9), fill="#333", tags=f"num_{i}")
            
            check_x = x + thumb_w//2 - 12
            check_y = y_pos + thumb_h + 35
            canvas.create_rectangle(check_x, check_y, check_x+24, check_y+24,
                                    outline="#666", fill="#fff", tags=f"checkbg_{i}")
            
            checked = "✓" if i in self.selected_pages else ""
            canvas.create_text(check_x + 12, check_y + 12, text=checked,
                               font=("Georgia", 14, "bold"), fill="#28a745", tags=f"check_{i}")
            
            for tag in [bg_tag, img_tag, f"checkbg_{i}", f"check_{i}"]:
                canvas.tag_bind(tag, "<Button-1>", lambda e, idx=i: self.toggle_page_selection_canvas(idx))
            
            if i in self.exported_pages:
                canvas.create_text(x + thumb_w//2, y_pos + thumb_h + 65,
                                   text="✓ Exported", font=("Georgia", 9, "bold"), fill="#28a745", tags=f"exp_{i}")
        
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        self.view_mode = "tile"
        self.update_selected_count()
    
    def toggle_page_selection_canvas(self, page_idx):
        if page_idx in self.selected_pages:
            self.selected_pages.discard(page_idx)
        else:
            self.selected_pages.add(page_idx)
        
        check_tag = f"check_{page_idx}"
        check_text = "✓" if page_idx in self.selected_pages else ""
        self.tile_canvas.itemconfig(check_tag, text=check_text)
        
        self.update_selected_count()
    
    def update_selected_count(self):
        count = len(self.selected_pages)
        self.selected_count_label.config(text=f"Selected: {count} page{'s' if count != 1 else ''}")
    
    def _on_mousewheel(self, event):
        if self.view_mode == "tile" and hasattr(self, 'tile_canvas'):
            self.tile_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def switch_view(self, mode):
        self.view_mode = mode
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        if mode == "tile":
            self.show_tile_canvas_view()
        else:
            self.show_full_view()
    
    def show_full_view(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        nav = tk.Frame(self.content_frame, bg="#f0f0f0")
        nav.pack(fill="x", pady=5)
        
        tk.Button(nav, text="← Previous", command=self.prev_page).pack(side="left", padx=10)
        
        tk.Label(nav, text=f"Page {self.current_page + 1} of {self.num_pages}", 
                 font=("Georgia", 12, "bold")).pack(side="left", expand=True)
        
        zoom_frame = tk.Frame(nav, bg="#f0f0f0")
        zoom_frame.pack(side="left", padx=20)
        
        tk.Button(zoom_frame, text="−", width=3, font=("Georgia", 12, "bold"),
                  command=self.zoom_out).pack(side="left", padx=(0, 2))
        
        self.zoom_label_full = tk.Label(zoom_frame, text=f"Zoom: {int(self.zoom*100)}%", 
                                        font=("Georgia", 10), bg="#f0f0f0")
        self.zoom_label_full.pack(side="left", padx=5)
        
        tk.Button(zoom_frame, text="+", width=3, font=("Georgia", 12, "bold"),
                  command=self.zoom_in).pack(side="left", padx=2)
        
        tk.Button(zoom_frame, text="Fit to Window", width=12, font=("Georgia", 9, "bold"),
                  command=self.fit_to_window).pack(side="left", padx=8)
        
        tk.Button(nav, text="Next →", command=self.next_page).pack(side="left", padx=10)
        
        self.full_canvas = tk.Canvas(self.content_frame, bg="#222222", highlightthickness=0)
        self.full_canvas.pack(fill="both", expand=True)
        
        self.full_canvas.bind("<ButtonPress-1>", self.start_pan)
        self.full_canvas.bind("<B1-Motion>", self.do_pan)
        
        chk_frame = tk.Frame(self.content_frame)
        chk_frame.pack(pady=10)
        
        self.full_view_var = tk.BooleanVar(value=self.current_page in self.selected_pages)
        self.full_chk = tk.Checkbutton(chk_frame, 
                                       text=f"Select Page {self.current_page + 1} for export",
                                       variable=self.full_view_var,
                                       command=self.toggle_current_page_selection)
        self.full_chk.pack()
        
        if self.current_page in self.exported_pages:
            tk.Label(chk_frame, text="✓ This page has been exported", fg="green",
                     font=("Georgia", 10, "bold")).pack()
        
        self.update_full_page_image()
    
    def start_pan(self, event):
        self.full_canvas.scan_mark(event.x, event.y)
    
    def do_pan(self, event):
        self.full_canvas.scan_dragto(event.x, event.y, gain=1)
    
    def fit_to_window(self):
        if not hasattr(self, 'full_canvas'):
            return
        canvas_w = self.full_canvas.winfo_width()
        canvas_h = self.full_canvas.winfo_height()
        if canvas_w < 50 or canvas_h < 50:
            return
        
        page = self.pdf_doc[self.current_page]
        native_pix = page.get_pixmap(matrix=fitz.Matrix(1, 1))
        native_w = native_pix.width
        native_h = native_pix.height
        if native_w == 0 or native_h == 0:
            return
        
        scale_x = canvas_w / native_w
        scale_y = canvas_h / native_h
        self.zoom = min(scale_x, scale_y)
        self.update_full_page_image()
    
    def toggle_current_page_selection(self):
        if self.full_view_var.get():
            self.selected_pages.add(self.current_page)
        else:
            self.selected_pages.discard(self.current_page)
        self.update_selected_count()
    
    def update_full_page_image(self):
        if not hasattr(self, 'full_canvas'):
            return
        
        self.full_canvas.delete("all")
        
        page = self.pdf_doc[self.current_page]
        matrix = fitz.Matrix(self.zoom, self.zoom)
        pix = page.get_pixmap(matrix=matrix)
        pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.full_photo = ImageTk.PhotoImage(pil_img)
        
        img_w = self.full_photo.width()
        img_h = self.full_photo.height()
        canvas_w = self.full_canvas.winfo_width()
        canvas_h = self.full_canvas.winfo_height()
        
        x = max(0, (canvas_w - img_w) // 2)
        y = max(0, (canvas_h - img_h) // 2)
        
        self.full_canvas.create_image(x, y, anchor="nw", image=self.full_photo)
        self.full_canvas.configure(scrollregion=(0, 0, img_w, img_h))
        
        if hasattr(self, 'zoom_label_full'):
            self.zoom_label_full.config(text=f"Zoom: {int(self.zoom*100)}%")
    
    def zoom_in(self):
        self.zoom *= 1.15
        self.zoom = min(4.0, self.zoom)
        self.update_full_page_image()
    
    def zoom_out(self):
        self.zoom /= 1.15
        self.zoom = max(0.2, self.zoom)
        self.update_full_page_image()
    
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.switch_view("full")
    
    def next_page(self):
        if self.current_page < self.num_pages - 1:
            self.current_page += 1
            self.switch_view("full")
    
    def export_selected(self):
        if not self.selected_pages:
            messagebox.showwarning("Nothing selected", "Please select at least one page to export.")
            return
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save exported pages as..."
        )
        if not save_path:
            return
        
        try:
            export_doc = fitz.open()
            for p in sorted(self.selected_pages):
                export_doc.insert_pdf(self.pdf_doc, from_page=p, to_page=p)
            
            export_doc.save(save_path, garbage=1, deflate=True, clean=True)
            export_doc.close()
            
            for p in list(self.selected_pages):
                self.exported_pages.add(p)
            
            messagebox.showinfo("Export Complete", f"{len(self.selected_pages)} page(s) exported to:\n{save_path}")
            self.selected_pages.clear()
            self.update_selected_count()
            self.switch_view(self.view_mode)
            
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
    
    def destroy(self):
        if hasattr(self, 'pdf_doc') and self.pdf_doc:
            self.pdf_doc.close()
        super().destroy()


if __name__ == "__main__":
    app = PDFStamperApp()
    app.run()