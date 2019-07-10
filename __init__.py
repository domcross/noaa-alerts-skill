from mycroft import MycroftSkill  #, intent_file_handler
from mycroft.skills.core import intent_handler, intent_file_handler
from mycroft.audio import wait_while_speaking
from noaa_sdk import noaa
from datetime import datetime, date

class NoaaAlerts(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.noaa = noaa.NOAA()

    def initialize(self):
        self._setup()
        self.settings.set_changed_callback(self.on_websettings_changed)

    def on_websettings_changed(self):
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
        if self.settings.get('auto_alert', False):
            self.monitoring = True
            self.update_interval = self.settings.get("update_interval", 10) * 60
            self.schedule_repeating_event(handler=self.auto_alert_handler, when=datetime.now(), frequency=self.update_interval, name='NOAAalerts')
            self.log.info("auto_alert on, update_interval {} seconds".format(self.update_interval))
        else:
            self.monitoring = False
            self.cancel_scheduled_event('NOAAalerts')
            self.log.info("auto_alert off")

    #def auto_alert_handler(self, message):
    def auto_alert_handler(self):
        self.log.info("auto_alert_handler")
        self._check_for_alerts(self.zone_id)
        filteredalerts = []
        for ap in self.alerts:
            #ap = alert['properties']
            status = ap['status']
            msgType = ap['messageType']
            urgency = ap['urgency']
            severity = ap['severity']
            certainty = ap['certainty']
            # filter messages: only actual and severity/certainty/urgency according to skill setting
            if status=='Actual' and msgType in ['Alert'] and severity in "Extreme,Severe" and certainty in "Observed" and urgency in "Immediate":
                filteredalerts.append(ap)

        self.log.info("found alerts: {}".format(len(filteredalerts)))

        if filteredalerts:
            self.status = "speaking"
            self.speak_dialog("alerts.noaa")
            for alert in filteredalerts:
                #event = alert["event"]
                headline = alert['headline']
                instruction = alert['instruction']

                wait_while_speaking()
                #if self.status == "speaking":
                #    self.speak(event)
                if self.status == "speaking":
                    self.speak(headline)
                if self.status == "speaking":
                    self.speak(instruction) 

    @intent_file_handler('alerts.noaa.intent')
    def handle_alerts_noaa(self, message):
        self.log.debug("handle_alerts for zone_id {}".format(self.zone_id))
        if not self.zone_id:
            self.speak_dialog('error')
            return

        if self.monitoring:
            foundalerts = len(self.alerts) > 0
        else:
            foundalerts = self._check_for_alerts(self.zone_id)
        if not foundalerts:
            self.speak_dialog("noalerts.noaa")
            return

        filteredalerts = []
        foundalerts = False
        for ap in self.alerts:
            #ap = alert['properties']
            status = ap['status']
            msgType = ap['messageType']
            urgency = ap['urgency']
            severity = ap['severity']
            certainty = ap['certainty']
            # filter messages: only actual and severity/certainty/urgency according to skill setting
            if status=='Actual' and msgType in ['Alert', 'Update'] and severity in self.severity and certainty in self.certainty and urgency in self.urgency:
                if not foundalerts:
                    filteredalerts = []
                    foundalerts = True
                filteredalerts.append(ap)

        self.log.info("found alerts: {}".format(len(filteredalerts)))

        if foundalerts:
            self.status = "speaking"
            self.speak_dialog("alerts.noaa")
            for alert in filteredalerts:
                event = alert["event"]
                #headline = alert['headline']
                description = alert['description']

                wait_while_speaking()
                if self.status == "speaking":
                    self.speak(event)
                if self.status == "speaking":
                    self.speak(description)
        else:
            self.speak_dialog("noalerts.noaa")


    def _check_for_alerts(self, zone_id=""):
        foundalerts = False
        if not zone_id:
            self.alerts = []
            return foundalerts
        self.log.debug("_check_for_alerts")
        newalerts = self.noaa.alerts(zone=zone_id)

        for alert in newalerts['features']:
            ap = alert['properties']
            # filter messages: only sent today or not expired
            if self._get_datetime(ap['sent']).date() == date.today() or ("expires" in ap.keys() and self._get_datetime(ap['expires']).date() >= date.today()):
                if not foundalerts:
                    self.alerts = []
                    foundalerts = True
                self.alerts.append(ap)
        return foundalerts

    def stop(self):
        self.status = "stopped"
        self.log.info("NOAA stop")

    def _get_datetime(self, dt_string):
        # "YYYY-MM-DDThh:mm:ssXzh:zm" -> "YYYY-MM-DDThhmmssXzhzm" for easier pattern matching
        dt_object = datetime.strptime(dt_string.replace(':', ''), "%Y-%m-%dT%H%M%S%z")
        return dt_object

def create_skill():
    return NoaaAlerts()

