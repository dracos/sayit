from instances.tests import InstanceTestCase

from speeches.models import Speaker, Speech

class SpeakerTests(InstanceTestCase):
    """Tests for the speaker functionality"""

    def test_speaker_page_lists_speeches(self):
        # Add a speaker
        speaker = Speaker.objects.create(name='Steve', instance=self.instance)
        
        # Call the speaker's page
        resp = self.client.get('/speaker/1')

        # Assert no speeches
        self.assertSequenceEqual([], resp.context['speech_list'])

        # Add a speech
        speech = Speech.objects.create(text="A test speech", speaker=speaker, instance=self.instance)

        # Call the speaker's page again
        resp = self.client.get('/speaker/1')

        self.assertSequenceEqual([speech], resp.context['speech_list'])

    def test_speaker_page_has_button_to_add_speech(self):
        # Add a speaker
        speaker = Speaker.objects.create(name='Steve', instance=self.instance)
        
        # Call the speaker's page
        resp = self.client.get('/speaker/1')

        self.assertContains(resp, '<a href="/speech/add?speaker=1">Add a new speech</a>', html=True)
