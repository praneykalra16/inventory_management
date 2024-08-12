import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import barcode
from barcode.writer import ImageWriter
from barcode.ean import EAN13
from PIL import Image, ImageTk
from io import BytesIO
import csv
from ttkthemes import ThemedTk
import subprocess
import os
import win32print
import win32ui
from PIL import Image, ImageDraw, ImageFont, ImageWin


barcode_images = []
features_list = []

import order_management


def open_order_management():
    order_management.main()


def run_new_script():
    subprocess.run(["python", "new.py"], check=True)


def refreshcus(event=None):
    customer_names = fetch_customer_names()
    customer_dropdown["values"] = customer_names
    if customer_names:
        customer_dropdown.current(0)
    else:
        customer_dropdown.set("")


def refresh_customer_dropdown():
    customer_names = fetch_customer_names()
    if customer_names:
        customer_dropdown["values"] = customer_names
        customer_dropdown.current(0)  # Optionally, set the first item as default
    else:
        customer_dropdown.set("")  # Clear the selection if no customers are available


# Database setup
def init_db():
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            reel_no TEXT,
            size TEXT,
            bf TEXT,
            gsm TEXT,
            product_type TEXT CHECK(product_type IN ('semi', 'rg')),
            barcode TEXT
        )
    """
    )
    conn.commit()
    conn.close()


# Initialize the database and run new.py script
init_db()
run_new_script()


# Function to save product and generate barcode
def get_last_id():
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM products")
    last_id = cursor.fetchone()[0] or 0
    conn.close()
    return last_id


import string


def generate_reel_no(last_id):
    def increment_string(s):
        """Increment a string in a way similar to incrementing numbers"""
        s = list(s)
        for i in reversed(range(len(s))):
            if s[i] == "z":
                s[i] = "a"
            else:
                s[i] = chr(ord(s[i]) + 1)
                break
        return "".join(s)

    last_id = int(last_id) if last_id else 0
    base = 26 * 1000
    length = 1
    while last_id >= base:
        length += 1
        base *= 26

    reel_base = string.ascii_lowercase
    reel_no = ""
    for _ in range(length):
        reel_no = increment_string(reel_no)

    # Ensure reel_no is not empty
    reel_no = reel_no or "a"
    return f"{reel_no}{last_id % 1000 + 1}"


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

    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO products (reel_no, size, bf, gsm, product_type) 
        VALUES (?, ?, ?, ?, ?)
    """,
        (reel_no, size, bf, gsm, product_type_value),
    )
    product_id = cursor.lastrowid

    # Generate barcode
    barcode_str = f"{product_id:012d}"
    ean = EAN13(barcode_str, writer=ImageWriter())  # Correct way to create the barcode
    full_barcode_str = ean.get_fullcode()
    buffer = BytesIO()
    ean.write(buffer)

    # Save barcode image to list
    barcode_image = Image.open(buffer)
    barcode_images.append(barcode_image)

    # Save the full barcode number (including check digit) in the database
    cursor.execute(
        """
        UPDATE products SET barcode = ? WHERE id = ?
    """,
        (full_barcode_str, product_id),
    )
    conn.commit()
    conn.close()

    # Display product features
    features_text = (
        f"Reel No.: {reel_no}\nSize: {size}\nGSM: {gsm}\nType: {product_type_value}"
    )
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

    canvas = tk.Canvas(
        preview_window, width=595, height=842
    )  # A4 size in points (1/72 of an inch)
    canvas.pack()

    x_offset = 50  # Initial x offset for the barcode images
    y_offset = 50  # Initial y offset for the barcode images
    photo_images = []  # List to keep references to PhotoImage objects

    for i, (barcode_image, features_text) in enumerate(
        zip(barcode_images, features_list)
    ):
        # Draw the barcode image on the canvas
        barcode_image_resized = barcode_image.resize(
            (200, 100)
        )  # Resize for better fit
        barcode_photo = ImageTk.PhotoImage(barcode_image_resized)
        canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=barcode_photo)
        photo_images.append(barcode_photo)  # Store the reference

        # Draw the text below the barcode image
        text_x = x_offset
        text_y = y_offset + 110  # Position below the barcode image
        for line in features_text.split("\n"):
            canvas.create_text(
                text_x, text_y, anchor=tk.NW, text=line, font=("Helvetica", 12)
            )
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
        barcode_image_pil.save("barcode.png", "PNG")

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
            text_y = (
                img_y + img_height + 20
            )  # 20 tenths of a millimeter below the image
            hdc.TextOut(text_x, text_y, features_text)

            # End the page and document
            hdc.EndPage()
            hdc.EndDoc()

        finally:
            # Close the printer handle
            win32print.ClosePrinter(hprinter)


