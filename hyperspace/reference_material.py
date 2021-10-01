from uuid import uuid4
from hyperspace import s3
from hyperspace.utilities import get_javascript_template


def s3_path(**kwargs):
    return "bountyboard/{bounty_id}/{refmat_filename}".format(**kwargs)


def get_refmat_surl(event):
    bounty_id = event['pathParameters']['bounty_id']
    refmat_filename = event['pathParameters']['refmat_filename']
    # TODO: assert path doesn't exist in purgatory or static assets
    file_path = s3_path(bounty_id=bounty_id, refmat_filename=refmat_filename)
    return 200, s3.presigned_write_url(file_path)


def render_refmat_upload_script(event):
    script_template = get_javascript_template("upload_reference_material.js")
    script_template += """

window.addEventListener('load', function() {
    console.log('All assets are loaded')
    document.getElementById('BountyId').value = "{bounty_id}"
    return true
})
"""
    return 200, script_template.replace("{bounty_id}", str(uuid4()))
