from time import sleep
import json
from dataclasses import dataclass, asdict
from urllib.parse import unquote_plus
from base64 import b64decode
from typing import ClassVar

from LambdaPage import LambdaPage
from murdaws import murd_ddb as mddb
from requests_toolbelt.multipart import MultipartDecoder
import s3
import ses


mddb.ddb_murd_prefix = "musbb_murd_"
try:
    murd = mddb.DDBMurd("BountyBoard")
except Exception:
    mddb.DDBMurd.create_murd_table("BountyBoard")
    sleep(10)
    murd = mddb.DDBMurd("BountyBoard")


@dataclass
class Bounty:
    Bounty: str
    BountyName: str
    Benefactor: str
    Contact: str
    BountyDescription: str
    ReferenceMaterial: list
    TemplateProject: str
    RequestedMaker: str = ""
    State: str = "submitted"
    states: ClassVar = ["submitted", "confirmed", "called", "claimed"]

    @classmethod
    def from_m(cls, m):
        bounty = cls(**{k: v for k, v in m.items() if k not in [mddb.group_key, mddb.sort_key]})
        return bounty

    def asdict(self):
        return asdict(self)


def bounty_exists(bounty):
    for group in Bounty.states:
        if murd.read(group=group, sort=bounty.BountyName):
            return group


def get_bounty_board(event):
    bounties = murd.read(group="confirmed", limit=200)
    return 200, [Bounty.from_m(bounty).asdict() for bounty in bounties]


def get_bounty(bounty_name):
    return Bounty.from_m(murd.read(group="bounty", sort=bounty_name)[0])


def handle_get_bounty(event):
    bounty_name = unquote_plus(event['pathParameters']['bounty_name'])
    return 200, get_bounty(bounty_name).asdict()

    return False


def write_bounty(new_bounty, group="confirmed"):
    # Update server data
    if bounty_exists(new_bounty):
        print(f"Bounty {new_bounty.BountyName} already exists")
        return False

    murd.update([{**{mddb.group_key: group,
                     mddb.sort_key: new_bounty.BountyName},
                  **new_bounty.asdict()}])
    # TODO: read back after write to test for success
    recovered_bounty = Bounty.from_m(murd.read_first(group=group, sort=new_bounty.BountyName))
    if recovered_bounty == new_bounty:
        return True
    else:
        print("Recovered bounty does not match intended value")
        print(recovered_bounty)
        print(new_bounty)
        return False


def get_form_name(part):
    defn = part.headers[b'Content-Disposition'].decode()
    return defn[defn.find(" name="):].split(";")[0].split("=")[1].replace('"', '')


def get_refmat_filename(part):
    defn = part.headers[b'Content-Disposition'].decode()
    return defn[defn.find(" filename="):].split(";")[0].split("=")[1].replace('"', '')


def write_refmat_to_s3(bounty_name, refmat_name, refmat_content):
    s3_path = f"bountyboard/{bounty_name}/{refmat_name}"
    s3.write(s3_path, refmat_content)


bounty_name_map = {
    "bounty_amount": "Bounty",
    "bounty_name": "BountyName",
    "benefactor": "Benefactor",
    "benefactor_contact": "Contact",
    "template_project": "TemplateProject",
    "bounty_description": "BountyDescription",
    "reference_material": "ReferenceMaterial",
}


def send_bounty_to_contact(new_bounty):
    with open("email_template.html") as fh:
        email_template = fh.read()

    for key, value in new_bounty.asdict().items():
        email_template = email_template.replace(f"{{{key}}}", f"{value}")

    ses.send_email(subject=f"{new_bounty.BountyName} Bounty", sender="commissions@makurspace.com",
                   contact="hello@makurspace.com", content=email_template)


def submit_bounty_form(event):
    new_bounty_defn = {}
    refmat_material = {}

    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    multipart_decoder = MultipartDecoder(content=form_data, content_type=content_type)
    for part in multipart_decoder.parts:
        form_name = get_form_name(part)
        form_name = form_name if form_name not in bounty_name_map else bounty_name_map[form_name]
        if form_name == 'ReferenceMaterial':
            filename = get_refmat_filename(part)
            new_bounty_defn['ReferenceMaterial'] = [filename]
            refmat_material[filename] = b64decode(part.content)
        else:
            new_bounty_defn[form_name] = part.content.decode()

    try:
        new_bounty = Bounty(**new_bounty_defn)
        if not write_bounty(new_bounty, group="submitted"):
            return 403, "Failed to submit bounty"
        for refmat, refmat_content in refmat_material.items():
            write_refmat_to_s3(new_bounty.BountyName, refmat, refmat_content)
    except:
        print("Deleting bounty")
        murd.delete([{mddb.group_key: "submitted", mddb.sort_key: new_bounty.BountyName, **new_bounty_defn}])
        raise

    send_bounty_to_contact(new_bounty)

    with open("bounty_submission_response_template.html", "r") as fh:
        response_template = fh.read().replace("{benefactor_email}", new_bounty.Contact)
    return 200, response_template


def return_index(event):
    return 200, open("../frontend/index.html", "r").read()


def build_page():
    page = LambdaPage()
    page.add_endpoint(method="post", path="/rest/bounty_form", func=submit_bounty_form, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/bountyboard/{bounty_name}", func=handle_get_bounty)
    page.add_endpoint(method="get", path="/rest/bountyboard", func=get_bounty_board)
    page.add_endpoint(method="get", path="/", content_type="text/html", func=return_index)
    return page


def lambda_handler(event, context):
    print(f"Handling event: {str(event)[:500]}")
    s3.write("last_request.json", json.dumps(event).encode())
    page = build_page()
    results = page.handle_request(event)
    print(results['statusCode'])
    return results


if __name__ == "__main__":
    page = build_page()
    page.start_local()
