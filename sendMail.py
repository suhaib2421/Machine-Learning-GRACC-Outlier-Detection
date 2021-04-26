import smtplib
import imghdr
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import ml
from tabulate import tabulate

graccOutlier = ml.ml()
graccOutlier.outlier(None)
graccOutlier.outlierPicture("outliers.png")

data = graccOutlier.printingTuples()
HTMLtable = tabulate(data, headers=["VO", "Site"], tablefmt="html")
table = tabulate(data, headers=["VO", "Site"])

userName = os.getenv('SECRET_USERNAME')
password = os.getenv('SECRET_PASSWORD')

msg = MIMEMultipart('alternative')
msg['Subject'] = "Daily Outliers"
msg['From'] = userName
msg['To'] = userName # Read env variable w/ os.environ["USERNAME"]
text = "Here are the outliers for today.\n\n" + table + "\n\n" + "See image attached as well\n"

html = """\
    <html>
    <head></head>
        <body>
            <p>Here are the outliers for today.</p>
            <p>
            {HTMLtable}
            </p>
        </body>
    </html>
    """.format(HTMLtable = HTMLtable)


part1 = MIMEText(text, 'plain')
part2 = MIMEText(html, 'html')

msg.attach(part1)
msg.attach(part2)

fp = open('outliers.png', 'rb')                                                    
img = MIMEImage(fp.read())
fp.close()
img.add_header('Outliers', '<{}>'.format('outliers.png'))
msg.attach(img)


with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(userName, password)

    smtp.sendmail(userName, userName, msg.as_string())