import smtplib
from email.message import EmailMessage
from google.cloud import firestore
import ssl

# Initialize Firestore client
db = firestore.Client(project='feed-ai-c379d')

def send_email(to_email, subject, message, from_email, smtp_server, smtp_port, smtp_user, smtp_password):
    # Create email message
    email = EmailMessage()
    email.set_content(message)
    email['Subject'] = subject
    email['From'] = from_email
    email['To'] = to_email

    context = ssl.create_default_context()

    # Send the email using SMTP
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
        server.login(smtp_user, smtp_password)
        server.send_message(email)


def mass_email():
    # Get user emails from Firestore collection
    users_ref = db.collection(u'service')
    docs = users_ref.stream()

    # Define the email content
    subject = 'Get $50 in ad credits'
    message = """
    Get $50 in ad credits completely free by answering one question. We want Feadl.io to provide our users as much value as possible. We are continuously imporving and updating our Marketing and Social Media Automation software and your feedback is crucial.

    How can we make Feadl.io better for you?
    or
    What is something you are looking for from a service that we don't offer?

    Reply to this email with your answer. We are so grateful for your feedback to improve our product.

    Best regards,
    Feadl.io Team

    Visit the site:
    https://feadl.io/free-trial/
    """
    from_email = 'team@feadl.io'

    # SMTP server details (e.g., Gmail)
    smtp_server = 'mail.privateemail.com'
    smtp_port = 465
    smtp_user = 'team@feadl.io'
    smtp_password = 'Teamcred#2000'

    # Loop through users and send emails
    for doc in docs:
        user = doc.to_dict()
        user_email = user.get('email')

        if user_email:  # Send email only if the user has an email
            send_email(
                to_email=user_email,
                subject=subject,
                message=message,
                from_email=from_email,
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                smtp_user=smtp_user,
                smtp_password=smtp_password
            )
            print(f"Email sent to {user_email}")

if __name__ == '__main__':
    mass_email()
