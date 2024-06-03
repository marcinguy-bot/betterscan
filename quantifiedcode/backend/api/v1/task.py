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

"""





import os

from flask import request

from quantifiedcode.settings import backend, settings

from ...utils.api import ArgumentError, get_pagination_args
from ...models import Task
from ...decorators import valid_user, valid_project
from ..resource import Resource

from .forms.task import TaskLogForm

class TaskDetails(Resource):
    export_map = (
        {'project': ('pk', 'name')},
        'pk',
        'status',
        'created_at',
        'updated_at',
        'last_ping',
        'type',
    )

    @valid_user(anon_ok=True)
    @valid_project(public_ok=True)
    def get(self, project_id, task_id):
        """ Get the task with the given task id for the project with the given project id.
        :param project_id: id of the project
        :param task_id: id of the task
        :return: task information
        """
        try:
            task = backend.get(Task, {'project.pk': request.project.pk, 'pk': task_id},
                                     only=self.export_fields, include=('project',), raw=True)
        except Task.DoesNotExist:
            return {'message': "unknown task"}, 404
        return {'task': self.export(task)}, 200


class TaskLog(Resource):

    @valid_user(anon_ok=True)
    @valid_project(public_ok=True)
    def get(self, project_id, task_id):
        """ Returns the log for the specified project task. Accepts a from request parameter, which seeks into
        the log file to return the rest of the file.
        :param project_id: id of the project
        :param task_id: id of the task
        :return: log, its length, offset, and the task status
        """

        form = TaskLogForm(request.args)

        if not form.validate():
            return {'message' : 'please correct the errors mentioned below.'}, 400

        data = form.data

        from_chr = data['from_chr']

        try:
            task = backend.get(Task, {'project.pk': request.project.pk, 'pk': task_id}, raw=True)
        except Task.DoesNotExist:
            return {'message': "unknown task"}, 404

        log_path = os.path.join(settings.get('backend.path'),
                                settings.get('backend.paths.tasks'),
                                "{}.log".format(task['pk']))

        try:
            with open(log_path, "r") as task_log:
                task_log.seek(from_chr)
                content = task_log.read()

            data = {
                'task_log': content,
                'len': len(content),
                'from': from_chr,
                'task_status': task['status'] if 'status' in task else "unknown"
            }
            return data, 200
        except IOError:
            return {'message': "no log found {}".format(log_path)}, 404


class Tasks(Resource):

    DEFAULT_LIMIT = 20
    DEFAULT_OFFSET = 0

    @valid_user(anon_ok=True)
    @valid_project(public_ok=True)
    def get(self, project_id):
        """ Get all tasks for the project with the given id.
        :param project_id: id of the project
        :return: tasks for the project
        """
        try:
            pagination_args = get_pagination_args(request)
        except ArgumentError as e:
            return {'message': e.message}, 500

        limit = pagination_args['limit'] if 'limit' in pagination_args else self.DEFAULT_LIMIT
        offset = pagination_args['offset'] if 'offset' in pagination_args else self.DEFAULT_OFFSET

        tasks = backend.filter(Task, {'project.pk': request.project.pk},
                                     include=('project',), only=TaskDetails.export_fields, raw=True
                                     ).sort('created_at', -1)

        return {'tasks': [TaskDetails.export(task) for task in tasks[offset:offset + limit]]}, 200
