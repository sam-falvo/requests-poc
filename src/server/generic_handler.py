#!/usr/bin/env python
#
# Generic web handler logic, applicable regardless of endpoint.

import logging

from tornado.web import RequestHandler
from tornado.escape import json_decode, json_encode


LOG = logging.getLogger(__name__)


def status(stats, msg=None):
    """
    Builds a dictionary containing a standard response format.

    {
        "status": s,
        "msg": m,
    }

    where:
    s is typically either "error" or "ok", and,
    m may be None or some other helpful, human-readable response message.
    """
    return {"status": stats, 'msg': msg}


def err(msg):
    """
    Answer with an error response dictionary.  Message payload required.
    """
    return status("error", msg)


def ok(msg=None):
    """
    Answer with a successful response dictionary.  Message payload optional.
    """
    return status("ok", msg)


def missing_field(field_name):
    """
    Answer with a standard error response for when the API client is missing
    a required field in its payload.
    """
    return err("Missing input `{}`".format(field_name))


class V3Handler(RequestHandler):
    """
    This class provides a common handler base class for all V3 handlers.
    It enhances RequestHandler with the following features:

    - Standard responses for API endpoints, including both error and success
      methods.

    - Standardized request logging.
    """

    # V3Handler-specific logic

    def _v3log(self, meth, status, msg):
        self.set_status(status)
        self.write(msg)
        meth("{}".format(msg))
        self.finish()

    def _error(self, msg, status=404):
        self._v3log(LOG.error, status, err(msg))

    def _exception(self, msg, status=500):
        self._v3log(LOG.exception, status, err(msg))

    def _ok(self, msg=None):
        self.write(ok(msg))
        self.finish()

    def missing_field(self, term):
        self._exception(missing_field(term))

    def not_live_system(self):
        self._error(
            "The given serial or token combination "
            "is not associated with a live system."
        )

    def forbidden(self, msg=None):
        self._error(
            "Permission denied ({})".format(msg),
            status=403,
        )

    def no_data(self, qualifier=None):
        self._error(
            "No data found{}"
            .format(
                " for {}"
                .format(qualifier) if qualifier else ""
            )
        )

    def method_not_allowed(self):
        self._error("Method not allowed", status=405)

    def conflict(self, term):
        self._error("Conflict detected ({})".format(term))

    def failed_precondition(self, term):
        self._error("Failed precondition ({})".format(term), status=412)

    def get_arg(self, arg_name, default=None, return_none=False):
        arg_val = self.get_argument(arg_name, None)
        if arg_val is None:
            arg_val = self.dic.get(arg_name, default)
            if arg_val is None:
                if not return_none:
                    raise KeyError(arg_name)
        return arg_val

    def _safely_handle(self, method, args=[], kw_args={}):
        """
        Safely handle any of the mixin handler methods by invoking it,
        and providing a standard set of exception handlers.  If any of
        these exceptions are caught, they're automatically converted into
        HTTP response codes appropriate for their semantics.
        """
        try:
            method(*args, **kw_args)
        except PreconditionError as e:
            self.failed_precondition(e[0])
        except ConflictedError as e:
            self.conflict(e[0])
        except PermissionError as e:
            self.forbidden(e[0])
        except KeyError as ke:
            self.missing_field(ke[0])
        except UnregisteredSystemError as e:
            self.not_live_system()
        
    def _simple_signature(self, specific=None):
        self.dic = dict()
        try:
            self.dic = json_decode(self.request.body)
        except ValueError:
            pass

        return [
            {
                'specific': specific,
            },
        ]

    def _standard_signature(self, specific=None):
        self.dic = dict()
        try:
            self.dic = json_decode(self.request.body)
        except ValueError:
            pass

        return [
            [self.dic],
            {
                'specific': specific,
            },
        ]

    # overriding RequestHandler methods

    def prepare(self):
        method = self.request.method
        url = self.request.path
        source = self.request.remote_ip
        LOG.info("{} - {} {}".format(source, method, url))


class V3GetMixin(object):
    """
    Mixin to encapsulate the common request-handling features of V3 endpoints.
    Focuses on GET endpoint.
    """

    def get(self, specific=None):
        self._safely_handle(
            self._get, *self._standard_signature(specific=specific)
        )

    def _get(self, dic, specific=None):
        raise NotImplementedError


class V3PostMixin(object):
    """
    Mixin to encapsulate the common request-handling features of V3 endpoints.
    Focuses on POST endpoint.
    """

    def post(self, specific=None):
        self._safely_handle(
            self._post, *self._standard_signature(specific=specific)
        )

    def _post(self, dic, specific=None):
        raise NotImplementedError
