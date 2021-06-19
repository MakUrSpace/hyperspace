from hyperspace.objects import Bounty
from hyperspace.utilities import get_html_template
from hyperspace import ses


SECONDS_IN_3_DAYS = 60 * 60 * 24 * 3


def bounties_in_need_of_wip(bounties=None):
    """ Returns bounties called 3 days or more ago or that last updated their WIP 3 or more days ago """
    if bounties is None:
        bounties = Bounty.get_bounties(group="called")
    return [
        bounty for bounty in bounties
        if bounty.time_since("called") > SECONDS_IN_3_DAYS or (
            bounty.get_stamp("wip") is not None and bounty.time_since("wip") > SECONDS_IN_3_DAYS
        )
    ]


def email_wips(bounties):
    for bounty in bounties:
        wip_email_template = get_html_template("wip_email_template.html")

        for pattern, replacement in {
            "{maker_name}": bounty.MakerName,
            "{bounty_name}": bounty.BountyName,
            "{bounty_id}": bounty.BountyId
        }.items():
            wip_email_template = wip_email_template.replace(pattern, replacement)

        ses.send_email(subject=f'MakUrSpace WIP Request', sender="commissions@makurspace.com",
                       contact=bounty.sanitized_maker_email, content=wip_email_template)
