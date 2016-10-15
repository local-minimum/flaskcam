#!/usr/bin/env python3

from flask_cam.server import get_app

app = get_app()
app.run(debug=True)