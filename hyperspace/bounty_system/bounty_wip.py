from urllib.parse import unquote_plus
from base64 import b64decode
import json

from requests_toolbelt.multipart import MultipartDecoder

from hyperspace.objects import Bounty
from hyperspace.utilities import get_html_template, get_javascript_template, get_form_name
from hyperspace import ses


SECONDS_IN_3_DAYS = 60 * 60 * 24 * 3


def bounties_in_need_of_wip(bounties=None):
    """ Returns bounties called 3 days or more ago or that last updated their WIP 3 or more days ago """
    if bounties is None:
        bounties = Bounty.get_bounties(group="called")
    return [
        bounty for bounty in bounties
        if bounty.time_since("called") > SECONDS_IN_3_DAYS or (
            bounty.get_stamp("wip") is not None and bounty.time_since("wip") > SECONDS_IN_3_DAYS
        )
    ]


def email_wips(bounties):
    for bounty in bounties:
        wip_email_template = get_html_template("wip_email_template.html")

        for pattern, replacement in {
            "{maker_name}": bounty.MakerName,
            "{bounty_name}": bounty.BountyName,
            "{bounty_id}": bounty.BountyId
        }.items():
            wip_email_template = wip_email_template.replace(pattern, replacement)

        ses.send_email(subject=f'MakUrSpace WIP Request', sender="commissions@makurspace.com",
                       contact=bounty.sanitized_maker_email, content=wip_email_template)


def wip_submission_form(event):
    """ Build WIP submission form """
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    upload_refmat_js = get_javascript_template("upload_reference_material.js").replace("{bounty_id}", bounty_id)
    form_template = get_html_template("wip_submission_template.html").replace("{upload_reference_material_js}", upload_refmat_js)
    return 200, form_template


def handle_wip_submission(event):
    """ Accept submission from WIP form """
    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])
    wip_submission = {}
    multipart_decoder = MultipartDecoder(content=form_data, content_type=content_type)
    for part in multipart_decoder.parts:
        form_name = get_form_name(part)
        assert form_name in ["PercentageDone", "WorkCompleted", "ReferenceMaterialNames", "BountyId"], \
            f"Unrecognized form name: {form_name}"
        if form_name == 'ReferenceMaterialNames':
            wip_submission['ReferenceMaterial'] = json.loads(part.content)
        else:
            wip_submission[form_name] = part.content.decode()

    bounty = Bounty.get_bounty(bounty_id=wip_submission.pop("BountyId"))
    bounty.wip_bounty(**wip_submission)

    response_template = get_html_template("bounty_wipped.html").replace(
        "{bounty_name}", bounty.BountyName)

    return 200, response_template
