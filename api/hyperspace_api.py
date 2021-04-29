from time import sleep
import json
from dataclasses import dataclass
from urllib.parse import unquote_plus
from base64 import b64decode

from LambdaPage import LambdaPage
from murdaws import murd_ddb as mddb
from requests_toolbelt.multipart import MultipartDecoder
import s3


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
    TemplateProject: str
    BountyDescription: str
    ReferenceMaterial: list

    def to_dict(self):
        return {key: attr if isinstance((attr := getattr(self, key)), str) else json.dumps(attr)
                for key in self.__annotations__}

    @classmethod
    def from_m(cls, m):
        bounty = cls(**{k: v for k, v in m.items() if k not in [mddb.group_key, mddb.sort_key]})
        bounty.ReferenceMaterial = json.loads(bounty.ReferenceMaterial)
        return bounty


def get_bounty_board(event):
    bounties = murd.read(group="bounty", limit=200)
    return 200, [Bounty.from_m(bounty).to_dict() for bounty in bounties]


def get_bounty(bounty_name):
    return Bounty.from_m(murd.read(group="bounty", sort=bounty_name)[0])


def handle_get_bounty(event):
    bounty_name = unquote_plus(event['pathParameters']['bounty_name'])
    return 200, get_bounty(bounty_name).to_dict()


def write_bounty(new_bounty):
    # Update server data
    try:
        get_bounty(new_bounty.BountyName)
        print(f"Bounty {new_bounty.BountyName} already exists")
        return False
    except IndexError:
        pass

    murd.update([{**{mddb.group_key: "bounty",
                     mddb.sort_key: new_bounty.BountyName},
                  **new_bounty.to_dict()}])
    # TODO: read back after write to test for success
    recovered_bounty = Bounty.from_m(murd.read_first(group="bounty", sort=new_bounty.BountyName))
    if recovered_bounty == new_bounty:
        return True
    else:
        print("Recovered bounty does not match intended value")
        print(recovered_bounty)
        print(new_bounty)
        return False


def handle_new_bounty(event):
    bounty_defn = Bounty(**json.loads(event['body']))
    return 200 if write_bounty(bounty_defn) else 503


def serve_bounty_submission(event):
    return 200, """
<head>
  <title>MakUrSpace Project Submission</title>
</head>

<body>
  Here's the form
  <form enctype="multipart/form-data" action="/rest/bounty_form" method="post">
    Bounty: <input type="float" name="Bounty"><br>
    Bounty Name: <input type="text" name="BountyName"><br>
    Benefactor: <input type="text" name="Benefactor"><br>
    Contact at: <input type="text" name="Contact"><br>
    Template Project: <input type="text" name="TemplateProject"><br>
    Bounty Description: <textarea rows="5" cols="50" name="BountyDescription"></textarea><br>
    Reference Material: <input type="file" name="ReferenceMaterial" multiple><br>
    <input type="submit"><br>
</body>
"""


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

    new_bounty = Bounty(**new_bounty_defn)
    if not write_bounty(new_bounty):
        return 503, 'Failed to create bounty'

    try:
        for refmat, refmat_content in refmat_material.items():
            write_refmat_to_s3(new_bounty.BountyName, refmat, refmat_content)
    except:
        print("Deleting bounty")
        murd.delete([{mddb.group_key: "bounty", mddb.sort_key: new_bounty.BountyName, **new_bounty_defn}])
        raise
    print(murd.read(group="bounty", sort=new_bounty.BountyName))

    return 200, ''


def build_page():
    page = LambdaPage()
    page.add_endpoint(method="get", path="/rest/bounty_form", func=serve_bounty_submission, content_type="text/html")
    page.add_endpoint(method="post", path="/rest/bounty_form", func=submit_bounty_form)
    page.add_endpoint(method="post", path="/rest/bountyboard", func=handle_new_bounty)
    page.add_endpoint(method="get", path="/rest/bountyboard/{bounty_name}", func=handle_get_bounty)
    page.add_endpoint(method="get", path="/rest/bountyboard", func=get_bounty_board)
    return page


def lambda_handler(event, context):
    print(f"Handling event: {str(event)}")
    page = build_page()
    results = page.handle_request(event)
    print(results['statusCode'])
    return results


if __name__ == "__main__":
    page = build_page()
    page.start_local()
