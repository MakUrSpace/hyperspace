from LambdaPage import LambdaPage
from markdown import markdown as md_to_html

template = """
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://igoradamenko.github.io/awsm.css/css/awsm.min.css">
<script
  src="https://code.jquery.com/jquery-3.1.1.min.js"
  integrity="sha256-hVVnYaiADRTO2PzUGmuLJr8BLUSjGIZsDYGmIJLv2b8="
  crossorigin="anonymous">
</script>
</style>
<title>MakUrSpace</title>
</head>
<body>
{body}
</body>
</html>
"""


def landing_page(event):
    with open("home.md", "r") as f:
        content = f.read()
    content = md_to_html(content, extensions=['extra', 'toc', 'markdown_checklist.extension', 'nl2br'])
    html = template.format(body=content)
    return 200, html


if __name__ == "__main__":
    page = LambdaPage()
    page.add_endpoint(method='get', path='/', func=landing_page, content_type="text/html")
    page.start_local()
