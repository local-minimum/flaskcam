from subprocess import Popen, PIPE
import re
from glob import glob
import os

import flask_cam.config as cfg

REQUESTS = {}

def usage():

    p = Popen(['df', cfg.tmp_path], stdout=PIPE, stderr=PIPE)
    out, _ = p.communicate()
    out = tuple(l for i, l in enumerate(out.split(b"\n")) if i > 0 and l)[0]
    out = {k: v for k, v in zip(("free", "used", "total", "percent"), re.sub(b' +', b' ', out).split(b' ')[1: -1])}
    for k in out:
        try:
            out[k] = int(out[k])
        except ValueError:
            pass
    return out


def get_stream_output(request_id, number_of_files, suffix):

    if isinstance(number_of_files, int):
        sequence_length = "0" * len(str(number_of_files))
    else:
        sequence_length = number_of_files

    return cfg.tmp_names.format(request=request_id,
                                sequence_length=sequence_length,
                                suffix=suffix)


def get_file_names(request_id="*", suffix="*"):

    return glob(os.path.join(cfg.tmp_path,
                             get_stream_output(request_id, number_of_files="*", suffix=suffix)))


def record(request_id, video_format="jpeg", times=10, fps=10, size=None, device=None):

    is_photos = isinstance(times, int)
    cmd = ["streamer", '-f', video_format, '-t', times, '-r', fps]
    if size:
        cmd += ['-s', size]
    if device:
        cmd += ['-c', device]

    out = get_stream_output(request_id, times if is_photos else "0", request_id)
    cmd += ['-o', os.path.join(cfg.tmp_path, out)]
    REQUESTS[request_id] = Recording(Popen(cmd, stdout=PIPE, stderr=PIPE), is_photos, times)


class Recording(object):

    _PATTERN = re.compile(b'(rec |)(\d+):(\d{2})\.(\d{2})')

    def __init__(self, process, records_images, duration):

        self._proc = process
        self._records_images = records_images

        if records_images:
            self._duration = duration
        else:
            self._duration = Recording.convert_time_to_duration(duration)

        self._output = b''

    @staticmethod
    def convert_time_to_duration(duration_expression):

        match = Recording._PATTERN.match(duration_expression)
        if match:
            return sum(int(v) * (60 ** i) for i, v in enumerate(match.groups()[:0:-1]))
        return None

    @property
    def progress(self):

        return 0

    @property
    def files_completed(self):

        return 0