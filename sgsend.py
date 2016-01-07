#!/usr/bin/python
## Simple command line utility to send mail notifications via sendgrid from the command line

import sendgrid
import sys, getopt
from ConfigParser import SafeConfigParser
import os.path

## Global Variables
_debug = 0
_CONFIG_FILE_NAME = 'sgsend.cnf'
_CONFIG = None

def readConfig():
    ## retrieves the API key from one of several standard places, or returns None if not found
    ## First check $HOME/.sgsend.conf, and if not, look in /etc/sgsend.conf
    global _CONFIG, _CONFIG_FILE_NAME, _debug

    if _CONFIG is not None:
        return _CONFIG

    _CONFIG = SafeConfigParser()
    global_config_file = os.path.join("/", "etc",  _CONFIG_FILE_NAME)
    user_config_file = os.path.join(os.path.expanduser("~"), ".config", "sgsend", _CONFIG_FILE_NAME)
    config_files_found = _CONFIG.read([global_config_file, user_config_file, _CONFIG_FILE_NAME])

    if len(config_files_found) == 0:
        print "Could not locate config file in /etc, ~/.config/sgsend or in the current directory: ", config_file
        return None

    if _debug:
        print "Found config files: ", ",".join(config_files_found)

    return _CONFIG

def getAPIKey():

    theKey = getConfig('auth', 'api_key')
    if theKey is None:
        print "*** ERROR *** Unable to retrieve API Key from config file. Is there an 'api_key' option in the 'auth' section?"
        sys.exit(1)

    if _debug:
        print "Using API Key: ", theKey

    return (theKey)

def getConfig(section, option, defaultValue=None):
    config = readConfig()
    if config is None or not config.has_option(section, option):
        if _debug:
            print "Using default value of '", defaultValue, "' for section '", section, "', option '", option, "'"
        return defaultValue

    theValue = config.get(section, option)
    if _debug:
        print "Using value '", theValue, "' for option '", option, "' from section '", section, "'"

    return (theValue)

def usage(argv):
    SG_FROM=getConfig('mail', 'from', 'sgsend@example.com')
    SG_SUBJECT=getConfig('mail', 'subject', 'Automated Notification from sgsend')

    print """Usage: %s [options] TO_EMAIL [message text]
Options:
    -m --message:
         Message text, can also be supplied after the options, but this option allows control over
         embedded spaces. When supplied with the option, the message body is sent verbatim with
         any embedded spaces etc., but when supplied after the TO_EMAIL they are treated as separate
         words and are sent with a single embedded space between the words.
         If the message text is neither supplied with the option nor after the TO_EMAIL then
         the message text is taken from stdin. Note that this is a blocking read, so you should
         use a pipe or unix redirection in batch (non-interactive) scripts.
    -s --subject:
         Subject line of email
    -f --from: 
         The FROM that the email will appear to be from (default: %s)
    -d:
         Turns on verbose debugging messages (default: %s)
""" % (argv[0], SG_FROM, SG_SUBJECT)


def main(argv):
    #set up basic variables
    global _API_KEY, _debug
    SG_FROM=getConfig('mail', 'from', 'sgsend@example.com')
    SG_SUBJECT=getConfig('mail', 'subject', 'Automated Notification from sgsend')
    SG_BODY_TEXT="If you are seeing this, I'm sorry but something probably went wrong with sgsend. :-("

    ## process the command line arguments
    try:
        opts, args = getopt.getopt(argv[1:], "hs:f:m:d", ["help", "subject=", "from=", "message="])
    except getopt.GetoptError:
        usage(argv)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(argv)
            sys.exit(0)
        elif opt == '-d':
            _debug = 1
            print "Debugging messages turned ON"
        elif opt in ("-s", "--subject"):
            SG_SUBJECT = arg
            if _debug:
                print "Setting subject from command line option:", SG_SUBJECT
        elif opt in ("-f", "--from"):
            SG_FROM = arg
            if _debug:
                print "Setting FROM ADDRESS from command line option:", SG_FROM
        elif opt in ("-m", "--message"):
            SG_BODY_TEXT = arg
            if _debug:
                print "Setting body text from command line option:", SG_BODY_TEXT

    ## process the other arguments
    if len(args) == 0:
        print "**ERROR** No TO_EMAIL found."
        usage(argv)
        sys.exit(1)

    SG_TO = args[0]
    if _debug:
        print "TO_EMAIL is set to: ", SG_TO

    if len(SG_TO) == 0:
        print "**ERROR** Empty TO_EMAIL address"
        usage(argv)
        sys.exit(1)

    if len(args) > 1:
        SG_BODY_TEXT = " ".join(args[1:])
        if _debug:
            print "Retrieving body text from command line:", SG_BODY_TEXT

    if len(SG_BODY_TEXT) == 0:
        ## get it from stdin
        SG_BODY_TEXT = sys.stdin.readlines()
        if _debug:
            print "Retrieving body text from stdin:", SG_BODY_TEXT

    if len(SG_BODY_TEXT) == 0:
        ## still 0, so give up
        usage(argv)
        sys.exit(1)


    sg = sendgrid.SendGridClient(getAPIKey())
    
    if sg is None:
        print "Unable to create client object. Are you sure you have the right API key embedded in the code?"
        sys.exit(1)
    elif _debug:
        print "Created Client Object ..."

    message = sendgrid.Mail()
        
    if message is None:
        print "Unable to create message object, giving up."
        sys.exit(1)
    elif _debug:
        print "Created Message Object ..."

    message.add_to(SG_TO)
    message.set_subject(SG_SUBJECT)
    message.set_text(SG_BODY_TEXT)
    message.set_from(SG_FROM)
    status, msg = sg.send(message)

    if _debug:
        print "Status Code: ", status
        print "Status Message: ", msg


if __name__ == "__main__":
  main(sys.argv)
