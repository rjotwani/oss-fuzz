# Copyright 2020 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################
"""Unit tests for Cloud Function sync, which syncs the list of github projects
and uploads them to the Cloud Datastore."""

from collections import namedtuple
import os
import unittest
import subprocess
import threading

from google.cloud import ndb

from main import sync_projects
from main import get_projects
from main import get_access_token
from main import Project

_EMULATOR_TIMEOUT = 20
_DATASTORE_READY_INDICATOR = b'is now running'
_DATASTORE_EMULATOR_PORT = 8432
_TEST_PROJECT_ID = 'test-project'
ProjectMetadata = namedtuple('ProjectMetadata', 'schedule')


def start_datastore_emulator():
  """Start Datastore emulator."""
  return subprocess.Popen([
      'gcloud',
      'beta',
      'emulators',
      'datastore',
      'start',
      '--consistency=1.0',
      '--host-port=localhost:' + str(_DATASTORE_EMULATOR_PORT),
      '--project=' + _TEST_PROJECT_ID,
      '--no-store-on-disk',
  ],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)


def _wait_for_emulator_ready(proc,
                             emulator,
                             indicator,
                             timeout=_EMULATOR_TIMEOUT):
  """Wait for emulator to be ready."""

  def _read_thread(proc, ready_event):
    """Thread to continuously read from the process stdout."""
    ready = False
    while True:
      line = proc.stdout.readline()
      if not line:
        break
      if not ready and indicator in line:
        ready = True
        ready_event.set()

  # Wait for process to become ready.
  ready_event = threading.Event()
  thread = threading.Thread(target=_read_thread, args=(proc, ready_event))
  thread.daemon = True
  thread.start()
  if not ready_event.wait(timeout):
    raise RuntimeError(
        '{} emulator did not get ready in time.'.format(emulator))
  return thread


# pylint: disable=too-few-public-methods
class Repository:
  """Mocking Github Repository."""

  def __init__(self, name, file_type, path, contents=None):
    self.contents = contents or []
    self.name = name
    self.type = file_type
    self.path = path
    self.decoded_content = b"name: test"

  def get_contents(self, path):
    """"Get contents of repository."""
    if self.path == path:
      return self.contents

    for content_file in self.contents:
      if content_file.path == path:
        return content_file.contents

    return None

  def set_yaml_contents(self, decoded_content):
    """Set yaml_contents."""
    self.decoded_content = decoded_content


class CloudSchedulerClient:
  """Mocking cloud scheduler client."""

  def __init__(self):
    self.schedulers = []

  # pylint: disable=no-self-use
  def location_path(self, project_id, location_id):
    """Return project path."""
    return 'projects/{}/location/{}'.format(project_id, location_id)

  def create_job(self, parent, job):
    """Simulate create job."""
    del parent
    if job['name'] not in self.schedulers:
      self.schedulers.append(job)

  # pylint: disable=no-self-use
  def job_path(self, project_id, location_id, name):
    """Return job path."""
    return 'projects/{}/location/{}/jobs/{}'.format(project_id, location_id,
                                                    name)

  def delete_job(self, name):
    """Simulate delete jobs."""
    for job in self.schedulers:
      if job['name'] == name:
        self.schedulers.remove(job)
        break

  def update(self, job, update_mask):
    """Simulate update jobs."""
    for existing_job in self.schedulers:
      if existing_job == job:
        job['schedule'] = update_mask['schedule']


