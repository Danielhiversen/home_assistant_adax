# Adax heaters
![Validate with hassfest](https://github.com/Danielhiversen/home_assistant_adax/workflows/Validate%20with%20hassfest/badge.svg)
[![GitHub Release][releases-shield]][releases]
[![hacs_badge][hacs-shield]][hacs]

Custom component for using [Adax](https://adax.no/en/) heaters in Home Assistant.

[Support the developer](http://paypal.me/dahoiv)


## Install
Use [hacs](https://hacs.xyz/) (probably easier) or copy the files to the custom_components folder in Home Assistant (should be placed in the same folder as configuration.yaml) .

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

## API

API details: https://adax.no/om-adax/api-development/


[releases]: https://github.com/Danielhiversen/home_assistant_adax/releases
[releases-shield]: https://img.shields.io/github/release/Danielhiversen/home_assistant_adax.svg?style=popout
[downloads-total-shield]: https://img.shields.io/github/downloads/Danielhiversen/home_assistant_adax/total
[hacs-shield]: https://img.shields.io/badge/HACS-Default-orange.svg
[hacs]: https://hacs.xyz/docs/default_repositories
