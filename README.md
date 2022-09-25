# HyperSpace

HyperSpace is the MakUrSpace operations and logistics system composed of a frontend web-app and a serverless backend.

## Deployment Setup

* [Create AWS Account](https://aws.amazon.com/)
* Configure environment for AWS access
  * [Create IAM Admin user](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html#id_users_create_console)
  * [Create admin user access key and secret](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)
  * [Configure environment for AWS (create .aws/credentials and .aws/config files)](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html)
    * AWS Profile names are used to control configuration scripts. Therefore, they must be strictly named:
        * mus
        * musint
        * musdev
* [Install Python 3](https://www.python.org/downloads/)
* [Install NodeJS (for serverless)](https://nodejs.org/en/download/)
* [Install Serverless Framework](https://www.serverless.com/framework/docs/getting-started/)
* [Guarantee stl_to_image has been deployed to AWS Account](https://github.com/MakUrSpace/solidpoly)
* Install serverless plugins:
```
sls plugin install --name serverless-s3-sync
sls plugin install --name serverless-python-requirements
sls plugin install --name serverless-apigw-binary
```

## Development Setup

* Deployment Setup
* Install python requirements: `pip3 install -r requirements.txt`

### Local Development Server

After making changes to local files, launch the development server to view results. This server uses local code to execute against server state data in AWS DynamoDB. As such, it requires an internet connection the environment be configured with an AWS role with DynamoDB list and read permissions at a minimum. Note, bounty reference material is stored as static data but not retained in the code repository. Because of this, the development server replaces all references to these images with filler images.

To launch: `python3 local.py`
