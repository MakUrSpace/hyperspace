import justpy as jp

class MUS_Navbar(jp.Div):

    def navbar(self, request):
        wp = jp.WebPage()
        navbar_html = jp.parse_html("""
            <div>
                <ul>
                    <li>MakUrSpace</li>
                    <li><input type="search" placeholder="Search Bounties"></li>
                    <li>Home</li>
                    <li>Bounty Board</li>
                    <li>Sign up / Login</li>
                </ul>
            </div>
            """, a=wp)
        #print()
        return wp

jp.justpy(MUS_Navbar().navbar)