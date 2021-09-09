from urllib.parse import unquote_plus
from base64 import b64decode

from requests_toolbelt.multipart import MultipartDecoder

from hyperspace.utilities import get_html_template, get_javascript_template, get_form_name
from hyperspace.objects import Bounty


def get_edit_bounty_form(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = Bounty.get_bounty(bounty_id)
    form_template = get_html_template("edit_bounty_form.html")
    script_template = get_javascript_template("upload_reference_material.js")
    script_template.replace("{bounty_id}", bounty_id)

    for pattern, replacement in {
            "{bounty_id}": bounty.BountyId,
            "{bounty_name}": bounty.BountyName,
            "{bounty_reward}": bounty.reward,
            "{bounty_description}": bounty.BountyDescription,
            "{upload_reference_material_script}": script_template}.items():
        form_template = form_template.replace(pattern, replacement)

    return 200, form_template


def receive_bounty_edit(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = Bounty.get_bounty(bounty_id)
    bounty_edit = {}

    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    multipart_decoder = MultipartDecoder(content=form_data, content_type=content_type)
    for part in multipart_decoder.parts:
        form_name = get_form_name(part)
        bounty_edit[form_name] = part.content.decode()

    bounty.BountyName = bounty_edit['BountyName']
    # murd.update([bounty.asm()])
    return 200, ""
