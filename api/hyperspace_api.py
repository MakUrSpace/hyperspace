from time import sleep
import json
from dataclasses import dataclass
from urllib.parse import unquote_plus

from LambdaPage import LambdaPage
from murdaws import murd_ddb as mddb
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
    ProjectDescription: str
    ReferenceMaterial: list

    def to_dict(self):
        return {key: attr if isinstance((attr := getattr(self, key)), str) else json.dumps(attr)
                for key in self.__annotations__}

    @classmethod
    def from_m(cls, m):
        return cls(**{k: v for k, v in m.items() if k not in [mddb.group_key, mddb.sort_key]})


def get_bounty_board(event):
    bounties = murd.read(group="bounty", limit=200)
    return 200, [Bounty.from_m(bounty).to_dict() for bounty in bounties]


def get_bounty(bounty_name):
    return Bounty.from_m(murd.read(group="bounty", sort=bounty_name)[0])


def handle_get_bounty(event):
    bounty_name = unquote_plus(event['pathParameters']['bounty_name'])
    return 200, get_bounty(bounty_name).to_dict()


def new_bounty(event):
    # Update server data
    new_bounty = Bounty(**json.loads(event['body']))
    try:
        get_bounty(new_bounty.BountyName)
        return 403, f"Bounty {new_bounty.BountyName} already exists"
    except IndexError:
        pass

    murd.update([{**{mddb.group_key: "bounty",
                     mddb.sort_key: new_bounty.BountyName},
                  **new_bounty.to_dict()}])
    # TODO: read back after write to test for success
    return 200


def submit_bounty_form(event):
    return 200


def build_page():
    page = LambdaPage()
    page.add_endpoint(method="post", path="/rest/bounty_form", func=submit_bounty_form)
    page.add_endpoint(method="post", path="/rest/bountyboard", func=new_bounty)
    page.add_endpoint(method="get", path="/rest/bountyboard/{bounty_name}", func=handle_get_bounty)
    page.add_endpoint(method="get", path="/rest/bountyboard", func=get_bounty_board)
    return page


def lambda_handler(event, context):
    print(f"Handling event: {str(event)[:500]}")
    page = build_page()
    results = page.handle_request(event)
    print(results['statusCode'])
    return results


if __name__ == "__main__":
    page = build_page()
    page.start_local()
