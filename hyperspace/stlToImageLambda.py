import boto3
import json


def stlToImage(stlPath: str, outputFile: str):
    lambdaClient = boto3.client('lambda')
    lambdaClient.invoke(
        FunctionName='stl_to_image',
        InvocationType='Event',
        Payload=json.dumps({"stlPath": stlPath, "outputFile": outputFile})
    )


stlPositionPattern = "_stlposition_(.*)x(.*)x(.*).stl"


def stlCenteringDimensions(stlPath: str):
    lambdaClient = boto3.client('lambda')
    resp = lambdaClient.invoke(
        FunctionName='stl_to_image',
        InvocationType='RequestResponse',
        Payload=json.dumps({"stlPath": stlPath, "operation": "stlCenteringDimensions"})
    )
    return json.loads(resp['Payload'].read().decode())
