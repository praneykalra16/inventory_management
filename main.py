import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageTk
from io import BytesIO
import csv
from ttkthemes import ThemedTk
import subprocess
import os
from PIL import ImageWin
import win32print
import win32ui
# Global lists for barcode images and features
barcode_images = []
features_list = []

import order_management

def open_order_management():
    order_management.main()
# Run the new.py script
def run_new_script():
    subprocess.run(["python", "new.py"], check=True)


# Database setup
def init_db():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            reel_no TEXT,
            size TEXT,
            bf TEXT,
            gsm TEXT,
            product_type TEXT CHECK(product_type IN ('semi', 'royal')),
            barcode TEXT
        )
    ''')
    conn.commit()
    conn.close()


# Initialize the database and run new.py script
init_db()
run_new_script()


# Function to save product and generate barcode
def get_last_id():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(id) FROM products')
    last_id = cursor.fetchone()[0] or 0
    conn.close()
    return last_id


import string


def generate_reel_no(last_id):
    def increment_string(s):
        """Increment a string in a way similar to incrementing numbers"""
        s = list(s)
        for i in reversed(range(len(s))):
            if s[i] == 'z':
                s[i] = 'a'
            else:
                s[i] = chr(ord(s[i]) + 1)
                break
        return ''.join(s)

    last_id = int(last_id) if last_id else 0
    base = 26 * 1000
    length = 1
    while last_id >= base:
        length += 1
        base *= 26

    reel_base = string.ascii_lowercase
    reel_no = ''
    for _ in range(length):
        reel_no = increment_string(reel_no)

    # Ensure reel_no is not empty
    reel_no = reel_no or 'a'
    return f'{reel_no}{last_id % 1000 + 1}'


def save_product():
    global barcode_images, features_list

    # Get the last product ID and generate the next reel number
    last_id = get_last_id()
    reel_no = generate_reel_no(last_id)
    size = entry_size.get()
    bf = entry_bf.get()
    gsm = entry_gsm.get()
    product_type_value = product_type.get()

    if not all([size, bf, gsm, product_type_value]):
        messagebox.showerror("Error", "All fields are required!")
        return

    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (reel_no, size, bf, gsm, product_type) 
        VALUES (?, ?, ?, ?, ?)
    ''', (reel_no, size, bf, gsm, product_type_value))
    product_id = cursor.lastrowid

    # Generate barcode
    barcode_str = f'{product_id:012d}'
    ean = barcode.get('ean13')(barcode_str, writer=ImageWriter())
    full_barcode_str = ean.get_fullcode()
    buffer = BytesIO()
    ean.write(buffer)

    # Save barcode image to list
    barcode_image = Image.open(buffer)
    barcode_images.append(barcode_image)

    # Save the full barcode number (including check digit) in the database
    cursor.execute('''
        UPDATE products SET barcode = ? WHERE id = ?
    ''', (full_barcode_str, product_id))
    conn.commit()
    conn.close()

    # Display product features
    features_text = f"Reel No.: {reel_no}\nSize: {size}\nGSM: {gsm}\nType: {product_type_value}"
    features_list.append(features_text)

    # Update the Text widget to show the new product label
    labels_display.insert(tk.END, features_text + "\n\n")
    labels_display.yview(tk.END)  # Auto-scroll to the end

    # Show success message
    messagebox.showinfo("Success", "Product saved and barcode generated!")

    # Run new.py script
    run_new_script()

