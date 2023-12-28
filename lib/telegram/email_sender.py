import smtplib
import os
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from lib.localization import _

# Load environment variables from .env file
load_dotenv()

class EmailSender:
    def __init__(self):
        self.sender_email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')

    def send_email(self, recipient_email, subject, text, attachment=None):
        # Setting up the MIME
        message = MIMEMultipart()
        message['From'] = self.sender_email
        message['To'] = recipient_email
        message['Subject'] = subject
        message.attach(MIMEText(text, 'plain'))

        # Attachment handling
        if attachment:
            try:
                with open(attachment, "rb") as attachment_file:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment_file.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {attachment}",
                )
                message.attach(part)
            except Exception as e:
                print(f"Error in attaching file: {e}")
                return _("Error in attaching file."), ''

        # Sending the email
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
                smtp_server.login(self.sender_email, self.password)
                smtp_server.sendmail(self.sender_email, recipient_email, message.as_string())
            return _("Email successfully sent!"), ''
        except Exception as e:
            print(f"Error in sending email: {e}")
            return _("Error in sending email."), ''

# Example of usage:
# sender = EmailSender()
# response, error = sender.send_email('chernyakov.sergey@gmail.com', 'Subject here', 'Body text here')
# print(response)
