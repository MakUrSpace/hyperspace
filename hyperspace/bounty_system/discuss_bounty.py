from urllib.parse import unquote_plus
from uuid import uuid4
from base64 import b64decode

from hyperspace.utilities import get_html_template, process_multipart_form_submission, billboardPage
from hyperspace.objects import HyperBounty, HyperQuestion
import hyperspace.ses as ses


def get_ask_benefactor_form(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = HyperBounty.retrieve(bounty_id)
    form = get_html_template("ask_benefactor_form.html")
    form = form.replace("{bounty_name}", bounty.Name)
    form = form.replace("{bounty_id}", bounty.Id)
    return 200, form


@billboardPage
def submit_benefactor_question(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = HyperBounty.retrieve(bounty_id)

    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    submitted_question = process_multipart_form_submission(form_data, content_type)

    question = HyperQuestion(Id=str(uuid4()), BountyId=bounty_id,
                             Questioner=submitted_question['Questioner'],
                             QuestionText=submitted_question['QuestionText'],
                             QuestionTitle=submitted_question['QuestionTitle'],
                             Answer="")
    question.set()

    email_template = get_html_template("ask_benefactor_email.html")
    for pattern, value in {
        "bounty_name": bounty.Name,
        "questioner": question.Questioner,
        "question_title": question.QuestionTitle,
        "question_text": question.QuestionText,
        "question_id": question.Id
    }.items():
        email_template = email_template.replace(f"{{{pattern}}}", value)

    ses.send_email(subject=f'MakUrSpace, got a question for you!', sender="commissions@makurspace.com",
                   contact=bounty.sanitized_contact, content=email_template)

    return 200, f"Bounty question submitted! Your question was sent along to the benefactor of {bounty.Name}. You'll be notified when they answer."


def get_question_answer_form(event):
    question_id = unquote_plus(event['pathParameters']['question_id'])
    question = HyperQuestion.retrieve(question_id)
    form = get_html_template("ask_benefactor_answer_form.html")
    for pattern, value in {
        "question_title": question.QuestionTitle,
        "question_text": question.QuestionText,
        "question_id": question.Id
    }.items():
        form = form.replace(f"{{{pattern}}}", value)
    return 200, form


@billboardPage
def submit_benefactor_answer(event):
    question_id = unquote_plus(event['pathParameters']['question_id'])
    question = HyperQuestion.retrieve(question_id)

    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    submitted_answer = process_multipart_form_submission(form_data, content_type)
    question.Answer = submitted_answer['QuestionAnswer']
    question.set()

    email_template = get_html_template("ask_benefactor_answer_email.html")
    for pattern, value in {
        "bounty_id": question.BountyId,
        "question_title": question.QuestionTitle,
        "question_text": question.QuestionText,
        "question_answer": question.Answer
    }.items():
        email_template = email_template.replace(f"{{{pattern}}}", value)

    return 200, f'Question answer received! Your answer was sent to the questioner and added to the <a href="https://www.makurspace.com/rest/rendered_bounty/{question.BountyId}">bounty listing</a>'
