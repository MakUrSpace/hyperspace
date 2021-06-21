from uuid import uuid4
from hyperspace import s3
from hyperspace.utilities import get_javascript_template


def s3_path(**kwargs):
    return "bountyboard/{bounty_id}/{refmat_filename}".format(**kwargs)


def write_refmat_to_s3(bounty_name, refmat_name, refmat_content):
    s3_path = f"bountyboard/{bounty_name}/{refmat_name}"
    s3.write_in_public(s3_path, refmat_content)


def get_refmat_surl(event):
    bounty_id = event['pathParameters']['bounty_id']
    refmat_filename = event['pathParameters']['refmat_filename']
    # TODO: assert path doesn't exist
    file_path = s3_path(bounty_id=bounty_id, refmat_filename=refmat_filename)
    return 200, s3.presigned_write_url(file_path, bucket="makurspace-purgatory")


def promote_out_of_purgatory(bounty_id, refmat_name):
    file_path = s3_path(bounty_id=bounty_id, refmat_filename=refmat_name)
    s3.copy(file_path, "makurspace-purgatory", s3.default_bucket)


def render_refmat_upload_script(event):
    script_template = get_javascript_template("upload_reference_material.js")
    return 200, script_template.replace("{bounty_id}", str(uuid4()))
