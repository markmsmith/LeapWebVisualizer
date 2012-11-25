LeapWebVisualizer
=================

Project to visualize the hand and finger data from the Leap Motion in a web browser.

Uses the Leap -> Python -> WebSockets bridge [leapfrog'](https://github.com/tylerwilliams/leapfrog) written by Tyler
 Williams.

##How to run
 0. Install the [Leap Motion SDK](https://developer.leapmotion.com/downloads), plug in the Leap Motion and run the Leap application (the icon should appear green in the system tray).
 1. Install [python](http://www.python.org/download/)
 2. Install [PIP](http://www.pip-installer.org/en/latest/installing.html) (you may have to setup [distribute](http://pypi.python.org/pypi/distribute#installation-instructions) or [easy_install](http://packages.python.org/distribute/easy_install.html) first)
 3. Run 'pip install tornado' (http://www.tornadoweb.org/)
 4. Run 'pip install simplejson' (https://github.com/simplejson/simplejson)
 5. Run 'python websocketserver.py'
 6. Open browser to http://localhost:8888

##If you don't have the Leap Motion hardware
For step 5, you can playback a file with a recording I made of the frame data by using this command instead:

    python websocketserver.py --playback=recording.json

You can also pass the arguments:

'--playbackDelay=10' to change how long it waits before playing the recording, to give you time to load up your browswer (the default is 5 seconds).

'--loop=True' if it should playback the recording in an endless loop (good for playing with the javascript, or for demos.)

##Making recordings
If you have a Leap Motion device and want to make your own recordings, you can run the server with this command:

    python websocketserver.py --record=myRecording.json

You can also pass the argument '--recordingDelay=10' if you want to change how long it waits before starting recording (the default is 5 seconds).

