import smtplib
import imghdr
import config
from email.message import EmailMessage
import ml


msg = EmailMessage()
msg['Subject'] = "Daily Outliers"
msg['From'] = config.EMAIL_ADDRESS
msg['To'] = config.EMAIL_ADDRESS
msg.set_content("Here are the outliers for today. See image attached: ")

with open('outliers.png', 'rb') as f:
    file_data = f.read()
    file_type = imghdr.what(f.name)
    file_name = f.name

msg.add_attachment(file_data, maintype='image', subtype=file_type, filename=file_name)


with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(config.EMAIL_ADDRESS, config.PASSWORD)

    smtp.send_message(msg)
