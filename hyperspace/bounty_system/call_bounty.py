from datetime import datetime
from urllib.parse import unquote_plus
from uuid import uuid4
from base64 import b64decode

from requests_toolbelt.multipart import MultipartDecoder

import hyperspace.ses as ses
from hyperspace.murd import mddb, murd
from hyperspace.utilities import get_html_template, get_form_name
from hyperspace.objects import Bounty, Maker


def get_call_bounty_form(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = Bounty.get_bounty(bounty_id)
    form_template = get_html_template("call_bounty_form.html")

    for pattern, replacement in {
            "{bounty_name}": bounty.BountyName,
            "{bounty_id}": bounty.BountyId}.items():
        form_template = form_template.replace(pattern, replacement)

    return 200, form_template


def receive_call_bounty(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = Bounty.get_bounty(bounty_id)
    maker_contact = {}

    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    multipart_decoder = MultipartDecoder(content=form_data, content_type=content_type)
    for part in multipart_decoder.parts:
        form_name = get_form_name(part)
        maker_contact[form_name] = part.content.decode()

    # Discover maker
    try:
        maker = Maker.retrieve(maker_contact['maker_email'])
    except KeyError:
        # TODO: email potential new maker (create maker application)
        raise Exception("Unable to process unregistered maker")

    bounty.MakerEmail = maker.MakerEmail
    confirmation_id = str(uuid4())
    email_template = get_html_template("call_bounty_email.html")

    for pattern, replacement in {
            "{bounty_name}": bounty.BountyName,
            "{call_confirmation_id}": confirmation_id,
            "{bounty_reward}": bounty.reward,
            "{bounty_description}": bounty.BountyDescription,
            "{maker_email}": bounty.sanitized_maker_email,
            "{maker_name}": maker_contact['maker_name']}.items():
        email_template = email_template.replace(pattern, replacement)

    murd.update([
        {mddb.group_key: "bounty_call_confirmations",
         mddb.sort_key: confirmation_id,
         "BountyId": bounty.BountyId,
         "MakerEmail": bounty.sanitized_maker_email,
         "MakerName": maker_contact["maker_name"],
         "CreationTime": datetime.utcnow().isoformat()}
    ])
    ses.send_email(subject=f'So, you wanna make "{bounty.BountyName}"?', sender="commissions@makurspace.com",
                   contact=bounty.sanitized_maker_email, content=email_template)
    call_confirmation_email_sent = get_html_template("call_confirmation_email_sent.html")
    return 200, call_confirmation_email_sent


def confirm_call_bounty(event):
    confirmation_id = event['pathParameters']['call_confirmation_id']
    confirmationm = murd.read_first(group="bounty_call_confirmations", sort=confirmation_id)
    bounty = Bounty.get_bounty(confirmationm['BountyId'])
    bounty.MakerName = confirmationm['MakerName']
    bounty.MakerEmail = confirmationm['MakerEmail']
    bounty.change_state(target_state="called", from_state="confirmed")

    called_bounty_confirmation = get_html_template("called_confirmation.html").replace("{bounty_name}", bounty.BountyName)

    return 200, called_bounty_confirmation
