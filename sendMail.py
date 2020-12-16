import smtplib
import imghdr
from decouple import config
from email.message import EmailMessage
import ml


userName = config('USER')
password = config('KEY')

msg = EmailMessage()
msg['Subject'] = "Daily Outliers"
msg['From'] = userName
msg['To'] = userName # Read env variable w/ os.environ["USERNAME"]
msg.set_content("Here are the outliers for today. See image attached: ")

with open('outliers.png', 'rb') as f:
    file_data = f.read()
    file_type = imghdr.what(f.name)
    file_name = f.name

msg.add_attachment(file_data, maintype='image', subtype=file_type, filename=file_name)


with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(userName, password)

    smtp.send_message(msg)