# Function to handle barcode scanning
def on_barcode_entry_change(*args):
    barcode_value = barcode_entry.get()
    if len(barcode_value) == 13:
        scan_barcode()

def scan_barcode():
    barcode_value = barcode_entry.get()
    if not barcode_value or len(barcode_value) != 13:
        return  # Exit if not a valid 13-digit barcode

    print(f"Scanning barcode: {barcode_value}")  # Debug statement

    # Check if the product exists in the database
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE barcode=?", (barcode_value,))
    product = cursor.fetchone()

    if product:
        print(f"Product found: {product}")  # Debug statement

        # Add product to the Treeview for display
        treeview_products.insert(
            "",
            tk.END,
            values=(product[0], product[1], product[2], product[3], product[4], product[5])
        )

    else:
        print("Product not found")  # Debug statement
        messagebox.showerror("Error", "Product not found in database!")

    # Clear barcode entry field
    barcode_entry.delete(0, tk.END)
    run_new_script()

def delete_selected_row_scanlist():
    selected_item_scan = treeview_products.selection()
    if not selected_item_scan:
        messagebox.showerror("Error", "Please select a row to delete!")
        return

    # Delete the selected row(s) from the Treeview
    for item in selected_item_scan:
        treeview_products.delete(item)

# Function to print scanned list
def print_scanned_list():
    # Get all items from treeview_products
    items = treeview_products.get_children()
    if not items:
        messagebox.showinfo("Information", "No items to print.")
        return

    # Get the selected customer name
    customer_name = selected_customer.get()
    if not customer_name:
        messagebox.showerror("Error", "Please select a customer!")
        return

    # Create an image for the printout
    canvas_width = 595  # Width in points for A4
    canvas_height = 842  # Height in points for A4
    img = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", 16)  # Increase font size for better visibility

    # Add customer name at the top
    draw.text(
        (canvas_width / 2 - 150, 30),
        f"Customer: {customer_name}",
        font=font,
        fill="black",
    )

    # Define table parameters
    x_start = 20
    y_start = 100
    row_height = 40  # Adjusted row height for better spacing
    column_widths = [
        70,
        100,
        100,
        70,
        70,
        160,
    ]  # Adjusted column widths to fit page width
    headers = ["ID", "Size", "GSM", "BF", "Print", "Product Type"]

    # Draw table headers
    x = x_start
    y = y_start
    for i, header in enumerate(headers):
        draw.text(
            (x + column_widths[i] / 2 - 10, y + row_height / 4 - 10),
            header,
            font=font,
            fill="black",
        )
        x += column_widths[i]

    # Draw horizontal line below headers
    y += row_height
    draw.line([(x_start, y), (x_start + sum(column_widths), y)], fill="black")

    # Draw vertical lines for table columns
    x = x_start
    for i in range(len(headers) + 1):
        draw.line([(x, y_start), (x, y + len(items) * row_height)], fill="black")
        x += column_widths[i] if i < len(headers) else 0

    # Draw horizontal lines for table rows
    draw.line(
        [(x_start, y_start - row_height), (x_start + sum(column_widths), y_start - row_height)],
        fill="black",
    )
    draw.line(
        [(x_start, y + len(items) * row_height), (x_start + sum(column_widths), y + len(items) * row_height)],
        fill="black",
    )

    # Draw table content
    y = y_start + row_height
    for item in items:
        # Retrieve the item values from Treeview
        fields = treeview_products.item(item, 'values')
        x = x_start
        for i, field in enumerate(fields):
            draw.text(
                (x + column_widths[i] / 2 - 10, y + row_height / 2 - 10),
                field,
                font=font,
                fill="black",
            )
            x += column_widths[i]
        y += row_height

    # Save the image as a temporary file
    temp_file_path = "scanned_list_preview.png"
    img.save(temp_file_path)

    # Print the image
    print("Printing scanned list...")

    # Open the printer
    printer_name = win32print.GetDefaultPrinter()
    hprinter = win32print.OpenPrinter(printer_name)

    try:
        # Start a print job
        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(printer_name)
        hdc.StartDoc("Scanned List Print")
        hdc.StartPage()

        # Set up the print area and dimensions for A4 paper
        a4_width = 2100  # A4 width in tenths of a millimeter (210 mm)
        a4_height = 2970  # A4 height in tenths of a millimeter (297 mm)
        margins = 100  # Margins in tenths of a millimeter (10 mm)

        # Open the image and prepare for printing
        img_pil = Image.open(temp_file_path)
        img_width, img_height = img_pil.size
        scale_x = a4_width / img_width
        scale_y = a4_height / img_height
        scale = min(scale_x, scale_y)

        img_width_scaled = int(img_width * scale)
        img_height_scaled = int(img_height * scale)

        img_x = (a4_width - img_width_scaled) // 2
        img_y = (a4_height - img_height_scaled) // 2
        img_rect = (img_x, img_y, img_x + img_width_scaled, img_y + img_height_scaled)
        bmp = ImageWin.Dib(img_pil.resize((img_width_scaled, img_height_scaled)))
        bmp.draw(hdc.GetHandleOutput(), img_rect)

        # End the page and document
        hdc.EndPage()
        hdc.EndDoc()

    finally:
        # Close the printer handle
        win32print.ClosePrinter(hprinter)

    delete_rows_from_products_table()

    # Optionally, clear the Treeview after printing
    for item in items:
        treeview_products.delete(item)


