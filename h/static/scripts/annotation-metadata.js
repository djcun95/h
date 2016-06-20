'use strict';

/**
 * Utility functions for querying annotation metadata.
 */

/** Extract a URI, domain and title from the given domain model object.
 *
 * @param {object} annotation An annotation domain model object as received
 *   from the server-side API.
 * @returns {object} An object with three properties extracted from the model:
 *   uri, domain and title.
 *
 */
function extractDocumentMetadata(annotation) {
  var document_;
  var uri = annotation.uri;
  var domain = new URL(uri).hostname;
  if (annotation.document) {
    if (uri.indexOf('urn') === 0) {
      var i;
      for (i = 0; i < annotation.document.link.length; i++) {
        var link = annotation.document.link[i];
        if (link.href.indexOf('urn:') === 0) {
          continue;
        }
        uri = link.href;
        break;
      }
    }

    var documentTitle;
    if (Array.isArray(annotation.document.title)) {
      documentTitle = annotation.document.title[0];
    } else {
      documentTitle = annotation.document.title;
    }

    document_ = {
      uri: uri,
      domain: domain,
      title: documentTitle || domain
    };
  } else {
    document_ = {
      uri: uri,
      domain: domain,
      title: domain
    };
  }

  if (document_.title.length > 30) {
    document_.title = document_.title.slice(0, 30) + '…';
  }

  return document_;
}

/** Return the type of an annotation is - annotation, page note or reply. */
function getAnnotationType(annotation) {
  if (isTypePageNote(annotation)) {
    return 'note';
  }
  if (isTypeAnnotation(annotation)) {
    return 'annotation';
  }
  if (isTypeReply(annotation)) {
    return 'reply';
  }
}

/** Return `true` if the given annotation is a reply, `false` otherwise. */
function isReply(annotation) {
  return (annotation.references || []).length > 0;
}

/** Return `true` if the given annotation is new, `false` otherwise.
 *
 * "New" means this annotation has been newly created client-side and not
 * saved to the server yet.
 */
function isNew(annotation) {
  return !annotation.id;
}

function isTypePageNote(annotation) {
  if (annotation && !annotation.deleted) {
    if (isTypeReply(annotation)) {
      return false;
    }
    if (annotation.target && (annotation.target.length === 0 || !annotation.target[0].selector)) {
      return true;
    }
  }
  return false;
}

function isTypeAnnotation(annotation) {
  if (annotation && !annotation.deleted) {
    if (annotation.target && annotation.target.length > 0 && annotation.target[0].selector) {
      return true;
    };
  }
  return false;
}

function isTypeReply(annotation) {
  if (annotation && !annotation.deleted) {
    if (annotation.references && annotation.references.length > 0) {
      return true;
    };
  }
  return false;
}

/** Return a numeric key that can be used to sort annotations by location.
 *
 * @return {number} - A key representing the location of the annotation in
 *                    the document, where lower numbers mean closer to the
 *                    start.
 */
 function location(annotation) {
   if (annotation) {
     var targets = annotation.target || [];
     for (var i=0; i < targets.length; i++) {
       var selectors = targets[i].selector || [];
       for (var k=0; k < selectors.length; k++) {
         if (selectors[k].type === 'TextPositionSelector') {
           return selectors[k].start;
         }
       }
     }
   }
   return Number.POSITIVE_INFINITY;
 }

module.exports = {
  extractDocumentMetadata: extractDocumentMetadata,
  isReply: isReply,
  isNew: isNew,
  location: location,
  isTypePageNote: isTypePageNote,
  isTypeAnnotation: isTypeAnnotation,
  isTypeReply: isTypeReply,
  getAnnotationType: getAnnotationType,
};
