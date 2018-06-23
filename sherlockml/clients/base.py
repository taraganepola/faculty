# Copyright 2018 ASI Data Science
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import requests

from six.moves import urllib

from sherlockml.clients.auth import SherlockMLAuth


def _service_url(profile, service, endpoint='/'):
    host = '{}.{}'.format(service, profile.domain)
    url_parts = (profile.protocol, host, endpoint, None, None)
    return urllib.parse.urlunsplit(url_parts)


class BaseClient(object):

    SERVICE_NAME = None

    def __init__(self, profile):
        if self.SERVICE_NAME is None:
            raise RuntimeError(
                'must set SERVICE_NAME in subclasses of BaseClient'
            )
        self.profile = profile
        self._http_session_cache = None

    @property
    def http_session(self):
        if self._http_session_cache is None:
            self._http_session_cache = requests.Session()
            self._http_session_cache.auth = SherlockMLAuth(
                _service_url(self.profile, 'hudson'),
                self.profile.client_id,
                self.profile.client_secret
            )
        return self._http_session_cache

    def _request(self, method, endpoint, *args, **kwargs):
        url = _service_url(self.profile, self.SERVICE_NAME, endpoint)
        return self.http_session.request(method, url, *args, **kwargs)

    def _get(self, endpoint, *args, **kwargs):
        return self._request('GET', endpoint, *args, **kwargs)
