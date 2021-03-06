## web hook dispatcher library
#
# Copyright (c) 2008, 2009 Adam Marshall Smith
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
#
# Idea:
# - recipients are urls
# - events are special strings starting with reversed domain
# - args are arbitrary dicts to post to each recipient of an event
# - cooldown time is the wait after a failed post before trying again
# - retry time is to total time during which retries will continue

from twisted.internet import defer, reactor
from twisted.web import client

import time
import urllib

class HookManager(object):
    """I manage a list of active recipients to which I will do my best to deliver payloads."""
    
    cooldownTime = 60 # between successive hooks
    retryTime = 3600 # stop retrying after this time

    def __init__(self):
        self.recipients = []
    
    def addRecipient(self, recipient):
        self.recipients.append(recipient)
        
    def dispatchEvent(self, event, args={}, **kw):
        entry = {"event": event}
        entry.update(kw)
        entry.update(args)
        
        now = time.time()
        for r in self.recipients:
            self.__dispatchEventToRecipient(entry, r, now)
        
    def __dispatchEventToRecipient(self, entry, recipient, ctime):
        
        def _good(page):
            # looks like it worked
            pass
        
        def _bad(reason):
            reactor.callLater(
                self.cooldownTime,
                self.__dispatchEventToRecipient,
                entry,
                recipient,
                ctime)
        
        now = time.time()
        if now < ctime + self.retryTime:
            data = urllib.urlencode(entry)
            headers = {
                'content-type': 'application/x-www-form-urlencoded',
                'content-length': str(len(data)),
            }
            client.getPage(recipient, method='POST', postdata=data, headers=headers) \
                .addCallbacks(_good,_bad) 
        else:
            # silently drop this guy because it is past his retry time
            pass
