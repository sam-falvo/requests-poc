#!/usr/bin/env python
#
# This script and its dependencies is a stripped down version of our API
# daemon which is exhibiting the problem discussed in #4639.  I wish I
# could simplify it further; however, this is as simple as I could make it
# while still preserving the run-time context of our API server.
#
# This source listing is derived directly from the closed-source code I'm
# experiencing problems with.

from __future__ import absolute_import

import argparse
import logging
import logging.config
import os

import tornado.ioloop
import tornado.web
from tornado_cors import CorsMixin

import toml

from src.server.api.config_reserve import ConfigReserve
from src.server.api.toml_client import TomlClient
from src.server.generic_handler import V3Handler


logging.config.fileConfig('logging.ini')
LOG = logging.getLogger(__name__)


class ApiApp(object):

    """
    Top-level class implementing the V3 API.  Configures the event
    loop, etc. from command-line arguments.
    """

    def __init__(self):
        self.app = None
        self.port = 8080

    def main(self):
        LOG.info("V3 starting")
        LOG.info("Registering configuration sources")
        self.cfg = (
            ConfigReserve()
            .with_config_source(TomlClient(
                base_url="http://localhost:8090/test-config.toml",
                headers={
                    'Cache-Control': 'no-cache',
                },
            ))
            .with_config_source(os.environ)
        )
        LOG.info("Parsing arguments")
        self.parse_arguments()
        self.app = self.make_app()
        self.app.listen(self.port)
        LOG.info("Listening on port {}".format(self.port))
        LOG.info("Dropping into main event loop now")
        tornado.ioloop.IOLoop.current().start()

    def parse_arguments(self):
        parser = argparse.ArgumentParser(
            description='Dummy daemon to illustrate issue #4639'
        )

        parser.add_argument(
            '-p', '--port',
            default=self.port,
            type=int,
            help=(
                'Port on which to run the API endpoint.  '
                '(Default: %(default)s)'
            ),
        )

        args = parser.parse_args()
        self.port = args.port or self.port

        LOG.info("Listening on port {}".format(self.port))

    def make_app(self):
        return tornado.web.Application(
            [
                (r"/.*", HealthHandler),
            ],
            debug=True,
            cfg=self.cfg,
        )


class HealthHandler(CorsMixin, V3Handler):

    """
    This class handles GETs to /.  This serves two purposes:
    for programmers, it's a nice cheat-sheet to create your own handler
    classes with; and, for operations, it's a convenient health-check.
    If the server responds, we know that the V3 event loop is up.
    """
    CORS_ORIGIN = '*'
    CORS_METHODS = 'GET'

    def get(self):
        key = self.request.path[1:]     # strip the leading /
        value = self.application.settings['cfg'][key]
        result = {
            'key': key,
            'val': value,
        }
        LOG.info(toml.dumps(result))
        self._ok(result)

    def post(self):
        if self.request.path == '/config/reconfig':
            self.application.settings['cfg'].reconfigure()
            LOG.info("Configuration reloaded")
            self._ok("Configuration reloaded")

        self.method_not_allowed()


if __name__ == "__main__":
    ApiApp().main()
