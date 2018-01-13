
import wx.html

import pyreinitializemodules_sub as sub

class EnthoughtWxApp(wx.App):
    mac_menubar_app_name = "Omnivore"

    def OnInit(self):
        # Set application name before anything else
        self.SetAppName(self.mac_menubar_app_name)
        return True

if __name__ == '__main__':
    import wx
    app = EnthoughtWxApp()
    import wx.adv
    #app = wx.App()
    import wx.html
    frame = wx.Frame(None, -1, "Test", size=(400,400))
    html = wx.html.HtmlWindow(frame, -1)
    frame.Show(True)
    #info = wx.adv.AboutDialogInfo()
    sub.test()
    app.MainLoop()
