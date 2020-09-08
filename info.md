[Buy me a coffee :)](http://paypal.me/dahoiv)

Async integration for Adax heaters

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



## Install
In configuration.yaml:

```
climate:
  - platform: adax
    account_id: "112395"  # replace with your account ID (see Adax WiFi app, Account Section)
    password: "6imtpX63D5WoRyKh"  # replace with your remote user password (see Adax WiFi app, Account Section)
```
