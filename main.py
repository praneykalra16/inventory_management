import tkinter as tk
from tkinter import messagebox
import sqlite3
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageTk
from io import BytesIO
import os

# Global variable for barcode image
barcode_image = None


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
            gsm TEXT
        )
    ''')
    conn.commit()
    conn.close()


# Initialize the database
init_db()


# Function to save product and generate barcode
def save_product():
    global barcode_image  # Declare barcode_image as global

    reel_no = entry_reel_no.get()
    size = entry_size.get()
    bf = entry_bf.get()
    gsm = entry_gsm.get()

    if not all([reel_no, size, bf, gsm]):
        messagebox.showerror("Error", "All fields are required!")
        return

    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (reel_no, size, bf, gsm) 
        VALUES (?, ?, ?, ?)
    ''', (reel_no, size, bf, gsm))
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Generate barcode
    barcode_str = f'{product_id:012d}'
    ean = barcode.get('ean13', barcode_str, writer=ImageWriter())
    buffer = BytesIO()
    ean.write(buffer)

    # Save barcode image to global variable
    barcode_image = Image.open(buffer)

    # Display barcode image in Tkinter Label
    barcode_photo = ImageTk.PhotoImage(barcode_image)
    barcode_label.config(image=barcode_photo)
    barcode_label.image = barcode_photo

    # Display product features
    features_text = f"Reel No.: {reel_no}\nSize: {size}\nBF: {bf}\nGSM: {gsm}"
    features_label.config(text=features_text)

    # Show success message
    messagebox.showinfo("Success", "Product saved and barcode generated!")


# Function to print label
def print_label():
    global barcode_image  # Access the global barcode_image

    if barcode_image is None:
        messagebox.showerror("Error", "Generate a barcode first!")
        return

    # Replace this with the actual command or library function for your label printer
    # For demonstration, we will print to console
    features_text = features_label.cget("text")
    print(f"Printing label...\n{features_text}")

    # Optionally, you can also print the barcode image
    # This requires converting ImageTk format back to PIL Image
    barcode_image_pil = barcode_image.copy()
    barcode_image_pil.save('barcode.png', 'PNG')

    # Simulate printing barcode image (you need to adjust this part based on your label printer)
    print("Printing barcode image...")
    os.system('lp barcode.png')  # Example for Unix-like systems using CUPS


# Function to handle barcode scanning
def scan_barcode():
    barcode_value = barcode_entry.get()
    if not barcode_value:
        messagebox.showerror("Error", "Please enter a barcode value!")
        return

    # Check if the product exists in the database
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id=?', (barcode_value,))
    product = cursor.fetchone()

    if product:
        # Add product to the list for printing
        listbox_products.insert(tk.END,
                                f"ID: {product[0]}, Reel No.: {product[1]}, Size: {product[2]}, BF: {product[3]}, GSM: {product[4]}")

        # Remove product from the database
        cursor.execute('DELETE FROM products WHERE id=?', (barcode_value,))
        conn.commit()
        conn.close()

        # Show success message
        messagebox.showinfo("Success", "Product scanned and removed from database!")
    else:
        messagebox.showerror("Error", "Product not found in database!")

    # Clear barcode entry field
    barcode_entry.delete(0, tk.END)


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


# Setup GUI
root = tk.Tk()
root.title("Product Management")

# Labels and Entry fields
tk.Label(root, text="Reel No.:").grid(row=0, column=0, padx=10, pady=5)
entry_reel_no = tk.Entry(root)
entry_reel_no.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Size:").grid(row=1, column=0, padx=10, pady=5)
entry_size = tk.Entry(root)
entry_size.grid(row=1, column=1, padx=10, pady=5)

tk.Label(root, text="BF:").grid(row=2, column=0, padx=10, pady=5)
entry_bf = tk.Entry(root)
entry_bf.grid(row=2, column=1, padx=10, pady=5)

tk.Label(root, text="GSM:").grid(row=3, column=0, padx=10, pady=5)
entry_gsm = tk.Entry(root)
entry_gsm.grid(row=3, column=1, padx=10, pady=5)

# Buttons for Save, Generate Barcode, and Print Label
tk.Button(root, text="Save and Generate Barcode", command=save_product).grid(row=4, columnspan=2, pady=10)
tk.Button(root, text="Print Label", command=print_label).grid(row=5, columnspan=2, pady=10)

# Barcode scanning section
tk.Label(root, text="Scan Barcode:").grid(row=6, column=0, padx=10, pady=5)
barcode_entry = tk.Entry(root)
barcode_entry.grid(row=6, column=1, padx=10, pady=5)
tk.Button(root, text="Scan", command=scan_barcode).grid(row=6, column=2, padx=10, pady=5)

# Listbox to display scanned products
tk.Label(root, text="Scanned Products:").grid(row=7, column=0, padx=10, pady=5)
listbox_products = tk.Listbox(root, width=50, height=10)
listbox_products.grid(row=8, column=0, columnspan=3, padx=10, pady=5)

# Button to print scanned list
tk.Button(root, text="Print Scanned List", command=print_scanned_list).grid(row=9, columnspan=3, pady=10)

# Label to display barcode image
barcode_label = tk.Label(root)
barcode_label.grid(row=10, columnspan=3, pady=10)

# Label to display product features
features_label = tk.Label(root, justify=tk.LEFT)
features_label.grid(row=11, columnspan=3, pady=10)

root.mainloop()
