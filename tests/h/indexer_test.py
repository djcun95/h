# -*- coding: utf-8 -*-

import mock
import pytest

from h.api import events
from h import indexer


@pytest.mark.usefixtures('celery', 'index')
class TestAddAnnotation(object):

    def test_it_fetches_the_annotation(self, fetch_annotation, celery):
        id_ = 'test-annotation-id'

        indexer.add_annotation(id_)

        fetch_annotation.assert_called_once_with(celery.request.db, id_)

    def test_it_calls_index_with_annotation(self, fetch_annotation, index, celery):
        id_ = 'test-annotation-id'
        annotation = mock.Mock(id=id_)
        fetch_annotation.return_value = annotation

        indexer.add_annotation(id_)

        index.assert_called_once_with(celery.request.es, annotation, celery.request)

    @pytest.fixture
    def index(self, patch):
        return patch('h.indexer.index')

    @pytest.fixture
    def fetch_annotation(self, patch):
        return patch('h.indexer.storage.fetch_annotation')


@pytest.mark.usefixtures('celery', 'delete')
class TestDeleteAnnotation(object):

    def test_it_deletes_from_index(self, delete, celery):
        id_ = 'test-annotation-id'
        indexer.delete_annotation(id_)

        delete.assert_called_once_with(celery.request.es, id_)

    @pytest.fixture
    def delete(self, patch):
        return patch('h.indexer.delete')


@pytest.mark.usefixtures('celery')
class TestReindex(object):
    def test_it_reindexes(self, celery, reindex):
        indexer.reindex_annotations()

        reindex.assert_called_once_with(
            celery.request.db, celery.request.es, celery.request)

    @pytest.fixture
    def reindex(self, patch):
        return patch('h.indexer.reindex')


@pytest.mark.usefixtures('add_annotation', 'delete_annotation')
class TestSubscribeAnnotationEvent(object):

    @pytest.mark.parametrize('action', ['create', 'update'])
    def test_it_enqueues_add_annotation_celery_task(self,
                                                    action,
                                                    add_annotation,
                                                    delete_annotation,
                                                    pyramid_request):
        event = events.AnnotationEvent(pyramid_request,
                                       {'id': 'test_annotation_id'},
                                       action)

        indexer.subscribe_annotation_event(event)

        add_annotation.delay.assert_called_once_with(event.annotation_id)
        assert not delete_annotation.delay.called

    def test_it_enqueues_delete_annotation_celery_task_for_delete(self,
                                                                  add_annotation,
                                                                  delete_annotation,
                                                                  pyramid_request):
        event = events.AnnotationEvent(pyramid_request,
                                       {'id': 'test_annotation_id'},
                                       'delete')

        indexer.subscribe_annotation_event(event)

        delete_annotation.delay.assert_called_once_with(event.annotation_id)
        assert not add_annotation.delay.called

    @pytest.fixture
    def add_annotation(self, patch):
        return patch('h.indexer.add_annotation')

    @pytest.fixture
    def delete_annotation(self, patch):
        return patch('h.indexer.delete_annotation')


@pytest.fixture
def celery(patch, pyramid_request):
    cel = patch('h.indexer.celery')
    cel.request = pyramid_request
    return cel


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.es = mock.Mock()
    return pyramid_request
