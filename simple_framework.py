#!/usr/bin/env python2.5

"""
a small test of initializing a wxImage from a numpy array
"""


import wx
import numpy as np
import numpy.random as rand

class ImagePanel(wx.Panel):
    """ 
    A very simple panel for displaying a wx.Image
    """
    def __init__(self, image, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        
        self.image = image
        self.Bind(wx.EVT_PAINT, self.OnPaint)
    
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(wx.BitmapFromImage(self.image), 0, 0)


global_action_ids = {
    "about": wx.ID_ABOUT,
    "quit": wx.ID_EXIT,
    "prefs": wx.ID_PREFERENCES,
}


def get_action_id(item):
    global global_action_ids

    try:
        id = global_action_ids[item]
    except KeyError:
        id = wx.NewId()
        global_action_ids[item] = id
    return id


class MenuDescription:
    def __init__(self, desc, usable_actions, valid_id_map):
        self.menu = wx.Menu()
        print(f"adding menu {desc}")
        self.name = desc[0]
        for item in desc[1:]:
            if item is None:
                self.menu.AppendSeparator()
            elif str(item) == item:
                if item.startswith("-"):
                    self.menu.AppendSeparator()
                else:
                    try:
                        action = usable_actions[item]
                    except:
                        pass
                    else:
                        id = get_action_id(item)
                        valid_id_map[id] = action
                        self.menu.Append(id, action.calc_name())
            else:
                submenu = MenuDescription(item, usable_actions, valid_id_map)
                self.menu.AppendSubMenu(submenu.menu, submenu.name)


class MenubarDescription:
    def __init__(self, parent, editor):
        self.menus = []
        self.valid_id_map = {}
        for desc in editor.menubar_desc:
            menu = MenuDescription(desc, editor.usable_actions, self.valid_id_map)
            parent.raw_menubar.Append(menu.menu, menu.name)
            self.menus.append(menu)


class SimpleFrame(wx.Frame):
    def __init__(self, editor):
        wx.Frame.__init__(self, None , -1, editor.title)
        self.editors = [editor]
        self.active_editor = editor
        self.raw_menubar = wx.MenuBar()
        self.create_menubar()
        self.SetMenuBar(self.raw_menubar)
        self.Bind(wx.EVT_MENU, self.on_menu)

    def create_menubar(self):
        self.menubar = MenubarDescription(self, self.active_editor)

    def on_menu(self, evt):
        action_id = evt.GetId()
        print(f"menu id: {action_id}")
        try:
            action = self.menubar.valid_id_map[action_id]
        except:
            print(f"menu id: {action_id} not found!")
        else:
            print(f"found action {action}")



class new_file:
    @classmethod
    def calc_name(cls):
        return "&New"


class open_file:
    @classmethod
    def calc_name(cls):
        return "&Open"


class application_quit:
    @classmethod
    def calc_name(cls):
        return "&Quit"


class copy:
    @classmethod
    def calc_name(cls):
        return "&Copy"


class paste:
    @classmethod
    def calc_name(cls):
        return "&Paste"


class paste_as_text:
    @classmethod
    def calc_name(cls):
        return "Paste As Text"


class prefs:
    @classmethod
    def calc_name(cls):
        return "&Preferences"


class about:
    @classmethod
    def calc_name(cls):
        return "&About"


class Editor:
    menubar_desc = [
    ["File", "new_file", "open_file", None, "quit"],
    ["Edit", "copy", "paste", "paste_rectangular", ["Paste Special", "paste_as_text", "paste_as_hex"], None, "prefs"],
    ["Help", "about"],
    ]

    usable_actions = {
         "new_file": new_file,
         "open_file": open_file,
         "quit": application_quit,
         "copy": copy,
         "paste": paste,
         "paste_as_text": paste_as_text,
         "prefs": prefs,
         "about": about,
    }

    def __init__(self):
        self.title = "Sample Editor"


class DemoFrame(SimpleFrame):
    """ This window displays a button """
    def __init__(self, editor):
        SimpleFrame.__init__(self, editor)

        btn = wx.Button(self, label = "NewImage")
        btn.Bind(wx.EVT_BUTTON, self.OnNewImage )

        self.Bind(wx.EVT_CLOSE, self.OnQuit)

        ##Create numpy array, and image from it
        w = h = 200
        self.array = rand.randint(0, 255, (h, w, 3)).astype('uint8')
        self.array = np.zeros((h, w, 3), dtype='uint8')
        self.array[:,:,0] = 128
        print(self.array.shape)
        image = wx.ImageFromBuffer(w, h, self.array)
        #image = wx.Image("Images/cute_close_up.jpg")
        self.Panel = ImagePanel(image, self)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(btn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        sizer.Add(self.Panel, 1, wx.GROW)
        
        self.SetSizer(sizer)

    def OnNewImage(self, event=None):
        """
        create a new image by changing underlying numpy array
        """
        self.array += 5
        self.Panel.Refresh()
        
        
    def OnQuit(self,Event):
        self.Destroy()
        
    def OnAbout(self, event):
        dlg = wx.MessageDialog(self, "This is a small program to test\n"
                                     "the use of menus on Mac, etc.\n",
                                "About Me", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnHelp(self, event):
        dlg = wx.MessageDialog(self, "This would be help\n"
                                     "If there was any\n",
                                "Test Help", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnOpen(self, event):
        dlg = wx.MessageDialog(self, "This would be an open Dialog\n"
                                     "If there was anything to open\n",
                                "Open File", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnPrefs(self, event):
        dlg = wx.MessageDialog(self, "This would be an preferences Dialog\n"
                                     "If there were any preferences to set.\n",
                                "Preferences", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

if __name__ == "__main__":
    app = wx.App(False)
    editor = Editor()
    frame = DemoFrame(editor)
    frame.Show()
    app.MainLoop()
