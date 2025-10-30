import smtplib
import ssl
import pandas as pd
import sqlite3
import secrets
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_ADDRESS, EMAIL_PASSWORD, ROLE_CONFIG, DB_NAME, DISCORD_INVITE_LINK

def create_database():
    """Initializes the SQLite database and table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            first_name TEXT,
            last_name TEXT,
            role_name TEXT,
            role_id INTEGER,
            token TEXT NOT NULL UNIQUE,
            verified INTEGER DEFAULT 0,
            discord_id TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' is ready.")

def load_template(template_path):
    """Loads an HTML email template from a file."""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: Template file not found at {template_path}")
        return None
    except Exception as e:
        print(f"Error reading template {template_path}: {e}")
        return None

def send_email_smtp(receiver_email, subject, html_content):
    """Connects to Gmail and sends the email."""
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"GDG ENSIA <{EMAIL_ADDRESS}>"
    msg['To'] = receiver_email

    msg.attach(MIMEText(html_content, 'html'))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, receiver_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Error sending email to {receiver_email}: {e}")
        return False

def process_and_send():
    """Main function to process CSVs, update DB, and send emails."""
    create_database()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for role_name, config in ROLE_CONFIG.items():
        csv_file = config['csv_file']
        template_file = config['template']
        role_id = config['role_id']

        print(f"\n--- Processing {role_name} Team from {csv_file} ---")

        try:
            # Read the CSV file, skipping the first row (header)
            df = pd.read_csv(csv_file, header=0)
        except FileNotFoundError:
            print(f"WARNING: File not found: {csv_file}. Skipping.")
            continue
        except Exception as e:
            print(f"Error reading {csv_file}: {e}. Skipping.")
            continue

        # Clean column names (remove potential leading/trailing spaces)
        df.columns = df.columns.str.strip()

        html_template = load_template(template_file)
        if not html_template:
            print(f"WARNING: Could not load template {template_file}. Skipping {role_name} team.")
            continue

        for _, row in df.iterrows():
            # Check for empty rows (which you have in your sample files)
            if row.isnull().all():
                continue

            email = str(row.get('email', '')).strip()
            first_name = str(row.get('firstName', '')).strip().title()
            last_name = str(row.get('lastName', '')).strip().title()

            if not email or not first_name:
                print(f"SKIPPED: Missing data for row: {row.to_dict()}")
                continue

            # Check if email already in database
            cursor.execute("SELECT * FROM members WHERE email = ?", (email,))
            if cursor.fetchone():
                print(f"SKIPPED: {first_name} {last_name} ({email}) already in database.")
                continue

            # Generate unique token
            token = secrets.token_urlsafe(16)

            # Personalize email
            email_body = html_template.replace("{{VERIFICATION_TOKEN}}", token)
            email_body = email_body.replace("{{FIRST_NAME}}", first_name)
            email_body = email_body.replace("https://discord.gg/YourGDGServer", DISCORD_INVITE_LINK)  # Replace placeholder link

            # Send email
            subject = f"{first_name} {last_name} - Accepted in {role_name} Department"
            if send_email_smtp(email, subject, email_body):
                # If email sends successfully, add to database
                try:
                    cursor.execute(
                        "INSERT INTO members (email, first_name, last_name, token, role_name, role_id, verified) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (email, first_name, last_name, token, role_name, role_id, 0)
                    )
                    conn.commit()
                    print(f"SUCCESS: Sent email to {first_name} {last_name} ({email}) and added to DB.")
                except sqlite3.Error as e:
                    print(f"ERROR: Could not add {email} to database: {e}")
            else:
                print(f"FAILED to send email to {first_name} {last_name} ({email}). Not added to DB.")

            # Pause for 1 second to avoid being rate-limited by the email server
            time.sleep(1)

    conn.close()
    print("\n--- All emails sent and database populated! ---")

if __name__ == "__main__":
    process_and_send()
