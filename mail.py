import smtplib
import db_query as db

def send_mail_reg(code, recipient):
    
    SUBJECT = "AllReview Account Activation"
    TEXT = "Activiation code: " + str(code)

    send_email(recipient, SUBJECT, TEXT)


def send_mail_new_pass(recipient, new_pass):
    
    SUBJECT = "AllReview Password Change"
    TEXT = "New Password: " + new_pass

    send_email(recipient, SUBJECT, TEXT)


def send_email(recipient, subject, text):
    gmail_user = "allreviewapp@gmail.com"
    gmail_pwd = 'wWF-7Ze-pBZ-CND'
    FROM = gmail_user
    TO = recipient if type(recipient) is list else [recipient]
    SUBJECT = subject
    TEXT = text
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s""" % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        print 'successfully sent the mail'
    except Exception as e:
        print "failed to send mail:", e
        raise db.MailProblemsException




