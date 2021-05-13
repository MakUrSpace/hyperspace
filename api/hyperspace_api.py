from time import sleep
from uuid import uuid4
import json
from dataclasses import dataclass, asdict
from urllib.parse import unquote_plus
from base64 import b64decode
from typing import ClassVar
from datetime import datetime

from LambdaPage import LambdaPage
from murdaws import murd_ddb as mddb
from requests_toolbelt.multipart import MultipartDecoder
import s3
import ses


mddb.ddb_murd_prefix = "musbb_murd_"
try:
    murd = mddb.DDBMurd("BountyBoard")
    purchase_murd = mddb.DDBMurd("purchases")
except Exception:
    mddb.DDBMurd.create_murd_table("BountyBoard")
    mddb.DDBMurd.create_murd_table("purchases")
    sleep(10)
    murd = mddb.DDBMurd("BountyBoard")
    purchase_murd = mddb.DDBMurd("purchases")


@dataclass
class Bounty:
    BountyId: str
    Bounty: str
    BountyName: str
    Benefactor: str
    Contact: str
    BountyDescription: str
    ReferenceMaterial: list
    ConfirmationId: str = ""
    State: str = "submitted"
    states: ClassVar = ["submitted", "confirmed", "called", "claimed"]

    @classmethod
    def fromm(cls, m):
        kwargs = {k: v for k, v in m.items() if k not in [mddb.group_key, mddb.sort_key, "CREATE_TIME"]}
        kwargs['BountyId'] = kwargs['BountyName'] if 'BountyId' not in m else kwargs['BountyId']
        bounty = cls(**kwargs)
        return bounty

    def asm(self):
        return {**{mddb.group_key: self.State,
                   mddb.sort_key: self.BountyId,
                   "CREATE_TIME": datetime.utcnow().isoformat()},
                **self.asdict()}

    def asdict(self):
        return asdict(self)

    def store(self):
        murd.update([self.asm()])

    @property
    def primary_image(self):
        formats = ["jpg", "jpeg", "png"]
        for refmat in self.ReferenceMaterial:
            filetype = refmat.split(".")[-1]
            if filetype in formats:
                return refmat
        return None


def bounty_exists(bounty, all_states=False):
    check_states = [bounty.State] if not all_states else Bounty.states[::-1]
    for state in check_states:
        if murd.read(group=state, sort=bounty.BountyName):
            return state


def get_bounty_board(event):
    bounties = murd.read(group="confirmed", limit=200)
    return 200, [Bounty.fromm(bounty).asdict() for bounty in bounties]


def get_bounty(bounty_id):
    for state in Bounty.states[::-1]:
        try:
            return Bounty.fromm(murd.read(group=state, sort=bounty_id)[0])
        except Exception:
            pass
    raise Exception(f"{bounty_id} not found")


