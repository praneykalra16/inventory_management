import sqlite3
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime

# Create and connect to the SQLite database
conn = sqlite3.connect('order_management.db')
c = conn.cursor()

products_conn = sqlite3.connect('products.db')
pc = products_conn.cursor()

# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS customers (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             name TEXT NOT NULL)''')

c.execute('''CREATE TABLE IF NOT EXISTS order_details (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             bf TEXT NOT NULL,
             size TEXT NOT NULL,
             gsm INTEGER NOT NULL,
             type TEXT NOT NULL CHECK(type IN ('s', 'r')),
             qty INTEGER NOT NULL,
             currDate TEXT NOT NULL,
             customerID INTEGER NOT NULL,
             FOREIGN KEY(customerID) REFERENCES customers(id))''')

conn.commit()

def add_customer(main_window):
    def add_order():
        bf = bf_entry.get()
        size = size_entry.get()
        gsm = gsm_entry.get()
        type_ = type_var.get()
        qty = qty_entry.get()

        if bf and size and gsm and type_ and qty:
            order_list.insert(END, (bf, size, gsm, type_, qty))
            bf_entry.delete(0, END)
            size_entry.delete(0, END)
            gsm_entry.delete(0, END)
            qty_entry.delete(0, END)
        else:
            messagebox.showerror("Error", "All fields are required!")

    def save_customer():
        name = name_entry.get()
        if name and order_list.size() > 0:
            c.execute("INSERT INTO customers (name) VALUES (?)", (name,))
            customer_id = c.lastrowid
            currDate = datetime.now().strftime("%Y-%m-%d")
            for order in order_list.get(0, END):
                bf, size, gsm, type_, qty = order
                c.execute("INSERT INTO order_details (bf, size, gsm, type, qty, currDate, customerID) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (bf, size, gsm, type_, qty, currDate, customer_id))
            conn.commit()
            messagebox.showinfo("Success", "Customer and order details added successfully!")
            add_customer_window.destroy()
        else:
            messagebox.showerror("Error", "Customer name and at least one order are required!")

    def preview_orders():
        preview_window = Toplevel(add_customer_window)
        preview_window.title("Preview Orders")
        for order in order_list.get(0, END):
            Label(preview_window, text=f"BF: {order[0]}, Size: {order[1]}, GSM: {order[2]}, Type: {order[3]}, Qty: {order[4]}").pack()

    add_customer_window = Toplevel(main_window)
    add_customer_window.title("Add New Customer")

    Label(add_customer_window, text="Customer Name").grid(row=0, column=0)
    name_entry = Entry(add_customer_window)
    name_entry.grid(row=0, column=1)

    Label(add_customer_window, text="BF").grid(row=1, column=0)
    bf_entry = Entry(add_customer_window)
    bf_entry.grid(row=1, column=1)

    Label(add_customer_window, text="Size").grid(row=2, column=0)
    size_entry = Entry(add_customer_window)
    size_entry.grid(row=2, column=1)

    Label(add_customer_window, text="GSM").grid(row=3, column=0)
    gsm_entry = Entry(add_customer_window)
    gsm_entry.grid(row=3, column=1)

    Label(add_customer_window, text="Type (s/r)").grid(row=4, column=0)
    type_var = StringVar(add_customer_window)
    type_var.set("s")
    OptionMenu(add_customer_window, type_var, "s", "r").grid(row=4, column=1)

    Label(add_customer_window, text="Quantity").grid(row=5, column=0)
    qty_entry = Entry(add_customer_window)
    qty_entry.grid(row=5, column=1)

    Button(add_customer_window, text="Add Order", command=add_order).grid(row=6, column=0, columnspan=2)

    order_list = Listbox(add_customer_window, width=50)
    order_list.grid(row=7, column=0, columnspan=2)

    Button(add_customer_window, text="Preview Orders", command=preview_orders).grid(row=8, column=0, columnspan=2)
    Button(add_customer_window, text="Save", command=save_customer).grid(row=9, column=0, columnspan=2)


def view_all_orders(main_window):
    view_all_orders_window = Toplevel(main_window)
    view_all_orders_window.title("View All Orders")

    frame = ttk.Frame(view_all_orders_window)
    frame.pack(padx=20, pady=20, fill=BOTH, expand=True)

    # Create the Treeview widget
    tree = ttk.Treeview(frame,
                        columns=("Order ID", "Customer Name", "BF", "Size", "GSM", "Type", "Qty", "Date", "Status"),
                        show="headings")
    tree.pack(side=LEFT, fill=BOTH, expand=True)

    # Define the column headings
    tree.heading("Order ID", text="Order ID")
    tree.heading("Customer Name", text="Customer Name")
    tree.heading("BF", text="BF")
    tree.heading("Size", text="Size")
    tree.heading("GSM", text="GSM")
    tree.heading("Type", text="Type")
    tree.heading("Qty", text="Qty")
    tree.heading("Date", text="Date")
    tree.heading("Status", text="Status")

    # Define column widths
    tree.column("Order ID", width=70)
    tree.column("Customer Name", width=150)
    tree.column("BF", width=50)
    tree.column("Size", width=100)
    tree.column("GSM", width=50)
    tree.column("Type", width=70)
    tree.column("Qty", width=50)
    tree.column("Date", width=100)
    tree.column("Status", width=100)

    # Add a vertical scrollbar
    scrollbar = ttk.Scrollbar(frame, orient=VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=RIGHT, fill=Y)

    # Fetch and display the orders
    c.execute('''
        SELECT order_details.id, customers.name, order_details.bf, 
               order_details.size, order_details.gsm, order_details.type, 
               order_details.qty, order_details.currDate
        FROM order_details 
        JOIN customers ON order_details.customerID = customers.id
    ''')
    orders = c.fetchall()

    for order in orders:
        order_id, customer_name, bf, size, gsm, type_, qty, currDate = order

        # Check if the product is in stock
        pc.execute("SELECT COUNT(*) FROM products WHERE bf=? AND size=? AND gsm=?", (bf, size, gsm))
        in_stock = pc.fetchone()[0]
        status = "In Stock" if in_stock > 0 else "To Be Made"

        # Insert the order into the Treeview
        tree.insert("", "end", values=(order_id, customer_name, bf, size, gsm, type_, qty, currDate, status))

def fetch_customer_names():
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM customers')
    customer_names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return customer_names

# Function to update the dropdown list based on the current entry
def update_customer_list(event, customer_names, customer_dropdown):
    typed = customer_dropdown.get()
    if typed == '':
        customer_dropdown['values'] = customer_names
    else:
        filtered_names = [name for name in customer_names if typed.lower() in name.lower()]
        customer_dropdown['values'] = filtered_names

# Function to view customer orders
def view_customer(main_window):
    def fetch_customer_orders():
        name = selected_customer.get()
        if name:
            c.execute("SELECT id FROM customers WHERE name=?", (name,))
            customer = c.fetchone()
            if customer:
                customer_id = customer[0]
                c.execute("SELECT * FROM order_details WHERE customerID=?", (customer_id,))
                orders = c.fetchall()
                order_text.delete("1.0", END)
                if orders:
                    for order in orders:
                        order_text.insert(END, f"Order ID: {order[0]}, BF: {order[1]}, Size: {order[2]}, GSM: {order[3]}, Type: {order[4]}, Qty: {order[5]}, Date: {order[6]}\n")
                else:
                    order_text.insert(END, "No orders found for this customer.\n")
            else:
                messagebox.showerror("Error", "Customer not found!")
        else:
            messagebox.showerror("Error", "Customer name is required!")

    # Fetch customer names
    customer_names = fetch_customer_names()

    # Create the view_customer window
    view_customer_window = Toplevel(main_window)
    view_customer_window.title("View Customer Orders")

    Label(view_customer_window, text="Customer Name").grid(row=0, column=0)

    # Create a StringVar to store the selected customer name
    selected_customer = StringVar()

    # Create a Combobox for customer name entry
    customer_dropdown = ttk.Combobox(view_customer_window, textvariable=selected_customer)
    customer_dropdown['values'] = customer_names
    customer_dropdown.grid(row=0, column=1)

    # Bind the key release event to update the dropdown list as the user types
    customer_dropdown.bind('<KeyRelease>', lambda event: update_customer_list(event, customer_names, customer_dropdown))

    # Bind the selection event to ensure the selected name is properly captured
    customer_dropdown.bind("<<ComboboxSelected>>", lambda event: selected_customer.set(customer_dropdown.get()))

    # Set focus on the combobox to start typing immediately
    customer_dropdown.focus()

    Button(view_customer_window, text="Fetch Orders", command=fetch_customer_orders).grid(row=1, column=0, columnspan=2)

    order_text = Text(view_customer_window, width=50, height=10)
    order_text.grid(row=2, column=0, columnspan=2)

# Close the database connection when the GUI is closed
def on_closing():
    conn.close()  # Close the database connection
    products_conn.close()
    main_window.destroy()  # Close the main window


# Entry point to create the main window
def main():
    global main_window  # Declare main_window as global to use it in on_closing
    main_window = Tk()
    main_window.title("Order Management System")

    Button(main_window, text="Add New Customer", command=lambda: add_customer(main_window)).grid(row=0, column=0, padx=20, pady=20)
    Button(main_window, text="View Customer Orders", command=lambda: view_customer(main_window)).grid(row=0, column=1, padx=20, pady=20)

    Button(main_window, text="View All Orders", command=lambda: view_all_orders(main_window)).grid(row=0, column=2,
                                                                                                   padx=20, pady=20)

    main_window.protocol("WM_DELETE_WINDOW", on_closing)
    main_window.mainloop()
