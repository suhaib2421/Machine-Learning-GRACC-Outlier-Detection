import smtplib
import imghdr
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import ml
from tabulate import tabulate
from premailer import transform

# Include bootstrap and do inline from that


# Calls to ml.py to get relevant information
graccOutlier = ml.ml()
graccOutlier.outlier(None)
graccOutlier.outlierPicture("outliers.png")
data = graccOutlier.printingTuples()

# Tabulating the outliers to present neatly in email
HTMLtable = tabulate(data, headers=["VO", "Site"], tablefmt="html")
table = tabulate(data, headers=["VO", "Site"])

userName = os.getenv('SECRET_USERNAME')
password = os.getenv('SECRET_PASSWORD')

msg = MIMEMultipart('alternative')
msg['Subject'] = "Daily Outliers"
msg['From'] = userName
msg['To'] = userName # Read env variable w/ os.environ["USERNAME"]
text = "Here are the outliers for today.\n\n" + table + "\n\n" + "See image attached as well\n"

# Puts the table into html to show in table
html = transform("""\
    <html>
    <head>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-eOJMYsd53ii+scO/bJGFsiCZc+5NDVN2yr8+0RDqr0Ql0h+rP48ckxlpbzKgwra6" crossorigin="anonymous">
    </head>
        <body>
            <p>Here are the outliers for today.</p>
            <p>
            <table class="table table-bordered">{}</table>
            </p>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/js/bootstrap.bundle.min.js" integrity="sha384-JEW9xMcG8R+pH31jmWH6WWP0WintQrMb4s7ZOdauHnUtxwoG2vI5DkLtS3qm9Ekf" crossorigin="anonymous"></script>
        </body>
    </html>
    """.format(HTMLtable))


part1 = MIMEText(text, 'plain')
part2 = MIMEText(html, 'html')

msg.attach(part1)
msg.attach(part2)

# Attaching image of outliers
fp = open('outliers.png', 'rb')                                                    
img = MIMEImage(fp.read())
fp.close()
img.add_header('Outliers', '<{}>'.format('outliers.png'))
msg.attach(img)

# Sending the email
with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(userName, password)

    smtp.sendmail(userName, userName, msg.as_string())