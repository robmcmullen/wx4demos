import logging
import sys

# Major package imports.
import wx

# Enthought library imports.
from traits.api import Bool, HasTraits, provides, Unicode
from pyface.util.guisupport import start_event_loop_wx

# Local imports.
from pyface.i_gui import IGUI, MGUI


# Logging.
logger = logging.getLogger(__name__)


@provides(IGUI)
class GUI(MGUI, HasTraits):

    busy = Bool(False)

    started = Bool(False)

    state_location = Unicode

    ###########################################################################
    # 'object' interface.
    ###########################################################################

    def __init__(self, splash_screen=None):
        # Display the (optional) splash screen.
        self._splash_screen = splash_screen

        if self._splash_screen is not None:
            self._splash_screen.open()
