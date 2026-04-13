import logging

log = logging.getLogger("cv_bot")
if not log.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    log.addHandler(h)
log.setLevel(logging.INFO)
