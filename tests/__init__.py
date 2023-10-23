try:
    import logging

    import coloredlogs

    coloredlogs.install(level=logging.DEBUG)

    for logger_name in ["faker", "transitions.core"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
except ImportError:
    pass
