=========
emocapper
=========

Script to view and record data from Emocap, - the modified Emotiv system with EASY CAP.

Recording
---------

Record 3 seconds to file with default filename 'recording.csv':

    $ emocapper record --duration=3
  
An electrode signal can be plotted with 

    >>> from everything import *
    >>> read_csv('recording.csv').O1.plot()
    <matplotlib.axes._subplots.AxesSubplot object at 0x7f88a10b1190>
    >>> show()

Show qualities
--------------
 
    $ emocapper showqualities
