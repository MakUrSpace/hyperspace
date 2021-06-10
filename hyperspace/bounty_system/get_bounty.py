from urllib.parse import unquote_plus
from hyperspace.objects import Bounty


def handle_get_bountyboard(event):
    return 200, [bounty.asdict() for bounty in Bounty.get_bounties()]


def handle_get_bounties_in_progress(event):
    return 200, [bounty.asdict() for bounty in Bounty.get_bounties(group="called")]


def handle_get_bounty_portfolio(event):
    return 200, [bounty.asdict() for bounty in Bounty.get_bounties(group="claimed")]


def handle_get_bounty(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    return 200, Bounty.get_bounty(bounty_id).asdict()
