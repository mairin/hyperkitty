# -*- coding: utf-8 -*-
# Copyright (C) 1998-2012 by the Free Software Foundation, Inc.
#
# This file is part of HyperKitty.
#
# HyperKitty is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# HyperKitty is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# HyperKitty.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Aamir Khan <syst3m.w0rm@gmail.com>
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

class PaginationMiddleware(object):
    """
    Inserts a variable representing the current page onto the request object if
    it exists in either **GET** or **POST** portions of the request.
    """
    def process_request(self, request):
        try:
            request.page = int(request.REQUEST['page'])
        except (KeyError, ValueError, TypeError):
            request.page = 1



# http://stackoverflow.com/questions/2799450/django-https-for-just-login-page

from django.conf import settings
from django.http import HttpResponsePermanentRedirect

SSL = 'SSL'

class SSLRedirect(object):

    def process_view(self, request, view_func, view_args, view_kwargs):
        secure = view_kwargs.pop(SSL, False)
        if request.user.is_authenticated():
            secure = True
        if not settings.USE_SSL: # User-disabled (e.g: development server)
            secure = False

        if not secure == self._is_secure(request):
            return self._redirect(request, secure)

    def _is_secure(self, request):
        if request.is_secure():
            return True

        #Handle the Webfaction case until this gets resolved in the request.is_secure()
        if 'HTTP_X_FORWARDED_SSL' in request.META:
            return request.META['HTTP_X_FORWARDED_SSL'] == 'on'

        return False

    def _redirect(self, request, secure):
        protocol = secure and "https" or "http"
        newurl = "%s://%s%s" % (protocol, request.get_host(), request.get_full_path())
        if settings.DEBUG and request.method == 'POST':
            raise RuntimeError, \
        """Django can't perform a SSL redirect while maintaining POST data.
           Please structure your views so that redirects only occur during GETs."""
        return HttpResponsePermanentRedirect(newurl)



# https://docs.djangoproject.com/en/dev/topics/i18n/timezones/

from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from hyperkitty.models import UserProfile

class TimezoneMiddleware(object):

    def process_request(self, request):
        if not request.user.is_authenticated():
            return
        try:
            user_profile = request.user.get_profile()
        except ObjectDoesNotExist:
            return
        if user_profile.timezone:
            timezone.activate(user_profile.timezone)



# Cache some metadata from Mailman about the logged in user

from mailmanclient import Client as MailmanClient
from mailmanclient import MailmanConnectionError
from django.conf import settings

class MailmanUserMetadata(object):

    session_key = "subscribed"

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated():
            return
        if not request.user.email:
            return # Can this really happen?
        if self.session_key in request.session:
            return # Already set
        client = MailmanClient('%s/3.0' %
                    settings.MAILMAN_REST_SERVER,
                    settings.MAILMAN_API_USER,
                    settings.MAILMAN_API_PASS)
        try:
            user = client.get_user(request.user.email)
        except MailmanConnectionError:
            return
        request.session[self.session_key] = \
                [ s.address for s in user.subscriptions ]
