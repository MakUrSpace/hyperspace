import justpy as jp

class MUS_Navbar(jp.Div):

    def navbar(self, request):
        wp = jp.WebPage()
        navbar_html = jp.parse_html("""
            <div>
                <div>
                    MakUrSpace
                </div>
                <input type="search" placeholder="Search Here!">
            </div>
            """, a=wp)
        for i in navbar_html.commands:
            print(i)
            jp.Div(text=i, classes='font-mono ml-2', a=wp)
        print()
        return wp

jp.justpy(MUS_Navbar().navbar)