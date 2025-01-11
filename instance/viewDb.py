import sqlite3

# Connect to the database
conn = sqlite3.connect('ecommerce.db')

# Create a cursor object to interact with the database
cursor = conn.cursor()

# Execute a query
cursor.execute("SELECT * FROM User")

# Fetch all results
rows = cursor.fetchall()

# Print results
for row in rows:
    print(row)

# Close the connection
conn.close()