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
"""Cloud functions for build scheduling."""

from collections import namedtuple
import logging
import os
import re
import yaml

from github import Github
from google.api_core import exceptions
from google.cloud import ndb
from google.cloud import scheduler_v1

VALID_PROJECT_NAME = re.compile(r'^[a-zA-Z0-9_-]+$')
DEFAULT_BUILDS_PER_DAY = 1
MAX_BUILDS_PER_DAY = 4

ProjectMetadata = namedtuple('ProjectMetadata', 'schedule')


class ProjectYamlError(Exception):
  """Error in project.yaml format."""


# pylint: disable=too-few-public-methods
class Project(ndb.Model):
  """Represents an integrated OSS-Fuzz project."""
  name = ndb.StringProperty()
  schedule = ndb.StringProperty()


# pylint: disable=too-few-public-methods
class GitAuth(ndb.Model):
  """Represents Github access token entity."""
  access_token = ndb.StringProperty()


def create_scheduler(cloud_scheduler_client, project_name, schedule):
  """Creates schedulers for new projects."""
  project_id = os.environ.get('GCP_PROJECT')
  location_id = os.environ.get('FUNCTION_REGION')
  parent = cloud_scheduler_client.location_path(project_id, location_id)
  job = {
      'name': parent + '/jobs/' + project_name + '-scheduler',
      'pubsub_target': {
          'topic_name': 'projects/' + project_id + '/topics/request-build',
          'data': project_name.encode()
      },
      'schedule': schedule
  }

  cloud_scheduler_client.create_job(parent, job)


def delete_scheduler(cloud_scheduler_client, project_name):
  """Deletes schedulers for projects that were removed."""
  project_id = os.environ.get('GCP_PROJECT')
  location_id = os.environ.get('FUNCTION_REGION')
  name = cloud_scheduler_client.job_path(project_id, location_id,
                                         project_name + '-scheduler')
  cloud_scheduler_client.delete_job(name)


def update_scheduler(cloud_scheduler_client, project, schedule):
  """Updates schedule in case schedule was changed."""
  project_id = os.environ.get('GCP_PROJECT')
  location_id = os.environ.get('FUNCTION_REGION')
  parent = cloud_scheduler_client.location_path(project_id, location_id)
  job = {
      'name': parent + '/jobs/' + project.name + '-scheduler',
      'pubsub_target': {
          'topic_name': 'projects/' + project_id + '/topics/request-build',
          'data': project.name.encode()
      },
      'schedule': project.schedule
  }

  update_mask = {'schedule': schedule}
  cloud_scheduler_client.update(job, update_mask)


def sync_projects(cloud_scheduler_client, projects):
  """Sync projects with cloud datastore."""
  for project in Project.query():
    if project.name in projects:
      continue

    try:
      delete_scheduler(cloud_scheduler_client, project.name)
      project.key.delete()
    except exceptions.GoogleAPICallError as error:
      logging.error('Scheduler deletion for %s failed with %s', project.name,
                    error)

  existing_projects = {project.name for project in Project.query()}
  for project_name in projects:
    if project_name in existing_projects:
      continue

    try:
      create_scheduler(cloud_scheduler_client, project_name,
                       projects[project_name].schedule)
      Project(name=project_name, schedule=projects[project_name].schedule).put()
    except exceptions.GoogleAPICallError as error:
      logging.error('Scheduler creation for %s failed with %s', project_name,
                    error)

  for project in Project.query():
    if project.name not in projects or project.schedule == projects[
        project.name]:
      continue
    try:
      update_scheduler(cloud_scheduler_client, project,
                       projects[project.name].schedule)
      project.schedule = projects[project.name].schedule
      project.put()
    except exceptions.GoogleAPICallError as error:
      logging.error('Updating scheduler for %s failed with %s', project.name,
                    error)


def _has_docker_file(project_contents):
  """Checks if project has a Dockerfile."""
  return any(
      content_file.name == 'Dockerfile' for content_file in project_contents)


def get_schedule(project_contents):
  """Checks for schedule parameter in yaml file else uses DEFAULT_SCHEDULE."""
  for content_file in project_contents:
    if content_file.name != 'project.yaml':
      continue
    project_yaml = yaml.safe_load(content_file.decoded_content.decode('utf-8'))
    times_per_day = project_yaml.get('schedule', DEFAULT_BUILDS_PER_DAY)
    if not isinstance(times_per_day, int) or times_per_day not in range(
        1, MAX_BUILDS_PER_DAY + 1):
      raise ProjectYamlError('Parameter is not an integer in range [1-4]')

      # Starting at 6:00 am, next build schedules are added at 'interval' slots
      # Example for interval 2, hours = [6, 18] and schedule = '0 6,18 * * *'

    interval = 24 // times_per_day
    hours = []
    for hour in range(6, 30, interval):
      hours.append(hour % 24)
    schedule = '0 ' + ','.join(str(hour) for hour in hours) + ' * * *'

  return schedule


def get_projects(repo):
  """Get project list from git repository."""
  projects = {}
  contents = repo.get_contents('projects')
  for content_file in contents:
    if content_file.type != 'dir' or not VALID_PROJECT_NAME.match(
        content_file.name):
      continue

    project_contents = repo.get_contents(content_file.path)
    if not _has_docker_file(project_contents):
      continue

    try:
      projects[content_file.name] = ProjectMetadata(
          schedule=get_schedule(project_contents))
    except ProjectYamlError as error:
      logging.error(
          'Incorrect format for project.yaml file of %s with error %s',
          content_file.name, error)

  return projects


def get_access_token():
  """Retrieves Github's Access token from Cloud Datastore."""
  token = GitAuth.query().get()
  if token is None:
    raise RuntimeError('No access token available')
  return token.access_token


def sync(event, context):
  """Sync projects with cloud datastore."""
  del event, context  #unused
  client = ndb.Client()

  with client.context():
    github_client = Github(get_access_token())
    repo = github_client.get_repo('google/oss-fuzz')
    projects = get_projects(repo)
    cloud_scheduler_client = scheduler_v1.CloudSchedulerClient()
    sync_projects(cloud_scheduler_client, projects)
