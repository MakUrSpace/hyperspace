from LambdaPage import LambdaPage


def build_page():
    page = LambdaPage()
    page.add_endpoint(method="get", path="/", func=lambda e: (200, "WIP"))
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
