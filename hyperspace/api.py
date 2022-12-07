from datetime import datetime

from hyperspace.LambdaPage import LambdaPage

from hyperspace.bounty_system.get_bounty import handle_get_bountyboard, handle_get_bounty
from hyperspace.bounty_system.render_bounties import rendered_bountyboard, rendered_bounties_in_progress, rendered_bounty_portfolio, get_rendered_bounty, get_rendered_bounty_refmat
from hyperspace.bounty_system.bounty_creation import submit_bounty_or_return_form, confirm_bounty_creation
from hyperspace.bounty_system.discuss_bounty import get_ask_benefactor_form, submit_benefactor_question, get_question_answer_form, submit_benefactor_answer
from hyperspace.bounty_system.edit_bounty import get_edit_bounty_form, receive_bounty_edits, submit_bounty_edits, confirm_bounty_edits
from hyperspace.bounty_system.call_bounty import get_call_bounty_form, receive_call_bounty, confirm_call_bounty
from hyperspace.bounty_system.bounty_up import up_submission_form, handle_up_submission
from hyperspace.bounty_system.claim_bounty import claim_bounty_form, handle_bounty_claim, claim_bounty
from hyperspace.bounty_system.completed_bounty_creation import submit_completed_bounty_form, confirm_completed_bounty_creation

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
    page.add_endpoint(method="post", path="/rest/bounty_form", func=submit_bounty_or_return_form, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/bounty_confirmation/{bounty_confirmation_id}", func=confirm_bounty_creation, content_type="text/html")

    # Portfolio Project/Completed Bounty Submission
    page.add_endpoint(method="post", path="/rest/completed_bounty_form", func=submit_completed_bounty_form, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/completed_bounty_confirmation/{bounty_confirmation_id}", func=confirm_completed_bounty_creation, content_type="text/html")

    # Ask the Benefactor
    page.add_endpoint(method="get", path="/rest/ask_benefactor/{bounty_id}", func=get_ask_benefactor_form, content_type="text/html")
    page.add_endpoint(method="post", path="/rest/ask_benefactor/{bounty_id}", func=submit_benefactor_question, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/question/{question_id}", func=get_question_answer_form, content_type="text/html")
    page.add_endpoint(method="post", path="/rest/question/{question_id}", func=submit_benefactor_answer, content_type="text/html")

    # Edit Bounty
    page.add_endpoint(method="get", path="/rest/edit_bounty/{bounty_id}", func=get_edit_bounty_form, content_type="text/html")
    page.add_endpoint(method="post", path="/rest/edit_bounty/{bounty_id}", func=receive_bounty_edits, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/submit_bounty_edits_and_call/{bounty_edit_id}", func=submit_bounty_edits, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/submit_bounty_edits/{bounty_edit_id}", func=submit_bounty_edits, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/confirm_bounty_edits/{bounty_edit_confirmation_id}", func=confirm_bounty_edits, content_type="text/html")

    # Call Bounty
    page.add_endpoint(method="get", path="/rest/call_bounty/{bounty_id}", func=get_call_bounty_form, content_type="text/html")
    page.add_endpoint(method="post", path="/rest/call_bounty/{bounty_id}", func=receive_call_bounty, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/call_bounty_confirm/{call_confirmation_id}", func=confirm_call_bounty, content_type="text/html")

    # Relinquish Bounty
    page.add_endpoint(method="get", path="/rest/relinquish_bounty/{bounty_id}", func=lambda: (200, "Not implemented"), content_type="text/html")

    # UP Bounty
    page.add_endpoint(method="get", path="/rest/bounty_up/{bounty_id}", func=up_submission_form, content_type="text/html")
    page.add_endpoint(method="post", path="/rest/bounty_up", func=handle_up_submission, content_type="text/html")

    # Claim Bounty
    page.add_endpoint(method="get", path="/rest/claim_bounty/{bounty_id}", func=claim_bounty_form, content_type="text/html")
    page.add_endpoint(method="post", path="/rest/claim_bounty", func=handle_bounty_claim, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/claim_bounty_confirm/{claim_confirmation_id}", func=claim_bounty, content_type="text/html")

    # Bounty Pages
    page.add_endpoint(method="get", path="/rest/rendered_bountyboard", func=rendered_bountyboard, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/rendered_bounties_in_progress", func=rendered_bounties_in_progress, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/rendered_bounty_portfolio", func=rendered_bounty_portfolio, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/rendered_bounty/{bounty_id}", func=get_rendered_bounty, content_type="text/html")
    page.add_endpoint(method="get", path="/rest/rendered_bounty_refmat/{bounty_id}", func=get_rendered_bounty_refmat, content_type="text/html")

    return page


def lambda_handler(event, context):
    start = datetime.utcnow()
    print(f"Handling {event}")
    page = build_page()
    results = page.handle_request(event)
    build_time = (datetime.utcnow() - start).total_seconds()
    print(f"SC: {results['statusCode']} || BT: {build_time}")
    return results


if __name__ == "__main__":
    page = build_page()
    page.start_local()
