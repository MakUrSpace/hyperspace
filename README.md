# HyperSpace

HyperSpace is the MakUrSpace operations and logistics system composed of a frontend web-app and a serverless backend.

## Setup

* Create AWS Account
* Configure environment for AWS (create .aws/credentials and .aws/config files)
* Install Python 3
* Install python requirements: `pip3 install -r requirements.txt`


## Local Development

After making changes to local files, launch the development server to view results. This server uses local code to execute against server state data in AWS DynamoDB. As such, it requires an internet connection the environment be configured with an AWS role with DynamoDB list and read permissions at a minimum. Note, bounty reference material is stored as static data but not retained in the code repository. Because of this, the development server replaces all references to these images with filler images.

To launch: `python3 local.py`
