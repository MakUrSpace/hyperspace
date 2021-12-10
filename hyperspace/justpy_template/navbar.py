import justpy as jp

class MUS_Navbar():

    def navbar():
        wp = jp.WebPage()
        navbar_html = jp.parse_html("""
        <head>
            <title>MUS Test</title>
        </head>
            <div>
            <p>Test</p>
            </div>
            """, a=wp)
        for i in navbar_html.commands:
            print(i)
            jp.Div(text=i, classes='font-mono ml-2', a=wp)
        print()
        return wp

jp.justpy(MUS_Navbar)