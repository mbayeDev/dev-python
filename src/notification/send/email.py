import smtplib, os, json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def notify(body):
    try:
        body = json.loads(body)
        mp3_fid = body['mp3_fid']
        username = body['username']

        sender_address = os.environ.get('SENDER_ADDRESS')
        sender_password = os.environ.get('SENDER_PASSWORD')
        msg = MIMEMultipart()
        msg['From'] =  sender_address #'dammy@gmail.com'
        msg['To'] = username
        msg['Subject'] = 'Download Notification'

        html_text_body = f"""
        <html>
            <body>
                <h1>Mp3 audio file</h1>
                <p>The mp3 audio <a href='http://mp3converter.com/api/v1/download?fid={mp3_fid}'> {mp3_fid} </a> is ready now for download !</p>
            </body>
        </html>
        """

        msg.attach(MIMEText(html_text_body, 'html'))

        smtp_server = os.environ.get('SMTP_SERVER') #"smtp.google.com": 587
        port = int(os.environ.get('SMTP_PORT'))

        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_address, sender_password)
            server.sendmail(sender_address, username, msg.as_string())

        print("Successfully sent email !")
    except Exception as err:
        print(err)
        return err
