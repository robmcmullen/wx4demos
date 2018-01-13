import logging
logging.basicConfig(level=logging.DEBUG)

print "importing wx"
import wx
import wx.html

app = wx.App()
print "app:", wx.GetApp()

print "importing pyface.about_dialog"
from pyface import about_dialog
print "app:", wx.GetApp()

            
def main(argv):
    """ A simple example of using Tasks.
    """
    print "creating frame"
    # Start the GUI event loop.
    frame = wx.Frame(None, -1, "Test", size=(400,400))
    print "app:", wx.GetApp()
    print "creating html"
    html = wx.html.HtmlWindow(frame, -1)
    frame.Show(True)
    #gui.start_event_loop()
    app.MainLoop()


if __name__ == '__main__':
    print "importing wx.adv"
    import wx.adv
    print "app:", wx.GetApp()

    import sys
    main(sys.argv)
