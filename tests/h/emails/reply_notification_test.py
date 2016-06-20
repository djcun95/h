# -*- coding: utf-8 -*-

import datetime

import mock
import pytest

from h.api.models import elastic
from h.emails.reply_notification import generate
from h.models import Annotation
from h.models import Document, DocumentMeta
from h.models import User
from h.notification.reply import Notification


@pytest.mark.usefixtures('routes', 'token_serializer')
class TestGenerate(object):

    def test_calls_renderers_with_appropriate_context(self,
                                                      notification,
                                                      parent_user,
                                                      pyramid_request,
                                                      reply_user,
                                                      html_renderer,
                                                      text_renderer):
        generate(pyramid_request, notification)

        expected_context = {
            'document_title': 'My fascinating page',
            'document_url': 'http://example.org/',
            'parent': notification.parent,
            'parent_url': 'http://example.com/ann/foo123',
            'parent_user': parent_user,
            'reply': notification.reply,
            'reply_url': 'http://example.com/ann/bar456',
            'reply_user': reply_user,
            'reply_user_url': 'http://example.com/stream/user/ron',
            'unsubscribe_url': 'http://example.com/unsub/FAKETOKEN',
        }
        html_renderer.assert_(**expected_context)
        text_renderer.assert_(**expected_context)

    def test_falls_back_to_target_uri_for_document_title(self,
                                                         notification,
                                                         pyramid_request,
                                                         html_renderer,
                                                         text_renderer):
        notification.document.meta[0].value = []

        generate(pyramid_request, notification)

        html_renderer.assert_(document_title='http://example.org/')
        text_renderer.assert_(document_title='http://example.org/')

    def test_returns_text_and_body_results_from_renderers(self,
                                                          notification,
                                                          pyramid_request,
                                                          html_renderer,
                                                          text_renderer):
        html_renderer.string_response = 'HTML output'
        text_renderer.string_response = 'Text output'

        _, _, text, html = generate(pyramid_request, notification)

        assert html == 'HTML output'
        assert text == 'Text output'

    @pytest.mark.usefixtures('html_renderer', 'text_renderer')
    def test_returns_subject_with_reply_username(self, notification, pyramid_request):
        _, subject, _, _ = generate(pyramid_request, notification)

        assert subject == 'ron has replied to your annotation'

    @pytest.mark.usefixtures('html_renderer', 'text_renderer')
    def test_returns_parent_email_as_recipients(self, notification, pyramid_request):
        recipients, _, _, _ = generate(pyramid_request, notification)

        assert recipients == ['pat@ric.ia']

    @pytest.mark.usefixtures('html_renderer', 'text_renderer')
    def test_calls_token_serializer_with_correct_arguments(self,
                                                           notification,
                                                           pyramid_request,
                                                           token_serializer):
        generate(pyramid_request, notification)

        token_serializer.dumps.assert_called_once_with({
            'type': 'reply',
            'uri': 'acct:patricia@example.com',
        })

    def test_jinja_templates_render(self,
                                    notification,
                                    pyramid_config,
                                    pyramid_request):
        """Ensure that the jinja templates don't contain syntax errors"""
        pyramid_config.include('pyramid_jinja2')
        pyramid_config.add_jinja2_extension('h.jinja_extensions.Filters')

        generate(pyramid_request, notification)

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route('annotation', '/ann/{id}')
        pyramid_config.add_route('stream.user_query', '/stream/user/{user}')
        pyramid_config.add_route('unsubscribe', '/unsub/{token}')

    @pytest.fixture
    def html_renderer(self, pyramid_config):
        return pyramid_config.testing_add_renderer('h:templates/emails/reply_notification.html.jinja2')

    @pytest.fixture
    def text_renderer(self, pyramid_config):
        return pyramid_config.testing_add_renderer('h:templates/emails/reply_notification.txt.jinja2')

    @pytest.fixture
    def document(self, db_session):
        doc = Document()
        doc.meta.append(DocumentMeta(type='title', value=['My fascinating page'], claimant='http://example.org'))
        db_session.add(doc)
        db_session.flush()
        return doc

    @pytest.fixture
    def parent(self):
        common = {
            'id': 'foo123',
            'created': datetime.datetime.utcnow(),
            'updated': datetime.datetime.utcnow(),
            'text': 'Foo is true',
        }
        return Annotation(target_uri='http://example.org/', **common)

    @pytest.fixture
    def reply(self):
        common = {
            'id': 'bar456',
            'created': datetime.datetime.utcnow(),
            'updated': datetime.datetime.utcnow(),
            'text': 'No it is not!',
        }
        return Annotation(target_uri='http://example.org/', **common)

    @pytest.fixture
    def notification(self, reply, reply_user, parent, parent_user, document):
        return Notification(reply=reply,
                            reply_user=reply_user,
                            parent=parent,
                            parent_user=parent_user,
                            document=document)

    @pytest.fixture
    def parent_user(self):
        return User(username='patricia', email='pat@ric.ia')

    @pytest.fixture
    def reply_user(self):
        return User(username='ron', email='ron@thesmiths.com')

    @pytest.fixture
    def token_serializer(self, pyramid_config):
        serializer = mock.Mock(spec_set=['dumps'])
        serializer.dumps.return_value = 'FAKETOKEN'
        pyramid_config.registry.notification_serializer = serializer
        return serializer
