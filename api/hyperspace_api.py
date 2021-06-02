import re
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
murd = mddb.DDBMurd("BountyBoard")
purchase_murd = mddb.DDBMurd("purchases")


def provision_murd_tables():
    mddb.DDBMurd.create_murd_table("BountyBoard")
    mddb.DDBMurd.create_murd_table("purchases")
    sleep(10)
    murd = mddb.DDBMurd("BountyBoard")
    purchase_murd = mddb.DDBMurd("purchases")
    return murd, purchase_murd


def get_javascript_template(filename):
    with open(f"javascript_templates/{filename}", "r") as f:
        template = f.read()
    return template


def get_html_template(filename):
    with open(f"html_templates/{filename}", "r") as f:
        template = f.read()
    return template


email_regex_pattern = re.compile(r"""(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])""")


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
    MakerName: str = ""
    MakerEmail: str = ""
    State: str = "submitted"
    states: ClassVar = ["submitted", "confirmed", "called", "claimed"]

    @property
    def sanitized_reward(self):
        sanitized_reward = self.Bounty
        if sanitized_reward.startswith("$"):
            sanitized_reward = sanitized_reward[1:].strip()
        try:
            return float(sanitized_reward)
        except ValueError:
            return 9999.99

    @property
    def reward(self):
        return f"${self.sanitized_reward:.2f}"

    @property
    def sanitized_contact(self):
        regexed = email_regex_pattern.match(self.Contact)
        return regexed.string

    @property
    def sanitized_maker_email(self):
        regexed = email_regex_pattern.match(self.MakerEmail)
        return regexed.string

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

    def change_state(self, target_state):
        assert target_state in Bounty.states
        orig = self.asm()
        self.State = target_state
        self.store()
        murd.delete([orig])

    @property
    def primary_image(self):
        formats = ["jpg", "jpeg", "png"]
        for refmat in self.ReferenceMaterial:
            filetype = refmat.split(".")[-1]
            if filetype in formats:
                return refmat
        return None

    def image_path(self, image):
        return f"/bountyboard/{self.BountyId}/{image}"


def bounty_exists(bounty, all_states=False):
    check_states = [bounty.State] if not all_states else Bounty.states[::-1]
    for state in check_states:
        if murd.read(group=state, sort=bounty.BountyName):
            return state


def get_bounties(group="confirmed", limit=200):
    return [Bounty.fromm(b) for b in murd.read(group=group, limit=limit)]


def handle_get_bountyboard(event):
    return 200, [bounty.asdict() for bounty in get_bounties()]


def handle_get_bounties_in_progress(event):
    return 200, [bounty.asdict() for bounty in get_bounties(group="called")]


