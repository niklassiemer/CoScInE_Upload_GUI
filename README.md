# CoScInE (Upload) GUI

Graphical user interface based on tkinter for the `coscine` python package. 
Right now, only the upload of files to already initialized Resources is possible.

Usage:
```
from coscine_gui import CoScInETokenGUI

CoScInETokenGUI()
```

This starts a window where the coscine token has to be provided. 
Afterwards, a new window to interact with CoScInE is opened.

If you already have an initialized `coscine.Client` you may directly use the CoScInE GUI:
```
from coscine import Client
from coscine_gui import CoScInEGUI

coscine_client = Client("YOUR_TOKEN")
CoScInEGUI(coscine_client)
```

## Standalone version

For each release, there is a standalone version available. This is generated by `pyinstaller`:

This repository contains a simple `coscine_gui.py` python script (with exactly the 'Usage' content from above) 
 which can be turned into a standalone application. To do so, you install this package and `pyinstaller` and run
`pyinstaller.exe --onefile .\coscine_gui.py` (on Windows) in the package directory. 
It will create (among other files) an EXE in the `dist` directory. Such an EXE is attached on releases.
