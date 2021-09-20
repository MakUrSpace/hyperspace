from datetime import datetime
from uuid import uuid4
import json
from base64 import b64decode

from hyperspace.murd import mddb, murd
from hyperspace.objects import Bounty, PurchaseConfirmation
from hyperspace.utilities import get_html_template, process_multipart_form_submission
import hyperspace.ses as ses
import hyperspace.s3 as s3


def send_bounty_to_contact(new_bounty):
    email_template = get_html_template("bounty_creation_email_template.html")

    for key, value in new_bounty.asdict().items():
        email_template = email_template.replace(f"{{{key}}}", f"{value}")

    confirmation_id = str(uuid4())
    email_template = email_template.replace("{bounty_confirmation_id}", confirmation_id)
    email_template = email_template.replace("{BountyReward}", new_bounty.reward)

    new_bounty.ConfirmationId = confirmation_id
    murd.update([
        new_bounty.asm(),
        {mddb.group_key: "bounty_creation_confirmations",
         mddb.sort_key: confirmation_id,
         "BountyId": new_bounty.BountyId,
         "CreationTime": datetime.utcnow().isoformat()}
    ])

    ses.send_email(subject=f"{new_bounty.BountyName} Bounty", sender="commissions@makurspace.com",
                   contact=new_bounty.sanitized_contact, content=email_template)


def submit_bounty_form(event):
    s3.write(f"submissions/sub-{uuid4()}", json.dumps(event).encode(), "makurspace")
    new_bounty_defn = {}

    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    new_bounty_defn = process_multipart_form_submission(form_data, content_type)

    new_bounty = Bounty(**new_bounty_defn)
    try:
        new_bounty.store()
    except Exception:
        print("Deleting bounty")
        murd.delete([new_bounty.asm()])
        return 403, "Failed to submit bounty"

    send_bounty_to_contact(new_bounty)

    response_template = get_html_template("bounty_submission_response_template.html")
    response_template = response_template.replace("{benefactor_email}", new_bounty.Contact)
    return 200, response_template


def submit_bounty_or_return_form(event):
    try:
        return submit_bounty_form(event)
    except Exception as e:
        bounty_form = get_html_template("bounty_submission_form.html")
        bounty_form = bounty_form.replace(
            "Submit a Bounty!",
            f"Failed to submit previous bounty:<br>{e}<br>Try Again or contact support@makurspace.com")
        return 400, bounty_form


def get_bounty_by_confirmation(confirmation_id):
    confirmationm = murd.read_first(group="bounty_creation_confirmations", sort=confirmation_id)
    return Bounty.get_bounty(confirmationm['BountyId'])


def confirm_bounty_creation(event):
    confirmation_id = event['pathParameters']['bounty_confirmation_id']
    bounty = get_bounty_by_confirmation(confirmation_id)
    if bounty.Benefactor.lower() in ['musingsole', 'mus', 'btrain', 'shaquille', 'briana']:
        bounty.set_state("confirmed")
        bounty_form = get_html_template("bounty_submission_form.html")
        bounty_form = bounty_form.replace("Submit a Bounty!", "Bounty Submitted!!! Another?")
        return 200, bounty_form
    confirmation_template = get_html_template("confirm_bounty.html")
    confirmation_template = confirmation_template.replace("{bounty_confirmation_id}", confirmation_id)
    return 200, confirmation_template


def bounty_confirmed(event):
    confirmation_id = event['pathParameters']['bounty_confirmation_id']
    bounty = get_bounty_by_confirmation(confirmation_id)
    purchase_confirmation = PurchaseConfirmation(**json.loads(event['body']))
    purchase_confirmation.store()
    bounty.change_state("confirmed", from_state="submitted")
