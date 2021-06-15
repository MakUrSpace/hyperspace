import os
import re


def get_installation_directory():
    return os.path.dirname(os.path.abspath(__file__))


def get_path(path):
    return os.path.join(get_installation_directory(), path)


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


email_regex_pattern = re.compile(r"""(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])""")


def sanitize_email(email_address):
    regexed = email_regex_pattern.match(email_address)
    return regexed.string
