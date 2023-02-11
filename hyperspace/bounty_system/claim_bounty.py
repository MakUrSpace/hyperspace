from urllib.parse import unquote_plus
from base64 import b64decode
import json
from uuid import uuid4
from datetime import datetime

from hyperspace.objects import HyperBounty, HyperMaker
import hyperspace.ses as ses
from hyperspace.murd import mddb, murd
from hyperspace.utilities import get_html_template, get_javascript_template, process_multipart_form_submission, billboardPage


def claim_bounty_form(event):
    """ Build Bounty claim form """
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = HyperBounty.retrieve(bounty_id)
    upload_refmat_js = get_javascript_template("upload_reference_material.js").replace("{bounty_id}", bounty_id)
    form_template = get_html_template("claim_bounty_template.html").replace(
        "{upload_reference_material_js}", upload_refmat_js).replace(
        "{bounty_name}", bounty.Name).replace(
        "{reference_material}", "[]")
    return 200, form_template


@billboardPage
def handle_bounty_claim(event):
    """ Accept bounty claim """
    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    claim = process_multipart_form_submission(form_data, content_type)
    claim["FinalImages"] = claim.pop("ReferenceMaterial")
    maker = HyperMaker.retrieveByEmail(claim.pop("MakerEmail"))
    bounty = HyperBounty.retrieve(claim.pop("BountyId"))
    bounty.FinalImages = claim["FinalImages"]
    print(f"Bounty has {len(bounty.FinalImages)} final images")

    confirmation_id = str(uuid4())

    email_template = get_html_template("claim_bounty_email.html")

    for pattern, replacement in {
            "{bounty_name}": bounty.Name,
            "{maker_email}": bounty.sanitized_maker_email,
            "{maker_name}": maker.MakerName,
            "{claim_confirmation_id}": confirmation_id,
            "{completion_notes}": claim["CompletionNotes"],
            "{product_images}": bounty.FinalImagesHTML}.items():
        email_template = email_template.replace(pattern, replacement)

    bounty.set()
    murd.update([
        {mddb.group_key: "bounty_claim_confirmations",
         mddb.sort_key: confirmation_id,
         "BountyId": bounty.Id,
         "MakerEmail": bounty.sanitized_maker_email,
         "Claim": json.dumps({
                k: v for k, v in claim.items()
                if k in ["CompletionNotes", "FinalImages"]}),
         "CreationTime": datetime.utcnow().isoformat()}
    ])
    ses.send_email(subject=f'How\'s this for "{bounty.Name}"?',
                   sender="commissions@makurspace.com",
                   contact=bounty.sanitized_contact_email,
                   content=email_template)
    return 200, "Bounty claim submitted! The bounty's benefactor will be contacted for approval, " \
        + "after which the bounty's product will be collected. Finally, the bounty award will be disbursed to you!"


@billboardPage
def claim_bounty(event):
    confirmation_id = event['pathParameters']['claim_confirmation_id']
    claim_confirmation = murd.read_first(group="bounty_claim_confirmations", sort=confirmation_id)
    claim = json.loads(claim_confirmation["Claim"])
    bounty = HyperBounty.retrieve(claim_confirmation["BountyId"])
    bounty.claim_bounty(**claim)

    return 200, f"""
<h3>You approved {bounty.Name}!</h3><br>
<h4>Congratulations on your bounty being fulfilled! The bounty's product will be collected from the maker and delivered to you.
Please contact commissions@makurspace.com with any questions or concerns</h4>
"""
