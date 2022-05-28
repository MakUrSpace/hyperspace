from datetime import datetime
from uuid import uuid4
import json
from base64 import b64decode

from hyperspace.murd import mddb, murd
from hyperspace.objects import HyperBounty, asdict
from hyperspace.utilities import get_html_template, process_multipart_form_submission
import hyperspace.ses as ses
import hyperspace.s3 as s3
from hyperspace.bounty_system.render_bounties import render_bounty


def approve_bounty(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = HyperBounty.retrieve(bounty_id)
    return 200, {}


def reject_bounty(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = HyperBounty.retrieve(bounty_id)
    return 200, {}
