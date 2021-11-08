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
