Integration for Adax heaters

[Buy me a coffee :)](http://paypal.me/dahoiv)

{% if version_installed.replace(".","") | int <= 22  %}
## Configuration by integration page

Option to implement using integrations page has been introduced.
{% endif %}

{%- if selected_tag == "master" %}
## This is a development version!
This is **only** intended for test by developers!
{% endif %}

{%- if prerelease %}
## This is a beta version
Please be careful and do NOT install this on production systems. Also make sure to take a backup/snapshot before installing.
{% endif %}

# Features
- Support for all Adax wifi heaters
- See temperature and set temperature
- Change set temperature and turn on/off


## Configuration (2 options)

You have two alternatives. In either case, you'll need the Account ID (which can be found in the Adax Wifi app, pressing 'Account'). You will also need a credential, which you can create in the 'Account' pane, selecting 'Remote user client API'. A new pane will open and you need to press 'Add credential', after which you should copy the password.

Alternative 1:
Go to integration page in HA, press + and search for Adax
Enter your account id as Account ID
Enter your credential password

Alternative 2:
In configuration.yaml:

```
climate:
  - platform: adax
    account_id: "112395"  # replace with your account ID 
    password: "6imtpX63D5WoRyKh"  # replace with your credential password
```

