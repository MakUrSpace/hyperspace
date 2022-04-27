from os.path import dirname, join, abspath
from re import compile as re_compile
from json import loads
from datetime import datetime

from requests_toolbelt.multipart import MultipartDecoder


def get_installation_directory():
    return dirname(abspath(__file__))


def get_path(path):
    return join(get_installation_directory(), path)


def get_form_name(part):
    defn = part.headers[b'Content-Disposition'].decode()
    return defn[defn.find(" name="):].split(";")[0].split("=")[1].replace('"', '')


def get_refmat_filename(part):
    defn = part.headers[b'Content-Disposition'].decode()
    return defn[defn.find(" filename="):].split(";")[0].split("=")[1].replace('"', '')


def get_javascript_template(filename):
    with open(get_path(f"javascript_templates/{filename}"), "r") as f:
        template = f.read()
    return template


def get_html_template(filename):
    with open(get_path(f"html_templates/{filename}"), "r") as f:
        template = f.read()
    return template


email_regex_pattern = re_compile(r"""\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b""")


class InvalidEmailAddress(Exception):
    """ Exception for an unsanitary email address """


def sanitize_email(email_address):
    regexed = email_regex_pattern.match(email_address)
    try:
        return regexed.string
    except AttributeError:
        raise sanitize_email.InvalidEmailAddress(f"'{email_address}' cannot be processed as an email address")


sanitize_email.InvalidEmailAddress = InvalidEmailAddress


def timestamp():
    return datetime.utcnow().isoformat()


def billboardPage(func):
    billboard = get_html_template("billboard.html")

    def billboarded(event):
        statusCode, body = func(event)
        return statusCode, billboard.replace("{body}", body)
    return billboarded


def process_multipart_form_submission(form_data, content_type):
    multipart_decoder = MultipartDecoder(content=form_data, content_type=content_type)
    decoded_data = {}
    for part in multipart_decoder.parts:
        form_name = get_form_name(part)
        if form_name == 'ReferenceMaterialNames':
            decoded_data['ReferenceMaterial'] = loads(part.content)
        else:
            decoded_data[form_name] = part.content.decode()
    return decoded_data
