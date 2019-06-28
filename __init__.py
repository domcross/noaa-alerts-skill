from mycroft import MycroftSkill, intent_file_handler


class NoaaAlerts(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('alerts.noaa.intent')
    def handle_alerts_noaa(self, message):
        self.speak_dialog('alerts.noaa')


def create_skill():
    return NoaaAlerts()

