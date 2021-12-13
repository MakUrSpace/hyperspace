import justpy as jp

class MUS_Navbar(jp.Div):

    def navbar(self, request):
        wp = jp.WebPage()
        navbar_class_html = "m-2 bg-gray-200 border-2 border-gray-200 rounded w-64 py-2 px-4 text-gray-700 focus:outline-none focus:bg-white focus:border-purple-500"
        navbar_html = jp.parse_html("""
            <div>
                <ul>
                    <li>MakUrSpace</li>
                    <li><input type="search" placeholder="Search Bounties"></li>
                    <li>Home</li>
                    <li>Bounty Board</li>
                    <li>Sign Up / Login</li>
                </ul>
            </div>
            """, a=wp, classes=navbar_class_html)
        return wp

jp.justpy(MUS_Navbar().navbar)