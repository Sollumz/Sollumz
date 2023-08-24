import os


def init_debug():
    """Starts a debugging server if requested by the user through environment variables.
    Requires `debugpy` to be installed in Blender python environment.

    Environment Variables:
    - `SOLLUMZ_DEBUG`: if `true`, start the debugging server; otherwise, do nothing.
    - `SOLLUMZ_DEBUG_HOST`: host used by the debugging server, default 127.0.0.1.
    - `SOLLUMZ_DEBUG_PORT`: port used by the debugging server, default 5678.
    - `SOLLUMZ_DEBUG_WAIT`: if `true`, blocks executing until a client connects. Useful to debug initialization code.
    """
    enable = os.environ.get("SOLLUMZ_DEBUG", "false") == "true"
    if not enable:
        return

    import debugpy

    host = os.environ.get("SOLLUMZ_DEBUG_HOST", "127.0.0.1")
    port = int(os.environ.get("SOLLUMZ_DEBUG_PORT", 5678))
    wait = os.environ.get("SOLLUMZ_DEBUG_WAIT", "false") == "true"

    debugpy.listen((host, port))
    if wait:
        debugpy.wait_for_client()
