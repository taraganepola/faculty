# Copyright 2020 Faculty Science Limited
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


import json
import uuid

import pytest
from sseclient import Event

from faculty.clients.notification import (
    NotificationClient,
    TemplatePublishingError,
)


PROJECT_ID = uuid.uuid4()
USER_ID_STRING = "3024d586-6a4a-4fc1-98a9-c6135b163f17"
USER_ID = uuid.UUID(USER_ID_STRING)


def test_url_default(mocker):
    mock_session = mocker.Mock()
    mock_session.profile = mocker.Mock()
    mock_session.profile.protocol = "http"
    mock_session.profile.domain = "sml-services"
    client = NotificationClient(mock_session)

    assert client.protocol == "http"
    assert client.host == "frontend.sml-services"


def test_url_custom(mocker):
    client = NotificationClient(
        mocker.Mock(), protocol="https", host="test.my.faculty.ai"
    )

    assert client.protocol == "https"
    assert client.host == "test.my.faculty.ai"


def test_user_updates(mocker):
    mocker.patch.object(NotificationClient, "_get_raw")

    client = NotificationClient(mocker.Mock())
    client.user_updates(USER_ID)

    # TODO test SSEClient?
    NotificationClient._get_raw.assert_called_once_with(
        "api/updates/user/{}".format(USER_ID_STRING), stream=True
    )


def test_check_publish_template_result_success(mocker):
    def events():
        yield Event(
            event="@SSE/PROJECT_TEMPLATE_PUBLISH_NEW_COMPLETED",
            data=json.dumps({"sourceProjectId": str(PROJECT_ID)}),
        )

    client = NotificationClient(mocker.Mock())
    client.check_publish_template_result(events(), PROJECT_ID)


def test_check_publish_template_result_other_project(mocker):
    def events():
        yield Event(
            event="@SSE/PROJECT_TEMPLATE_PUBLISH_NEW_FAILED",
            data=json.dumps({"sourceProjectId": "other project ID"}),
        )
        yield Event(
            event="@SSE/PROJECT_TEMPLATE_PUBLISH_NEW_COMPLETED",
            data=json.dumps({"sourceProjectId": str(PROJECT_ID)}),
        )

    client = NotificationClient(mocker.Mock())
    client.check_publish_template_result(events(), PROJECT_ID)


@pytest.mark.parametrize("error_code", ["name_conflict", "unexpected_error"])
def test_check_publish_template_result_errors(mocker, error_code):
    def events():
        yield Event(
            event="@SSE/PROJECT_TEMPLATE_PUBLISH_NEW_FAILED",
            data=json.dumps(
                {
                    "sourceProjectId": str(PROJECT_ID),
                    "errorCode": error_code,
                    "error": "dummy error message",
                }
            ),
        )

    client = NotificationClient(mocker.Mock())
    with pytest.raises(TemplatePublishingError, match="dummy error message"):
        client.check_publish_template_result(events(), PROJECT_ID)


def test_check_publish_template_result_rendering_errors(mocker):
    def events():
        yield Event(
            event="@SSE/PROJECT_TEMPLATE_PUBLISH_NEW_FAILED",
            data=json.dumps(
                {
                    "sourceProjectId": str(PROJECT_ID),
                    "errorCode": "template_rendering_error",
                    "errors": [
                        {"error": "Unexpected key { abc }", "path": "a.py"},
                        {"error": "Unexpected key { abc }", "path": "a/b.py"},
                    ],
                }
            ),
        )

    client = NotificationClient(mocker.Mock())
    expected_message = """Failed to render the template with default parameters:
\tUnexpected key { abc } in file a.py
\tUnexpected key { abc } in file a/b.py"""
    with pytest.raises(TemplatePublishingError, match=expected_message):
        client.check_publish_template_result(events(), PROJECT_ID)


def test_check_publish_template_result_rendering_unexpected_error_code(mocker):
    def events():
        yield Event(
            event="@SSE/PROJECT_TEMPLATE_PUBLISH_NEW_FAILED",
            data=json.dumps(
                {
                    "sourceProjectId": str(PROJECT_ID),
                    "errorCode": "unkown erorr code",
                }
            ),
        )

    client = NotificationClient(mocker.Mock())
    with pytest.raises(
        TemplatePublishingError, match="Unexpected error code received"
    ):
        client.check_publish_template_result(events(), PROJECT_ID)


def test_check_publish_template_result_rendering_no_error_code(mocker):
    def events():
        yield Event(
            event="@SSE/PROJECT_TEMPLATE_PUBLISH_NEW_FAILED",
            data=json.dumps({"sourceProjectId": str(PROJECT_ID)}),
        )

    client = NotificationClient(mocker.Mock())
    with pytest.raises(
        TemplatePublishingError, match="Unexpected server response"
    ):
        client.check_publish_template_result(events(), PROJECT_ID)