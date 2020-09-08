# Adax heaters

Custom component for using [Adax](https://adax.no/en/) heaters in Home Assistant.

## Install
Use [hacs](https://hacs.xyz/) or copy the files to the custom_components folder in Home Assistant config.

In configuration.yaml:

```
climate:
  - platform: adax
    account_id: "112395"  # replace with your account ID (see Adax WiFi app, Account Section)
    password: "6imtpX63D5WoRyKh"  # replace with your remote user password (see Adax WiFi app, Account Section)
```

API details: https://adax.no/om-adax/api-development/

[Buy me a coffee :)](http://paypal.me/dahoiv)
