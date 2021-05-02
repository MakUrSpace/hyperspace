import boto3
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(subject, sender, contact, content, content_type="html"):
    sesc = boto3.client("ses")

    message = MIMEMultipart()
    message["Subject"] = f"MakUrSpace - {subject}"
    message["From"] = sender
    message["To"] = contact

    body = MIMEText(content, content_type)
    message.attach(body)

    try:
        result = sesc.send_raw_email(
            Source=sender, Destinations=[contact], RawMessage={"Data": message.as_string()}
        )
        return (
            {"message": "error", "status": "fail"}
            if "ErrorResponse" in result
            else {"message": "mail sent successfully", "status": "success"}
        )
    except ClientError as exc:
        return {"message": exc.response["Error"]["Message"], "status": "fail"}
