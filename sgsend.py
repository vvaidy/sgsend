#!/usr/bin/env python
## Simple command line utility to send mail notifications via sendgrid from the command line

import sendgrid
import sys, getopt, re
from ConfigParser import SafeConfigParser
import os.path

## Global Variables
_debug = 0
_CONFIG_FILE_NAME = 'sgsend.cnf'
_CONFIG = None
_DEFAULT_FROM = 'sgsend@example.com'
_DEFAULT_SUBJECT = 'Automated Notification from sgsend'

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
        if _debug:
            print "Could not locate config file in /etc, ~/.config/sgsend or in the current directory: ", _CONFIG_FILE_NAME
        return None

    if _debug:
        print "Found config files: ", ",".join(config_files_found)

    return _CONFIG

def getConfig(section, option, defaultValue=None):
    global _debug
    config = readConfig()

    if config is None or not config.has_option(section, option):
        if _debug:
            print "Using default value of '%s' for section '%s', option '%s'" % (defaultValue, section, option)
        return defaultValue

    theValue = config.get(section, option)
    if _debug:
            print "Using retrieved value of '%s' for section '%s', option '%s'" % (theValue, section, option)

    return (theValue)

def getAPIKey():
    global _debug
    theKey = getConfig('auth', 'api_key')
    if theKey is None:
        print "*** ERROR *** Unable to retrieve API Key from config file. Is there an 'api_key' option in the 'auth' section?"
        sys.exit(1)

    if _debug:
        print "Using API Key: ", theKey

    return (theKey)

def genConfig():
    global _debug
    print("Hit ENTER to skip a particular configuration value.")
    apiKey = ''
    while not apiKey:
        apiKey = raw_input("(required) API Key: ").strip()
    fromStr = raw_input("(optional) From: ").strip()
    subStr = raw_input("(optional) Subject: ").strip()
    where = ''

    while where not in ['a', 'u', 'd']:
        where = raw_input('Destination (enter a for all users, u for this user, d for this directory): ').strip()

    fileDest = '.'

    if where == 'a':
        fileDest = os.path.join("/", "etc")
    elif where == 'u':
        fileDest = os.path.join(os.path.expanduser("~"), ".config", "sgsend")

    config = "[auth]\nAPI_KEY=%s\n[mail]\n" % apiKey

    if fromStr:
        config += "from=" + fromStr + "\n"
    if subStr:
        config += "subject=" + subStr + "\n"

    if _debug:
        print"Configuration (file destination: %s)\n%s" % (fileDest, config)

    configFilename = os.path.join(fileDest, _CONFIG_FILE_NAME)
    try:
        if not os.path.exists(fileDest):
            os.makedirs(fileDest)
        if os.path.exists(configFilename):
            yn = ''

            while yn not in ['y', 'n']:
                yn = raw_input(
"""
***************
*** WARNING ***
***************

The file %s already exists.

Are you sure you want to irretrievably overwrite it? (Y/N): """ % configFilename
                ).strip().lower()
                if yn not in ['y', 'n']:
                    print "Please enter 'Y' or 'N'"

            if yn == 'n':
                print "OK, exiting without writing configuration file."
                return
        ## safe to proceed.
        file = open(configFilename, "w")
        file.write(config)
        print "Configuration successfully written to '%s'" % configFilename
    except IOError as e:
        print "**ERROR** Configuration information could not be written to %s, probable cause: %s" % (configFilename, e.strerror)

def usage(argv):
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
         Subject line of email (overrides config defaults)
    -f --from: 
         The FROM that the email will appear to be from (overrides config defaults)
    --configure:
         Interactively generates an sgsend configuration file
    -d:
         Turns on verbose debugging messages
""" % argv[0]


def main(argv):
    #set up basic variables
    global _debug, _DEFAULT_FROM, _DEFAULT_SUBJECT, _DEFAULT_BODY_TEXT
    ## set up code defaults
    SG_SUBJECT = _DEFAULT_SUBJECT
    SG_FROM = _DEFAULT_FROM
    SG_BODY_TEXT = None

    ## process the command line arguments
    try:
        opts, args = getopt.getopt(argv[1:], "hs:f:m:d", ["help", "subject=", "from=", "message=", "configure"])
    except getopt.GetoptError:
        usage(argv)
        sys.exit(2)

    # process the debug flag first
    if '-d' in argv:
        _debug = 1
        print "Debugging messages turned ON"

    ## override code defaults with config defaults
    SG_SUBJECT=getConfig('mail', 'subject', SG_SUBJECT)
    SG_FROM=getConfig('mail', 'from', SG_FROM)
    ## override config defaults with command line defaults and
    ## process other command lines while we are at it
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(argv)
            sys.exit(0)
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
        elif opt in ("--configure"):
            if _debug:
                print "Generating configuration file:"
            genConfig()
            sys.exit(1)

    ## process the other arguments
    if len(args) == 0:
        print "**ERROR** No TO_EMAIL found."
        usage(argv)
        sys.exit(1)

    SG_TO = args[0].strip()

    if not re.match(r'[^@]+@[^@]+\.[^@]+', SG_TO):
        print "*********\n**ERROR**\n********* TO_EMAIL address (%s) looks suspect." % SG_TO
        usage(argv)
        sys.exit(2)

    if len(args) > 1 and SG_BODY_TEXT is None:
        SG_BODY_TEXT = " ".join(args[1:])
        if _debug:
            print "Retrieving body text from command line:", SG_BODY_TEXT

    if SG_BODY_TEXT is None:
        ## get it from stdin
        SG_BODY_TEXT = "".join(sys.stdin.readlines())
        if _debug:
            print "Retrieving body text from stdin:", SG_BODY_TEXT

    if not SG_BODY_TEXT:
        ## still 0, so give up
        usage(argv)
        sys.exit(1)

    if _debug:
        print "TO is set to: ", SG_TO
        print "FROM is set to: ", SG_FROM
        print "SUBJECT is set to: ", SG_SUBJECT
        print "BODY is set to: ", SG_BODY_TEXT

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

    if status != 200:
        print "**** WARNING *** Unexpected status code: %d, probable cause: %s" % (status, msg)

if __name__ == "__main__":
  main(sys.argv)
