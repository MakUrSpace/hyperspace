import json
from io import BytesIO
import boto3


bucket = "makurspace"


def retrieve(s3_path):
    print(f"Retrieving {s3_path}")
    s3b = boto3.resource("s3").Bucket(bucket)
    contents = BytesIO()
    s3b.download_fileobj(s3_path, contents)
    contents.seek(0)
    return contents


def retrieve_json(s3_path):
    content = retrieve(s3_path)
    content.seek(0)
    return json.loads(content.read())


def retrieve_presigned_url(s3_path):
    s3c = boto3.client("s3")
    url = s3c.generate_presigned_url('get_object',
                                     ExpiresIn=1800,
                                     Params={'Bucket': 'musingsole',
                                             'Key': s3_path})
    return url


def list_contents(s3_path):
    print(f"Listing {s3_path}")
    s3b = boto3.resource("s3").Bucket(bucket)
    return [content.key[len(s3_path):] for content in s3b.objects.filter(Prefix=s3_path)]


def write(s3_path, content):
    print(f"Writting {s3_path}")
    s3b = boto3.resource("s3").Bucket("musingsole")
    content_bytes = BytesIO(content.encode("utf-8"))
    s3b.upload_fileobj(content_bytes, s3_path)


def write_json(s3_path, content):
    print(f"Writing JSON at {s3_path}")
    write(s3_path, json.dumps(content))


def delete(s3_path):
    print(f"Deleting {s3_path}")
    s3b = boto3.resource("s3").Bucket("musingsole")
    s3b.delete_objects(Delete={"Objects": [{"Key": s3_path}]})