def preview_print():
    global barcode_images, features_list  # Access the global lists

    if not barcode_images:
        messagebox.showerror("Error", "Generate a barcode first!")
        return

    # Create a new window for the preview
    preview_window = tk.Toplevel(root)
    preview_window.title("Print Preview")

    canvas = tk.Canvas(preview_window, width=595, height=842)  # A4 size in points (1/72 of an inch)
    canvas.pack()

    x_offset = 50  # Initial x offset for the barcode images
    y_offset = 50  # Initial y offset for the barcode images
    photo_images = []  # List to keep references to PhotoImage objects

    for i, (barcode_image, features_text) in enumerate(zip(barcode_images, features_list)):
        # Draw the barcode image on the canvas
        barcode_image_resized = barcode_image.resize((200, 100))  # Resize for better fit
        barcode_photo = ImageTk.PhotoImage(barcode_image_resized)
        canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=barcode_photo)
        photo_images.append(barcode_photo)  # Store the reference

        # Draw the text below the barcode image
        text_x = x_offset
        text_y = y_offset + 110  # Position below the barcode image
        for line in features_text.split('\n'):
            canvas.create_text(text_x, text_y, anchor=tk.NW, text=line, font=("Helvetica", 12))
            text_y += 20  # Line spacing

        # Update the x offset for the next barcode image
        x_offset += 220  # Adjust the x offset to position the next barcode side by side

        # Move to the next row if the barcodes exceed the canvas width
        if x_offset + 220 > 595:
            x_offset = 50
            y_offset += 250

    # Show the preview window
    preview_window.mainloop()


# Function to print label
def print_label():
    global barcode_images, features_list  # Access the global lists

    if not barcode_images:
        messagebox.showerror("Error", "Generate a barcode first!")
        return

    # Replace this with the actual command or library function for your label printer
    # For demonstration, we will print to console
    for features_text in features_list:
        print(f"Printing label...\n{features_text}")

    # Optionally, you can also print the barcode images
    for barcode_image in barcode_images:
        # This requires converting ImageTk format back to PIL Image
        barcode_image_pil = barcode_image.copy()
        barcode_image_pil.save('barcode.png', 'PNG')

        # Simulate printing barcode image (you need to adjust this part based on your label printer)
        print("Printing barcode image...")

        # Open the printer
        printer_name = win32print.GetDefaultPrinter()
        hprinter = win32print.OpenPrinter(printer_name)

        try:
            # Start a print job
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(printer_name)
            hdc.StartDoc("Barcode Label")
            hdc.StartPage()

            # Set up the print area and dimensions for A4 paper
            a4_width = 2100  # A4 width in tenths of a millimeter (210 mm)
            a4_height = 2970  # A4 height in tenths of a millimeter (297 mm)
            margins = 100  # Margins in tenths of a millimeter (10 mm)

            # Print the barcode image
            img_width, img_height = barcode_image_pil.size
            img_x = margins
            img_y = margins
            img_rect = (img_x, img_y, img_x + img_width, img_y + img_height)
            bmp = ImageWin.Dib(barcode_image_pil)
            bmp.draw(hdc.GetHandleOutput(), img_rect)

            # Print the text below the barcode image
            text_x = margins
            text_y = img_y + img_height + 20  # 20 tenths of a millimeter below the image
            hdc.TextOut(text_x, text_y, features_text)

            # End the page and document
            hdc.EndPage()
            hdc.EndDoc()

        finally:
            # Close the printer handle
            win32print.ClosePrinter(hprinter)


# Function to handle barcode scanning
def scan_barcode():
    barcode_value = barcode_entry.get()
    if not barcode_value:
        messagebox.showerror("Error", "Please enter a barcode value!")
        return

    print(f"Scanning barcode: {barcode_value}")  # Debug statement
    # Check if the product exists in the database
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE barcode=?', (barcode_value,))
    product = cursor.fetchone()

    if product:
        print(f"Product found: {product}")  # Debug statement

        # Add product to the list for printing
        listbox_products.insert(tk.END,
                                f"ID: {product[0]}, Reel No.: {product[1]}, Size: {product[2]}, BF: {product[3]}, GSM: {product[4]}, Type: {product[5]}")

        # Remove product from the database
        cursor.execute('DELETE FROM products WHERE barcode=?', (barcode_value,))
        conn.commit()
        conn.close()

        # Show success message
        messagebox.showinfo("Success", "Product scanned and removed from database!")
    else:
        print("Product not found")  # Debug statement
        messagebox.showerror("Error", "Product not found in database!")

    # Clear barcode entry field
    barcode_entry.delete(0, tk.END)
    run_new_script()