def delete_csv_row(row_index):
    temp_file = "temp_products_export.csv"
    product_id = None

    try:
        with open("products_export.csv", "r") as csvfile, open(temp_file, "w", newline="") as temp_csvfile:
            reader = csv.reader(csvfile)
            writer = csv.writer(temp_csvfile)

            for i, row in enumerate(reader):
                if i == row_index:
                    product_id = row[0]  # Assuming the first column is the product ID
                    print(f"Found product ID {product_id} for row index {row_index}.")
                else:
                    writer.writerow(row)

        if product_id:
            # Replace the original CSV with the updated temp file
            os.replace(temp_file, "products_export.csv")
            print(f"Replaced the original CSV with the temp file.")

            # Delete from database
            conn = sqlite3.connect("products.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
            conn.commit()
            conn.close()
            print(f"Deleted product with ID {product_id} from the database.")
        else:
            print("No product ID found for deletion in the specified row.")

    except Exception as e:
        print(f"An error occurred: {e}")


def open_csv_window():
    csv_window = tk.Toplevel(root)
    csv_window.title("CSV Data")

    frame = ttk.Frame(csv_window)
    frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

    # Create the Treeview widget
    tree = ttk.Treeview(
        frame,
        columns=("ID", "Reel No.", "Size", "BF", "GSM", "Product Type", "Barcode"),
        show="headings",
    )
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
        try:
            selected_item = tree.selection()[0]
            row_index = tree.index(selected_item)
            print(f"Selected row index: {row_index}")
            delete_csv_row(row_index )  # +1 assuming CSV rows start from 1
            tree.delete(selected_item)
        except Exception as e:
            print(f"An error occurred while deleting row: {e}")

    # Add a delete button
    delete_button = ttk.Button(
        csv_window, text="Delete Selected Row", command=delete_selected_row
    )
    delete_button.pack(pady=10)

    # Populate the Treeview with data from the CSV file
    try:
        with open("products_export.csv", "r") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                tree.insert("", tk.END, values=row)
    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")


def toggle_fullscreen(event=None):
    root.state("zoomed")

def print_preview_scanned_list():
    # Get the selected customer name
    customer_name = selected_customer.get()
    if not customer_name:
        messagebox.showerror("Error", "Please select a customer!")
        return

    # Get all items from treeview_products
    items = treeview_products.get_children()
    if not items:
        messagebox.showinfo("Information", "No items to preview.")
        return

    # Create a new window for the print preview
    preview_window = tk.Toplevel(root)
    preview_window.title("Print Preview")

    # Create a Canvas widget
    canvas_width = 595  # Width in points for A4
    canvas_height = 842  # Height in points for A4
    canvas = tk.Canvas(preview_window, width=canvas_width, height=canvas_height)
    canvas.pack()

    # Add customer name at the top
    canvas.create_text(
        canvas_width / 2,
        30,
        text=f"Customer: {customer_name}",
        font=("Helvetica", 16, "bold"),
        anchor=tk.N,
    )

    # Define table parameters
    x_start = 30
    y_start = 80
    row_height = 50  # Increased row height for spacing
    column_widths = [80, 100, 80, 80, 80, 80]  # Decreased column widths
    headers = ["ID", "Reel No.", "Size", "BF", "GSM", "Type"]

    # Draw table headers
    x = x_start
    y = y_start
    canvas.create_line(
        x_start, y_start, x_start + sum(column_widths), y_start, fill="black"
    )
    for i, header in enumerate(headers):
        canvas.create_text(
            x + column_widths[i] / 2,
            y + row_height / 4,
            text=header,
            font=("Helvetica", 12, "bold"),
            anchor=tk.N,
        )
        x += column_widths[i]

    # Draw horizontal line below headers
    y += row_height
    canvas.create_line(x_start, y, x_start + sum(column_widths), y, fill="black")

    # Draw vertical lines for table columns
    x = x_start
    for i in range(len(headers) + 1):
        canvas.create_line(x, y_start, x, y + len(items) * row_height, fill="black")
        x += column_widths[i] if i < len(headers) else 0

    # Draw horizontal lines for table rows
    canvas.create_line(
        x_start,
        y_start - row_height,
        x_start + sum(column_widths),
        y_start - row_height,
        fill="black",
    )
    canvas.create_line(
        x_start,
        y + len(items) * row_height,
        x_start + sum(column_widths),
        y + len(items) * row_height,
        fill="black",
    )

    # Draw table content
    y = y_start + row_height
    for item in items:
        fields = treeview_products.item(item, "values")
        # Ensure fields align with the updated headers
        if len(fields) >= 4:
            fields = [
                fields[0],
                fields[2],
                fields[4],
                "",
                "",
                fields[5],
            ]  # Added empty fields for BF and Rate
        x = x_start
        for i, field in enumerate(fields):
            canvas.create_text(
                x + column_widths[i] / 2,
                y + row_height / 2,
                text=field,
                font=("Helvetica", 12),
                anchor=tk.N,
            )
            x += column_widths[i]
        y += row_height

    # Show the preview window
    preview_window.mainloop()


def print_preview(preview_window):

    print("Printing the preview...")
    preview_window.destroy()


def fetch_customer_names():
    conn = sqlite3.connect("order_management.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM customers")
    customer_names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return customer_names

# Fetch customer names
customer_names = fetch_customer_names()

# Function to update the dropdown list based on the current entry
def update_customer_list(event):
    typed = selected_customer.get()
    if typed == "":
        customer_dropdown["values"] = fetch_customer_names()
    else:
        filtered_names = [
            name for name in fetch_customer_names() if typed.lower() in name.lower()
        ]
        customer_dropdown["values"] = filtered_names


def update_dispatched_qty():
    # Get selected customer name
    customer_name = selected_customer.get()
    if not customer_name:
        messagebox.showerror("Error", "Please select a customer!")
        return

    conn_orders = sqlite3.connect("order_management.db")
    cursor_orders = conn_orders.cursor()

    # Check if customer exists in the database
    cursor_orders.execute("SELECT id FROM customers WHERE name=?", (customer_name,))
    customer = cursor_orders.fetchone()
    if not customer:
        messagebox.showerror("Error", "Customer not found!")
        conn_orders.close()
        return

    customer_id = customer[0]

    # Check if the customer has any orders
    cursor_orders.execute("SELECT * FROM order_details WHERE customerID=?", (customer_id,))
    orders = cursor_orders.fetchall()
    if not orders:
        messagebox.showinfo("No Order Found", f"No orders found for customer {customer_name}.")
        conn_orders.close()
        return

    # Get all items from the Treeview
    items = treeview_products.get_children()
    if not items:
        messagebox.showinfo("Information", "No items in the list to process.")
        conn_orders.close()
        return

    conn_products = sqlite3.connect("products.db")
    cursor_products = conn_products.cursor()

    wrong_reel_scanned = False

    for item in items:
        product_data = treeview_products.item(item, "values")
        product_type, size, gsm = product_data[5], product_data[2], product_data[4]

        # Check if there's a matching order for the item
        cursor_orders.execute(
            """
            SELECT qty, dispatched_qty 
            FROM order_details 
            WHERE customerID=? AND size=? AND gsm=? AND type=? 
            """,
            (customer_id, size, gsm, product_type)
        )
        order = cursor_orders.fetchone()

        if order:
            new_dispatched_qty = order[1] + 1  # Add 1 to the dispatched quantity
            cursor_orders.execute(
                """
                UPDATE order_details
                SET dispatched_qty=?
                WHERE customerID=? AND size=? AND gsm=? AND type=?
                """,
                (new_dispatched_qty, customer_id, size, gsm, product_type)
            )
        else:
            wrong_reel_scanned = True

    if wrong_reel_scanned:
        messagebox.showerror("Error", "Wrong reel scanned. Some items do not match with the orders.")
    else:
        messagebox.showinfo("Success", "Dispatched quantities updated successfully.")

    conn_orders.commit()
    conn_orders.close()
    conn_products.close()


def delete_rows_from_products_table():
    # Connect to the products database
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()

    # Delete each product in the Treeview from the products table
    for item in treeview_products.get_children():
        product = treeview_products.item(item, 'values')
        product_id = product[0]  # Assuming the ID is the first column in the Treeview
        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))

    conn.commit()
    conn.close()

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
    "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
