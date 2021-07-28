class BaseDevice:
    def handle_command(self, command):
        raise NotImplemented('Method handle_command must be implemented')

    def get_keyboard(self):
        raise NotImplemented('Method get_keyboard must be implemented')
