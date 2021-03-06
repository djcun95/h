# -*- coding: utf-8 -*-

import os

import pytest
from webtest import TestApp
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker

TEST_SETTINGS = {
    'es.host': os.environ.get('ELASTICSEARCH_HOST', 'http://localhost:9200'),
    'es.index': 'hypothesis-test',
    'legacy.es.index': 'annotator-test',
    'h.db.should_create_all': True,
    'h.db.should_drop_all': True,
    'h.search.autoconfig': True,
    'sqlalchemy.url': os.environ.get('TEST_DATABASE_URL',
                                     'postgresql://postgres@localhost/htest')
}

Session = sessionmaker()


@pytest.fixture
def config():
    from h.config import configure
    from h.db import Session

    # Expire any previous database session
    Session.remove()

    config = configure()
    config.registry.settings.update(TEST_SETTINGS)
    _drop_indices(settings=config.registry.settings)
    config.include('h.app')
    config.include('h.session')
    return config


@pytest.fixture
def app(config):
    return TestApp(config.make_wsgi_app())


@pytest.fixture
def db_session(request, config):
    """Get a standalone database session for preparing database state."""
    engine = engine_from_config(config.registry.settings, 'sqlalchemy.')
    session = Session(bind=engine)
    request.addfinalizer(session.close)
    return session


def _drop_indices(settings):
    import elasticsearch

    conn = elasticsearch.Elasticsearch([settings['es.host']])

    for name in [settings['es.index'], settings['legacy.es.index']]:
        if conn.indices.exists(index=name):
            conn.indices.delete(index=name)
