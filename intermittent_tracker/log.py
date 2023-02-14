import logging
import sys


APP_NAME = 'intermittent_tracker'


def logger():
    """Get the main Flask logger, equivalent to app.logger."""
    return logging.getLogger(APP_NAME)


class WerkzeugFilter(logging.Filter):
    """Adjust the levels of request logs to help filter them."""

    def filter(self, record):
        if record.msg.endswith('] "%s" %s %s') and record.levelno == 20:
            status_code = record.args[1]
            if status_code.startswith('2'):
                record.levelname = 'DEBUG'
                record.levelno = logging.getLevelName(record.levelname)
            if status_code.startswith('4') or status_code.startswith('5'):
                record.levelname = 'WARNING'
                record.levelno = logging.getLevelName(record.levelname)
        return logging.getLogger(self.name).isEnabledFor(record.levelno)
