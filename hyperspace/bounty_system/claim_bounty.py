from urllib.parse import unquote_plus
from base64 import b64decode
import json

from requests_toolbelt.multipart import MultipartDecoder

from hyperspace.objects import Bounty
from hyperspace.utilities import get_html_template, get_javascript_template, get_form_name


def claim_bounty_form(event):
    """ Build Bounty claim form """
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = Bounty.get_bounty(bounty_id=bounty_id)
    upload_refmat_js = get_javascript_template("upload_reference_material.js").replace("{bounty_id}", bounty_id)
    form_template = get_html_template("claim_bounty_template.html").replace(
        "{upload_reference_material_js}", upload_refmat_js).replace("{bounty_name}", bounty.BountyName)
    return 200, form_template


def handle_bounty_claim(event):
    """ Accept bounty claim """
    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])
    claim = {}
    multipart_decoder = MultipartDecoder(content=form_data, content_type=content_type)
    for part in multipart_decoder.parts:
        form_name = get_form_name(part)
        assert form_name in ["CompletionNotes", "ReferenceMaterialNames", "BountyId"], \
            f"Unrecognized form name: {form_name}"
        if form_name == 'ReferenceMaterialNames':
            claim['FinalImages'] = json.loads(part.content)
        else:
            claim[form_name] = part.content.decode()

    bounty = Bounty.get_bounty(bounty_id=claim.pop("BountyId"))
    bounty.claim_bounty(**claim)

    response_template = get_html_template("bounty_claimed.html").replace(
        "{bounty_name}", bounty.BountyName)

    return 200, response_template