def handle_get_bounty(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    return 200, get_bounty(bounty_id).asdict()

    return False


def get_rendered_bounty(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = get_bounty(bounty_id)

    with open("bountycard.html", "r") as fh:
        template = fh.read()

    for pattern, replacement in {
            "{bounty_name}": bounty.BountyName,
            "{primary_image}": f"/bountyboard/{bounty.BountyName}/{bounty.primary_image}",
            "{bounty_description}": bounty.BountyDescription}.items():
        template = template.replace(pattern, replacement)

    return 200, template


def get_form_name(part):
    defn = part.headers[b'Content-Disposition'].decode()
    return defn[defn.find(" name="):].split(";")[0].split("=")[1].replace('"', '')


def get_refmat_filename(part):
    defn = part.headers[b'Content-Disposition'].decode()
    return defn[defn.find(" filename="):].split(";")[0].split("=")[1].replace('"', '')


def write_refmat_to_s3(bounty_name, refmat_name, refmat_content):
    s3_path = f"bountyboard/{bounty_name}/{refmat_name}"
    s3.write_in_public(s3_path, refmat_content)


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

    confirmation_id = str(uuid4())
    email_template = email_template.replace("{bounty_confirmation_id}", confirmation_id)

    new_bounty.ConfirmationId = confirmation_id
    murd.update([
        new_bounty.asm(),
        {mddb.group_key: "confirmations",
         mddb.sort_key: confirmation_id,
         "BountyName": new_bounty.BountyName}
    ])

    ses.send_email(subject=f"{new_bounty.BountyName} Bounty", sender="commissions@makurspace.com",
                   contact="hello@makurspace.com", content=email_template)


def submit_bounty_form(event):
    s3.write(f"submissions/sub-{uuid4()}", json.dumps(event).encode(), "makurspace")
    new_bounty_defn = {}
    refmat_material = {}

    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    multipart_decoder = MultipartDecoder(content=form_data, content_type=content_type)
    for part in multipart_decoder.parts:
        form_name = get_form_name(part)
        form_name = form_name if form_name not in bounty_name_map else bounty_name_map[form_name]
        assert form_name != 'State'
        if form_name == 'ReferenceMaterialNames':
            new_bounty_defn['ReferenceMaterial'] = json.loads(part.content)
        else:
            new_bounty_defn[form_name] = part.content.decode()

    new_bounty = Bounty(**new_bounty_defn, BountyId=str(uuid4()))
    try:
        new_bounty.store()
        for refmat, refmat_content in refmat_material.items():
            write_refmat_to_s3(new_bounty.BountyName, refmat, refmat_content)
    except Exception:
        print("Deleting bounty")
        murd.delete([new_bounty.asm()])
        return 403, "Failed to submit bounty"

    send_bounty_to_contact(new_bounty)

    with open("bounty_submission_response_template.html", "r") as fh:
        response_template = fh.read().replace("{benefactor_email}", new_bounty.Contact)
    return 200, response_template


def confirm_bounty(event):
    confirmation_id = event['pathParameters']['bounty_confirmation_id']
    confirmationm = murd.read_first(group="confirmations", sort=confirmation_id)
    get_bounty(confirmationm['BountyName'])
    with open("confirm_bounty.html", "r") as fh:
        confirmation_template = fh.read()
    confirmation_template = confirmation_template.replace("{bounty_confirmation_id}", confirmation_id)
    return 200, confirmation_template


@dataclass
class PurchaseConfirmation:
    create_time: str
    update_time: str
    id: str
    intent: str
    status: str
    payer: dict
    purchase_units: list
    links: list

    def asm(self):
        return {**{mddb.group_key: "purchase_confirmation",
                   mddb.sort_key: self.id},
                **self.asdict()}

    @classmethod
    def fromm(cls, m):
        bounty = cls(**{k: v for k, v in m.items() if k not in [mddb.group_key, mddb.sort_key]})
        return bounty

    def asdict(self):
        return asdict(self)

    def store(self):
        purchase_murd.update([self.asm()])


def bounty_confirmed(event):
    confirmation_id = event['pathParameters']['bounty_confirmation_id']
    confirmationm = murd.read_first(group="confirmations", sort=confirmation_id)
    bounty = get_bounty(confirmationm['BountyName'])
    purchase_confirmation = PurchaseConfirmation(**json.loads(event['body']))
    purchase_confirmation.store()
    bounty.State = "confirmed"
    bounty.store()


def get_refmat_surl(event):
    bounty_id = event['pathParameters']['bounty_id']
    refmat_filename = event['pathParameters']['refmat_filename']
    s3_path = f"bountyboard/{bounty_id}/{refmat_filename}"
    # TODO: assert path doesn't exist
    return 200, s3.presigned_write_url(s3_path)


def render_refmat_upload_script(event):
    return 200, """
var refmat = document.getElementById('ReferenceMaterial')

function updateList(){
    var output = document.getElementById('reference_material_file_list')
    var children = "";
    for (var i = 0; i < refmat.files.length; ++i) {
        children += '<li>' + refmat.files.item(i).name + '</li>'
    }
    if (refmat.files.length > 1) {
      output.innerHTML = '<ul>'+children+'</ul>';
    } else {
      output.innerHTML = ''
    }
}

function upload_reference_material(){
  updateList()
  var refmat = document.getElementById('ReferenceMaterial')
  var refmat_by_name = {}
  $(refmat.files).each(function(i, elem){
    refmat_by_name[elem.name] = elem
  })

  var file_names = []
  for (var file_index = 0; file_index < refmat.files.length; file_index++){
    file_names.push(refmat.files[file_index].name)
    $.ajax({
        url : `/rest/bounty_form/{bounty_id}/${refmat.files[file_index].name}`,
        type : "GET",
        mimeType : "multipart/form-data",
        cache : false,
        contentType : false,
        processData : false
      }).done(function(response){
        response = JSON.parse(response)
        var url = response['url']
        var filename = response['key'].split("/").pop()

        var file_data = new FormData()
        for (var form_key in response){
            if (form_key !== 'url'){
                file_data.set(form_key, response[form_key])
            }
        }
        file_data.set("ACL", "public-read")
        file_data.set("file", refmat_by_name[filename], filename)

        $.ajax({
            url : url,
            type : "POST",
            data : file_data,
            mimeType : "multipart/form-data",
            cache : false,
            contentType : false,
            processData : false
          }).done(function(response){
            console.log(response)
          })
        })
    }
  document.getElementById('ReferenceMaterialNames').value = JSON.stringify(file_names)
}
""".replace("{bounty_id}", str(uuid4()))


def rendered_bountyboard(event):
    with open("bountyboard.html", "r") as f:
        bountyboard_template = f.read()
    return 200, bountyboard_template


def build_page():
    page = LambdaPage()
    page.add_endpoint(method="get", path="/rest/upload_reference_material.js", func=render_refmat_upload_script, content_type="text/javascript")
    page.add_endpoint(method="get", path="/rest/bounty_form/{bounty_id}/{refmat_filename}", func=get_refmat_surl)
    page.add_endpoint(method="post", path="/rest/bounty_form", func=submit_bounty_form, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/bounty_confirmation/{bounty_confirmation_id}", func=confirm_bounty, content_type="text/html")
    page.add_endpoint(method="post", path="/rest/bounty_confirmation/{bounty_confirmation_id}", func=bounty_confirmed, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/bountyboard/{bounty_id}", func=handle_get_bounty)
    page.add_endpoint(method="get", path="/rest/rendered_bountyboard", func=rendered_bountyboard, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/rendered_bounty/{bounty_id}", func=get_rendered_bounty, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/bountyboard", func=get_bounty_board)
    return page


def lambda_handler(event, context):
    print(f"Handling {event['path']} + {event['httpMethod']}")
    page = build_page()
    results = page.handle_request(event)
    print(results['statusCode'])
    return results


if __name__ == "__main__":
    page = build_page()
    page.start_local()
