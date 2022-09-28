from urllib.parse import unquote_plus
import re

from hyperspace.utilities import get_html_template
from hyperspace.objects import HyperBounty
import random


def get_rendered_bounty(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    return 200, render_bounty(bounty_id)


def build_secondary_image_carousel(bounty):
    carousel_template = """
      <div class="container">
        <div class="carousel slide" data-ride="carousel" id="multi_item">
          <div class="carousel-inner">
            <div class="carousel-item active">
              <div class="row">
                {secondary_images}
              </div>
            </div>
          </div>
          <a class="carousel-control-prev" href="#multi_item" role="button" data-slide="prev">
            <span class="carousel-control-prev-icon" aria-hidden="true"></span>
            <span class="sr-only">Previous</span>
          </a>
          <a class="carousel-control-next" href="#multi_item" role="button" data-slide="next">
            <span class="carousel-control-next-icon" aria-hidden="true"></span>
            <span class="sr-only">Next</span>
          </a>
        </div>
      </div>
"""

    sec_img_template = """<div class="col-sm"><img class="d-block" src="{src_url}" alt="{alt_text}"></div>"""
    secondary_images = []
    for sec_img in bounty.secondary_images:
        secondary_images.append(sec_img_template.format(src_url=bounty.image_path(sec_img), alt_text=""))
    secondary_images = "\n\n".join(secondary_images)
    return carousel_template.replace("{secondary_images}", secondary_images) if secondary_images else ""


def render_bounty(bounty_id):
    bounty_interactions = {
        "suggest_edit": """<button class="col btn btn-primary" id="suggest_edit_button" onclick="location.href='/rest/edit_bounty/{bounty_id}';">Suggest Edit</button>""",
        "make_this": """<button class="col btn btn-primary" id="make_this_button" onclick="location.href='/rest/call_bounty/{bounty_id}';">I can make this!</button>""",
        "up_this": """<button class="col btn btn-primary" id="up_this_button" onclick="location.href='/rest/bounty_up/{bounty_id}';">I can UP this!</button>""",
        "claim_this": """<button class="col btn btn-primary" id="claim_this_butotn" onclick="location.href='/rest/claim_bounty/{bounty_id}';">I've finished this!</button>""",
        "ask_benefactor": """<button class="col btn btn-primary" id="ask_this_butotn" onclick="location.href='/rest/ask_benefactor/{bounty_id}';">Ask the Benefactor!</button>""",
    }
    bounty = HyperBounty.retrieve(bounty_id)

    if bounty.State == "confirmed":
        interactions = ["ask_benefactor", "suggest_edit", "make_this"]
    elif bounty.State == "called":
        interactions = ["ask_benefactor", "up_this", "claim_this"]
    else:
        interactions = []
    interactions = "\n".join([bounty_interactions[i] for i in interactions])

    template = get_html_template("bountycard_stl.html" if len(bounty.stls) > 0 else "bountycard.html")

    secondary_image_carousel = build_secondary_image_carousel(bounty)

    primary_stl = bounty.stls[0] if len(bounty.stls) > 0 else ''
    primary_stl_image_path = bounty.image_path(primary_stl)
    position_search = re.search("_stlposition_(.*)x(.*)x(.*).stl", primary_stl)
    stl_position = "0 0 -15" if position_search is None else " ".join([str(int(float(pos))) for pos in position_search.groups()])

    related_bounties = random.sample(HyperBounty.get(limit=30), 4)
    related_bounties = "\n\n".join([f"""
      <div class="col-md-3 col-sm-6 mb-4">
        <a href="/rest/rendered_bounty/{related_bounty.Id}">
          <img class="img-fluid" src="{related_bounty.image_path(related_bounty.primary_image)}" alt="{related_bounty.Name}">
        </a>
      </div>
""" for related_bounty in related_bounties])

    for pattern, replacement in {
            "{interactions}": interactions,
            "{bounty_state}": bounty.State.upper(),
            "{bounty_name}": bounty.Name,
            "{bounty_id}": bounty.Id,
            "{bounty_reward}": bounty.reward,
            "{primary_image}": bounty.image_path(bounty.primary_image),
            "{primary_stl}": primary_stl_image_path,
            "{model_position}": stl_position,
            "{secondary_image_carousel}": secondary_image_carousel,
            "{bounty_description}": bounty.Description,
            "{related_bounties}": related_bounties}.items():
        template = template.replace(pattern, replacement)

    return template


def render_bountyboard(group="confirmed", limit=200):
    bountyboard_template = get_html_template("bountyboard.html")
    bountyboard_card_template = get_html_template("bountyboard_card.html")
    bountyboard = HyperBounty.getByState(group)
    bountyboard_cards = []
    for bounty in bountyboard:
        bountyboard_card = bountyboard_card_template.replace("{bounty_id}", bounty.Id)
        bountyboard_card = bountyboard_card.replace("{primary_image}", bounty.image_path(bounty.primary_image))
        bountyboard_card = bountyboard_card.replace("{bounty_name}", bounty.Name)
        bountyboard_card = bountyboard_card.replace("{bounty_reward}", bounty.reward)
        bountyboard_card = bountyboard_card.replace("{bounty_description}", bounty.Description)
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
