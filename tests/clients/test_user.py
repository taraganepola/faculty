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

import uuid

import pytest
from marshmallow import ValidationError

from sherlockml.clients.user import (
    UserClient, User, UserSchema, AuthenticationResponse,
    AuthenticationResponseSchema
)

from tests.clients.fixtures import PROFILE

USER_ID = uuid.uuid4()


def test_user_schema():
    data = UserSchema().load({'userId': str(USER_ID)})
    assert data == User(id=USER_ID)


@pytest.mark.parametrize('data', [{},
                                  {'id': str(USER_ID)},
                                  {'userId': 'not-a-uuid'}])
def test_user_schema_invalid(data):
    with pytest.raises(ValidationError):
        UserSchema().load(data)


def test_authentication_response_schema():
    data = AuthenticationResponseSchema().load(
        {'account': {'userId': str(USER_ID)}}
    )
    assert data == AuthenticationResponse(user=User(id=USER_ID))


@pytest.mark.parametrize('data', [{},
                                  {'user': {'id': str(USER_ID)}},
                                  {'account': 'not-an-account'}])
def test_authentication_response_schema_invalid(data):
    with pytest.raises(ValidationError):
        AuthenticationResponseSchema().load(data)


def test_user_client_authenticated_user_id(mocker):
    mocker.patch.object(
        UserClient, '_get',
        return_value=AuthenticationResponse(user=User(id=USER_ID))
    )

    schema_mock = mocker.patch(
        'sherlockml.clients.user.AuthenticationResponseSchema'
    )

    client = UserClient(PROFILE)

    assert client.authenticated_user_id() == USER_ID

    UserClient._get.assert_called_once_with(
        '/authenticate', schema_mock.return_value
    )