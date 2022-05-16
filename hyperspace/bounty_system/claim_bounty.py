from urllib.parse import unquote_plus
from base64 import b64decode

from hyperspace.objects import HyperBounty
from hyperspace.utilities import get_html_template, get_javascript_template, process_multipart_form_submission


def claim_bounty_form(event):
    """ Build Bounty claim form """
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = HyperBounty.retrieve(bounty_id)
    upload_refmat_js = get_javascript_template("upload_reference_material.js").replace("{bounty_id}", bounty_id)
    form_template = get_html_template("claim_bounty_template.html").replace(
        "{upload_reference_material_js}", upload_refmat_js).replace("{bounty_name}", bounty.Name)
    return 200, form_template


def handle_bounty_claim(event):
    """ Accept bounty claim """
    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    claim = process_multipart_form_submission(form_data, content_type)
    claim["FinalImages"] = claim.pop("ReferenceMaterial")

    bounty = HyperBounty.retrieve(claim.pop("BountyId"))
    bounty.claim_bounty(**claim)

    response_template = get_html_template("bounty_claimed.html").replace(
        "{bounty_name}", bounty.Name).replace(
        "{bounty_amount}", bounty.reward)

    return 200, response_template
