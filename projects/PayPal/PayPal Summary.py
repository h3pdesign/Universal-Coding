import imaplib
import email
from email.header import decode_header
import pandas as pd
import re
import os

# --- Configuration ---
IMAP_SERVER = "imap.ionos.de"  # Replace with your actual IMAP server (e.g., ionos, strato, etc.)
EMAIL_ACCOUNT = "your_email@hpedersen.de"
PASSWORD = "your_email_password"  # Use an App Password if 2FA is enabled
TARGET_ADDRESS = "paypal@hpedersen.de"

def clean_text(text):
    # Simple cleaner to remove excessive whitespace and newlines
    return re.sub(r'\s+', ' ', text)

def extract_amount(text):
    # Regex to find amounts like "€15,50", "15,50 EUR", "15.50"
    # Adjust this regex if your PayPal emails use a different format
    match = re.search(r'(?:€|EUR)\s*([\d.,]+)|([\d.,]+)\s*(?:€|EUR)', text, re.IGNORECASE)
    if match:
        raw_val = match.group(1) if match.group(1) else match.group(2)
        # Convert German number formatting (1.000,50) to standard float (1000.50)
        clean_val = raw_val.replace('.', '').replace(',', '.')
        try:
            return float(clean_val)
        except ValueError:
            return 0.0
    return 0.0

def main():
    print(f"Connecting to {IMAP_SERVER}...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    
    try:
        mail.login(EMAIL_ACCOUNT, PASSWORD)
        mail.select("inbox")
        
        # Search for emails from PayPal sent to your specific address
        search_query = f'(FROM "service@paypal" TO "{TARGET_ADDRESS}")'
        status, messages = mail.search(None, search_query)
        
        if status != "OK":
            print("No messages found or search failed.")
            return

        email_ids = messages[0].split()
        print(f"Found {len(email_ids)} PayPal emails. Processing...")

        transactions = []
        total_sum = 0.0

        for e_id in email_ids:
            res, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Decode Date
                    date_str = msg.get("Date")
                    
                    # Extract Body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode()
                                except:
                                    pass
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode()
                        except:
                            pass
                    
                    body = clean_text(body)
                    
                    # Skip emails that are just marketing or policy updates
                    if "Zahlung erhalten" in msg.get("Subject", "") or "payment received" in msg.get("Subject", "").lower():
                        amount = extract_amount(body)
                        if amount > 0:
                            transactions.append({
                                "Date": date_str,
                                "Amount (EUR)": amount
                            })
                            total_sum += amount

        # Create DataFrame and export to Excel
        if transactions:
            df = pd.DataFrame(transactions)
            df['Date'] = pd.to_datetime(df['Date'], format='mixed', utc=True).dt.tz_localize(None)
            df = df.sort_values(by="Date", ascending=False)
            
            # Add a total row at the bottom
            total_row = pd.DataFrame([{"Date": "TOTAL", "Amount (EUR)": total_sum}])
            df = pd.concat([df, total_row], ignore_index=True)
            
            output_file = "paypal_summary.xlsx"
            df.to_excel(output_file, index=False)
            print(f"\nSuccess! Processed {len(transactions)} payments.")
            print(f"Total Sum: €{total_sum:.2f}")
            print(f"Summary saved to {os.path.abspath(output_file)}")
        else:
            print("No valid payment amounts could be extracted.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        mail.logout()

if __name__ == "__main__":
    main()
