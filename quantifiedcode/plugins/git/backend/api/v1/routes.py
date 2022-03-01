# -*- coding: utf-8 -*-

"""

    Contains routes provided by the GitHub plugin

"""





prefix = "/git"

from .resources.git_snapshots import GitSnapshots
from .resources.project import ProjectDetails

routes = [
    {'/project/<project_id>/git_snapshots/<remote>/<regex(".*$"):branch_name>': [GitSnapshots,
                                                                                 {'methods': ["GET", "POST"]}]},
    {'/project/git': [ProjectDetails,{'methods': ["POST"]}]},
    {'/project/git/<project_id>': [ProjectDetails,{'methods': ["PUT"]}]},
]
