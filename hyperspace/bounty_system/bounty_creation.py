from datetime import datetime
from uuid import uuid4
import json
from base64 import b64decode

from requests_toolbelt.multipart import MultipartDecoder

from hyperspace.murd import mddb, murd
from hyperspace.objects import Bounty, PurchaseConfirmation
from hyperspace.utilities import get_html_template, get_form_name
import hyperspace.ses as ses
import hyperspace.s3 as s3
from hyperspace.reference_material import write_refmat_to_s3, promote_out_of_purgatory


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
    refmat_material = {}

    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    multipart_decoder = MultipartDecoder(content=form_data, content_type=content_type)
    for part in multipart_decoder.parts:
        form_name = get_form_name(part)
        assert form_name != 'State'
        if form_name == 'ReferenceMaterialNames':
            new_bounty_defn['ReferenceMaterial'] = json.loads(part.content)
        else:
            new_bounty_defn[form_name] = part.content.decode()

    new_bounty = Bounty(**new_bounty_defn, BountyId=str(uuid4()))
    try:
        new_bounty.store()
        for refmat, refmat_content in refmat_material.items():
            write_refmat_to_s3(new_bounty.BountyName, refmat, refmat_content)
    except Exception:
        print("Deleting bounty")
        murd.delete([new_bounty.asm()])
        return 403, "Failed to submit bounty"

    send_bounty_to_contact(new_bounty)

    response_template = get_html_template("bounty_submission_response_template.html")
    response_template = response_template.replace("{benefactor_email}", new_bounty.Contact)
    return 200, response_template


def confirm_bounty_creation(event):
    confirmation_id = event['pathParameters']['bounty_confirmation_id']
    confirmationm = murd.read_first(group="bounty_creation_confirmations", sort=confirmation_id)
    Bounty.get_bounty(confirmationm['BountyId'])
    confirmation_template = get_html_template("confirm_bounty.html")
    confirmation_template = confirmation_template.replace("{bounty_confirmation_id}", confirmation_id)
    return 200, confirmation_template


def bounty_confirmed(event):
    confirmation_id = event['pathParameters']['bounty_confirmation_id']
    confirmationm = murd.read_first(group="bounty_creation_confirmations", sort=confirmation_id)
    bounty = Bounty.get_bounty(confirmationm['BountyId'])
    purchase_confirmation = PurchaseConfirmation(**json.loads(event['body']))
    purchase_confirmation.store()
    murd.delete([bounty.asm(), confirmationm])
    bounty.change_state("confirmed")
    for refmat in bounty.ReferenceMaterial:
        promote_out_of_purgatory(bounty.BountyId, refmat)
