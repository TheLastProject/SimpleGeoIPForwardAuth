import ipaddress
import logging

import geoip2.database

from flask import Flask, abort, request

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)


class Helpers:
    HEADER_START = "SIMPLE_GEOIP_FORWARDAUTH_ALLOW_LOCATION_"

    __data = {
        'init': False,
        'geoip_reader': None,
        'cache': {}
    }

    @staticmethod
    def _init():
        if not Helpers.__data['init']:
            Helpers.__data['geoip_reader'] = geoip2.database.Reader('/db/GeoLite2-City.mmdb')

    @staticmethod
    def _format_cache(ip_allowlist, location_allowlist):
        return "{ip_allowlist}%{location_allowlist}"

    @staticmethod
    def _get_cache(ip, ip_allowlist, location_allowlist):
        entry = Helpers._format_cache(ip_allowlist, location_allowlist)
        if entry not in Helpers.__data['cache']:
            Helpers.__data['cache'][entry] = {}

        return Helpers.__data['cache'][entry].get(ip, None)

    @staticmethod
    def _write_cache(ip, allowed, ip_allowlist, location_allowlist):
        Helpers.__data['cache'][Helpers._format_cache(ip_allowlist, location_allowlist)][ip] = allowed

    @staticmethod
    def is_allowed(ip, ip_allowlist, location_allowlist):
        cache = Helpers._get_cache(ip, ip_allowlist, location_allowlist)

        if cache is not None:
            return cache

        Helpers._init()

        # Check if IP is allowed explicitly
        allowed = Helpers._in_ip_allowlist(ip, ip_allowlist)
        if not allowed:
            # Check if IP is in allowed area
            allowed = Helpers._is_allowed_area(ip, location_allowlist)

        # Cache result
        Helpers._write_cache(ip, allowed, ip_allowlist, location_allowlist)
        return allowed

    @staticmethod
    def _in_ip_allowlist(ip, ip_allowlist):
        if not ip_allowlist:
            return False

        ip = ipaddress.ip_address(ip)
        for allowed_ip in ip_allowlist:
            if ip in ipaddress.ip_network(allowed_ip):
                return True

        return False

    @staticmethod
    def _is_allowed_area(ip, location_allowlist):
        countries = location_allowlist.split(";")

        match = Helpers.__data['geoip_reader'].city(ip)
        iso_country = match.country.iso_code
        iso_subdivision = match.subdivisions.most_specific.iso_code

        for entry in countries:
            if ":" in entry:
                country, areas = entry.split(":", 1)
            else:
                country = entry
                areas = None

            if iso_country == country:
                if areas is None:
                    app.logger.info(f"[ALLOW] {ip}: {iso_country} ({iso_subdivision})")
                    return True
                else:
                    for area in areas.split(","):
                        if iso_subdivision == area:
                            app.logger.info(f"[ALLOW] {ip}: {iso_country} ({iso_subdivision})")
                            return True
                    app.logger.info(f"[DENY] {ip}: {iso_country} ({iso_subdivision})")
                    return False

        app.logger.info(f"[DENY] {ip}: {iso_country} ({iso_subdivision})")
        return False


@app.route("/")
def check_ip():
    location_allowlist = request.args.get('locations', default='')
    ip_allowlist = request.args.get('ips', default='')

    app.logger.debug(f"Checking {request.access_route} for locations {location_allowlist} with IP allowlist {ip_allowlist}")
    for request_ip in request.access_route:
        if not Helpers.is_allowed(request_ip, ip_allowlist, location_allowlist):
            abort(403)
            return "FORBIDDEN"

    app.logger.debug(f"Allowed {request.access_route}")
    return "OK"


if __name__ == '__main__':
    app.run()
