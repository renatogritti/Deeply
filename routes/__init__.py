from app import *

from routes import (
    root,
    cards,
    teams,
    tags,
    projects,
    share
    )

root.init_app(app)
cards.init_app(app)
teams.init_app(app)
tags.init_app(app)
projects.init_app(app)
share.init_app(app)