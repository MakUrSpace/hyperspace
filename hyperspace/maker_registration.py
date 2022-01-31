from uuid import uuid4
from datetime import datetime
from base64 import b64decode
from dataclasses import asdict

from requests_toolbelt.multipart import MultipartDecoder

import hyperspace.ses as ses
from hyperspace.objects import mddb, murd, HyperMaker
from hyperspace.utilities import get_form_name, get_html_template


def send_confirmation_to_maker(maker):
    email_template = get_html_template("maker_registration_response_email_template.html")

    for key, value in asdict(maker).items():
        email_template = email_template.replace(f"{{{key}}}", f"{value}")

    email_template = email_template.replace("{maker_name}", maker.MakerName)
    email_template = email_template.replace("{maker_id}", maker.MakerId)

    murd.update([
        maker.asm(),
        {mddb.group_key: "maker_registrations",
         mddb.sort_key: maker.MakerId,
         **asdict(maker),
         "CreationTime": datetime.utcnow().isoformat()}
    ])

    ses.send_email(subject=f"MakUrSpace Maker Registration", sender="commissions@makurspace.com",
                   contact=maker.sanitized_maker_email, content=email_template)


def submit_maker_registration(event):
    new_maker_defn = {}

    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    multipart_decoder = MultipartDecoder(content=form_data, content_type=content_type)
    for part in multipart_decoder.parts:
        form_name = get_form_name(part)
        content = part.content.decode()
        if form_name == 'ConfirmedContract':
            content = content == 'on'
        new_maker_defn[form_name] = content

    maker = HyperMaker(**new_maker_defn, Id=str(uuid4()))
    send_confirmation_to_maker(maker)

    response_template = get_html_template("maker_registration_response_template.html")
    response_template = response_template.replace("{maker_email}", maker.MakerEmail)
    return 200, response_template


def confirm_maker_registration(event):
    maker_id = event['pathParameters']['maker_id']
    try:
        maker_registration = murd.read_first(group="maker_registrations", sort=maker_id)
    except Exception:
        return 404

    maker = HyperMaker.fromm(maker_registration)
    maker.store()
    murd.delete([maker_registration])
    confirmation_template = get_html_template("confirm_maker_registration_template.html")
    confirmation_template = confirmation_template.replace("{maker_id}", maker.MakerId)
    return 200, confirmation_template
