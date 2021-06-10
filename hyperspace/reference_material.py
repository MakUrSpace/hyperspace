from uuid import uuid4
import hyperspace.s3 as s3
from hyperspace.utilities import get_javascript_template


def write_refmat_to_s3(bounty_name, refmat_name, refmat_content):
    s3_path = f"bountyboard/{bounty_name}/{refmat_name}"
    s3.write_in_public(s3_path, refmat_content)


def get_refmat_surl(event):
    bounty_id = event['pathParameters']['bounty_id']
    refmat_filename = event['pathParameters']['refmat_filename']
    s3_path = f"bountyboard/{bounty_id}/{refmat_filename}"
    # TODO: assert path doesn't exist
    return 200, s3.presigned_write_url(s3_path)


def render_refmat_upload_script(event):
    script_template = get_javascript_template("upload_reference_material.js")
    return 200, script_template.replace("{bounty_id}", str(uuid4()))
