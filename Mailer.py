import smtplib
import imaplib
import email
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import os
import datetime
global stop_receiving
stop_receiving = False  # Control flag for stopping email reception
last_notification = None  # Store last notification

# Email Server Config
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
## To run a test case with the GUI:
## 1. Run the code so that the gui appears
## 2. Fill in the fields with the email and app password for the email for the receiving
## 3. Click on the "Check Email" button
## 4. Fill in the fields with the email and app password for the email for the sending
## 5. Click on the "Send Email" button, a notification will appear with the email sent
## 6. Click on the "Stop Receiving" button to stop the email receiving process
## 7. Click on the "Show Last Notification" button to show the last notification, which should be the one you sent

def show_notification(title, message):
    """Displays a desktop notification and stores the last notification."""
    global last_notification
    last_notification = (title, message)
    os.system(f'notify-send "{title}" "{message}"')


def show_last_notification():
    """Displays the last stored notification in the inbox area."""
    inbox_display.config(state=tk.NORMAL)
    inbox_display.delete(1.0, tk.END)
    if last_notification:
        title, message = last_notification
        inbox_display.insert(tk.END, f"Last Notification:\n{title}\n{message}\n")
    else:
        inbox_display.insert(tk.END, "No notifications yet.\n")
    inbox_display.config(state=tk.DISABLED)


def send_email():
    """Sends an email using SMTP."""
    sender_email = sender_email_entry.get()
    sender_password = sender_password_entry.get()
    recipient_email = recipient_email_entry.get()
    subject = subject_entry.get()
    body = body_text.get("1.0", tk.END)
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        messagebox.showinfo("Success", "Email sent successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send email: {e}")


def receive_email():
    """Fetches unread emails in a separate thread."""
    global stop_receiving
    stop_receiving = False

    def fetch_emails():
        email_address = receiver_email_entry.get()
        email_password = receiver_password_entry.get()
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            mail.login(email_address, email_password)
            mail.select('inbox')

            while not stop_receiving:
                date = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%d-%b-%Y")
                result, data = mail.search(None, f'(X-GM-RAW "category:primary is:unread" SINCE {date})')
                email_ids = data[0].split()

                if not email_ids:
                    inbox_display.config(state=tk.NORMAL)
                    inbox_display.delete(1.0, tk.END)
                    inbox_display.insert(tk.END, "No new emails.\n")
                    inbox_display.config(state=tk.DISABLED)

                email_texts = []
                for email_id in email_ids:
                    result, msg_data = mail.fetch(email_id, '(RFC822)')
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    sender = msg['From']
                    subject = msg['Subject']
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()

                    email_text = f"From: {sender}\nSubject: {subject}\n\n{body}\n{'-' * 40}"
                    email_texts.append(email_text)

                    # Show notification
                    show_notification(f"New Email from {sender}", f"Subject: {subject}\n{body[:100]}...")

                # Display emails in inbox
                inbox_display.config(state=tk.NORMAL)
                inbox_display.delete(1.0, tk.END)
                inbox_display.insert(tk.END, '\n'.join(email_texts))
                inbox_display.config(state=tk.DISABLED)

            mail.logout()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to receive email: {e}")

    threading.Thread(target=fetch_emails, daemon=True).start()


def stop_receiving_emails():
    """Stops the email fetching process."""
    global stop_receiving
    stop_receiving = True
    messagebox.showinfo("Stopped", "Stopped receiving emails.")


# GUI setup
root = tk.Tk()
root.title("Email Client")
root.geometry("550x750")

ttk.Label(root, text="Send Email", font=("Arial", 12, "bold")).pack(pady=5)

# Sender email credentials
ttk.Label(root, text="Sender Email:").pack()
sender_email_entry = ttk.Entry(root, width=50)
sender_email_entry.pack()
ttk.Label(root, text="Sender Password:").pack()
sender_password_entry = ttk.Entry(root, width=50, show="*")
sender_password_entry.pack()

# Recipient email
ttk.Label(root, text="Recipient Email:").pack()
recipient_email_entry = ttk.Entry(root, width=50)
recipient_email_entry.pack()

# Email subject
ttk.Label(root, text="Subject:").pack()
subject_entry = ttk.Entry(root, width=50)
subject_entry.pack()

# Email body
ttk.Label(root, text="Body:").pack()
body_text = scrolledtext.ScrolledText(root, height=5, width=60)
body_text.pack()

# Send button
ttk.Button(root, text="Send Email", command=send_email).pack(pady=5)

ttk.Label(root, text="Check Inbox", font=("Arial", 12, "bold")).pack(pady=5)

# Receiver email credentials
ttk.Label(root, text="Receiver Email:").pack()
receiver_email_entry = ttk.Entry(root, width=50)
receiver_email_entry.pack()
ttk.Label(root, text="Receiver Password:").pack()
receiver_password_entry = ttk.Entry(root, width=50, show="*")
receiver_password_entry.pack()

# Buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=5)

ttk.Button(button_frame, text="Check Email", command=receive_email).pack(side=tk.LEFT, padx=5)
ttk.Button(button_frame, text="Stop Receiving", command=stop_receiving_emails).pack(side=tk.LEFT, padx=5)
ttk.Button(button_frame, text="Show Last Notification", command=show_last_notification).pack(side=tk.LEFT, padx=5)

# Inbox display
ttk.Label(root, text="Inbox Messages:").pack()
inbox_display = scrolledtext.ScrolledText(root, height=10, width=60, state=tk.DISABLED)
inbox_display.pack()

root.mainloop()
