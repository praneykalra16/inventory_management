import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# Initialize customer database
def init_customer_db():
    conn = sqlite3.connect('customers.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

# Function to add a new customer
def add_new_customer():
    def save_customer():
        customer_name = entry_customer_name.get()
        if not customer_name:
            messagebox.showerror("Error", "Customer name is required!")
            return

        conn = sqlite3.connect('customers.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO customers (name) VALUES (?)', (customer_name,))
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS "{customer_name}" (
                    id INTEGER PRIMARY KEY,
                    size TEXT,
                    type TEXT,
                    gsm TEXT,
                    qty INTEGER
                )
            ''')
            conn.commit()
            messagebox.showinfo("Success", f"Customer '{customer_name}' added successfully!")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", f"Customer '{customer_name}' already exists!")
        finally:
            conn.close()
            new_customer_window.destroy()

    new_customer_window = tk.Toplevel()
    new_customer_window.title("Add New Customer")

    ttk.Label(new_customer_window, text="Customer Name:").grid(row=0, column=0, padx=5, pady=5)
    entry_customer_name = ttk.Entry(new_customer_window)
    entry_customer_name.grid(row=0, column=1, padx=5, pady=5)

    btn_save_customer = ttk.Button(new_customer_window, text="Save", command=save_customer)
    btn_save_customer.grid(row=1, column=0, columnspan=2, padx=5, pady=10)

# Function to search for an existing customer
def search_customer():
    def find_customer():
        customer_name = entry_search.get()
        if not customer_name:
            messagebox.showerror("Error", "Please enter a customer name!")
            return

        conn = sqlite3.connect('customers.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM customers WHERE name=?', (customer_name,))
        customer = cursor.fetchone()

        if customer:
            messagebox.showinfo("Found", f"Customer '{customer_name}' exists in the database.")
        else:
            messagebox.showerror("Not Found", f"Customer '{customer_name}' does not exist in the database.")
        conn.close()
        search_window.destroy()

    search_window = tk.Toplevel()
    search_window.title("Search Customer")

    ttk.Label(search_window, text="Customer Name:").grid(row=0, column=0, padx=5, pady=5)
    entry_search = ttk.Entry(search_window)
    entry_search.grid(row=0, column=1, padx=5, pady=5)

    btn_find_customer = ttk.Button(search_window, text="Search", command=find_customer)
    btn_find_customer.grid(row=1, column=0, columnspan=2, padx=5, pady=10)

# Function to open customer log window
def open_customer_log():
    init_customer_db()

    customer_log_window = tk.Toplevel()
    customer_log_window.title("Customer Log")

    btn_new_customer = ttk.Button(customer_log_window, text="New Customer", command=add_new_customer)
    btn_new_customer.grid(row=0, column=0, padx=10, pady=10)

    btn_old_customer = ttk.Button(customer_log_window, text="Old Customer", command=search_customer)
    btn_old_customer.grid(row=0, column=1, padx=10, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    open_customer_log()
    root.mainloop()