# Function to print scanned list
def print_scanned_list():
    # Get all items from listbox_products
    items = listbox_products.get(0, tk.END)
    if not items:
        messagebox.showinfo("Information", "No items to print.")
        return

    # Replace with actual printing logic for the list
    print("Printing scanned list...")
    for item in items:
        print(item)

    # Optionally, clear the listbox after printing
    listbox_products.delete(0, tk.END)


# Function to delete a row from the CSV file and database
def delete_csv_row(row_index):
    temp_file = 'temp_products_export.csv'
    product_id = None

    with open('products_export.csv', 'r') as csvfile, open(temp_file, 'w', newline='') as temp_csvfile:
        reader = csv.reader(csvfile)
        writer = csv.writer(temp_csvfile)

        for i, row in enumerate(reader):
            if i == row_index:
                product_id = row[0]  # Assuming the first column is the product ID
            else:
                writer.writerow(row)

    os.replace(temp_file, 'products_export.csv')

    if product_id:
        conn = sqlite3.connect('products.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE id=?', (product_id,))
        conn.commit()
        conn.close()


# Function to open a new window with CSV data
def open_csv_window():
    csv_window = tk.Toplevel(root)
    csv_window.title("CSV Data")

    frame = ttk.Frame(csv_window)
    frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

    # Create the Treeview widget
    tree = ttk.Treeview(frame, columns=("ID", "Reel No.", "Size", "BF", "GSM", "Product Type", "Barcode"), show="headings")
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Define the column headings
    tree.heading("ID", text="ID")
    tree.heading("Reel No.", text="Reel No.")
    tree.heading("Size", text="Size")
    tree.heading("BF", text="BF")
    tree.heading("GSM", text="GSM")
    tree.heading("Product Type", text="Product Type")
    tree.heading("Barcode", text="Barcode")

    # Define column widths
    tree.column("ID", width=50)
    tree.column("Reel No.", width=100)
    tree.column("Size", width=100)
    tree.column("BF", width=50)
    tree.column("GSM", width=50)
    tree.column("Product Type", width=100)
    tree.column("Barcode", width=150)

    # Add a vertical scrollbar
    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Function to delete the selected row
    def delete_selected_row():
        selected_item = tree.selection()[0]
        row_index = tree.index(selected_item)
        delete_csv_row(row_index + 1)
        tree.delete(selected_item)

    # Add a delete button
    delete_button = ttk.Button(csv_window, text="Delete Selected Row", command=delete_selected_row)
    delete_button.pack(pady=10)

    # Populate the Treeview with data from the CSV file
    with open('products_export.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            tree.insert("", tk.END, values=row)


# Function to toggle full screen
def toggle_fullscreen(event=None):
    root.state('zoomed')

def fetch_customer_names():
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM customers')
    customer_names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return customer_names

# Fetch customer names
customer_names = fetch_customer_names()

# Create a StringVar for the customer name

# Function to update the dropdown list based on the current entry
def update_customer_list(event):
    typed = selected_customer.get()
    if typed == '':
        customer_dropdown['values'] = customer_names
    else:
        filtered_names = [name for name in customer_names if typed.lower() in name.lower()]
        customer_dropdown['values'] = filtered_names





# Main application window
root = ThemedTk(theme="breeze")
root.title("Product Management")
root.geometry("800x500")
selected_customer = tk.StringVar(root)

# Create a scrollable frame
main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

canvas = tk.Canvas(main_frame)
scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Create a frame to hold input fields and label display
input_frame = ttk.Frame(scrollable_frame)
input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# Fetch customer names
customer_names = fetch_customer_names()

# Create a StringVar for the customer name
selected_customer = tk.StringVar()

# Create the dropdown beside the scan barcode button
ttk.Label(scrollable_frame, text="Select Customer:").grid(row=5, column=3, padx=10, pady=10)
customer_dropdown = ttk.Combobox(scrollable_frame, textvariable=selected_customer)
customer_dropdown['values'] = customer_names
customer_dropdown.grid(row=5, column=4, padx=10, pady=10)
customer_dropdown.current(0)  # Set default value


# Barcode scanning
ttk.Label(scrollable_frame, text="Enter Barcode:").grid(row=5, column=0, padx=10, pady=10)
barcode_entry = ttk.Entry(scrollable_frame)
barcode_entry.grid(row=5, column=1, padx=10, pady=10)
scan_button = ttk.Button(scrollable_frame, text="Scan Barcode", command=scan_barcode)
scan_button.grid(row=5, column=2, padx=10, pady=10)

# Fetch customer names
customer_names = fetch_customer_names()

# Create a StringVar for the customer name

# Create the dropdown beside the scan barcode button
ttk.Label(scrollable_frame, text="Select Customer:").grid(row=5, column=3, padx=10, pady=10)
customer_dropdown = ttk.Combobox(scrollable_frame, textvariable=selected_customer)
customer_dropdown['values'] = customer_names
customer_dropdown.grid(row=5, column=4, padx=10, pady=10)
customer_dropdown.bind('<KeyRelease>', update_customer_list)
# Input fields
# Input fields
ttk.Label(input_frame, text="Size:").grid(row=0, column=0, padx=10, pady=10)
entry_size = ttk.Entry(input_frame)
entry_size.grid(row=0, column=1, padx=10, pady=10)

ttk.Label(input_frame, text="BF:").grid(row=1, column=0, padx=10, pady=10)
entry_bf = ttk.Entry(input_frame)
entry_bf.grid(row=1, column=1, padx=10, pady=10)

ttk.Label(input_frame, text="GSM:").grid(row=2, column=0, padx=10, pady=10)
entry_gsm = ttk.Entry(input_frame)
entry_gsm.grid(row=2, column=1, padx=10, pady=10)

ttk.Label(input_frame, text="Product Type:").grid(row=3, column=0, padx=10, pady=10)
product_type = tk.StringVar()
dropdown_product_type = ttk.Combobox(input_frame, textvariable=product_type)
dropdown_product_type['values'] = ('semi', 'royal')
dropdown_product_type.grid(row=3, column=1, padx=10, pady=10)
dropdown_product_type.current(0)  # Set default value


# Save button
save_button = ttk.Button(input_frame, text="Save Product", command=save_product)
save_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

# Labels display
labels_display = tk.Text(scrollable_frame, height=10, width=30, wrap=tk.WORD)
labels_display.grid(row=0, column=1, rowspan=3, padx=10, pady=10, sticky="ns")

# Print and Preview buttons
print_button = ttk.Button(scrollable_frame, text="Print Label", command=print_label)
print_button.grid(row=4, column=0, padx=10, pady=10)

preview_button = ttk.Button(scrollable_frame, text="Preview Label", command=preview_print)
preview_button.grid(row=4, column=1, padx=10, pady=10)

open_order_management_button = tk.Button(root, text="Open Order Management", command=open_order_management)
open_order_management_button.pack(pady=20)

ttk.Label(scrollable_frame, text="Enter Barcode:").grid(row=5, column=0, padx=10, pady=10)
barcode_entry = ttk.Entry(scrollable_frame)
barcode_entry.grid(row=5, column=1, padx=10, pady=10)
scan_button = ttk.Button(scrollable_frame, text="Scan Barcode", command=scan_barcode)
scan_button.grid(row=5, column=2, padx=10, pady=10)

# Listbox for scanned products
listbox_products = tk.Listbox(scrollable_frame)
listbox_products.grid(row=6, column=0, columnspan=3, padx=10, pady=10)

# Print scanned list button
print_list_button = ttk.Button(scrollable_frame, text="Print Scanned List", command=print_scanned_list)
print_list_button.grid(row=7, column=0, columnspan=3, padx=10, pady=10)

# Open CSV data window button
csv_button = ttk.Button(scrollable_frame, text="Open CSV Data", command=open_csv_window)
csv_button.grid(row=8, column=0, columnspan=3, padx=10, pady=10)

# Bind the F11 key to toggle fullscreen mode
root.bind("<F11>", toggle_fullscreen)

# Run the application
root.mainloop()
