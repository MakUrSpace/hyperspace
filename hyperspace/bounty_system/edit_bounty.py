from uuid import uuid4
from urllib.parse import unquote_plus
from base64 import b64decode
from datetime import datetime
import json

from hyperspace.murd import mddb, murd
from hyperspace.utilities import get_html_template, get_javascript_template, billboardPage, process_multipart_form_submission, sanitize_email
from hyperspace.objects import HyperBounty, HyperMaker, asdict
from hyperspace.bounty_system.render_bounties import render_bounty
import hyperspace.ses as ses


def get_edit_bounty_form(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = HyperBounty.retrieve(bounty_id)
    form_template = get_html_template("edit_bounty_form.html")
    script_template = \
        get_javascript_template("upload_reference_material.js").replace("{bounty_id}", bounty_id)

    for pattern, replacement in {
            "{bounty_id}": bounty.Id,
            "{bounty_name}": bounty.Name,
            "{bounty_reward}": bounty.reward,
            "{reference_material}": json.dumps(bounty.ReferenceMaterial),
            "{bounty_description}": bounty.Description,
            "{upload_reference_material_script}": script_template}.items():
        form_template = form_template.replace(pattern, replacement)

    return 200, form_template


@billboardPage
def receive_bounty_edits(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = HyperBounty.retrieve(bounty_id)
    bounty_edit = {}

    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    bounty_edit = process_multipart_form_submission(form_data, content_type)

    try:
        editMaker = HyperMaker.retrieveByEmail(bounty_edit.pop("EditorContact"))
        editor = editMaker.Id
    except sanitize_email.InvalidEmailAddress:
        raise Exception("To suggest a Bounty edit, you must submit a valid email address")
    except HyperMaker.UnrecognizedMaker:
        raise Exception('To suggest a Bounty edit, you must be a registered maker. <a href="https://www.bountyboard.makurspace.com/maker_registration.html">Consider registering here</a>')

    changeMap = json.loads(bounty_edit.pop("changed"))
    editted_bounty = HyperBounty(**{**asdict(bounty), **bounty_edit,
                                    "Id": bounty.Id,
                                    "Benefactor": bounty.Benefactor,
                                    "Contact": bounty.Contact})

    for attr in changeMap:
        print(f"Updating {attr}")
        setattr(bounty, attr, getattr(editted_bounty, attr))

    send_edit_to_editor(bounty, bounty.Name, editMaker)
    return 200, f"Edit form submission received! Expect an email at <b>{editMaker.sanitized_maker_email}</b> to confirm the submission"


def send_edit_to_editor(new_bounty, old_bounty_name, editMaker):
    email_template = get_html_template("bounty_editor_email_template.html")

    new_bounty_map = asdict(new_bounty)
    new_bounty_map['ReferenceMaterial'] = new_bounty.ReferenceMaterialHTML

    for key, value in {
            **new_bounty_map,
            **{"BountyName": new_bounty.Name, "BountyDescription": new_bounty.Description}}.items():
        email_template = email_template.replace(f"{{{key}}}", f"{value}")
    email_template = email_template.replace("{OldBountyName}", old_bounty_name)

    bounty_edit_id = str(uuid4())
    murd.update([
        {mddb.group_key: "bounty_edit_submission",
         mddb.sort_key: bounty_edit_id,
         "BountyId": new_bounty.Id,
         "CreationTime": datetime.utcnow().isoformat(),
         "Editor": editMaker.Id,
         "EdittedBounty": new_bounty.asm()}
    ])
    email_template = email_template.replace("{bounty_edit_id}", bounty_edit_id)
    email_template = email_template.replace("{BountyReward}", new_bounty.reward)

    ses.send_email(subject=f"Submit {new_bounty.Name} Bounty Suggested Edits?", sender="commissions@makurspace.com",
                   contact=editMaker.sanitized_maker_email, content=email_template)


@billboardPage
def submit_bounty_edits(event):
    bounty_edit_id = unquote_plus(event['pathParameters']['bounty_edit_id'])
    edit_ticket = murd.read_first(group="bounty_edit_submission", sort=bounty_edit_id)
    editted_bounty = HyperBounty.fromm(edit_ticket['EdittedBounty'])
    send_edit_to_benefactor(editted_bounty, edit_ticket['Editor'])
    return 200, "Bounty edits confirmed! Your suggested edits have been sent to the bounty's benefactor for review"


def send_edit_to_benefactor(new_bounty, editor):
    email_template = get_html_template("bounty_suggestion_email_template.html")
    editMaker = HyperMaker.retrieve(editor)

    bounty_edit_confirmation_id = str(uuid4())
    murd.update([
        {mddb.group_key: "bounty_edit_confirmation",
         mddb.sort_key: bounty_edit_confirmation_id,
         "BountyId": new_bounty.Id,
         "CreationTime": datetime.utcnow().isoformat(),
         "Editor": editMaker.Id,
         "EdittedBounty": new_bounty.asm()}
    ])

    new_bounty_map = asdict(new_bounty)
    new_bounty_map['ReferenceMaterial'] = new_bounty.ReferenceMaterialHTML

    for key, value in {
        **new_bounty_map,
        **{"bounty_edit_confirmation_id": bounty_edit_confirmation_id, "BountyReward": new_bounty.reward, "editor": editMaker.MakerName,
           "BountyName": new_bounty.Name, "BountyDescription": new_bounty.Description}
    }.items():
        email_template = email_template.replace(f"{{{key}}}", f"{value}")

    email_template = email_template.replace("{bounty_edit_confirmation_id}", bounty_edit_confirmation_id)
    email_template = email_template.replace("{BountyReward}", new_bounty.reward)
    email_template = email_template

    ses.send_email(subject=f"Accept {new_bounty.Name} Bounty Suggested Edits?", sender="commissions@makurspace.com",
                   contact=new_bounty.sanitized_contact_email, content=email_template)


def confirm_bounty_edits(event):
    bounty_edit_confirmation_id = unquote_plus(event['pathParameters']['bounty_edit_confirmation_id'])
    edit_ticket = murd.read_first(group="bounty_edit_confirmation", sort=bounty_edit_confirmation_id)
    editted_bounty = HyperBounty.fromm(edit_ticket['EdittedBounty'])
    editted_bounty.set()

    return 200, render_bounty(editted_bounty.Id).replace(
        f">{editted_bounty.Name}</h1>", f">Updated! - {editted_bounty.Name}</h1>")
