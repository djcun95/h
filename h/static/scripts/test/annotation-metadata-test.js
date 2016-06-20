'use strict';

var annotationMetadata = require('../annotation-metadata');

var extractDocumentMetadata = annotationMetadata.extractDocumentMetadata;

describe('annotation-metadata', function () {
  describe('.extractDocumentMetadata', function() {

    context('when target[0].locator is available', function() {
      it('returns it as the uri', function() {
        var model = {
          uri: 'http://example.com/',
          target: [{
            locator: 'http://wikipedia.org/'
          }],
        };

        assert.equal(extractDocumentMetadata(model).uri, 'http://wikipedia.org/');
      });

      it('uses it for the domain', function() {
        var model = {
          uri: 'http://example.com/',
          target: [{
            locator: 'http://wikipedia.org/'
          }],
        };

        assert.equal(extractDocumentMetadata(model).domain, 'wikipedia.org');
      });
    });

    context('when target has no locator', function() {
      it('returns the annotation.uri as the uri', function() {
        var model = {
          uri: 'http://example.com/',
          target: [{}],
        };

        assert.equal(extractDocumentMetadata(model).uri, 'http://example.com/');
      });

      it('uses the annotation.uri for the domain', function() {
        var model = {
          uri: 'http://example.com/',
          target: [{}],
        };

        assert.equal(extractDocumentMetadata(model).domain, 'example.com');
      });
    });

    context('when the model has a document property', function() {
      context('when the document has a title', function() {
        it('returns the first value as the title', function() {
          var model = {
            uri: 'http://example.com/',
            target: [{}],
            document: {
              title: ['My Document', 'My Other Document']
            },
          };

          assert.equal(
            extractDocumentMetadata(model).title, model.document.title[0]);
        });
      });

      context('when there is no document.title', function() {
        it('returns the domain as the title', function() {
          var model = {
            uri: 'http://example.com/',
            target: [{}],
          };

          assert.equal(extractDocumentMetadata(model).title, 'example.com');
        });
      });
    });

    context('when the model does not have a document property', function() {
      context('when there is a target locator', function() {
        it('returns the hostname of target locator for the title', function() {
          var model = {
            target: [{
              locator: 'http://example.com/'
            }],
          };

          assert.equal(extractDocumentMetadata(model).title, 'example.com');
        });
      });

      context('when there is no target locator', function() {
        it('returns the hostname of model.uri for the title', function() {
          var model = {
            uri: 'http://example.com/',
            target: [{}],
          };

          assert.equal(extractDocumentMetadata(model).title, 'example.com');
        });
      });
    });

    context('when the title is longer than 30 characters', function() {
      it('truncates the title with "…"', function() {
        var model = {
          uri: 'http://example.com/',
          target: [{}],
          document: {
            title: ['My Really Really Long Document Title']
          },
        };

        assert.equal(
          extractDocumentMetadata(model).title,
          'My Really Really Long Document…'
        );
      });
    });
  });

  describe('.location', function () {
    it('returns the position for annotations with a text position', function () {
      assert.equal(annotationMetadata.location({
        target: [{
          selector: [{
            type: 'TextPositionSelector',
            start: 100,
          }]
        }]
      }), 100);
    });

    it('returns +ve infinity for annotations without a text position', function () {
      assert.equal(annotationMetadata.location({
        target: [{
          selector: undefined,
        }]
      }), Number.POSITIVE_INFINITY);
    });
  });
});
