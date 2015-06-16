"""ZNC AlertMod - Module to send user an alert when their nick is mentioned"""

import os
import smtplib

import znc


class alertmod(znc.Module):
    description = "Alert module"
    module_types = [znc.CModInfo.NetworkModule]
    wiki_page = 'https://github.com/treytabner/znc-alert/wiki'

    def OnLoad(self, args, message):
        if not self.nv.get('smtp_server') or not self.nv.get('alert_email'):
            self.do_help()

        return znc.CONTINUE

    def OnModCommand(self, command):
        try:
            if command.lower().startswith("set "):
                (_, key, value) = command.split()
                if ((key.lower() == 'smtp_server' or
                     key.lower() == 'alert_email')):
                    self.nv[key.lower()] = value
                    return znc.CONTINUE
        except:
            pass

        if not command.lower().startswith("help"):
            self.PutModule("Sorry, I didn't understand.")
        self.do_help()

        return znc.CONTINUE

    def OnPrivAction(self, nick, message):
        return self.alert(message, nick, action=True)

    def OnChanAction(self, nick, channel, message):
        return self.alert(message, nick, channel=channel, action=True)

    def OnPrivMsg(self, nick, message):
        return self.alert(message, nick)

    def OnChanMsg(self, nick, channel, message):
        return self.alert(message, nick, channel=channel)

    def do_help(self):
        if self.nv.get('smtp_server'):
            self.PutModule("Your outgoing SMTP server is set to: %s" %
                           self.nv.get('smtp_server'))
        else:
            self.PutModule("Please set your outgoing SMTP server, for "
                           "example: 'set smtp_server mail.example.com'")

        if self.nv.get('alert_email'):
            self.PutModule("Your alert email address is set to: %s" %
                           self.nv.get('alert_email'))
        else:
            self.PutModule("Please set your alert email address, for "
                           "example: 'set alert_email user@example.com'")

        if self.nv.get('smtp_server') and self.nv.get('alert_email'):
            self.PutModule("You can update your settings with: "
                           "'set smtp_server ...' or 'set alert_email ...'")

        try:
            text_message = self.nv.get('alert_email').split('@')[0].isdigit()
        except:
            text_message = False

        if not text_message:
            self.PutModule("Did you know you can send "
                           "yourself a text message too?")
            self.PutModule("""
AT&T - cellnumber@txt.att.net
Verizon - cellnumber@vtext.com
T-Mobile - cellnumber@tmomail.net
Sprint PCS - cellnumber@messaging.sprintpcs.com
Virgin Mobile - cellnumber@vmobl.com
US Cellular - cellnumber@email.uscc.net
Nextel - cellnumber@messaging.nextel.com
Boost - cellnumber@myboostmobile.com
Alltel - cellnumber@message.alltel.com
""".strip())

    def alert(self, message, nick, channel=None, action=False):
        # Make sure we've been setup first
        if not self.nv.get('smtp_server') or self.nv.get('alert_email'):
            return self.do_help()

        # If we're not away, ignore
        if not self.GetNetwork().IsIRCAway():
            return znc.CONTINUE

        my_nick = self.GetNetwork().GetNick()

        # Don't bother sending ourselves email
        if my_nick == nick.GetNick():
            return znc.CONTINUE

        if channel and my_nick not in message.s:
            return znc.CONTINUE

        fromaddr = 'ZNC <%s@%s>' % (os.environ.get('USER'),
                                    os.environ.get('HOSTNAME'))
        if action:
            body = '* %s %s' % (nick.GetNick(),
                                message.s) if channel else message.s
        else:
            body = '<%s> %s' % (nick.GetNick(),
                                message.s) if channel else message.s
        subject = channel.GetName() if channel else nick.GetNick()
        msg_tpl = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s"
        msg = msg_tpl % (fromaddr, self.nv.get('alert_email'), subject, body)

        server = smtplib.SMTP(self.nv.get('smtp_server'))
        server.sendmail(fromaddr, [self.nv.get('alert_email')], msg)
        server.quit()

        return znc.CONTINUE
