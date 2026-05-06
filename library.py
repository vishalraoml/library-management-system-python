import sqlite3
from datetime import datetime
ALLOWED_DAYS = 7
FINE_PER_DAY = 5

# Connect to database
conn = sqlite3.connect("library.db")
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

# Create table with UNIQUE constraint (prevents duplicates)
cursor.execute("""
CREATE TABLE IF NOT EXISTS books(
    id INTEGER PRIMARY KEY,
    title TEXT,
    author TEXT,
    quantity INTEGER,
    UNIQUE(title, author)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS issued_books(
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    book_id INTEGER,
    issue_date TEXT,
    return_date TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(book_id) REFERENCES books(id)
)
""")

while True:
    print("\n--- Library Menu ---")
    print("1. Add Book")
    print("2. View Books")
    print("3. delete book")
    print("4. Update quantity")
    print("5. Issue")
    print("6. Return")
    print("7. exit....")
    print("8. View Issued Books (Detailed)")
    print("9. Add User")
    print("10. Total Users")
    print("11. User Detailed Report")
    print("12. Search Book")
    print("13. Most Issued Books")

    choice = input("Enter choice: ").strip()

    # Add Book
    if choice == '1':
        title = input("Enter book title: ")
        author = input("Enter author name: ")
        quantity = int(input("Enter quantity: "))

        try:
            cursor.execute("""
            INSERT INTO books (title, author, quantity)
            VALUES (?, ?, ?)
            """, (title, author, quantity))

            conn.commit()
            print("Book added successfully")

        except sqlite3.IntegrityError:
            print("Book already exists!")

    # View Books
    elif choice == '2':
        cursor.execute("SELECT * FROM books")
        rows = cursor.fetchall()

        print("\n--- Book List ---")
        for row in rows:
            print(f"ID:{row[0]} | Title:{row[1]} | Author:{row[2]} | Qty:{row[3]}")
    
    #delete book
    elif choice == '3':
        cursor.execute("SELECT * FROM books")
        rows = cursor.fetchall()

        print("\n--- Book List ---")
        for row in rows:
            print(f"ID:{row[0]} | Title:{row[1]} | Author:{row[2]} | Qty:{row[3]}")

        book_id = int(input("Enter Book ID to delete: "))

        confirm = input("Are you sure? (y/n): ")

        if confirm.lower() == 'y':
            cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
            conn.commit()

            if cursor.rowcount > 0:
                print("Book deleted successfully")
            else:
                print("Book not found")
        else:
            print("Deletion cancelled")
            
    #update        
    elif choice == '4':
        cursor.execute("SELECT * FROM books")
        rows = cursor.fetchall()

        if not rows:
            print("No books available")
            continue

        print("\n--- Book List ---")
        for row in rows:
            print(f"ID:{row[0]} | Title:{row[1]} | Author:{row[2]} | Qty:{row[3]}")

        try:
            book_id = int(input("Enter Book ID to update: "))
            new_quantity = int(input("Enter new quantity: "))
        except ValueError:
            print("Invalid input")
            continue

        if new_quantity < 0:
            print("Quantity cannot be negative")
            continue

        cursor.execute(
            "UPDATE books SET quantity = ? WHERE id = ?",
            (new_quantity, book_id)
        )
        conn.commit()

        if cursor.rowcount > 0:
            print("Quantity updated successfully")
        else:
            print("Book not found")
    
    #issue book
    elif choice == '5':
        cursor.execute("SELECT * FROM books")
        rows = cursor.fetchall()

        if not rows:
            print("No books available")
            continue

        print("\n--- Available Books ---")
        for row in rows:
            print(f"ID:{row[0]} | Title:{row[1]} | Author:{row[2]} | Qty:{row[3]}")

        try:
            user_id = int(input("Enter User ID: "))
            book_id = int(input("Enter Book ID: "))
        except ValueError:
            print("Invalid input")
            continue

        #Check user exists
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            print("User does not exist")
            continue

        #Check book exists
        cursor.execute("SELECT quantity FROM books WHERE id = ?", (book_id,))
        result = cursor.fetchone()

        if not result:
            print("Book does not exist")
            continue

        #Check quantity
        if result[0] <= 0:
            print("Book not available")
            continue

        #Issue book
        issue_date = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("""
        INSERT INTO issued_books (user_id, book_id, issue_date)
        VALUES (?, ?, ?)
        """, (user_id, book_id, issue_date))

        cursor.execute("""
        UPDATE books SET quantity = quantity - 1 WHERE id = ?
        """, (book_id,))

        conn.commit()
        print("Book issued successfully")
    
    #return book
    elif choice == '6':
        cursor.execute("SELECT * FROM issued_books WHERE return_date IS NULL")
        rows = cursor.fetchall()

        if not rows:
            print("No books issued")
            continue

        print("\n--- Issued Books ---")
        for row in rows:
            print(f"IssueID:{row[0]} | UserID:{row[1]} | BookID:{row[2]} | Issued:{row[3]}")

        try:
            issue_id = int(input("Enter Issue ID to return: "))
        except ValueError:
            print("Invalid ID")
            continue

        cursor.execute("""
        SELECT book_id, issue_date FROM issued_books 
        WHERE id = ? AND return_date IS NULL
        """, (issue_id,))

        book = cursor.fetchone()

        if book:
            return_date = datetime.now()

            # fine calculation
            issue_date = datetime.strptime(book[1], "%Y-%m-%d")
            days = (return_date - issue_date).days

            if days > ALLOWED_DAYS:
                fine = (days - ALLOWED_DAYS) * FINE_PER_DAY
                print(f"Late return! Fine = ₹{fine}")
            else:
                print("Returned on time. No fine.")

            # convert to string before saving
            return_date_str = return_date.strftime("%Y-%m-%d")

            cursor.execute("""
            UPDATE issued_books
            SET return_date = ?
            WHERE id = ?
            """, (return_date_str, issue_id))

            cursor.execute("""
            UPDATE books
            SET quantity = quantity + 1
            WHERE id = ?
            """, (book[0],))

            conn.commit()
            print("Book returned successfully")
        else:
            print("Invalid or already returned Issue ID")

    #Exit
    elif choice == '7':
        print("Exiting...")
        break
    
    # issued book details
    elif choice == '8':
        cursor.execute("""
        SELECT 
        issued_books.id,
        users.name,
        books.title,
        issued_books.issue_date,
        issued_books.return_date
    FROM issued_books
    JOIN books ON issued_books.book_id = books.id
    JOIN users ON issued_books.user_id = users.id
    """)

        rows = cursor.fetchall()

        print("\n--- Issued Books Details ---")
        for row in rows:
            print(f"IssueID:{row[0]} | User:{row[1]} | Book:{row[2]} | Issued:{row[3]} | Returned:{row[4]}")

    #to add user
    elif choice == '9':
        name = input("Enter user name: ")

        cursor.execute("""
        INSERT INTO users (name)
        VALUES (?)
        """, (name,))

        conn.commit()
        print("User added successfully")
        
    # total users
    elif choice == '10':
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]

        print("\n--- Users List ---")
        for row in rows:
            print(f"ID:{row[0]} | Name:{row[1]}")

        print(f"\nTotal Users: {count}")
        
    elif choice == '11':
        cursor.execute("""
        SELECT 
            users.name,
            COUNT(issued_books.id),
            GROUP_CONCAT(books.title, ', ')
        FROM users
        LEFT JOIN issued_books 
            ON users.id = issued_books.user_id
            AND issued_books.return_date IS NULL
        LEFT JOIN books 
            ON issued_books.book_id = books.id
        GROUP BY users.id
        """)

        rows = cursor.fetchall()

        print("\n--- User Detailed Report ---")
        for row in rows:
            name = row[0]
            count = row[1]
            books = row[2] if row[2] else "None"

            print(f"User: {name} | Total: {count} | Books: {books}")
    
    
    elif choice == '12':
        keyword = input("Enter title or author to search: ").strip()

        if not keyword:
            print("Empty search")
            continue

        cursor.execute("""
        SELECT * FROM books
        WHERE title LIKE ? OR author LIKE ?
        """, (f"%{keyword}%", f"%{keyword}%"))

        results = cursor.fetchall()

        if not results:
            print("No matching books found")
        else:
            print("\n--- Search Results ---")
            for row in results:
                print(f"ID:{row[0]} | Title:{row[1]} | Author:{row[2]} | Qty:{row[3]}")
    
    
    elif choice == '13':
        cursor.execute("""
        SELECT 
            books.title,
            books.author,
            COUNT(issued_books.id) AS total_issued
        FROM issued_books
        JOIN books 
            ON issued_books.book_id = books.id
        GROUP BY books.id
        ORDER BY total_issued DESC
        LIMIT 5
        """)

        rows = cursor.fetchall()

        if not rows:
            print("No issued data available")
        else:
            print("\n--- Most Issued Books ---")
            for row in rows:
                print(f"Title: {row[0]} | Author: {row[1]} | Issued: {row[2]}")
    
    else:
        print("Invalid choice")
    

# Close connection
conn.close()