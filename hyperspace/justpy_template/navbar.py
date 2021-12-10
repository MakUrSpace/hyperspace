import justpy as jp

class MUS_Navbar(jp.Div):

    def navbar(self, request):
        wp = jp.WebPage()
        navbar_div = jp.Div(classes='bg-black', a=wp)
        return wp

jp.justpy(MUS_Navbar().navbar)