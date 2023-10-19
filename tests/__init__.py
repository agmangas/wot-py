try:
    import logging

    import coloredlogs

    coloredlogs.install(level=logging.DEBUG)
    logging.getLogger("faker").level = logging.WARNING
    logging.getLogger("hbmqtt").level = logging.INFO
except ImportError:
    pass
