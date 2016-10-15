from flask import Flask, jsonify
from threading import Thread
from flask_cam import util, config
import time

__RESTING = True
__BACKGROUND_SERVICE = True


def background_service():

    __BACKGROUND_SERVICE = True

    while __BACKGROUND_SERVICE:

        if not util.is_processing(config.background_request_id):

            util.record(config.background_request_id, times=1)

        time.sleep(1.0 / config.background_fps)


def get_app():

    app = Flask("FlaskCamServer")

    # TODO: Add routes

    return app
