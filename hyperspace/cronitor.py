from hyperspace.bounty_system.bounty_up import process_ups
from hyperspace.objects import HyperBounty
import hyperspace.ses as ses


def flagForApproval():
    bountiesInNeedOfApproval = HyperBounty.getByState("verified")
    if bountiesInNeedOfApproval:
        ses.send_email(subject=f"Bounty Approval Needed ({len(bountiesInNeedOfApproval)})", sender="commissions@makurspace.com",
                       contact="hello@makurspace.com", content=f"{len(bountiesInNeedOfApproval)} need admin approval")


def lambda_handler(event, context):
    process_ups()
    flagForApproval()
