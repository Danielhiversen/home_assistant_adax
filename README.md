# Adax heaters
![Validate with hassfest](https://github.com/Danielhiversen/home_assistant_adax/workflows/Validate%20with%20hassfest/badge.svg)
[![GitHub Release][releases-shield]][releases]
[![hacs_badge][hacs-shield]][hacs]

Custom component for using [Adax](https://adax.no/en/) heaters in Home Assistant.

[Support the developer](http://paypal.me/dahoiv)


## Install
Use [hacs](https://hacs.xyz/) or copy the files to the custom_components folder in Home Assistant config.

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
    account_id: "112395"  # replace with your account ID (see Adax WiFi app, Account Section)
    password: "6imtpX63D5WoRyKh"  # replace with your remote user password (see Adax WiFi app, Account Section)
```

## API

API details: https://adax.no/om-adax/api-development/


[releases]: https://github.com/Danielhiversen/home_assistant_adax/releases
[releases-shield]: https://img.shields.io/github/release/Danielhiversen/home_assistant_adax.svg?style=popout
[downloads-total-shield]: https://img.shields.io/github/downloads/Danielhiversen/home_assistant_adax/total
[hacs-shield]: https://img.shields.io/badge/HACS-Default-orange.svg
[hacs]: https://hacs.xyz/docs/default_repositories
