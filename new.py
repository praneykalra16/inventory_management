import sqlite3
import csv

# Connect to SQLite database
conn = sqlite3.connect('products.db')
cursor = conn.cursor()

# Execute a query to fetch all rows from 'products' table
cursor.execute('SELECT * FROM products')
rows = cursor.fetchall()

# Define CSV file path
csv_file = 'products_export.csv'

# Write fetched data to CSV file
with open(csv_file, 'w', newline='') as file:
    csv_writer = csv.writer(file)
    # Write header row
    csv_writer.writerow(['S.No.', 'Reelno.', 'Size', 'BF', 'GSM','Type','Barcode No.'])
    # Write data rows
    csv_writer.writerows(rows)

print(f'Data exported to {csv_file}')

# Close connection
conn.close()
