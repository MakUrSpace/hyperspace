from hyperspace.api import build_page


def get_static_path(event):
    path = "/".join([
        sp
        for key, sp in event['pathParameters'].items()
        if "static_path" in key[:len("static_path")]
    ])
    path = f"./frontend/{path}"
    print(f"Opening {path}")
    file_type = path.split(".")[-1]
    binary_types = ["png", "jpg"]

    read_type = "rb" if file_type in binary_types else "r"
    with open(path, read_type) as f:
        page = f.read()

    content_map = {
        "html": "text/html",
        "css": "text/css",
        "json": "application/json",
        "js": "text/javascript",
        "png": "image/png",
        "jpg": "image/jpg"
    }
    get_static_path.headers["content-type"] = content_map[file_type]
    return 200, page


def get_filler(event):
    with open("./filler.jpg", "rb") as f:
        page = f.read()
    get_filler.headers["content-type"] = "image/jpg"
    return 200, page


if __name__ == "__main__":
    page = build_page()
    page.add_endpoint(method="get", path="/bountyboard/{static_path}/{static_path1}", func=get_filler)
    page.add_endpoint(method="get", path="/{static_path}", func=get_static_path)
    page.add_endpoint(method="get", path="/{static_path}/{static_path1}", func=get_static_path)
    page.add_endpoint(method="get", path="/{static_path}/{static_path1}/{static_path2}", func=get_static_path)
    page.add_endpoint(method="get", path="/{static_path}/{static_path1}/{static_path2}/{static_path3}", func=get_static_path)
    page.start_local()
