#!/usr/bin/env python3

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import shutil
from pathlib import Path
import threading

cache = {}

def get_folder_size(path):
    key = str(path.resolve())

    if key in cache:
        return cache[key]
    
    total = 0

    try:
        with os.scandir(path) as it:
                for entry in it:
                    try:
                        if entry.is_file(follow_symlinks=False):
                                total += entry.stat().st_size
               
                        elif entry.is_dir(follow_symlinks=False):
                                total += get_folder_size(Path(entry.path))

                    except PermissionError:
                        pass

    except PermissionError:
        print(f"Permission Denied: {path}")

    cache[key] = total
    return total

kb = 1024
mb = 1024 * kb
gb = 1024 * mb
tb = 1024 * gb
pb = 1024 * tb

def scan_folder(folder_path, progress_callback=None):
    items = []
    folder = Path(folder_path)
    all_entries = list(folder.iterdir())
    total_entries = len(all_entries)
    
    for idx, path in enumerate(all_entries):
        if progress_callback:
            should_continue = progress_callback(idx, total_entries)
            if should_continue is False:  # Cancellation requested
                return [], 0, "0 bytes"
        
        name = path.name
        if path.is_dir():
            try:
                size = get_folder_size(path)
                if size < kb:
                    d_size = f"{size} bytes"
                elif size < mb:
                    d_size = f"{round(size / kb, 2)} KB"
                elif size < gb:
                    d_size = f"{round(size / mb, 2)} MB"
                elif size < tb:
                    d_size = f"{round(size / gb, 2)} GB"
                elif size < pb:
                    d_size = f"{round(size / tb, 2)} TB"
                else:
                    d_size = f"{round(size / pb, 2)} PB"
                
                items.append((f"[FOLDER] {name}", size, d_size, "folder", str(path)))
            except:
                pass
            continue

        try:
            size = path.stat().st_size

            if size < kb:
                d_size = f"{size} bytes"
            elif size < mb:
                d_size = f"{round(size / kb, 2)} KB"
            elif size < gb:
                d_size = f"{round(size / (mb), 2)} MB"
            elif size < tb:
                d_size = f"{round(size / (gb), 2)} GB"
            elif size < pb:
                d_size = f"{round(size / (tb), 2)} TB"
            else:
                d_size = f"{round(size / pb, 2)} PB"

            color = "normal"
            if size >= 20 * gb:
                color = "red"
            elif size >= 10 * gb:
                color = "orange"
            elif size >= 2.5 * gb:
                color = "yellow"
            
            items.append((name, size, d_size, color, str(path)))
        except:
            pass

    if progress_callback:
        progress_callback(total_entries, total_entries)

    items.sort(key=lambda x: x[1], reverse=True)

    total = sum(item[1] for item in items)

    if total < kb:
        d_total = f"{total} bytes"
    elif total < mb:
        d_total = f"{round(total / kb, 2)} KB"
    elif total < gb:
        d_total = f"{round(total / (mb), 2)} MB"
    elif total < tb:
        d_total = f"{round(total / (gb), 2)} GB"
    elif total < pb:
        d_total = f"{round(total / (tb), 2)} TB"
    else:
        d_total = f"{round(total / pb, 2)} PB"

    return items, total, d_total

# GUI Code
root = tk.Tk()
root.title("Sweepy - Folder Size Analyzer")
try:
    root.state('zoomed')
except:
    root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")

style = ttk.Style(root)
style.theme_use("clam")
style.configure("Green.TButton", background="#4CAF50", foreground="white", font=("Arial", 10, "bold"), padding=6, relief="raised")
style.map("Green.TButton", background=[("active", "#2e7d32"), ("pressed", "#1b5e20")], foreground=[("active", "white")])
style.configure("Blue.TButton", background="#2196F3", foreground="white", font=("Arial", 10, "bold"), padding=6, relief="raised")
style.map("Blue.TButton", background=[("active", "#1976D2"), ("pressed", "#1565C0")], foreground=[("active", "white")])

# Progress bar styles
style.configure("Red.Horizontal.TProgressbar", background="#f44336")
style.configure("Orange.Horizontal.TProgressbar", background="#ff9800")
style.configure("Yellow.Horizontal.TProgressbar", background="#ffeb3b")
style.configure("Green.Horizontal.TProgressbar", background="#4caf50")

# Folder selection
folder_frame = tk.Frame(root)
folder_frame.pack(pady=10)

folder_var = tk.StringVar(value=str(Path.home() / "Downloads"))
folder_label = tk.Label(folder_frame, text="Folder:", font=("Arial", 10, "bold"))
folder_label.pack(side=tk.LEFT)
folder_entry = tk.Entry(folder_frame, textvariable=folder_var, width=50)
folder_entry.pack(side=tk.LEFT, padx=5)

def choose_folder():
    new_folder = filedialog.askdirectory()
    if new_folder:
        folder_var.set(new_folder)

choose_button = ttk.Button(folder_frame, text="Choose Folder", style="Green.TButton", command=choose_folder)
choose_button.pack(side=tk.LEFT, padx=5)

