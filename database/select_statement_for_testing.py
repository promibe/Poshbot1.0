import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect("users.db")
cursor = conn.cursor()


# selecting all the courses in course table
# Fetch all courses
cursor.execute(''' SELECT * FROM Users ''')
courses = cursor.fetchall()  # Retrieve all rows

# Print courses
for course in courses:
    print(course)

# Commit changes and close connection
conn.commit()
conn.close()

print("successfully!")

