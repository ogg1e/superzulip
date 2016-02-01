#!/usr/bin/env python
##############################################################################
#
##############################################################################

# A event listener meant to be subscribed to PROCESS_STATE_CHANGE
# events.  It will send zulip messages when processes that are children of
# supervisord transition unexpectedly to the EXITED state.

# A supervisor config snippet that tells supervisor to use this script
# as a listener is below.
#
# [eventlistener:superzulip]
# command=python superzulip
# events=PROCESS_STATE,TICK_60

import os
import sys
import copy
import zulip
import logging
import ssl

logging.basicConfig(filename='/tmp/superZulip.log',level=logging.DEBUG)
logging.debug('at the start of the zulip event listener.')

#os.environ['REQUESTS_CA_BUNDLE'] = os.path.join(
#    '/etc/ssl/certs/',
#   'ca-bundle.crt')

#sys.path.insert(0, os.path.dirname(__file__))
VERSION = "0.1"

doc = """\
superzulip.py [--key=<Zulip API Key>]
        [--stream=<zulip stream>]
        [--user=<zulip user email>]
        [--apiPath=<zulip api path>]
        [--zhost=<zulip server url>]
        [--subject=<zulip subject>]
        [--cert=<path to the cert>]

Options:

--key - API key for the users

--stream - The stream to send messages to

--user - The email address for the zulip bot

--apiPath - The path to the apis (/api/v1/messages or /v1/messages)

--zhost - The URL to the server (https://zulip.com or https://myserver.com:443)

--subject - the subject to be used in the stream

--cert - The full path to the certificate file for https.

A sample invocation:

superzulip.py --key="your api key" --stream="Supervisor" --user="supervisor-bot@yourcompany.com": --apiPath="/api/v1/messages" --zhost="https://myserver:443 --subject="MyServer" --cert="/path/to/cert.crt"

"""

from supervisor import childutils
from superlance.process_state_email_monitor import ProcessStateMonitor


class SuperZulip(ProcessStateMonitor):

    process_state_events = ['PROCESS_STATE_STOPPED','PROCESS_STATE_EXITED','PROCESS_STATE_FATAL']

    @classmethod
    def _get_opt_parser(cls):
        from optparse import OptionParser

        parser = OptionParser()
        parser.add_option("-k", "--key", dest="key", default="",
                          help="Zulip Api Key")

        parser.add_option("-s", "--stream", dest="stream", default="",
                          help="Zulip Stream")

        parser.add_option("-u", "--user", dest="user", default="",
                          help="User Email")

        parser.add_option("-a", "--apiPath", dest="api", default="",
                          help="API Path")

        parser.add_option("-z", "--zhost", dest="hostname", default="",
                          help="Server URL")

        parser.add_option("-j", "--subject", dest="subject", default="",
                          help="Supervisor stream subject")

        parser.add_option("-c", "--cert", dest="cert", default="",
                          help="location of cert bundle")
        return parser

    @classmethod
    def parse_cmd_line_options(cls):
        parser = cls._get_opt_parser()
        (options, args) = parser.parse_args()
        return options

    @classmethod
    def validate_cmd_line_options(cls, options):
        parser = cls._get_opt_parser()
        if not options.key:
            parser.print_help()
            sys.exit(1)
        if not options.stream:
            parser.print_help()
            sys.exit(1)
        if not options.user:
            parser.print_help()
            sys.exit(1)
        if not options.api:
            parser.print_help()
            sys.exit(1)
        if not options.subject:
            parser.print_help()
            sys.exit(1)
        if not options.hostname:
            import socket
            options.hostname = socket.gethostname()

        validated = copy.copy(options)
        return validated

    @classmethod
    def get_cmd_line_options(cls):
        return cls.validate_cmd_line_options(cls.parse_cmd_line_options())

    @classmethod
    def create_from_cmd_line(cls):
        options = cls.get_cmd_line_options()

        if 'SUPERVISOR_SERVER_URL' not in os.environ:
            sys.stderr.write('Must run as a supervisor event listener\n')
            sys.exit(1)

        return cls(**options.__dict__)

    def __init__(self, **kwargs):
        ProcessStateMonitor.__init__(self, **kwargs)
        logging.debug('location of cert = %s ', kwargs['cert']) 
        self.zulip_client = zulip.Client(
           email=kwargs['user'],
           site=kwargs['hostname'],
           api_key=kwargs['key'],
           client="SuperZulip/" + VERSION,
           insecure='false',
           cert_bundle=kwargs['cert'])
 
        sys.path.append(kwargs['api'])

        self.stream = kwargs['stream']
        self.subject = kwargs['subject']
        self.now = kwargs.get('now', None)

    def get_process_state_change_msg(self, headers, payload):
        logging.debug('at the start of the get_process_state_change_msg.')
        pheaders, pdata = childutils.eventdata(payload + '\n')
        logging.debug('pheaders = %s', pheaders)
        logging.debug('pdata = %s', pdata)
        txt = 'Process %(groupname)s:%(processname)s (pid %(pid)s) stopped unexpectedly with a state of %(from_state)s' % pheaders
        logging.debug('The text = %s', txt)
        return txt

    def send_batch_notification(self):
        logging.debug('at the start of the send_batch_notification.')
        message = self.get_batch_message()
        if message:
            self.send_message(message)

    def get_batch_message(self):
        logging.debug('at the start of the get_batch_message.')
        return {
            'subject': self.subject,
            'stream': self.stream,
            'messages': self.batchmsgs
        }

    def send_message(self, message):
        logging.debug('at the start of the send_message. stream = %s', self.stream)
        for msg in message['messages']:
            logging.debug('we have a message: %s', msg)
            message_data = {
              "type": "stream",
              "to": message["stream"],
              "subject": message["subject"],
              "content": msg,
            }
            logging.debug('message data : %s', message_data)
            logging.debug(': %s', message_data)
            logging.debug('client response = %s', self.zulip_client.send_message(message_data))
            logging.debug('message sent')

def main():
    superZ = SuperZulip.create_from_cmd_line()
    superZ.run()

if __name__ == '__main__':
    main()
