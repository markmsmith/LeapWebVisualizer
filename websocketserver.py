import os
import time
import Queue
import logging
import threading

import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket

import Leap
import simplejson as json

logger = logging.getLogger(__name__)


class LeapJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to serialize leap swig things
    """
    def default(self, o):
        if isinstance(o, Leap.Vector):
            return {
                "x": o.x,
                "y": o.y,
                "z": o.z,
            }
        elif isinstance(o, Leap.Ray):
            return {
                "position": o.position,
                "direction": o.direction,
            }
        elif isinstance(o, Leap.Ball):
            return {
                "position": o.position,
                "radius": o.radius,
            }
        elif isinstance(o, Leap.Finger):
            return {
                'id': o.id(),
                'tip': o.tip(),
                'velocity': o.velocity(),
                'width': o.width(),
                'length': o.length(),
                'isTool': o.isTool(),
            }
        elif isinstance(o, Leap.Hand):
            return {
                'id': o.id(),
                'fingers': o.fingers(),
                'palm': o.palm(),
                'velocity': o.velocity(),
                'normal': o.normal(),
                'ball': o.ball(),
            }
        elif isinstance(o, Leap.Frame):
            return {
                'id': o.id(),
                'timestamp': o.timestamp(),
                'hands': o.hands(),
            }
        else:
            return super(LeapJSONEncoder, self).default(o)


class LListener(Leap.Listener):
    """
    Listener to throw things on a queue
    """
    def __init__(self, event_queue, *args, **kwargs):
        super(LListener, self).__init__(*args, **kwargs)
        self.event_queue = event_queue

    def try_put(self, msg):
        assert isinstance(msg, dict)
        try:
            self.event_queue.put(msg, block=False)
        except Queue.Full:
            pass

    def onInit(self, controller):
        self.try_put(
            {
                "state": "initialized"
            }
        )

    def onConnect(self, controller):
        self.try_put(
            {
                "state": "connected"
            }
        )

    def onDisconnect(self, controller):
        self.try_put(
            {
                "state": "disconnected"
            }
        )

    def onFrame(self, controller):
        self.try_put(
            {
                "state": "frame",
                "frame": controller.frame(),
            }
        )


class LeapThread(threading.Thread):
    def __init__(self, event_queue):
        threading.Thread.__init__(self)
        self.daemon = True
        self.event_queue = event_queue

    def run(self):
        self.listener = LListener(self.event_queue)
        self.controller = Leap.Controller(self.listener)
        while 1:
            time.sleep(1)
        self.controller = None


class PlaybackThread(threading.Thread):
    def __init__(self, event_queue, playback, loop, playbackDelay):
        threading.Thread.__init__(self)
        self.daemon = True
        self.event_queue = event_queue
        self.playback = playback
        self.loop = loop
        self.playbackDelay = playbackDelay

    def try_put(self, msg):
        assert isinstance(msg, dict)
        try:
            self.event_queue.put(msg, block=False)
        except Queue.Full:
            pass

    def run(self):
        # give them time to connect
        print "Delaying playback for %d seconds" % self.playbackDelay
        time.sleep(self.playbackDelay)
        print "Playing back recording %s" % self.playback
        self.playback_recording()
        if(self.loop):
            print "looping recording"
            while(True):
                self.playback_recording()

    def playback_recording(self):
        with open(self.playback, 'r') as f:
            for line in f:
                lineJson = json.loads(line)
                print line
                self.try_put(lineJson)
                time.sleep(0.01)
        print "Playback complete"


class Application(tornado.web.Application):
    def __init__(self, options):
        self.options = options
        self.recording = False
        self.lsh = LeapSocketHandler
        handlers = [
            (r"/", MainHandler),
            (r"/leapsocket", self.lsh),
        ]
        settings = {
            'static_path': os.path.join(os.path.dirname(__file__), "static"),
        }
        tornado.web.Application.__init__(self, handlers, **settings)

        self.event_queue = Queue.Queue()
        if(options.playback):
            self.playback_thread = PlaybackThread(self.event_queue, options.playback, options.loop, options.playbackDelay)
            self.playback_thread.start()
        else:
            self.leap_thread = LeapThread(self.event_queue)
            self.leap_thread.start()

        self.startTime = time.time()
        tornado.ioloop.PeriodicCallback(self._poll_for_leap_events, 1).start()

    def _poll_for_leap_events(self):
        try:
            d = self.event_queue.get(block=False)
            logger.debug("pending event queue size: %i", self.event_queue.qsize())
            frameJson = json.dumps(d, cls=LeapJSONEncoder)

            if(self.options.record):
                now = time.time()
                if(self.recording or
                   ((now - self.startTime) >= self.options.recordingDelay)):
                    if(not self.recording):
                        print "Starting recording to %s" % self.options.record
                        self.recording = True

                    with open(self.options.record, 'a') as f:
                        f.write(frameJson)
                        f.write('\n')

            self.lsh.send_updates(frameJson)
            self.event_queue.task_done()
        except Queue.Empty:
            pass


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.redirect("/static/html/index.html")


class LeapSocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()

    def allow_draft76(self):
        # for iOS 5.0 Safari
        return True

    def open(self):
        LeapSocketHandler.waiters.add(self)

    def on_close(self):
        LeapSocketHandler.waiters.remove(self)

    @classmethod
    def send_updates(cls, chat):
        if cls.waiters:
            logger.debug("sending message to %d waiters", len(cls.waiters))
        for waiter in cls.waiters:
            try:
                waiter.write_message(chat)
            except:
                logger.error("Error sending message", exc_info=True)


def main():
    logging.basicConfig(level=logging.INFO)
    tornado.options.define("port", default=8888, help="run on the given port", type=int)
    tornado.options.define("playback", default=None, help="A frame data recording file (in json format) to playback isntead of getting data from the Leap", type=str)
    tornado.options.define("playbackDelay", default=5.0, help="How long to wait (in seconds) before playing back the recording (only relevant when using --playback)", type=float)
    tornado.options.define("loop", default=False, help="Whether to loop playback of the recording (only relevant when using --playback)", type=bool)
    tornado.options.define("record", default=None, help="The name of a file to record frame data to.  Can be played back with --playback=<file name>", type=str)
    tornado.options.define("recordingDelay", default=5.0, help="How long to wait (in seconds) before starting to record (only relevant when using --record)", type=float)

    tornado.options.parse_command_line()
    app = Application(tornado.options.options)
    app.listen(tornado.options.options.port)
    print "%s listening on http://%s:%s" % (__file__, "0.0.0.0", tornado.options.options.port)
    print "ctrl-c to stop!"
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
