from mycroft import MycroftSkill, intent_file_handler
from noaa_sdk import noaa

class NoaaAlerts(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.noaa = noaa.NOAA()

    def initialize(self):
        self._setup()
        self.settings.set_changed_callback(self.on_websettings_changed)

    def on_websettings_changed(self):
        # Only attempt to load if the host is set
        self.log.debug("websettings changed")
        self._setup()

    def _setup(self):
        self.zone_id = self.settings.get('zone_id','')

    @intent_file_handler('alerts.noaa.intent')
    def handle_alerts_noaa(self, message):
        self.log.debug("handle_alerts for zone_id {}".format(self.zone_id))
        if not self.zone_id:
            self.speak_dialog('error')
            return

        alerts = self.noaa.alerts(zone=self.zone_id)
        foundalerts = False
        for alert in alerts['features']:
            if alert['properties']['status']=='Actual' and alert['properties']['messageType']=='Alert':
                if not foundalerts:
                    self.speak_dialog('alerts.noaa')
                    foundalerts = True
                self.speak(alert['properties']['headline'])
                self.speak(alert['properties']['description'])


def create_skill():
    return NoaaAlerts()

