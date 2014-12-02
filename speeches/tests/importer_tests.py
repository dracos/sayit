import datetime
import json
import re
import requests
from mock import patch

from speeches.tests import InstanceTestCase
from speeches.models import Speech, Speaker, Section
from speeches.importers.import_akomantoso import ImportAkomaNtoso
from speeches.importers.import_popolo import PopoloImporter


class FakeRequestsOutput(object):
    def __init__(self, source):
        assert source.startswith('http://example.com/')

        # We'll put things that would have been served from a url ending
        # in a / at the same place ending in and _, so as to avoid a
        # name clash with directories.
        source = re.sub(r'/$', '_', source)
        source = re.sub(
            r'^http://example.com/',
            'speeches/tests/data/fake_http/',
            source)

        self.file_path = source

    def json(self):
        return json.load(open(self.file_path))

    @property
    def content(self):
        return open(self.file_path).read()


@patch.object(requests, 'get', FakeRequestsOutput)
class AkomaNtosoImportTestCase(InstanceTestCase):
    def setUp(self):
        super(AkomaNtosoImportTestCase, self).setUp()
        self.importer = ImportAkomaNtoso(instance=self.instance, commit=True)

    def test_import_sample_file(self):
        self.importer.import_document(
            'speeches/tests/data/fake_http/Debate_Bungeni_1995-10-31.xml')

        # To get us started, let's just check that we get the right kind of
        # speech in the right order.
        self.assertEqual(
            [x.type for x in Speech.objects.all()],
            [u'scene', u'other', u'narrative', u'speech', u'question',
             u'summary', u'speech', u'answer', u'narrative', u'speech',
             u'narrative']
            )

    def test_already_imported(self):
        self.importer.import_document(
            'speeches/fixtures/test_inputs/test_xpath.xml')

        ImportAkomaNtoso(instance=self.instance, commit=True, clobber=False).import_document(
            'speeches/fixtures/test_inputs/test_clobber.xml')
        self.assertEqual(
            [ x.text for x in Speech.objects.all() ],
            [ '<p>Hello</p>' ]
        )

        ImportAkomaNtoso(instance=self.instance, commit=True, clobber=True).import_document(
            'speeches/fixtures/test_inputs/test_clobber.xml')
        self.assertEqual(
            [ x.text for x in Speech.objects.all() ],
            [ '<p>Howdy</p>' ]
        )

        ImportAkomaNtoso(instance=self.instance, commit=True).import_document(
            'speeches/fixtures/test_inputs/test_clobber.xml')
        self.assertEqual(
            [ x.text for x in Speech.objects.all() ],
            [ '<p>Howdy</p>', '<p>Howdy</p>' ]
        )

    def test_not_already_imported(self):
        ImportAkomaNtoso(instance=self.instance, commit=True, clobber=False).import_document(
            'speeches/fixtures/test_inputs/test_xpath.xml')
        self.assertEqual(
            [ x.title for x in Section.objects.all() ],
            [ 'This is the title' ]
        )
        Section.objects.all().delete()

        ImportAkomaNtoso(instance=self.instance, commit=True, clobber=True).import_document(
            'speeches/fixtures/test_inputs/test_xpath.xml')
        self.assertEqual(
            [ x.title for x in Section.objects.all() ],
            [ 'This is the title' ]
        )
        Section.objects.all().delete()

        ImportAkomaNtoso(instance=self.instance, commit=True).import_document(
            'speeches/fixtures/test_inputs/test_xpath.xml')
        self.assertEqual(
            [ x.title for x in Section.objects.all() ],
            [ 'This is the title' ]
        )
        Section.objects.all().delete()

    def test_empty_title(self):
        self.importer.import_document(
            'speeches/fixtures/test_inputs/test_empty_title.xml')

        ImportAkomaNtoso(instance=self.instance, commit=True, clobber=False).import_document(
            'speeches/fixtures/test_inputs/test_empty_title.xml')
        self.assertEqual(
            [ x.title for x in Section.objects.all() ],
            [ '', '' ]
        )

        ImportAkomaNtoso(instance=self.instance, commit=True, clobber=True).import_document(
            'speeches/fixtures/test_inputs/test_empty_title.xml')
        self.assertEqual(
            [ x.title for x in Section.objects.all() ],
            [ '', '', '' ]
        )

        ImportAkomaNtoso(instance=self.instance, commit=True).import_document(
            'speeches/fixtures/test_inputs/test_empty_title.xml')
        self.assertEqual(
            [ x.title for x in Section.objects.all() ],
            [ '', '', '', '' ]
        )

    def test_xpath_preface_elements(self):
        self.importer.import_document(
            'speeches/fixtures/test_inputs/test_xpath.xml')
        self.assertEqual(
            [x.title for x in Section.objects.all()],
            ['This is the title']
        )
        self.assertEqual(
            [x.start_date for x in Speech.objects.all()],
            [datetime.date(2014, 7, 24)]
        )

    def test_unicode_character(self):
        self.importer.import_document(
            'speeches/fixtures/test_inputs/test_unicode_character.xml')

        self.assertEqual(
            [x.type for x in Speech.objects.all()],
            ['other']
            )

    def test_blank_speakers(self):
        self.importer.import_document(
            'speeches/fixtures/test_inputs/test_blank_speakers.xml')

        speaker = Speaker.objects.get(name='Speaker')
        speeches = Speech.objects.all()
        speeches_s = Speech.objects.filter(type='speech')
        self.assertEqual(speeches.count(), speeches_s.count())

        for i in range(4):
            s = speaker if i % 2 else None
            sd = 'Speaker' if i > 1 else None
            self.assertEqual(speeches[i].speaker, s)
            self.assertEqual(speeches[i].speaker_display, sd)

    def test_import_remote_file(self):
        self.importer.import_document(
            'http://example.com/Debate_Bungeni_1995-10-31.xml')

        # To get us started, let's just check that we get the right kind of
        # speech in the right order.
        self.assertEqual(
            [x.type for x in Speech.objects.all()],
            [u'scene', u'other', u'narrative', u'speech', u'question',
             u'summary', u'speech', u'answer', u'narrative', u'speech',
             u'narrative']
            )


