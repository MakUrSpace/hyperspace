from urllib.parse import unquote as url_decode
from traceback import format_exc
from LambdaPage import LambdaPage
import s3
from makurspaceweb import landing_page
from maker_module import serve_maker_module


content_type_map = {
    "html": "text/html",
    "js": "application/javascript"
}


def serve_static_path(event):
    path = "server/static/{}".format(url_decode(event['pathParameters']['path']))
    try:
        file_type = path.split(".")[-1]
        content = s3.retrieve(path)
    except Exception:
        print(format_exc())
        return 404, "Not found"
    headers = getattr(serve_static_path, "headers", {})
    headers['content-type'] = content_type_map[file_type]
    serve_static_path.headers = headers
    return 200, content.read().decode()


def build_page():
    page = LambdaPage()
    page.add_endpoint(method="get", path="/static/{path}", func=serve_static_path)
    page.add_endpoint(method="get", path="/maker_module/{gpid}", func=serve_maker_module, content_type="text/html")
    page.add_endpoint(method="get", path="/", func=landing_page, content_type="text/html")
    return page


def lambda_handler(event, context):
    print(f"Handling event: {event}")
    page = build_page()
    results = page.handle_request(event)
    print(results['statusCode'])
    return results


if __name__ == "__main__":
    page = build_page()
    page.start_local()
