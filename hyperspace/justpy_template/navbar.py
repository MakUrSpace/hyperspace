import justpy as jp

class MUS_Navbar(jp.Div):

    def navbar(self, request):
        wp = jp.WebPage()
        navbar_html = jp.parse_html("""
            <div>
                <div>
                    MakUrSpace
                </div>
                <div>
                    <input type="search" placeholder="Search Bounties">
                </div>
                <div>
                    <p>Home</p>
                </div>
                <div>
                    <p>Bounty Board</p>
                </div>
                <div>
                    <p>Sign up / Login</p>
                </div>
            </div>
            """, a=wp)
        #print()
        return wp

jp.justpy(MUS_Navbar().navbar)