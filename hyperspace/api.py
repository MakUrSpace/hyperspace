from datetime import datetime

from LambdaPage import LambdaPage

from hyperspace.bounty_system.get_bounty import handle_get_bountyboard, handle_get_bounty
from hyperspace.bounty_system.render_bounties import rendered_bountyboard, rendered_bounties_in_progress, rendered_bounty_portfolio, get_rendered_bounty
from hyperspace.bounty_system.bounty_creation import submit_bounty_form, confirm_bounty_creation, bounty_confirmed
from hyperspace.bounty_system.edit_bounty import get_edit_bounty_form, receive_bounty_edit
from hyperspace.bounty_system.call_bounty import get_call_bounty_form, receive_call_bounty, confirm_call_bounty
from hyperspace.bounty_system.bounty_wip import wip_submission_form, handle_wip_submission

from hyperspace.reference_material import get_refmat_surl, render_refmat_upload_script
from hyperspace.maker_registration import submit_maker_registration, confirm_maker_registration


def build_page():
    page = LambdaPage()

    # Get bounties
    page.add_endpoint(method="get", path="/rest/bountyboard", func=handle_get_bountyboard)
    page.add_endpoint(method="get", path="/rest/bountyboard/{bounty_id}", func=handle_get_bounty)
    page.add_endpoint(method="get", path="/rest/bounties_in_progress", func=handle_get_bountyboard)
    page.add_endpoint(method="get", path="/rest/bounty_portfolio", func=handle_get_bountyboard)

    # Reference Material Handling
    page.add_endpoint(method="get", path="/rest/upload_reference_material.js", func=render_refmat_upload_script, content_type="text/javascript")
    page.add_endpoint(method="get", path="/rest/reference_material/{bounty_id}/{refmat_filename}", func=get_refmat_surl)

    # Maker Registration
    page.add_endpoint(method="post", path="/rest/maker_registration", func=submit_maker_registration, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/maker_registration/{maker_id}", func=confirm_maker_registration, content_type="text/html")

    # Bounty Submission
    page.add_endpoint(method="post", path="/rest/bounty_form", func=submit_bounty_form, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/bounty_confirmation/{bounty_confirmation_id}", func=confirm_bounty_creation, content_type="text/html")
    page.add_endpoint(method="post", path="/rest/bounty_confirmation/{bounty_confirmation_id}", func=bounty_confirmed, content_type="text/html")

    # Edit Bounty
    page.add_endpoint(method="get", path="/rest/edit_bounty/{bounty_id}", func=get_edit_bounty_form, content_type="text/html")
    page.add_endpoint(method="post", path="/rest/edit_bounty/{bounty_id}", func=receive_bounty_edit, content_type="text/html")

    # Call Bounty
    page.add_endpoint(method="get", path="/rest/call_bounty/{bounty_id}", func=get_call_bounty_form, content_type="text/html")
    page.add_endpoint(method="post", path="/rest/call_bounty/{bounty_id}", func=receive_call_bounty, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/call_bounty_confirm/{call_confirmation_id}", func=confirm_call_bounty, content_type="text/html")

    # Relinquish Bounty
    page.add_endpoint(method="get", path="/rest/relinquish_bounty/{bounty_id}", func=lambda: (200, "Not implemented"), content_type="text/html")

    # Bounty WIP
    page.add_endpoint(method="get", path="/rest/bounty_wip/{bounty_id}", func=wip_submission_form, content_type="text/html")
    page.add_endpoint(method="post", path="/rest/bounty_wip/{bounty_id}", func=handle_wip_submission, content_type="text/html")

    # Bounty Pages
    page.add_endpoint(method="get", path="/rest/rendered_bountyboard", func=rendered_bountyboard, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/rendered_bounties_in_progress", func=rendered_bounties_in_progress, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/rendered_bounty_portfolio", func=rendered_bounty_portfolio, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/rendered_bounty/{bounty_id}", func=get_rendered_bounty, content_type="text/html")

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
