import yagmail

# Email configuration
smtp_user = 'joshua@nticomputers.com'
smtp_pass = 'NTI2024!'
smtp_host = 'smtp.office365.com'
smtp_port = 587

# Setup Yagmail client
yag = yagmail.SMTP(user=smtp_user, password=smtp_pass, host=smtp_host, port=smtp_port)

# Send the email
to_address = 'jtanner5674@gmail.com'
subject = 'Subject of the email'
body = 'This is the body of the email in HTML format.'

yag.send(to=to_address, subject=subject, contents=body)

print("Email sent successfully!")



# smtp_host = 'smtp.office365.com'
# smtp_port = 25
# smtp_user = 'joshua@nticomputers.com'
# smtp_pass = 'NTI2024!'
# from_name = 'Joshua'