input_frame = ttk.Frame(scrollable_frame)
input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
customer_names = fetch_customer_names()
selected_customer = tk.StringVar()

# Create the dropdown beside the scan barcode button
ttk.Label(scrollable_frame, text="Select Customer:").grid(
    row=5, column=3, padx=10, pady=10
)
customer_dropdown = ttk.Combobox(scrollable_frame, textvariable=selected_customer)
customer_dropdown["values"] = fetch_customer_names()
customer_dropdown.grid(row=5, column=4, padx=10, pady=10)

# Preview scanned list button
print_preview_scanned_list_button = ttk.Button(
    scrollable_frame,
    text="Preview Scanned List",
    command=print_preview_scanned_list,
)
print_preview_scanned_list_button.grid(row=9, column=0, columnspan=3, padx=10, pady=10)

# Add a refresh button beside the dropdown
refresh_button = ttk.Button(
    scrollable_frame, text="Refresh", command=refresh_customer_dropdown
)
refresh_button.grid(row=5, column=5, padx=10, pady=10)
# Hypothetical function to get customers
if not customer_names:
    customer_names = ["No customers available"]
customer_dropdown["values"] = customer_names
customer_dropdown.current(0)

# Fetch customer names
customer_names = fetch_customer_names()

# Create the dropdown beside the scan barcode button
ttk.Label(scrollable_frame, text="Select Customer:").grid(
    row=5, column=3, padx=10, pady=10
)
customer_dropdown = ttk.Combobox(scrollable_frame, textvariable=selected_customer)
customer_dropdown["values"] = customer_names
customer_dropdown.grid(row=5, column=4, padx=10, pady=10)
customer_dropdown.bind("<KeyRelease>", update_customer_list)

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
dropdown_product_type["values"] = ("semi", "rg")
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

