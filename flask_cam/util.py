from subprocess import Popen, PIPE
import re
from glob import glob
import os

import flask_cam.config as cfg

REQUESTS = {}


def is_processing(request_id):

    return request_id in REQUESTS and REQUESTS[request_id].working


def usage():

    p = Popen(['df', cfg.tmp_path], stdout=PIPE, stderr=PIPE)
    out, _ = p.communicate()
    out = tuple(l for i, l in enumerate(out.split(b"\n")) if i > 0 and l)[0]
    out = {k: v for k, v in zip(("free", "used", "total", "percent"), re.sub(b" +", b" ", out).split(b" ")[1: -1])}
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

    out = get_stream_output(request_id, times if is_photos else "0", video_format)
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
        self._running = True
        self._stop_polling = False
        self._completed_files = 0
        self._progress = 0

    @staticmethod
    def convert_time_to_duration(duration_expression):

        match = Recording._PATTERN.match(duration_expression)
        if match:
            return sum(int(v) * (60 ** i) for i, v in enumerate(match.groups()[:0:-1]))
        return None

    @property
    def progress(self):

        self._poll()
        return self._progress

    @property
    def files_completed(self):

        self._poll()
        return self._completed_files

    @property
    def completed(self):

        if self._running:
            self._poll()
        return not self._running

    @property
    def working(self):

        if self._running:
            self._poll()
        return self._running

    def _poll(self):

        if self._stop_polling:
            return

        addition = self._proc.stderr.readline()
        if addition:
            self._output += addition
            recs = [Recording.convert_time_to_duration(line) for line in self._output.split(b'\r')]
            if self._records_images:
                self._files_completed = sum(0 if l is None else 1 for l in recs)
                self._progress = self._files_completed / self._duration
            else:
                self._progress = max(l for l in recs if l is not None) / self._duration
                if self._progress >= 1:
                    self._files_completed = 1

        elif not self._running:
            self._stop_polling = True
        self._running = self._proc.poll() is None
