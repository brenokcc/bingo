from sloth.api.dashboard import Dashboard
from .models import *


class AppDashboard(Dashboard):

    def __init__(self, request):
        super().__init__(request)
        self.styles('/static/css/sloth.css')
        self.scripts('/static/js/sloth.js')
        self.libraries(fontawesome=False, materialicons=False)
        self.web_push_notification(False)
        self.login(logo='/static/images/bingo.png', title=None, mask=None, two_factor=False)
        self.navbar(title='Bingo', icon='/static/images/bingo.png', favicon='/static/images/bingo.png')
        self.header(title='Bingo', shadow=True)
        self.settings_menu('change_password')
        self.tools_menu('show_icons')
        self.footer(title='© 2022 Bingo', text='Todos os direitos reservados', version='1.0.0')

        self.action_bar('bingo.pessoa', 'bingo.evento')

    def view(self):
        return self.objects('bingo.evento').all().actions('view').calendar('data')

