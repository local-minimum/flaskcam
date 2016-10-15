from flask import Flask, jsonify, send_file
from threading import Thread
from flask_cam import util, config
import time
import io
import os

__RESTING = True
__BACKGROUND_SERVICE = False
__CACHE = [None] * config.background_cache_length
__CACHE_INDEX = -1


def background_service():

    __BACKGROUND_SERVICE = True

    while __BACKGROUND_SERVICE:
        t = time.time()
        req = util.get_recording(config.background_request_id)

        if req is None or req.completed:

            if req is not None:

                files = req.get_file_names()
                if files:
                    insert_image_into_cache(files[0])

            util.record(config.background_request_id, times=1)

        delta = 1.0 / config.background_fps - (time.time() - t)
        if delta > 0:
            time.sleep(delta)


def insert_image_into_cache(path):
    global __CACHE_INDEX, __CACHE

    try:
        with open(path, 'rb') as fh:
            stream = io.BytesIO()
            stream.write(fh.read())
        stream.flush()
        os.remove(path)
        stream.seek(0)
        __CACHE_INDEX = (__CACHE_INDEX + 1) % config.background_cache_length
        __CACHE[__CACHE_INDEX] = stream
    except IOError:
        print("Error reading/removing image")


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

        global __CACHE, __CACHE_INDEX
        stream = __CACHE[__CACHE_INDEX]
        if stream is None:
            return jsonify(success=False, is_endpoint=True, reason="No image recorded")
        else:
            stream.seek(0)
            return send_file(stream, mimetype='image/png')
