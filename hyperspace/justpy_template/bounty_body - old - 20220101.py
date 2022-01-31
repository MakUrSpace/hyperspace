import justpy as jp

class MUS_Bounty_Board(jp.Div):

    def bounty_board(self, request):
        wp = jp.WebPage()
        bounty_board_html = jp.parse_html("""
            <div class="container mx-auto space-y-2 lg:space-y-0 lg:gap-2 lg:grid lg:grid-cols-3">
                <div class="w-1/2 rounded hover:opacity-50">
                    <img src="https://images.unsplash.com/photo-1523275335684-37898b6baf30?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=989&q=80"
                        alt="image">
                </div>
                <div class="w-1/2 rounded hover:opacity-50">
                    <img src="https://images.unsplash.com/photo-1523275335684-37898b6baf30?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=989&q=80"
                        alt="image">
                </div>
                <div class="w-1/2 rounded hover:opacity-50">
                    <img src="https://images.unsplash.com/photo-1523275335684-37898b6baf30?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=989&q=80"
                        alt="image">
                </div>
            </div>
            """, a=wp)
        return wp

jp.justpy(MUS_Bounty_Board().bounty_board)