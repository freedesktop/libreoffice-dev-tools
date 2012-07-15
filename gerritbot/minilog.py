#!/usr/bin/env python

import logging
import threading
import subprocess

class LogThread(threading.Thread):
    def __init__(self, logger, level, extra, stream):
        threading.Thread.__init__(self)
        self.logger = logger
        self.level = level
        self.extra = extra
        self.stream = stream
        self.daemon = False
    def run(self):
        while True:
            outline = self.stream.readline()
            if len(outline) == 0:
                break;
            self.logger.log(self.level, outline[:-1], extra=self.extra)
        
def logged_call(args, logger, extra):
    p = subprocess.Popen(args=args, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    outthread = LogThread(logger, logging.INFO, extra, p.stdout)
    errthread = LogThread(logger, logging.WARNING, extra, p.stderr)
    outthread.start()
    errthread.start()    
    p.wait()
    outthread.join()
    errthread.join()
    if p.returncode == 0:
        logger.info('call to "%s" succeeded.' % ' '.join(args), extra=extra)
    else:
        logger.error('call to "%s" returned: %d' % (' '.join(args), p.returncode), extra=extra)
        raise Exception('"%s" command returned non-null.' % ' '.join(args))