def handle_get_bounty_portfolio(event):
    return 200, [bounty.asdict() for bounty in get_bounties(group="claimed")]


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

    template = get_html_template("bountycard.html")

    for pattern, replacement in {
            "{bounty_name}": bounty.BountyName,
            "{bounty_id}": bounty.BountyId,
            "{bounty_reward}": bounty.reward,
            "{primary_image}": bounty.image_path(bounty.primary_image),
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
    email_template = get_html_template("bounty_creation_email_template.html")

    for key, value in new_bounty.asdict().items():
        email_template = email_template.replace(f"{{{key}}}", f"{value}")

    confirmation_id = str(uuid4())
    email_template = email_template.replace("{bounty_confirmation_id}", confirmation_id)
    email_template = email_template.replace("{BountyReward}", new_bounty.reward)

    new_bounty.ConfirmationId = confirmation_id
    murd.update([
        new_bounty.asm(),
        {mddb.group_key: "bounty_creation_confirmations",
         mddb.sort_key: confirmation_id,
         "BountyId": new_bounty.BountyId,
         "CreationTime": datetime.utcnow().isoformat()}
    ])

    ses.send_email(subject=f"{new_bounty.BountyName} Bounty", sender="commissions@makurspace.com",
                   contact=new_bounty.sanitized_contact, content=email_template)


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

    response_template = get_html_template("bounty_submission_response_template.html")
    response_template = response_template.replace("{benefactor_email}", new_bounty.Contact)
    return 200, response_template


def confirm_bounty_creation(event):
    confirmation_id = event['pathParameters']['bounty_confirmation_id']
    confirmationm = murd.read_first(group="bounty_creation_confirmations", sort=confirmation_id)
    get_bounty(confirmationm['BountyId'])
    confirmation_template = get_html_template("confirm_bounty.html")
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
    confirmationm = murd.read_first(group="bounty_creation_confirmations", sort=confirmation_id)
    bounty = get_bounty(confirmationm['BountyId'])
    purchase_confirmation = PurchaseConfirmation(**json.loads(event['body']))
    purchase_confirmation.store()
    murd.delete([bounty.asm(), confirmationm])
    bounty.change_state("confirmed")


def get_refmat_surl(event):
    bounty_id = event['pathParameters']['bounty_id']
    refmat_filename = event['pathParameters']['refmat_filename']
    s3_path = f"bountyboard/{bounty_id}/{refmat_filename}"
    # TODO: assert path doesn't exist
    return 200, s3.presigned_write_url(s3_path)


def render_refmat_upload_script(event):
    script_template = get_javascript_template("upload_reference_material.js")
    return 200, script_template.replace("{bounty_id}", str(uuid4()))


def render_bountyboard(group="confirmed", limit=200):
    bountyboard_template = get_html_template("bountyboard.html")
    bountyboard_card_template = get_html_template("bountyboard_card.html")
    bountyboard = get_bounties(group=group, limit=limit)
    bountyboard_cards = []
    for bounty in bountyboard:
        bountyboard_card = bountyboard_card_template.replace("{bounty_id}", bounty.BountyId)
        bountyboard_card = bountyboard_card.replace("{primary_image}", bounty.image_path(bounty.primary_image))
        bountyboard_card = bountyboard_card.replace("{bounty_name}", bounty.BountyName)
        bountyboard_card = bountyboard_card.replace("{bounty_reward}", bounty.reward)
        bountyboard_card = bountyboard_card.replace("{bounty_description}", bounty.BountyDescription)
        bountyboard_cards.append(bountyboard_card)
    bountyboard_template = bountyboard_template.replace("{bounties}", "\n".join(bountyboard_cards))
    return bountyboard_template


def rendered_bountyboard(event):
    bountyboard = render_bountyboard(group="confirmed")
    return 200, bountyboard


def rendered_bounties_in_progress(event):
    bountyboard = render_bountyboard(group="called")
    return 200, bountyboard


def rendered_bounty_portfolio(event):
    bountyboard = render_bountyboard(group="claimed")
    return 200, bountyboard


def get_edit_bounty_form(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = get_bounty(bounty_id)
    form_template = get_html_template("edit_bounty_form.html")
    script_template = get_javascript_template("upload_reference_material.js")
    script_template.replace("{bounty_id}", bounty_id)

    for pattern, replacement in {
            "{bounty_name}": bounty.BountyName,
            "{bounty_reward}": bounty.reward,
            "{bounty_description}": bounty.BountyDescription,
            "{upload_reference_material_script}": script_template}.items():
        form_template = form_template.replace(pattern, replacement)

    return 200, form_template


def receive_bounty_edit(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = get_bounty(bounty_id)
    bounty_edit = {}

    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    multipart_decoder = MultipartDecoder(content=form_data, content_type=content_type)
    for part in multipart_decoder.parts:
        form_name = get_form_name(part)
        form_name = form_name if form_name not in bounty_name_map else bounty_name_map[form_name]
        bounty_edit[form_name] = part.content.decode()

    bounty.BountyName = bounty_edit['BountyName']
    # murd.update([bounty.asm()])
    return 200, ""


def get_call_bounty_form(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = get_bounty(bounty_id)
    form_template = get_html_template("call_bounty_form.html")

    for pattern, replacement in {
            "{bounty_name}": bounty.BountyName,
            "{bounty_id}": bounty.BountyId}.items():
        form_template = form_template.replace(pattern, replacement)

    return 200, form_template


def receive_call_bounty(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = get_bounty(bounty_id)
    maker_contact = {}

    content_type = event['headers']['content-type']
    form_data = b64decode(event['body'])

    multipart_decoder = MultipartDecoder(content=form_data, content_type=content_type)
    for part in multipart_decoder.parts:
        form_name = get_form_name(part)
        form_name = form_name if form_name not in bounty_name_map else bounty_name_map[form_name]
        maker_contact[form_name] = part.content.decode()

    bounty.MakerEmail = maker_contact['maker_email']
    confirmation_id = str(uuid4())
    email_template = get_html_template("call_bounty_email.html")

    for pattern, replacement in {
            "{bounty_name}": bounty.BountyName,
            "{call_confirmation_id}": confirmation_id,
            "{bounty_reward}": bounty.reward,
            "{bounty_description}": bounty.BountyDescription,
            "{maker_email}": bounty.sanitized_maker_email,
            "{maker_name}": maker_contact['maker_name']}.items():
        email_template = email_template.replace(pattern, replacement)

    murd.update([
        {mddb.group_key: "bounty_call_confirmations",
         mddb.sort_key: confirmation_id,
         "BountyId": bounty.BountyId,
         "MakerEmail": bounty.sanitized_maker_email,
         "MakerName": maker_contact["maker_name"],
         "CreationTime": datetime.utcnow().isoformat()}
    ])
    ses.send_email(subject=f'So, you wanna make "{bounty.BountyName}"?', sender="commissions@makurspace.com",
                   contact=bounty.sanitized_maker_email, content=email_template)
    call_confirmation_email_sent = get_html_template("call_confirmation_email_sent.html")
    return 200, call_confirmation_email_sent


def confirm_call_bounty(event):
    confirmation_id = event['pathParameters']['call_confirmation_id']
    confirmationm = murd.read_first(group="bounty_call_confirmations", sort=confirmation_id)
    bounty = get_bounty(confirmationm['BountyId'])
    bounty.MakerName = confirmationm['MakerName']
    bounty.MakerEmail = confirmationm['MakerEmail']
    murd.delete([bounty.asm()])
    bounty.change_state("called")

    called_bounty_confirmation = get_html_template("called_confirmation.html").replace("{bounty_name}", bounty.BountyName)

    return 200, called_bounty_confirmation


def build_page():
    page = LambdaPage()
    page.add_endpoint(method="get", path="/rest/upload_reference_material.js", func=render_refmat_upload_script, content_type="text/javascript")
    page.add_endpoint(method="get", path="/rest/bounty_form/{bounty_id}/{refmat_filename}", func=get_refmat_surl)
    page.add_endpoint(method="post", path="/rest/bounty_form", func=submit_bounty_form, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/bounty_confirmation/{bounty_confirmation_id}", func=confirm_bounty_creation, content_type="text/html")
    page.add_endpoint(method="post", path="/rest/bounty_confirmation/{bounty_confirmation_id}", func=bounty_confirmed, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/bountyboard/{bounty_id}", func=handle_get_bounty)
    page.add_endpoint(method="get", path="/rest/rendered_bountyboard", func=rendered_bountyboard, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/rendered_bounties_in_progress", func=rendered_bounties_in_progress, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/rendered_bounty_portfolio", func=rendered_bounty_portfolio, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/rendered_bounty/{bounty_id}", func=get_rendered_bounty, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/bountyboard", func=handle_get_bountyboard)
    page.add_endpoint(method="get", path="/rest/bounties_in_progress", func=handle_get_bountyboard)
    page.add_endpoint(method="get", path="/rest/bounty_portfolio", func=handle_get_bountyboard)
    page.add_endpoint(method="get", path="/rest/edit_bounty/{bounty_id}", func=get_edit_bounty_form, content_type="text/html")
    page.add_endpoint(method="post", path="/rest/edit_bounty/{bounty_id}", func=receive_bounty_edit, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/call_bounty/{bounty_id}", func=get_call_bounty_form, content_type="text/html")
    page.add_endpoint(method="post", path="/rest/call_bounty/{bounty_id}", func=receive_call_bounty, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/call_bounty_confirm/{call_confirmation_id}", func=confirm_call_bounty, content_type="text/html")
    return page


def lambda_handler(event, context):
    start = datetime.utcnow()
    print(f"Handling {event['path']} + {event['httpMethod']}")
    page = build_page()
    results = page.handle_request(event)
    build_time = (datetime.utcnow() - start).total_seconds()
    print(f"SC: {results['statusCode']} || BT: {build_time}")
    return results


if __name__ == "__main__":
    page = build_page()
    page.start_local()
