import plistlib
import csv
from pathlib import Path

# Path to the Books.plist file (update this path as needed)
plist_path = (
    Path.home()
    / "/Users/h3p/Library/Containers/com.apple.BKAgentService/Data/Documents/iBooks/Books/Books.plist"
)

# Output CSV file path
output_csv = "apple_books_export.csv"

# Goodreads-compatible CSV headers
csv_headers = [
    "Title",
    "Author",
    "ISBN",
    "ISBN13",
    "My Rating",
    "Date Read",
    "Bookshelves",
]


# Function to parse the plist and extract book data
def parse_apple_books_plist(plist_path):
    try:
        # Read the plist file
        with open(plist_path, "rb") as fp:
            plist_data = plistlib.load(fp)

        books = []
        # Assuming the plist contains a 'Books' key with a list of book dictionaries
        for book in plist_data.get("Books", []):
            # Extract relevant fields (adjust keys based on your plist structure)
            title = book.get("title", "") or book.get("itemName", "")
            # Author might be a list or string; join if list
            author = book.get("artistName", "") or book.get("author", "")
            if isinstance(author, list):
                author = ", ".join(author)
            isbn = book.get("isbn", "") or ""
            isbn13 = book.get("isbn13", "") or ""
            # Default values for optional fields
            rating = "0"  # Default rating (0-5)
            date_read = ""  # Format: YYYY/MM/DD, leave blank if unknown
            bookshelves = "read"  # Default shelf, adjust as needed

            books.append(
                {
                    "Title": title,
                    "Author": author,
                    "ISBN": isbn,
                    "ISBN13": isbn13,
                    "My Rating": rating,
                    "Date Read": date_read,
                    "Bookshelves": bookshelves,
                }
            )

        return books

    except Exception as e:
        print(f"Error reading plist file: {e}")
        return []


# Write books to CSV
def write_to_csv(books, output_file):
    try:
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
            writer.writeheader()
            for book in books:
                writer.writerow(book)
        print(f"CSV file saved as {output_file}")
    except Exception as e:
        print(f"Error writing CSV file: {e}")


# Main execution
if __name__ == "__main__":
    books = parse_apple_books_plist(plist_path)
    if books:
        write_to_csv(books, output_csv)
    else:
        print("No books found or error occurred.")
