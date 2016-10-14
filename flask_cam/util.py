from subprocess import Popen, PIPE
import re

import flask_cam.config as cfg


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
