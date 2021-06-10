from urllib.parse import unquote_plus

from hyperspace.utilities import get_html_template
from hyperspace.objects import Bounty


def get_rendered_bounty(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = Bounty.get_bounty(bounty_id)

    template = get_html_template("bountycard.html")

    for pattern, replacement in {
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
