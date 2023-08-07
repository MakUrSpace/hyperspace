from datetime import datetime
from uuid import uuid4
import json
from base64 import b64decode

from hyperspace.murd import mddb, murd
from hyperspace.objects import HyperBounty, HyperMaker, asdict
from hyperspace.utilities import get_html_template, process_multipart_form_submission
import hyperspace.ses as ses
import hyperspace.s3 as s3
from hyperspace.bounty_system.render_bounties import render_bounty


def send_completed_bounty_to_contact(completed_bounty):
    email_template = get_html_template("bounty_creation_completed_email_template.html")

    completed_bounty_map = asdict(completed_bounty)
    completed_bounty_map['ReferenceMaterial'] = completed_bounty.ReferenceMaterialHTML

    for key, value in completed_bounty_map.items():
        email_template = email_template.replace(f"{{{key}}}", f"{value}")

    confirmation_id = str(uuid4())
    email_template = email_template.replace("{bounty_confirmation_id}", confirmation_id)
    email_template = email_template.replace("{BountyReward}", completed_bounty.reward)

    completed_bounty.ConfirmationId = confirmation_id
    murd.update([
        completed_bounty.asm(),
        {mddb.group_key: "completed_bounty_creation_confirmations",
         mddb.sort_key: confirmation_id,
         "BountyId": completed_bounty.Id,
         "CreationTime": datetime.utcnow().isoformat()}
    ])

    ses.send_email(subject=f"{completed_bounty.Name} Bounty", sender="commissions@makurspace.com",
                   contact=completed_bounty.sanitized_contact_email, content=email_template)


def submit_completed_bounty_form(event):
    s3.write(f"submissions/sub-{uuid4()}", json.dumps(event).encode(), "makurspace")
    completed_bounty_defn = {}

    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    completed_bounty_defn = process_multipart_form_submission(form_data, content_type)
    completed_bounty_defn['Id'] = completed_bounty_defn.pop("BountyId")

    maker_email = completed_bounty_defn["Contact"]
    try:
        maker = HyperMaker.retrieveByEmail(maker_email)
    except Exception:
        raise Exception(f"Unrecognized maker: {maker_email}")
    completed_bounty_defn["Recipient"] = maker.MakerName
    completed_bounty_defn["DueDate"] = None

    completed_bounty = HyperBounty(**completed_bounty_defn,
                                   State="submitted")
    completed_bounty.stampSUBMITTED()
    try:
        completed_bounty.set()
        send_completed_bounty_to_contact(completed_bounty)
        response_template = get_html_template("bounty_submission_response_template.html")
        response_template = response_template.replace("{recipient_email}", completed_bounty.Contact)
    except Exception as e:
        print(f"FAILURE: Deleting bounty due to: {e}")
        murd.delete([completed_bounty.asm()])
        return 403, "Failed to submit bounty"

    return 200, response_template


def submit_completed_bounty_or_return_form(event):
    try:
        return submit_completed_bounty_form(event)
    except Exception as e:
        bounty_form = get_html_template("completed_bounty_form.html")
        bounty_form = bounty_form.replace(
            "Submit a completed project for the MakUrSpace Community Portfolio!",
            f"Failed to submit previous completed bounty:<br>{e}<br>Try Again or contact support@makurspace.com")
        return 400, bounty_form


def get_completed_bounty_by_confirmation(confirmation_id):
    confirmationm = murd.read_first(group="completed_bounty_creation_confirmations", sort=confirmation_id)
    return HyperBounty.retrieve(confirmationm['BountyId'])


def confirm_completed_bounty_creation(event):
    confirmation_id = event['pathParameters']['bounty_confirmation_id']
    bounty = get_completed_bounty_by_confirmation(confirmation_id)
    bounty.change_state("claimed", from_state="submitted")
    bounty.stampCLAIMED()

    bounty_template = render_bounty(bounty.Id).replace(
        '<ol class="breadcrumb">',
        '<h1 class="mt-4 mb-3">Bounty Posted!!!</h1><ol class="breadcrumb">')
    return 200, bounty_template
