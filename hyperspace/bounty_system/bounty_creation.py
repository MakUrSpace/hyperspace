from datetime import datetime
from uuid import uuid4
import json
from base64 import b64decode

from hyperspace.murd import mddb, murd
from hyperspace.objects import HyperBounty, asdict
from hyperspace.utilities import get_html_template, process_multipart_form_submission
import hyperspace.ses as ses
import hyperspace.s3 as s3
from hyperspace.bounty_system.render_bounties import render_bounty


def send_bounty_to_contact(new_bounty):
    email_template = get_html_template("bounty_creation_email_template.html")

    new_bounty_map = asdict(new_bounty)
    new_bounty_map['ReferenceMaterial'] = new_bounty.ReferenceMaterialHTML

    for key, value in new_bounty_map.items():
        email_template = email_template.replace(f"{{{key}}}", f"{value}")

    confirmation_id = str(uuid4())
    email_template = email_template.replace("{bounty_confirmation_id}", confirmation_id)
    email_template = email_template.replace("{BountyReward}", new_bounty.reward)

    new_bounty.ConfirmationId = confirmation_id
    murd.update([
        new_bounty.asm(),
        {mddb.group_key: "bounty_creation_confirmations",
         mddb.sort_key: confirmation_id,
         "BountyId": new_bounty.Id,
         "CreationTime": datetime.utcnow().isoformat()}
    ])

    ses.send_email(subject=f"{new_bounty.Name} Bounty", sender="commissions@makurspace.com",
                   contact=new_bounty.sanitized_contact_email, content=email_template)


def submit_bounty_form(event):
    s3.write(f"submissions/sub-{uuid4()}", json.dumps(event).encode(), "makurspace")
    new_bounty_defn = {}

    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    new_bounty_defn = process_multipart_form_submission(form_data, content_type)
    new_bounty_defn['Id'] = new_bounty_defn.pop("BountyId")

    new_bounty = HyperBounty(**new_bounty_defn,
                             State="submitted")
    new_bounty.stampSUBMITTED()
    try:
        new_bounty.set()
        send_bounty_to_contact(new_bounty)
        response_template = get_html_template("bounty_submission_response_template.html")
        response_template = response_template.replace("{benefactor_email}", new_bounty.Contact)
    except Exception as e:
        print(f"FAILURE: Deleting bounty due to: {e}")
        murd.delete([new_bounty.asm()])
        return 403, "Failed to submit bounty"

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
    return HyperBounty.retrieve(confirmationm['BountyId'])


def confirm_bounty_creation(event):
    confirmation_id = event['pathParameters']['bounty_confirmation_id']
    bounty = get_bounty_by_confirmation(confirmation_id)
    bounty.change_state("verified", from_state="submitted")

    bounty_template = render_bounty(bounty.Id).replace(
        '<ol class="breadcrumb">',
        '<h1 class="mt-4 mb-3">Bounty submitted for review!</h1><ol class="breadcrumb">')
    return 200, bounty_template
