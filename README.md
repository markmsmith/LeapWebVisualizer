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

