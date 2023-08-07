# Hyperspace API

This module provides dynamic server computation for Hyperspace events.

# Deployment
Configure environment for AWS programmatic environment and install Serverless. Then run: `serverless deploy`

The server can be started locally by running `python hyperspace_api.py`

# Bounty Definition

Many endpoints return a bounty definition or a collection of bounty definitions. The attributes of a Bounty Definition are defined below:

## Bounty

Asking price for the described good. Defined as a float, though typically stored and returned as a string

## BountyName

Name for the bounty. This must be a unique string among active bounties.

## Recipient

Name of the entity to receive the described good

## Contact

Email address at which to contact the Recipient

## TemplateProject

Name of a template project to use as a reference

## ProjectDescription

Up to 2000 words describing the good the bounty is requesting.

## ReferenceMaterial

A list of the names of larger assets to use for reference in describing the requested good. The actual assets are stored separately from the bounty definitions in S3. This list is the portion of the S3 object key beneath the bounty's allocated storage location.


# Endpoints
## /bountyboard/{bounty_name}

### GET

Retrieve a specific bounty with the BountyName bounty_name.

#### Response Body

The bounty_name endpoint will return a JSON dictionary defining a bounty.

```json
{
    "Bounty": "300",
    "BountyName": "Drink Stabilizer",
    "Recipient": "b.d.trane",
    "Contact": "commissions@makurspace.com",
    "TemplateProject": "None",
    "ProjectDescription": "Pocketable, imprintable, disposable drink-attachment to prevent spilling and enhance bigdogity",
    "ReferenceMaterial": "[\"DrinkStabilizerConcept.png\"]"}
```

## /bountyboard

### GET

Retrieve up to 500 items from the bounty board.

#### Response Body

The bountyboard endpoint will return a JSON list of dictionaries, each dictionary defining a bounty.


```json
[
    {
        "Bounty": "150.3",
        "BountyName": "Vat Drain",
        "Recipient": "musingsole",
        "Contact": "commissions@makurspace",
        "TemplateProject": "None",
        "ProjectDescription": "A stand that can hold a resin vat and allow it to drain into a storage bottle",
        "ReferenceMaterial": "[\"VatDrain.stl\"]"
    },
    {
        "Bounty": "300",
        "BountyName": "Drink Stabilizer",
        "Recipient": "b.d.trane",
        "Contact": "commissions@makurspace.com",
        "TemplateProject": "None",
        "ProjectDescription": "Pocketable, imprintable, disposable drink-attachment to prevent spilling and enhance bigdogity",
        "ReferenceMaterial": "[\"DrinkStabilizerConcept.png\"]"
    },
    ...
]
```

### POST

Submit a new bounty definition to the bountyboard.

#### Request Body

The request body must be a JSON dictionary defining a bounty. The BountyName must be a unique value or the API will return a 403 error.

```json
{
    "Bounty": "150.3",
    "BountyName": "Vat Drain",
    "Recipient": "musingsole",
    "Contact": "commissions@makurspace",
    "TemplateProject": "None",
    "ProjectDescription": "A stand that can hold a resin vat and allow it to drain into a storage bottle",
    "ReferenceMaterial": "[\"VatDrain.stl\"]"
}
```

The API will return a 200 response with an empty body on success.

## /bounty_form

### POST

Accept submissions from the new bounty submission form. The form must be submitted with the POST method and use the 'multipart/form-data' enctype. The form keys must be the same as the Bounty definition.