# Simple GeoIP ForwardAuth for Traefik

Return HTTP 200 is the IP is allowed to access services, HTTP 403 otherwise.

## Preparation
You will need the GeoLite2-City.mmdb database from MaxMind.

This database can be obtained free of charge from MaxMind by making an account on https://dev.maxmind.com/geoip/geolite2-free-geolocation-data?lang=en.

The container expects the database available on `/db/GeoLite2-City.mmdb`.

Alternatively, you can create a license key and have the container automatically download the database for you if it isn't found (see configuration).

## Configuration
### Environment variables
| Environment variable | Description |
| -------------------- | ----------- |
| SIMPLE_GEOIP_FORWARDAUTH_MAXMIND_LICENSE_KEY | A MaxMind license key to automatically download and update the GeoIP database (optional) |

### URL generation
This container will look at the request URL to calculate if a request is allowed or not.

#### locations
locations is a semi-colon separated list of countries. Each country can contain a comma-separated list of areas.

For example, to allow the whole of the Netherlands:
```
NL
```

To allow only [the top 3 most LGBT-friendly US states](https://eu.usatoday.com/story/money/2020/06/19/the-best-and-worst-states-for-lgbtq-people/111968524/) (Nevada, Vermont and New York):
```
US:NV,VT,NY
```

To allow all of the Netherlands and the above-named US states:
```
NL;US:NV,VT,NY
```

#### ips
IPs is a comma-separated list of IPs or networks allowed. For example, to allow both 127.0.0.1 and 192.168.0.0/16 simply use:
```
127.0.0.1,192.168.0.0/16
```

## Setup
*Note: in the setup steps, I will use the locations and ip example explained above*

Start the container into a bridge network called `geoipforwardauth`, giving it the hostname `geoip`. Then, make sure your Traefik container is also in that network.

On your Traefik container, add a label with URLencoded parameters stating the allowed sources:
```
labels:
- traefik.http.middlewares.simple-geoip.forwardauth.address=http://geoip:5000/?locations=NL;US:NV,VT,NY&ips=127.0.0.1,192.168.0.0/16
```

Now, add this newly made simple-geoip middleware to the desired container labels:
```
labels:
- traefik.http.routers.my_route.middlewares=simple-geoip@docker
```
