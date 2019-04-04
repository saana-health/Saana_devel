import os
import json
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

to_emails = [
    # ('somj94@gmail.com', 'Min Joon')
    # # ,
    ('stephanie@saana.co', 'minjoon')
]

to_name = 'first-name'

message = Mail(
    from_email=('minjoon@saana.co', 'Min Joon'),
    to_emails=to_emails,
    subject='Your Saana Order is Confirmed',
    html_content='Hi <strong>' + to_name + "\
    </strong>, \
    <br> <h1> Your personalize nutrition has just been calculated.</h1> \
    <p style = \"width\":60%;'>Good News! Our team of scientists just finished up personalizing your next delivery of meals based on your latest medical information. \
    <br>Our suppliers will start cooking your meals next Monday and you should receive it by the end of next week (shipped within 1-2 business days). \
    <br>Your next tailored meal program, that will therefore start next Friday, will be sent over in a separate email.</p>\
    <p style = \"width: 60%\">As always, don’t hesitate to contact us via text message (862) 256-3059 or email (hello@saana.co) for any questions regarding your meals,\
     your well-being or anything! Coaching and follow-up is always part of your plan.</p>\
    With love,\
    <br> Saana Team\
    <br>\
    <img src='https://minjoon-test-bucket.s3.amazonaws.com/logo', height = \"40\", width = \"160\">\
    "
)


try:
    sendgrid_client = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    response = sendgrid_client.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e.message)