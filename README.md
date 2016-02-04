# sgsend: Command Line interface to send email using SendGrid

SendGrid is a email service provider that supports a range of language interfaces to send email. Details at www.sendgrid.com

sgsend is a simple Python utility that allows you to send email from the unix command line via the Send Grid service. Of course this is only useful if you don't already have a mail transport mechanism installed on the machine, which is the case on my Mac as well as on most of the cloud servers that I install. I find it easier to skip setting up postfix etc on my machines and use sendgrid instead.

I use this on my macs and on several different Linux configurations that have Python 2.x installed. YMMV.

## Disclaimer and License

This code is licensed under the MIT License (also supplied in this folder) and you should read it to make sure you understand the terms. It's only a few lines long, and says what it says quite clearly, so please do take the time to read and understand it.

## Installation - Sources and Dependent Modules

sgsend is available on GitHub at [https://github.com/vvaidy/sgsend](https://github.com/vvaidy/sgsend).

You'll also need to install the sendgrid python API, which is also on GitHub but you can also install it using pip or easy_install:

```
pip install sendgrid
# or
easy_install sendgrid
```


## Setting up the SendGrid API Key

Before you can send email using sgsend, you will need to generate a SendGrid API key that you'll need in the configuration step below. It's simple enough to generate a key through your [SendGrid Dashboard](https://app.sendgrid.com/settings/api_keys).

## Configuration

`sgsend` looks for its configuration information in a series of files. The config files are consulted in the following order, with later files overriding values from earlier files, and command line options overriding the config parameters:

* /etc/sgsend.cnf
* ~/.config/sgsend.cnf
* ./sgsend.cnf

A config file should look something like this:

```
[auth]
API_KEY=YOUR API KEY HERE
[mail]
from=devops@yourcompany.com
subject=Automated Notification from sgsend
```

## Generating a config file

You can interactively generate a config file by using the `--config` command, which will prompt you for the information you need. The only mandatory value is for the API_KEY, you can skip the other values.

```
$ ./sgsend.py --config
Hit ENTER to skip a particular configuration value.
(required) API Key: THIS_IS_MY_API_KEY_I_GOT_FROM_SENDGRID
(optional) From: vijay@MyEmailForever.com
(optional) Subject:
Destination (enter a for all users, u for this user, d for this directory): u

***************
*** WARNING ***
***************

The file /Users/vijay/.config/sgsend/sgsend.cnf already exists.

Are you sure you want to irretrievably overwrite it? (Y/N): y
Configuration successfully written to '/Users/vijay/.config/sgsend/sgsend.cnf'
$
```

## Installation

You can either run the python program directly (with `./sgsend.py`) as I showed you above, or just put it someplace in your PATH.

This is what I usually do on a new machine:

```
sudo cp ./sgsend.py /usr/local/bin/sgsend
sudo chmod +x /usr/local/bin/sgsend
sgsend --configure
```

Good Luck!
