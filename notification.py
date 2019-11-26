import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class notification(object):

    def __init__(self, sender, receiver, password, smtp, port):
        self.sender = sender
        self.receiver = receiver
        self.password = password
        self.smtp = smtp
        self.port = port

    def prepare_message(self, text):
        self.message = MIMEMultipart("alternative")
        self.message["Subject"] = "notification about compression job"
        self.message["From"] = self.sender
        self.message["To"] = self.receiver
        part1 = MIMEText(text, "plain")
        self.message.attach(part1)
        
    def sent(self):
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.smtp, self.port, context=context) as server:
            server.login(self.sender, self.password)
            server.sendmail( self.sender, self.receiver, self.message.as_string())


if __name__ == '__main__':
    sender = "test123comp@seznam.cz"
    receiver = "test123comp@seznam.cz"
    password = "abdtrewiuo"
    smtp = "smtp.seznam.cz"
    port = 465
    msg_text = "nejake info"
    notification = notification(sender, receiver, password, smtp, port) 
    notification.prepare_message(msg_text) 
    notification.sent() 
    
    
 