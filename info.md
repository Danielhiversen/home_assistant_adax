Async integration for Adax heaters

[Buy me a coffee :)](http://paypal.me/dahoiv)

{% if version_installed.replace(".","") | int <= 22  %}
## Change in platform

For versions above 0.2.2 the setting of account_id has been replaced with username.
After installation of this update using configuration.yaml change your configuration to match below (replace account_id with username)
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

1.
Go to integration page in HA, press + and search for Adax
Enter your account id as username
Enter your remote secret as password

2.
In configuration.yaml:

```
climate:
  - platform: adax
    username: "112395"  # replace with your account ID (see Adax WiFi app, Account Section)
    password: "6imtpX63D5WoRyKh"  # replace with your remote user password (see Adax WiFi app, Account Section)
```
