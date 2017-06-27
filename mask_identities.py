#!/usr/bin/env python3

"""Mask entities that potentially reveal personally identifying information.

Note: You should NOT assume that the results are pefect nor that all personally
identifying language has been removed!
"""

import csv
import sys
import os
import urllib

from getpass import getpass

EXTERNALS = ('rosette_api',)

try:
    from rosette.api import API, DocumentParameters
except ImportError:
    print('This script depends on the following modules:')
    print('', *EXTERNALS, sep='\n\t')
    print('\nIf you are missing any of these modules, install them with pip3:')
    print('$ pip3 install', *EXTERNALS)

DEFAULT_ROSETTE_API_URL = 'https://api.rosette.com/rest/v1/'

# Default entity type masks
# (refer to https://developer.rosette.com/features-and-functions#entity-extraction-entity-types for a full description of supported entity types)
MASKS = {
    # Masks including "{}" will index each mention of that type so that
    # they can still be distinghuished from other entities of that type
    # E.g., "LOCATION1", "LOCATION2", ...
    
    "ORGANIZATION": "ORGANIZATION{}",
    "PERSON": "PERSON{}",
    "LOCATION": "LOCATION{}",
    "PRODUCT": "PRODUCT{}",
    "TITLE": "TITLE{}",
    "NATIONALITY": "NATIONALITY{}",
    "RELIGION": "RELIGION{}",
    
    # The following masks are generic and don't require indexes
    "IDENTIFIER:CREDIT_CARD_NUM": "IDENTIFIER:CREDIT_CARD_NUM",
    "IDENTIFIER:EMAIL": "IDENTIFIER:EMAIL",
    "IDENTIFIER:MONEY": "IDENTIFIER:MONEY",
    "IDENTIFIER:PERSONAL_ID_NUM": "IDENTIFIER:PERSONAL_ID_NUM",
    "IDENTIFIER:PHONE_NUMBER": "IDENTIFIER:PHONE_NUMBER",
    "TEMPORAL:DATE": "TEMPORAL:DATE",
    "TEMPORAL:TIME": "TEMPORAL:TIME",
    "IDENTIFIER:LATITUDE_LONGITUDE": "IDENTIFIER:LATITUDE_LONGITUDE",
    "IDENTIFIER:URL": "IDENTIFIER:URL",
    "IDENTIFIER:DISTANCE": "IDENTIFIER:DISTANCE"
}

DEFAULT_MASKS = {
    "ORGANIZATION": "ORGANIZATION{}",
    "PERSON": "PERSON{}",
    "IDENTIFIER:CREDIT_CARD_NUM": "IDENTIFIER:CREDIT_CARD_NUM",
    "IDENTIFIER:EMAIL": "IDENTIFIER:EMAIL",
    "IDENTIFIER:MONEY": "IDENTIFIER:MONEY",
    "IDENTIFIER:PERSONAL_ID_NUM": "IDENTIFIER:PERSONAL_ID_NUM",
    "IDENTIFIER:PHONE_NUMBER": "IDENTIFIER:PHONE_NUMBER",
    "TEMPORAL:DATE": "TEMPORAL:DATE",
    "TEMPORAL:TIME": "TEMPORAL:TIME",
    "IDENTIFIER:LATITUDE_LONGITUDE": "IDENTIFIER:LATITUDE_LONGITUDE",
}

def entities(content, api, language=None, uri=False, **kwargs):
    """Get a entities from the given content.
    
    content:  a string
              (can be content itself, or, if uri=True, a URI from which to
              extract document content)
    api:      a rosette.api.API instance
    language: a language override
              (by default Rosette API automatically detects the language)
    uri:      specify if the content is to be interpreted as data or if it is
              a URI from which the data should be extracted
    
    E.g.:
    
    api = API(user_key=<key>, service_url='https://api.rosette.com/rest/v1/')
    api.setUrlParameter('output', 'rosette') 
    adm = entities(
        'John Smith is the alleged perpetrator of serious crimes.',
        api
    ) -> [
      {
        "mentions": [
          {
            "startOffset": 0,
            "endOffset": 10,
            "source": "statistical",
            "subsource": "/data/roots/rex/7.26.3.c58.3/data/statistical/eng/model-LE.bin",
            "normalized": "John Smith"
          }
        ],
        "headMentionIndex": 0,
        "type": "PERSON",
        "entityId": "Q228024"
      }
    ]

    """
    print('Extracting entities via Rosette API ...', file=sys.stderr)
    parameters = DocumentParameters()
    if uri:
        parameters['contentUri'] = content
    else:
        parameters['content'] = content
    parameters['language'] = language
    adm = api.entities(parameters, **kwargs)
    print('Done!', file=sys.stderr)
    return adm

def ngrams(iterable, n=1):
    """Generate ngrams from an iterable
    
    l = range(5)
    list(ngrams(l)) -> [(0,), (1,), (2,), (3,), (4,)]
    list(ngrams(l, 2)) -> [(0, 1), (1, 2), (2, 3), (3, 4)]
    list(ngrams(l, 3)) -> [(0, 1, 2), (1, 2, 3), (2, 3, 4)]
    
    """
    return zip(*(iterable[i:] for i in range(n)))

def extent(obj):
    """Get the start and end offset attributes of a dict-like object

    a = {'startOffset': 0, 'endOffset': 5}
    b = {'startOffset': 0, 'endOffset': 10}
    c = {'startOffset': 5, 'endOffset': 10}

    extent(a) -> (0, 5)
    extent(b) -> (0, 10)
    extent(c) -> (5, 10)
    extent({}) -> (-1, -1)

    """
    return obj.get('startOffset', -1), obj.get('endOffset', -1)

