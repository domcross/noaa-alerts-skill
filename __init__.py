from mycroft import MycroftSkill, intent_file_handler
from mycroft.audio import wait_while_speaking
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
        self.severity = self.settings.get('severity','Extreme')
        self.urgency = self.settings.get('urgency','Immediate')
        self.certainty = self.settings.get('certainty','Observed')
        self.alerts = []
        self.status = "stopped"
        self.log.info("zone_id {} severity {} urgency {} certainty {}".format(self.zone_id, self.severity, self.urgency, self.certainty))

    @intent_file_handler('alerts.noaa.intent')
    def handle_alerts_noaa(self, message):
        self.log.debug("handle_alerts for zone_id {}".format(self.zone_id))
        if not self.zone_id:
            self.speak_dialog('error')
            return

        alerts = self.noaa.alerts(zone=self.zone_id)
        foundalerts = False

        for alert in alerts['features']:
            ap = alert['properties']
            status = ap['status']
            msgType = ap['messageType']
            urgency = ap['urgency']
            severity = ap['severity']
            certainty = ap['certainty']
            category = ap['category']

            if status=='Actual' and msgType in ['Alert', 'Update'] and severity in self.severity and certainty in self.certainty and urgency in self.urgency:
                if not foundalerts:
                    #self.speak_dialog('alerts.noaa')            
                    foundalerts = True
                self.alerts.append(ap)
        self.log.info("found alerts: {}".format(len(self.alerts)))

        if foundalerts:
            self.status = "speaking"
            for alert in self.alerts:
                event = alert["event"]
                headline = alert['headline']
                description = alert['description']

                wait_while_speaking()
                if self.status == "speaking":
                    self.speak(event)
                if self.status == "speaking":
                    self.speak(description)

    def stop(self):
        self.status = "stopped"
        self.log.info("NOAA stop")

def create_skill():
    return NoaaAlerts()

