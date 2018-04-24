import unittest

from django.conf import settings
from django.test import Client
from mock import patch

from django_docker_engine.docker_utils import (DockerClientRunWrapper,
                                               DockerClientWrapper)


class DemoPathRoutingTests(unittest.TestCase):

    def setUp(self):
        self.client = Client()

    def assert_response_redirect(self, response, expected_redirect):
        # In some environments, it's a complete URL, in others,
        # just the path and query; I think either is fine.
        self.assertIn(response.redirect_chain,
                      [[(expected_redirect, 302)],
                       ('http://testserver' + expected_redirect, 302)])

    def test_home(self):
        response = self.client.get('/?uploaded=3x3.csv')
        context = response.context

        fields = context['launch_form'].fields
        self.assertEqual(['container_name', 'data', 'tool'],
                         sorted(set(fields.keys())))
        # More wrapping for older pythons / older djangos.

        self.assertIn(('3x3.csv', '3x3.csv'), fields['data'].choices)
        # Locally, you may also have data choices which are not checked in.

        self.assertEquals(
            [('debugger', 'debugger'),
             ('heatmap', 'heatmap'),
             ('lineup', 'lineup')],
            sorted(fields['tool'].choices))

        self.assertEqual(
            context['launch_form'].initial,
            {'data': '3x3.csv'})

        content = response.content.decode('utf-8')
        self.assertIn('<option value="debugger">debugger</option>', content)
        self.assertIn('<option value="3x3.csv" selected', content)
        # For older django versions, it's
        # > selected="selected"
        # but in newer versions, there is no value for the attribute.

    def test_lauch_get_405(self):
        response = self.client.get('/launch/')
        self.assertEqual(405, response.status_code)

    def test_lauch_post(self):
        with patch.object(DockerClientRunWrapper,
                          'run') as mock_run:
            response = self.client.post('/launch/',
                                        {'data': 'fake-data',
                                         'tool': 'debugger',
                                         'container_name': 'fake-name'},
                                        follow=True)
            self.assert_response_redirect(response, '/docker/fake-name/')

            spec = mock_run.call_args[0][0]
            self.assertEqual(spec.container_input_path, '/tmp/input.json')
            self.assertEqual(spec.container_name, 'fake-name')
            self.assertEqual(spec.container_port, 80)
            self.assertEqual(spec.cpus, 0.5)
            self.assertEqual(spec.extra_directories, [])
            self.assertEqual(
                spec.image_name,
                'scottx611x/refinery-developer-vis-tool:v0.0.7')
            self.assertRegexpMatches(
                spec.input['file_relationships'][0],
                r'^http://[^/]+/upload/fake-data')
            self.assertEqual(spec.labels, {})

    def test_kill_get_405(self):
        response = self.client.get('/kill/foo')
        self.assertEqual(405, response.status_code)

    def test_kill_post(self):
        with patch.object(DockerClientWrapper,
                          'list') as mock_list:
            with patch.object(DockerClientWrapper,
                              'kill') as mock_kill:
                response = self.client.post('/kill/foo', follow=True)
                self.assert_response_redirect(response, '/')
                mock_list.assert_called()
                mock_kill.assert_called()

    def test_upload_get_200(self):
        response = self.client.get('/upload/3x3.csv')
        content = response.content.decode('utf-8')
        self.assertIn(',a,b,c', content)

    def test_upload_get_404(self):
        response = self.client.get('/upload/foobar.csv')
        self.assertEqual(404, response.status_code)

    def test_upload_post(self):
        # Just load the fixture on top of itself.
        # Using mocks would be an alternative.
        path = settings.BASE_DIR + '/demo_path_routing/upload/3x3.csv'
        with open(path) as handle:
            response = self.client.post('/upload/',
                                        {'file': handle},
                                        follow=True)
            self.assert_response_redirect(response, '/?uploaded=3x3.csv')
