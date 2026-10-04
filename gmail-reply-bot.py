import imaplib
import email
from email.header import decode_header
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# --- CONFIGURATION ---
GMAIL_USER = "your_email@gmail.com"
GMAIL_APP_PASSWORD = "your_app_password_here"  # 16-character app password
AUTO_REPLY_BODY = "Thank you for your email. This is an automated response to confirm I have received it."

def check_and_reply():
    try:
        # 1. Connect to Gmail IMAP to check for unread emails
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        mail.select("inbox")

        # Search for all unread ("UNSEEN") emails
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            print("No new messages or error searching.")
            return

        # Convert search results to a list of email IDs
        email_ids = messages[0].split()
        
        if not email_ids:
            print("No unread emails found.")
            return

        print(f"Found {len(email_ids)} unread email(s). Processing...")

        # 2. Connect to Gmail SMTP to send replies
        smtp_server = smtplib.SMTP("smtp.gmail.com", 587)
        smtp_server.starttls()
        smtp_server.login(GMAIL_USER, GMAIL_APP_PASSWORD)

        for e_id in email_ids:
            # Fetch the email headers
            res, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    # Parse the raw email bytes into a usable object
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Extract Subject and Sender
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8")
                        
                    sender = msg.get("From")
                    
                    print(f"Processing email from: {sender} | Subject: {subject}")

                    # Prevent the bot from replying to itself
                    if GMAIL_USER in sender:
                        print("Skipping self-sent email.")
                        continue

                    # Craft the automatic reply
                    reply_msg = MIMEMultipart()
                    reply_msg["From"] = GMAIL_USER
                    reply_msg["To"] = sender
                    reply_msg["Subject"] = f"Re: {subject}"
                    reply_msg.attach(MIMEText(AUTO_REPLY_BODY, "plain"))

                    # Send the email
                    smtp_server.sendmail(GMAIL_USER, sender, reply_msg.as_string())
                    print(f"Successfully replied to {sender}")

                    # Optional: Mark the email as read so it isn't replied to again next time
                    mail.store(e_id, "+FLAGS", "\\Seen")

        # Close connections cleanly
        smtp_server.quit()
        mail.close()
        mail.logout()

    except Exception as e:
        print(f"An error occurred: {e}")

# Run the loop every 60 seconds
if __name__ == "__main__":
    print("Starting Gmail Auto-Responder... Press Ctrl+C to stop.")
    while True:
        check_and_reply()
        time.sleep(60)