def masked_mentions(adm, masks):
    """Generate pairs of mentions and their masks from an ADM
    
    adm:   an Annotated Data Model with an 'entities' attribute
    masks: a dict mapping entity types to mask format strings
    
    Mapping examples:
    {'PERSON': 'PERSON{}'}:
        Each person entity mention will be masked as "PERSON1", "PERSON2", ...
    {'IDENTIFIER:CREDIT_CARD_NUM': 'CREDIT-CARD-NUMBER'}:
        Each credit card number mention will be masked as "CREDIT-CARD-NUMBER".
    {'IDENTIFIER:PERSONAL_ID_NUM': '#ID#'}:
        Each personal identification number mention will be masked as "#ID#".
    
    E.g.:
    
    api = API(user_key=<key>, service_url='https://api.rosette.com/rest/v1/')
    api.setUrlParameter('output', 'rosette') 
    adm = entities(
        'John Smith is accused of stealing $1,000,000.',
        api
    )
    list(
        masked_mentions(
            adm,
            masks={
                'PERSON': 'PERSON{}',
                'IDENTIFIER:MONEY': 'MONEY-AMOUNT'
            }
        )
    ) -> [
      {
        "startOffset": 0,
        "endOffset": 10,
        "source": "statistical",
        "subsource": "/data/roots/rex/7.26.3.c58.3/data/statistical/eng/model-LE.bin",
        "normalized": "John Smith",
        "mask": "PERSON1"
      },
      {
        "startOffset": 34,
        "endOffset": 44,
        "source": "regex",
        "subsource": "xxx_0",
        "normalized": "$1,000,000",
        "mask": "MONEY-AMOUNT"
      }
    ]
    """
    # Keep track of separate indices per masked entity type
    index = {k: 0 for k in MASKS}
    for entity in adm['attributes']['entities']['items']:
        if entity['type'] in masks:
            index[entity['type']] += 1
            for mention in entity['mentions']:
                # add the appropriate mask to the mention
                mention['mask'] = masks[entity['type']].format(
                    index[entity['type']]
                )
                yield mention

def mask(adm, masks):
    """Return a masked version of the adm['data'] from the given ADM
    
    adm: an Annotated Data Model with an 'entities' attribute
    masks: a dict mapping entity types to the mask to use for that type
    
    E.g.:
    
    api = API(user_key=<key>, service_url='https://api.rosette.com/rest/v1/')
    api.setUrlParameter('output', 'rosette') 
    adm = entities(
        'John Smith is accused of stealing $1,000,000.',
        api
    )
    mask(
        adm,
        masks={
            'PERSON': 'PERSON{}',
            'IDENTIFIER:MONEY': 'MONEY-AMOUNT'
        }
    ) -> 'PERSON1 is accused of stealing MONEY-AMOUNT.'
    """
    # Get a list of mentions to mask sorted by character offsets
    masked = sorted(masked_mentions(adm, masks), key=extent)
    data = ''
    if any(masked):
        # Add data before the first mention
        subsequent, *_ = masked
        start = min(extent(subsequent))
        data += adm['data'][:start]
        # Add each masked mention and the subsequent data
        for current, subsequent in ngrams(masked, n=2):
            start = max(extent(current))
            end = min(extent(subsequent))
            data += current['mask'] + adm['data'][start:end]
        # Add the remaining data after the last masked mention
        data += subsequent['mask'] + adm['data'][max(extent(subsequent)):]
        return data
    # In case there were no mentions to mask, just return the data as is
    return adm['data']

def get_content(content, uri=False):
    """Load content from file or stdin"""
    # Rosette API may balk at non-Latin characters in a URI so we can get urllib
    # to %-escape the URI for us
    if uri:
        unquoted = urllib.parse.unquote(content)
        return urllib.parse.quote(unquoted, '/:')
    if content is None:
        content = sys.stdin.read()
    elif os.path.isfile(content):
        with open(content, mode='r') as f:
            content = f.read()
    return content

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument(
        '-i', '--input',
        help=(
            'Path to a file containing input data (if not specified data is '
            'read from stdin)'
        ),
        default=None
    )
    parser.add_argument(
        '-u',
        '--content-uri',
        action='store_true',
        help='Specify that the input is a URI (otherwise load text from file)'
    )
    parser.add_argument(
        '-k', '--key',
        help='Rosette API Key',
        default=None
    )
    parser.add_argument(
        '-a', '--api-url',
        help='Alternative Rosette API URL',
        default=DEFAULT_ROSETTE_API_URL
    )
    parser.add_argument(
        '-l', '--language',
        help=(
            'A three-letter (ISO 639-2 T) code that will override automatic '
            'language detection'
        ),
        default=None
    )
    parser.add_argument(
        '-t', '--entity-types',
        nargs='+',
        choices=list(MASKS.keys()),
        default=list(DEFAULT_MASKS.keys()),
        metavar='TYPE',
        help=(
            'A list of named entity types to mask (refer to '
            'https://developer.rosette.com/features-and-functions#entity-extraction-entity-types '
            'for a full description of supported entity types)'
        )
    )
    args = parser.parse_args()
    # Get the user's Rosette API key
    key = (
        os.environ.get('ROSETTE_USER_KEY') or
        args.key or
        getpass(prompt='Enter your Rosette API key: ')
    )
    # Instantiate the Rosette API
    api = API(user_key=key, service_url=args.api_url)
    # Get API results as full ADM
    api.setUrlParameter('output', 'rosette')
    adm = entities(
        get_content(args.input),
        api,
        language=args.language,
        uri=args.content_uri
    )
    # Mask and print the data and print to stdout
    print(mask(adm, {type_: MASKS[type_] for type_ in args.entity_types}))
