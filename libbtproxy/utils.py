
import sys,time
from . import argparser

if sys.version < '3':
    from threading import Semaphore
    class Barrier:
        def __init__(self, n):
            self.n = n
            self.count = 0
            self.mutex = Semaphore(1)
            self.barrier = Semaphore(0)

        def wait(self):
            self.mutex.acquire()
            self.count = self.count + 1
            self.mutex.release()
            if self.count == self.n: self.barrier.release()
            self.barrier.acquire()
            self.barrier.release()
else:
    from threading import Barrier

def print_verbose(*args):
    if argparser.args.verbose: 
        print(args)

def die(msg=None):
    if msg: print (msg)
    sys.exit()

def print_service(svc):
    print("Service Name: %s"    % svc["name"])
    print("    Host:        %s" % svc["host"])
    print("    Description: %s" % svc["description"])
    print("    Provided By: %s" % svc["provider"])
    print("    Protocol:    %s" % svc["protocol"])
    print("    channel/PSM: %s" % svc["port"])
    print("    svc classes: %s "% svc["service-classes"])
    print("    profiles:    %s "% svc["profiles"])
    print("    service id:  %s "% svc["service-id"])

def inc_last_octet(addr):
    return addr[:15] + hex((int(addr.split(':')[5], 16) + 1) & 0xff).replace('0x','').upper()


def RateLimited(maxPerSecond):
    """
        Decorator for rate limiting a function
    """
    minInterval = 1.0 / float(maxPerSecond)
    
    def decorate(func):
        lastTimeCalled = [0.0]
        def rateLimitedFunction(*args,**kargs):
            elapsed = time.clock() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed
            if leftToWait>0:
                time.sleep(leftToWait)
            ret = func(*args,**kargs)
            lastTimeCalled[0] = time.clock()
            return ret
        return rateLimitedFunction
    return decorate


