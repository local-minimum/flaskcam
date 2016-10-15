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
    register_api(app)

    return app


def register_api(app):

    @app.route("/api/camera/on")
    def _set_camera_on():
        global __BACKGROUND_SERVICE
        if __BACKGROUND_SERVICE is False:
            t = Thread(target=background_service)
            t.start()
            return jsonify(success=True, is_endpoint=True)
        return jsonify(success=False, is_endpoint=True, reason="Already running image acquisition")

    @app.route("/api/camera/off")
    def _set_camera_off():
        global __BACKGROUND_SERVICE
        if __BACKGROUND_SERVICE:
            __BACKGROUND_SERVICE = False
            return jsonify(success=True, is_endpoint=True)
        return jsonify(success=False, is_endpoint=True, reason="Not running image acquisition")

    @app.route("/api/image/recent")
    def _get_most_resent_image():

        return None
