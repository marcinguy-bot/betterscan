"""
This file is part of Betterscan CE (Community Edition).

Betterscan is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Betterscan is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with Betterscan. If not, see <https://www.gnu.org/licenses/>.

Originally licensed under the BSD-3-Clause license with parts changed under
LGPL v2.1 with Commons Clause.
See the original LICENSE file for details.

"""
# -*- coding: utf-8 -*-

"""

    Contains celery tasks to reset pending projects and users

"""





import os
import shutil
import logging
import datetime

from checkmate.management.commands.reset import Command as ResetCommand

from quantifiedcode.settings import settings, backend

from ...worker import celery
from ...models import Project, User
from ..helpers import ExclusiveTask, TaskLogger

logger = logging.getLogger(__name__)

@celery.task(queue="reset", ignore_result=False)
def reset_project(project_id, task_id=None):
    if not task_id:
        task_id = reset_project.request.id
    try:
        project = backend.get(Project, {'pk': project_id})
    except Project.DoesNotExist:
        logger.warning("Project %s does not exist and thus cannot be deleted." % project_id)
        return

    try:
        with ExclusiveTask(backend,
                           {'project.pk': project.pk,
                            'type': {'$in': ['analysis', 'reset', 'delete']}},
                           {'type': 'reset',
                            'project': project},
                           task_id) as reset_task:
            with TaskLogger(reset_task, backend=backend, ping=True):
                _reset_project(project)
    except ExclusiveTask.LockError:
        # We were unable to acquire a lock for this project.
        logger.info("Project %s (%s) is currently being processed, aborting..." % (project.name, project.pk))
        with backend.transaction():
            backend.update(project,
                           {'last_reset': {'dt': datetime.datetime.now(),
                                           'status': 'blocked'}
                            })
    finally:
        logger.info("Done.")

def _reset_project(project):
    try:

        settings.hooks.call("project.reset.before", project)

        reset_command = ResetCommand(project, settings.checkmate_settings, backend)
        reset_command.run()

        with backend.transaction():
            backend.update(project,
                           {'last_reset': {'dt': datetime.datetime.now(),
                                           'status': 'succeeded'},
                            'analyze': True,
                            'analysis_priority': Project.AnalysisPriority.high,
                            'analysis_requested_at': datetime.datetime.now()
                            }, unset_fields=["first_analysis_email_sent"])

        settings.hooks.call("project.reset.after", project)

    except:
        with backend.transaction():
            backend.update(project,
                           {'last_reset': {'dt': datetime.datetime.now(),
                                           'status': 'failed'},
                            })
        logger.error("Reset of project {project.name} (pk={project.pk}) failed!".format(project=project))
        raise
    finally:
        with backend.transaction():
            backend.update(project,
                           {'reset': False},
                           unset_fields=['reset_requested_at'])
