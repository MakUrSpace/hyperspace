from urllib.parse import unquote_plus
from uuid import uuid4
from base64 import b64decode

from hyperspace.utilities import get_html_template, process_multipart_form_submission, billboardPage
from hyperspace.objects import Bounty, Question
import hyperspace.ses as ses


def get_ask_benefactor_form(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = Bounty.get_bounty(bounty_id)
    form = get_html_template("ask_benefactor_form.html")
    form = form.replace("{bounty_name}", bounty.BountyName)
    form = form.replace("{bounty_id}", bounty.BountyId)
    return form


def submit_benefactor_question(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = Bounty.get_bounty(bounty_id)

    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    submitted_question = process_multipart_form_submission(form_data, content_type)

    question = Question(QuestionId=str(uuid4()), BountyId=bounty_id,
                        Questioner=submitted_question['Questioner'],
                        QuestionText=submitted_question['QuestionText'],
                        QuestionTitle=submitted_question['QuestionTitle'],
                        Answer="")

    email_template = get_html_template("ask_benefactor_email.html")
    for pattern, value in {
        "bounty_name": bounty.BountyName,
        "questioner": question.Questioner,
        "question_title": question.QuestionTitle,
        "question_text": question.QuestionText,
        "question_id": question.QuestionId
    }.items():
        email_template = email_template.replace(f"{{{pattern}}}", value)

    ses.send_email(subject=f'So, you wanna make "{bounty.BountyName}"?', sender="commissions@makurspace.com",
                   contact=bounty.sanitized_maker_email, content=email_template)


def get_question_answer_form(event):
    question_id = unquote_plus(event['pathParameters']['question_id'])
    question = Question.get(question_id)
    form = get_html_template("ask_benefactor_answer_form.html")
    for pattern, value in {
        "question_title": question.QuestionTitle,
        "question_text": question.QuestionText,
        "question_id": question.QuestionId
    }.items():
        form = form.replace("{{{pattern}}}", value)
    return form


@billboardPage
def submit_benefactor_answer(event):
    question_id = unquote_plus(event['pathParameters']['question_id'])
    question = Question.get(question_id)

    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    submitted_answer = process_multipart_form_submission(form_data, content_type)
    question.Answer = submitted_answer['QuestionAnswer']
    question.store()

    return 200, f'Question answer received! Your answer will be sent to the questioner and added to the <a href="https://www.makurspace.com/rendered_bounty/{question.BountyId}">bounty listing</a>'
