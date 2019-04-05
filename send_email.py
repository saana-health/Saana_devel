import os
import pdb
import json
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

to_emails = [
    # ('somj94@gmail.com', 'Min Joon'),
    ('stephanie@saana.co','Stephanie')
]

to_name = 'Beata'

message = Mail(
    from_email=('hello@saana.co', 'Jacki from Saana'),
    to_emails=to_emails,
    subject='Your Saana Order is Confirmed',
    html_content = open('email_format.html','r').read()
)

try:
    sendgrid_client = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    response = sendgrid_client.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e.message)