@patch.object(requests, 'get', FakeRequestsOutput)
class AkomaNtosoImportViewTestCase(InstanceTestCase):
    def test_import_page_smoke_test(self):
        resp = self.client.get('/import/akomantoso')

        self.assertContains(resp, 'Import Speeches')

    def test_import_data(self):
        resp = self.client.post(
            '/import/akomantoso',
            {'location': 'http://example.com/Debate_Bungeni_1995-10-31.xml',
             'existing_sections': 'Skip',
             },
            follow=True,
            )

        # To get us started, let's just check that we get the right kind of
        # speech in the right order.
        self.assertEqual(
            [x.type for x in Speech.objects.all()],
            [u'scene', u'other', u'narrative', u'speech', u'question',
             u'summary', u'speech', u'answer', u'narrative', u'speech',
             u'narrative']
            )

        self.assertContains(resp, 'Created: 7 speakers, 8 sections, 11 speeches')

    def test_import_bad_data(self):
        resp = self.client.post(
            '/import/akomantoso',
            {'location': 'http://example.com/welsh_assembly/persons',
             'existing_sections': 'Skip',
             },
            )

        self.assertContains(resp, 'Sorry - something went wrong with the import')


@patch.object(requests, 'get', FakeRequestsOutput)
class PopitImportTestCase(InstanceTestCase):
    popit_url = 'http://example.com/welsh_assembly_popit/'

    def test_popit_import_persons(self):
        popit_importer = PopoloImporter(self.popit_url)
        popit_importer.import_all()

        self.assertEqual(
            Speaker.objects.filter(instance=popit_importer.instance).count(),
            3,
            )


@patch.object(requests, 'get', FakeRequestsOutput)
class PopoloImportTestCase(InstanceTestCase):
    popit_url = 'http://example.com/welsh_assembly/persons'

    def test_popit_import_persons(self):
        popolo_importer = PopoloImporter(self.popit_url)
        popolo_importer.import_all()

        self.assertEqual(Speaker.objects.filter(instance=popolo_importer.instance).count(), 3)

    def test_popolo_import_remote_single_json_file(self):
        popolo_importer = PopoloImporter(
            'http://example.com/welsh_assembly.json'
            )
        popolo_importer.import_all()

        self.assertEqual(
            Speaker.objects.filter(instance=popolo_importer.instance).count(),
            3,
            )

    def test_popolo_import_remote_single_json_file(self):
        popolo_importer = PopoloImporter(
            'http://example.com/welsh_assembly.json'
            )
        popolo_importer.import_all()

        self.assertEqual(
            Speaker.objects.filter(instance=popolo_importer.instance).count(),
            3,
            )


class PopoloImportFromLocalSourceTestCase(InstanceTestCase):
    def test_import_persons(self):
        popolo_importer = PopoloImporter(
            'speeches/tests/data/fake_http/welsh_assembly.json'
            )
        popolo_importer.import_all()

        self.assertEqual(
            Speaker.objects.filter(instance=popolo_importer.instance).count(),
            3,
            )


@patch.object(requests, 'get', FakeRequestsOutput)
class PopoloImportViewsTestCase(InstanceTestCase):
    def test_import_page_smoke_test(self):
        resp = self.client.get('/import/popolo')

        self.assertContains(resp, 'Import Speakers')

    def test_import_with_data(self):
        resp = self.client.post(
            '/import/popolo',
            {'location': 'http://example.com/welsh_assembly/persons'},
            follow=True,
            )

        self.assertEqual(
            Speaker.objects.filter(instance=self.instance).count(),
            3,
            )
        self.assertContains(resp, '3 speakers created. 0 speakers refreshed.')

        # Repeat the same post
        resp = self.client.post(
            '/import/popolo',
            {'location': 'http://example.com/welsh_assembly/persons'},
            follow=True,
            )

        self.assertEqual(
            Speaker.objects.filter(instance=self.instance).count(),
            3,
            )
        self.assertContains(resp, '0 speakers created. 3 speakers refreshed.')

    def test_import_empty(self):
        resp = self.client.post(
            '/import/popolo',
            {'location': 'http://example.com/empty.json'},
            follow=True,
            )

        self.assertEqual(
            Speaker.objects.filter(instance=self.instance).count(),
            0,
            )
        self.assertContains(resp, 'No speakers found')
