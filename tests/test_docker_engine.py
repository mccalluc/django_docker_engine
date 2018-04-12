import re
import unittest
from datetime import datetime

import docker
from django_docker_engine.container_managers.docker_engine import (DockerEngineManager,
                                                                   ExpectedPortMissing,
                                                                   MisconfiguredPort,
                                                                   NoPortLabel,
                                                                   PossiblyOutOfDiskSpace)
from tests import ALPINE_IMAGE, NGINX_IMAGE


class DockerEngineManagerTests(unittest.TestCase):

    def setUp(self):
        timestamp = re.sub(r'\W', '-', datetime.now().isoformat())
        data_dir = '/tmp/django-docker-tests-' + timestamp
        self.root_label = 'test-root'
        self.manager = DockerEngineManager(data_dir, self.root_label)
        self.container_name = timestamp
        self.kwargs = {
            'cmd': None
        }

    def assert_add_kwarg_still_fails(self, key, value, image, expected_error):
        self.kwargs[key] = value
        self.manager.run(image, **self.kwargs)
        if expected_error:
            with self.assertRaises(expected_error):
                self.manager.get_url(self.container_name)
        else:
            self.manager.get_url(self.container_name)
        # TODO: Why the '/'?
        self.manager.list({'name': '/' + self.container_name})[0].remove(
            force=True,
            v=True  # Remove volumes associated with the container
        )

    def test_bad_image_pull(self):
        with self.assertRaises(PossiblyOutOfDiskSpace):
            self.manager.pull('no_such_image')

    def test_bad_image_run(self):
        with self.assertRaises(PossiblyOutOfDiskSpace):
            self.manager.run('no_such_image', cmd='foo')

    def test_minimum_kwargs_to_run(self):
        self.assert_add_kwarg_still_fails(
            'name', self.container_name,
            ALPINE_IMAGE,
            NoPortLabel
        )

        self.assert_add_kwarg_still_fails(
            'labels', {self.root_label + '.port': '12345'},
            ALPINE_IMAGE,
            ExpectedPortMissing
            # Had been 'NoPortsOpen': I'm not sure why behavior changed. :(
        )

        self.assert_add_kwarg_still_fails(
            'detach', True,
            NGINX_IMAGE,
            ExpectedPortMissing
        )

        self.assert_add_kwarg_still_fails(
            'labels', {self.root_label + '.port': '80'},
            NGINX_IMAGE,
            MisconfiguredPort
        )

        self.assert_add_kwarg_still_fails(
            'ports', {'80/tcp': None},
            NGINX_IMAGE,
            None
        )