class TestDataSync(unittest.TestCase):
  """Unit tests for sync."""

  @classmethod
  def setUpClass(cls):
    ds_emulator = start_datastore_emulator()
    _wait_for_emulator_ready(ds_emulator, 'datastore',
                             _DATASTORE_READY_INDICATOR)
    os.environ['DATASTORE_EMULATOR_HOST'] = 'localhost:' + str(
        _DATASTORE_EMULATOR_PORT)
    os.environ['GOOGLE_CLOUD_PROJECT'] = _TEST_PROJECT_ID
    os.environ['DATASTORE_DATASET'] = _TEST_PROJECT_ID
    os.environ['GCP_PROJECT'] = 'test-project'
    os.environ['FUNCTION_REGION'] = 'us-central1'

  def test_sync_projects_update(self):
    """Testing sync_projects() updating a schedule."""
    client = ndb.Client()
    cloud_scheduler_client = CloudSchedulerClient()

    with client.context():
      Project(name='test1', schedule='0 8 * * *').put()
      Project(name='test2', schedule='0 9 * * *').put()

      projects = {
          'test1': ProjectMetadata('0 8 * * *'),
          'test2': ProjectMetadata('0 7 * * *')
      }
      sync_projects(cloud_scheduler_client, projects)

      projects_query = Project.query()
      self.assertEqual({
          'test1': '0 8 * * *',
          'test2': '0 7 * * *'
      }, {project.name: project.schedule for project in projects_query})
      clean = [project.key for project in projects_query]
      ndb.delete_multi(clean)

  def test_sync_projects_create(self):
    """"Testing sync_projects() creating new schedule."""
    client = ndb.Client()
    cloud_scheduler_client = CloudSchedulerClient()

    with client.context():
      Project(name='test1', schedule='0 8 * * *').put()

      projects = {
          'test1': ProjectMetadata('0 8 * * *'),
          'test2': ProjectMetadata('0 7 * * *')
      }
      sync_projects(cloud_scheduler_client, projects)

      projects_query = Project.query()
      self.assertEqual({
          'test1': '0 8 * * *',
          'test2': '0 7 * * *'
      }, {project.name: project.schedule for project in projects_query})
      clean = [project.key for project in projects_query]
      ndb.delete_multi(clean)

  def test_sync_projects_delete(self):
    """Testing sync_projects() deleting."""
    client = ndb.Client()
    cloud_scheduler_client = CloudSchedulerClient()

    with client.context():
      Project(name='test1', schedule='0 8 * * *').put()
      Project(name='test2', schedule='0 9 * * *').put()

      projects = {'test1': ProjectMetadata('0 8 * * *')}
      sync_projects(cloud_scheduler_client, projects)

      projects_query = Project.query()
      self.assertEqual(
          {'test1': '0 8 * * *'},
          {project.name: project.schedule for project in projects_query})
      clean = [project.key for project in projects_query]
      ndb.delete_multi(clean)

  def test_get_projects_yaml(self):
    """Testing get_projects() yaml get_schedule()."""

    repo = Repository('oss-fuzz', 'dir', 'projects', [
        Repository('test0', 'dir', 'projects/test0', [
            Repository('Dockerfile', 'file', 'projects/test0/Dockerfile'),
            Repository('project.yaml', 'file', 'projects/test0/project.yaml')
        ]),
        Repository('test1', 'dir', 'projects/test1', [
            Repository('Dockerfile', 'file', 'projects/test1/Dockerfile'),
            Repository('project.yaml', 'file', 'projects/test1/project.yaml')
        ])
    ])
    repo.contents[0].contents[1].set_yaml_contents(b'schedule: 2')
    repo.contents[1].contents[1].set_yaml_contents(b'schedule: 3')

    self.assertEqual(
        get_projects(repo), {
            'test0': ProjectMetadata('0 6,18 * * *'),
            'test1': ProjectMetadata('0 6,14,22 * * *')
        })

  def test_get_projects_no_docker_file(self):
    """Testing get_projects() with missing dockerfile"""

    repo = Repository('oss-fuzz', 'dir', 'projects', [
        Repository('test0', 'dir', 'projects/test0', [
            Repository('Dockerfile', 'file', 'projects/test0/Dockerfile'),
            Repository('project.yaml', 'file', 'projects/test0/project.yaml')
        ]),
        Repository('test1', 'dir', 'projects/test1')
    ])

    self.assertEqual(get_projects(repo),
                     {'test0': ProjectMetadata('0 6 * * *')})

  def test_get_projects_invalid_project_name(self):
    """Testing get_projects() with invalid project name"""

    repo = Repository('oss-fuzz', 'dir', 'projects', [
        Repository('test0', 'dir', 'projects/test0', [
            Repository('Dockerfile', 'file', 'projects/test0/Dockerfile'),
            Repository('project.yaml', 'file', 'projects/test0/project.yaml')
        ]),
        Repository('test1@', 'dir', 'projects/test1', [
            Repository('Dockerfile', 'file', 'projects/test1/Dockerfile'),
            Repository('project.yaml', 'file', 'projects/test0/project.yaml')
        ])
    ])

    self.assertEqual(get_projects(repo),
                     {'test0': ProjectMetadata('0 6 * * *')})

  def test_get_projects_non_directory_type_project(self):
    """Testing get_projects() when a file in projects/ is not of type 'dir'."""

    repo = Repository('oss-fuzz', 'dir', 'projects', [
        Repository('test0', 'dir', 'projects/test0', [
            Repository('Dockerfile', 'file', 'projects/test0/Dockerfile'),
            Repository('project.yaml', 'file', 'projects/test0/project.yaml')
        ]),
        Repository('test1', 'file', 'projects/test1')
    ])

    self.assertEqual(get_projects(repo),
                     {'test0': ProjectMetadata('0 6 * * *')})

  def test_invalid_yaml_format(self):
    """Testing invalid yaml schedule parameter argument."""

    repo = Repository('oss-fuzz', 'dir', 'projects', [
        Repository('test0', 'dir', 'projects/test0', [
            Repository('Dockerfile', 'file', 'projects/test0/Dockerfile'),
            Repository('project.yaml', 'file', 'projects/test0/project.yaml')
        ])
    ])
    repo.contents[0].contents[1].set_yaml_contents(b'schedule: some-string')

    self.assertEqual(get_projects(repo), {})

  def test_yaml_out_of_range(self):
    """Testing invalid yaml schedule parameter argument."""

    repo = Repository('oss-fuzz', 'dir', 'projects', [
        Repository('test0', 'dir', 'projects/test0', [
            Repository('Dockerfile', 'file', 'projects/test0/Dockerfile'),
            Repository('project.yaml', 'file', 'projects/test0/project.yaml')
        ])
    ])
    repo.contents[0].contents[1].set_yaml_contents(b'schedule: 5')

    self.assertEqual(get_projects(repo), {})

  def test_get_access_token(self):
    """Testing get_access_token()."""
    client = ndb.Client()

    with client.context():
      self.assertRaises(RuntimeError, get_access_token)

  @classmethod
  def tearDownClass(cls):
    # TODO: replace this with a cleaner way of killing the process
    os.system('pkill -f datastore')


if __name__ == '__main__':

  unittest.main(exit=False)