# Scan button
def scan():
    global scanning_thread, cancel_button
    
    folder = folder_var.get()
    if not Path(folder).exists():
        messagebox.showerror("Error", "Folder does not exist")
        return
    
    # Reset cancel flag
    cancel_var.set(False)
    
    # Disable scan button
    scan_button.config(state=tk.DISABLED)
    
    # Show progress bar and cancel button
    progress_canvas.pack(side=tk.LEFT, padx=5)
    progress_label.pack(side=tk.LEFT, padx=5)
    
    if cancel_button is None:
        cancel_button = ttk.Button(progress_frame, text="Cancel", style="Green.TButton", command=lambda: cancel_var.set(True))
    cancel_button.pack(side=tk.LEFT, padx=5)
    
    def scan_in_thread():
        try:
            def update_progress(current, total):
                if cancel_var.get():
                    return False  # Signal to stop scanning
                progress = (current / total) * 100 if total > 0 else 0
                progress_label.config(text=f"{int(progress)}%")
                
                # Update gradient progress bar
                update_progress_bar(progress)
                
                root.update()
                return not cancel_var.get()
            
            items, total, d_total = scan_folder(folder, progress_callback=update_progress)
            
            if cancel_var.get():
                return
            
            # Store the data
            global current_items, current_total
            current_items = items
            current_total = total
            
            # Display the results
            refresh_display()
            
            total_var.set(f"Total: {d_total}")
        except Exception as e:
            if not cancel_var.get():
                messagebox.showerror("Error", str(e))
        finally:
            # Hide progress bar and cancel button
            progress_canvas.pack_forget()
            progress_label.pack_forget()
            cancel_button.pack_forget()
            scan_button.config(state=tk.NORMAL)
    
    scanning_thread = threading.Thread(target=scan_in_thread, daemon=True)
    scanning_thread.start()

def refresh_display():
    global current_items, current_total
    if not current_items:
        return
    
    # Clear tree
    for i in tree.get_children():
        tree.delete(i)
    item_paths.clear()
    
    # Add items with optional percentages
    for item_data in current_items:
        if len(item_data) == 5:
            name, size, d_size, color, file_path = item_data
        else:
            name, size, d_size, color = item_data
            file_path = ""
        
        # Calculate percentage if enabled
        if show_percent_var.get() and current_total > 0:
            percentage = (size / current_total) * 100
            pct_text = f"{percentage:.1f}%"
        else:
            pct_text = ""
        
        item_id = tree.insert("", tk.END, values=(name, d_size, pct_text), tags=(color,) if color != "normal" else ())
        if file_path:
            item_paths[item_id] = file_path

scan_button = ttk.Button(folder_frame, text="Scan Total", style="Blue.TButton", command=lambda: scan())
scan_button.pack(side=tk.LEFT)

# Show % toggle button
show_percent_var = tk.BooleanVar(value=False)

def toggle_percent():
    show_percent_var.set(not show_percent_var.get())
    if item_paths:  # Only refresh if we have data
        refresh_display()

show_percent_button = ttk.Button(folder_frame, text="Show %", style="Green.TButton", command=toggle_percent)
show_percent_button.pack(side=tk.LEFT, padx=5)

# Back button
def go_back():
    current_path = Path(folder_var.get())
    parent = current_path.parent
    if parent != current_path:  # Not at root
        folder_var.set(str(parent))
        scan()

back_button = ttk.Button(folder_frame, text="← Back", style="Blue.TButton", command=go_back)
back_button.pack(side=tk.LEFT, padx=5)

# Cancel button variable
cancel_var = tk.BooleanVar(value=False)
cancel_button = None
scanning_thread = None

# Dictionary to store file paths for tree items
item_paths = {}
# Store the current scan data
current_items = []
current_total = 0

# Progress bar (initially hidden) - Canvas-based gradient
progress_frame = tk.Frame(root)
progress_frame.pack(pady=10)

progress_canvas = tk.Canvas(progress_frame, width=400, height=20, bg='white', highlightthickness=1, highlightbackground='gray')
progress_label = tk.Label(progress_frame, text="", font=("Arial", 10))

def update_progress_bar(progress):
    """Update the gradient progress bar - entire bar fades from red to green"""
    progress_canvas.delete("progress")
    
    if progress < 0:
        progress = 0
    elif progress > 100:
        progress = 100
    
    # Calculate color based on overall progress (0-100%)
    if progress < 25:
        # Red to Orange (0-25%)
        ratio = progress / 25
        r = 255
        g = int(165 * ratio)
        b = 0
    elif progress < 50:
        # Orange to Yellow (25-50%)
        ratio = (progress - 25) / 25
        r = 255
        g = int(165 + (255 - 165) * ratio)
        b = 0
    elif progress < 75:
        # Yellow to Green (50-75%)
        ratio = (progress - 50) / 25
        r = int(255 * (1 - ratio))
        g = 255
        b = 0
    else:
        # Green (75-100%)
        r = 0
        g = 255
        b = 0
    
    color = f'#{r:02x}{g:02x}{b:02x}'
    # Draw the entire bar with the current color
    progress_canvas.create_rectangle(0, 0, 400, 20, fill=color, outline=color, tags="progress")

