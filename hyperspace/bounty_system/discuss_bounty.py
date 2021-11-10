from urllib.parse import unquote_plus
from uuid import uuid4
from base64 import b64decode

from requests_toolbelt.multipart import MultipartDecoder

from hyperspace.utilities import get_html_template, get_form_name
from hyperspace.objects import Bounty, Question
import hyperspace.ses as ses


def get_ask_benefactor_form(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = Bounty.get_bounty(bounty_id)
    form = get_html_template("get_ask_benefactor_form.html")
    form = form.replace("{bounty_name}", bounty.BountyName)
    return form


def ask_the_benefactor(event):
    email_template = email_template.replace("{Bount")


def submit_benefactor_question(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = Bounty.get_bounty(bounty_id)

    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    submitted_question = {}
    multipart_decoder = MultipartDecoder(content=form_data, content_type=content_type)
    for part in multipart_decoder.parts:
        form_name = get_form_name(part)
        submitted_question[form_name] = part.content.decode()

    question = Question(QuestionId=str(uuid4()), BountyId=bounty_id,
                        Questioner=submitted_question['Questioner'], QuestionText=submitted_question['QuestionText'],
                        QuestionText=submitted_question['QuestionText'])

    email_template = get_html_template("ask_benefactor_email.html")
    for pattern, value in {
        "questioner": question.Questioner,
        "question_title": question.QuestionTitle,
        "question_text": question.QuestionText,
        "question_id": question.QuestionId
    }.items():
        email_template = email_template.replace(f"{{{pattern}}}", value)

    ses.send_email(subject=f'So, you wanna make "{bounty.BountyName}"?', sender="commissions@makurspace.com",
                   contact=bounty.sanitized_maker_email, content=email_template)
