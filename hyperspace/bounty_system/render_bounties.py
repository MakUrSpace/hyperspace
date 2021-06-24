from urllib.parse import unquote_plus

from hyperspace.utilities import get_html_template
from hyperspace.objects import Bounty


def get_rendered_bounty(event):
    bounty_interactions = {
        "suggest_edit": """<button class="col btn btn-primary" id="suggest_edit_button" style="margin-bottom: 7px" onclick="location.href='/rest/edit_bounty/{bounty_id}';">Suggest Edit</button>""",
        "make_this": """<button class="col btn btn-primary" id="make_this_button" onclick="location.href='/rest/call_bounty/{bounty_id}';">I can make this!</button>""",
        "wip_this": """<button class="col btn btn-primary" id="make_this_button" onclick="location.href='/rest/bounty_wip/{bounty_id}';">I can WIP this!</button>""",
        "claim_this": """<button class="col btn btn-primary" id="make_this_button" onclick="location.href='/rest/claim_bounty/{bounty_id}';">I've finished this!</button>""",
    }
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = Bounty.get_bounty(bounty_id)

    if bounty.State == "confirmed":
        interactions = ["suggest_edit", "make_this"]
    elif bounty.State == "called":
        interactions = ["wip_this", "claim_this"]
    else:
        interactions = []
    interactions = "\n".join([bounty_interactions[i] for i in interactions])

    template = get_html_template("bountycard.html")

    for pattern, replacement in {
            "{interactions}": interactions,
            "{bounty_name}": bounty.BountyName,
            "{bounty_id}": bounty.BountyId,
            "{bounty_reward}": bounty.reward,
            "{primary_image}": bounty.image_path(bounty.primary_image),
            "{bounty_description}": bounty.BountyDescription}.items():
        template = template.replace(pattern, replacement)

    return 200, template


def render_bountyboard(group="confirmed", limit=200):
    bountyboard_template = get_html_template("bountyboard.html")
    bountyboard_card_template = get_html_template("bountyboard_card.html")
    bountyboard = Bounty.get_bounties(group=group, limit=limit)
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