# Treeview for results
tree_frame = tk.Frame(root)
tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

tree = ttk.Treeview(tree_frame, columns=("Name", "Size", "Percent"), show="headings", height=15)
tree.heading("Name", text="Name")
tree.heading("Size", text="Size")
tree.heading("Percent", text="%")
tree.column("Name", width=300)
tree.column("Size", width=150)
tree.column("Percent", width=80, anchor="e")

# Configure tree to receive events
tree.configure(selectmode="browse")

# Scrollbar
scrollbar = tk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
tree.configure(yscroll=scrollbar.set)
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Configure tags for colors
tree.tag_configure("red", foreground="#c62828")
tree.tag_configure("orange", foreground="#ef6c00")
tree.tag_configure("yellow", foreground="#f9a825")
tree.tag_configure("folder", foreground="#1976D2")

# Total label
total_var = tk.StringVar(value="Total: ")
total_label = tk.Label(root, textvariable=total_var, font=("Arial", 12, "bold"))
total_label.pack(pady=5)

# Context menu for files
def move_to_trash(file_path):
    try:
        shutil.move(file_path, os.path.expanduser("~/.Trash"))
        messagebox.showinfo("Success", "File moved to trash")
        # Refresh the display to update percentages and remove the item
        if current_items:
            scan()  # Re-scan to get updated data
    except Exception as e:
        messagebox.showerror("Error", f"Could not move to trash: {str(e)}")

def view_in_finder(file_path):
    try:
        subprocess.Popen(["open", "-R", file_path])
    except Exception as e:
        messagebox.showerror("Error", f"Could not open in Finder: {str(e)}")

def on_right_click(event):
    try:
        # Get the item at the click position
        item = tree.identify_row(event.y)
        if not item:
            return
        
        # Select the item (this will highlight it blue)
        tree.selection_set(item)
        tree.focus(item)
        
        # Check if we have the file path
        if item not in item_paths:
            # Try to recreate the path from the display name
            values = tree.item(item)["values"]
            if values:
                name = values[0]
                folder = folder_var.get()
                if name.startswith("[FOLDER]"):
                    display_name = name.replace("[FOLDER] ", "")
                    file_path = os.path.join(folder, display_name)
                else:
                    file_path = os.path.join(folder, name)
            else:
                return
        else:
            file_path = item_paths[item]
        
        if not os.path.exists(file_path):
            return
        
        # Create and show context menu
        menu = tk.Menu(root, tearoff=0, bg="white")
        menu.add_command(label="View in Finder", command=lambda fp=file_path: view_in_finder(fp))
        menu.add_command(label="Move to Trash", command=lambda fp=file_path: move_to_trash(fp))
        menu.tk_popup(event.x_root, event.y_root)
        
    except Exception as e:
        messagebox.showerror("Error", f"Error in right-click: {str(e)}")

def on_double_click(event):
    """Handle double-click to navigate into folders"""
    try:
        item = tree.identify_row(event.y)
        if not item:
            return
        
        # Get the item values
        values = tree.item(item)["values"]
        if not values:
            return
        
        name = values[0]
        
        # Check if it's a folder
        if not name.startswith("[FOLDER]"):
            return
        
        # Get the folder path
        if item in item_paths:
            folder_path = item_paths[item]
        else:
            display_name = name.replace("[FOLDER] ", "")
            folder_path = os.path.join(folder_var.get(), display_name)
        
        # Navigate into the folder
        if os.path.isdir(folder_path):
            folder_var.set(folder_path)
            scan()
    except Exception as e:
        messagebox.showerror("Error", f"Error in double-click: {str(e)}")

# Try binding to multiple possible right-click events
tree.bind("<Double-Button-1>", on_double_click)  # Double-click to navigate

tree.bind("<Button-3>", on_right_click)  # Standard right-click
tree.bind("<Button-2>", on_right_click)  # Middle-click
tree.bind("<Control-Button-1>", on_right_click)  # Ctrl+click (macOS right-click)
tree.bind("<ButtonRelease-3>", on_right_click)  # Right-click release
tree.bind("<ButtonRelease-2>", on_right_click)  # Middle-click release
tree.bind("<Control-ButtonRelease-1>", on_right_click)  # Ctrl+click release

tree_frame.bind("<Button-3>", on_right_click)
tree_frame.bind("<Button-2>", on_right_click)
tree_frame.bind("<Control-Button-1>", on_right_click)
tree_frame.bind("<ButtonRelease-3>", on_right_click)
tree_frame.bind("<ButtonRelease-2>", on_right_click)
tree_frame.bind("<Control-ButtonRelease-1>", on_right_click)

# Make sure tree can receive focus
tree.focus_set()
tree.focus()

# Run the app
root.mainloop()