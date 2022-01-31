from urllib.parse import unquote_plus
from hyperspace.objects import HyperBounty, asdict


def handle_get_bountyboard(event):
    return 200, [asdict(bounty) for bounty in HyperBounty.getByState()]


def handle_get_bounties_in_progress(event):
    return 200, [asdict(bounty) for bounty in HyperBounty.getByState(state="called")]


def handle_get_bounty_portfolio(event):
    return 200, [asdict(bounty) for bounty in HyperBounty.getByState(state="claimed")]


def handle_get_bounty(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    return 200, asdict(HyperBounty.retrieve(bounty_id))
