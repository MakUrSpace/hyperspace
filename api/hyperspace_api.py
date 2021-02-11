from LambdaPage import LambdaPage


def handle_get(event):
    assert 'GID' in event['body']
    # Retrieve GID from Murd
    return 200


def handle_put(event):
    # Update server data
    return 200


def handle_delete(event):
    # Delete server data
    return 200


def build_page():
    page = LambdaPage()
    page.add_endpoint(method="get", path="/", func=lambda e: (200, "WIP"))
    page.add_endpoint(method="put", path="/", func=lambda e: (200, "WIP"))
    page.add_endpoint(method="delete", path="/", func=lambda e: (200, "WIP"))
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
