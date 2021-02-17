from boto3.dynamodb.types import Binary
from murdaws import DDBMurd


page_template = """
<html>
<head>
<meta http-equiv="refresh" content="15" >
<script
  src="https://code.jquery.com/jquery-3.1.1.min.js"
  integrity="sha256-hVVnYaiADRTO2PzUGmuLJr8BLUSjGIZsDYGmIJLv2b8="
  crossorigin="anonymous">
</script>
</style>
<title>Maker Module {gpid}</title>
</head>
<body>
{status}
</body>
</html>
"""

body_template = """
<h1>Maker Module {gpid}</h1>
<h2>Status as of {timestamp}:</h2>
{thing_states}
"""


power_template = """
<h3>Power</h3>
<table>
    <tr>
        {plug_headers}
    </tr>
    <tr>
        {plug_states}
    </tr>
</table>
"""


cams_template = """
<h3>Cams</h3>
{images}
"""


def serve_maker_module(event):
    murd = DDBMurd("hyperspace")
    gpid = event['pathParameters']['gpid']
    mm = murd.read_first(group=gpid)
    body = body_template.replace("{gpid}", mm['GROUP']).replace("{timestamp}", mm['SORT'])

    power = power_template.replace(
        "{plug_headers}",
        " ".join([f"<th>{plug}</th>" for plug in mm['power']['state']])
    ).replace(
        "{plug_states}",
        " ".join([f"<th>{ps}</th>" for ps in mm['power']['state'].values()]))

    cam_nums = [k for k in mm['cams'].keys() if k != 'TIMESTAMP']
    cam_images = {cn: murd.read_first(group=f"0_SNAPSHOT", sort=mm['cams'][cn])['SNAPSHOT'] for cn in cam_nums}
    cam_images = {cn: image.value.decode() for cn, image in cam_images.items() if isinstance(image, Binary)}
    cams = cams_template.replace(
        "{images}",
        "\n".join([f'<h4>{cam_num} Snapshot</h4>\n'
                   f'<img src="data:image/jpg;base64,{cam_images[cam_num]}" alt="{cam_num} snapshot"/>\n'
                   for cam_num in cam_images]))

    body = body.replace("{thing_states}", "\n".join([power, cams]))
    page = page_template.replace("{status}", body).replace("{gpid}", mm['GROUP'])

    return 200, page