preview_button = ttk.Button(
    scrollable_frame, text="Preview Label", command=preview_print
)
preview_button.grid(row=4, column=1, padx=10, pady=10)

open_order_management_button = tk.Button(
    scrollable_frame, text="Open Order Management", command=open_order_management
)
open_order_management_button.grid(row=0, column=3, padx=10, pady=10)

ttk.Label(scrollable_frame, text="Enter Barcode:").grid(
    row=5, column=0, padx=10, pady=10
)

# Barcode entry linked to StringVar for automatic scanning
barcode_var = tk.StringVar()
barcode_var.trace("w", on_barcode_entry_change)

barcode_entry = ttk.Entry(scrollable_frame, textvariable=barcode_var)
barcode_entry.grid(row=5, column=1, padx=10, pady=10)

columns = ("ID", "Reel No.", "Size", "BF", "GSM", "Type")
treeview_products = ttk.Treeview(scrollable_frame, columns=columns, show="headings",height=6)
treeview_products.grid(row=6, column=0, columnspan=3, padx=10, pady=10)

# Define the column headings
for col in columns:
    treeview_products.heading(col, text=col)
    treeview_products.column(col, width=80)

delete_button_scan = ttk.Button(scrollable_frame, text="Delete from list", command=delete_selected_row_scanlist)
delete_button_scan.grid(row=7, column=1, columnspan=3, padx=10, pady=10)
# Print scanned list button
print_list_button = ttk.Button(
    scrollable_frame, text="Print Scanned List", command=print_scanned_list
)
print_list_button.grid(row=7, column=0, columnspan=3, padx=10, pady=10)

update_button = tk.Button(scrollable_frame, text="Update Dispatched Quantity", command=update_dispatched_qty)
update_button.grid(row=9, column=2, columnspan=3, padx=10, pady=10)

# Open CSV data window button
csv_button = ttk.Button(scrollable_frame, text="Open CSV Data", command=open_csv_window)
csv_button.grid(row=9, column=1, columnspan=3, padx=10, pady=10)
root.bind("<F11>", toggle_fullscreen)
root.mainloop()
