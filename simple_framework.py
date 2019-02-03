""" Simple menubar & tabbed window framework
"""
import collections
import time

import wx
import wx.aui as aui
# import wx.lib.agw.aui as aui
import numpy as np
import numpy.random as rand

class SimpleFrameworkError(RuntimeError):
    pass

class RecreateDynamicMenuBar(SimpleFrameworkError):
    pass

class EditorNotFound(SimpleFrameworkError):
    pass


global_action_ids = {
    "about": wx.ID_ABOUT,
    "quit": wx.ID_EXIT,
    "prefs": wx.ID_PREFERENCES,
}


def get_action_id(action_key):
    global global_action_ids

    try:
        id = global_action_ids[action_key]
    except KeyError:
        id = wx.NewId()
        global_action_ids[action_key] = id
    return id


class MenuDescription:
    def __init__(self, desc, editor, valid_id_map):
        self.menu = wx.Menu()
        print(f"adding menu {desc}")
        self.name = desc[0]
        for action_key in desc[1:]:
            if action_key is None:
                self.menu.AppendSeparator()
            elif str(action_key) == action_key:
                if action_key.startswith("-"):
                    self.menu.AppendSeparator()
                else:
                    # usable_actions limit the visible actions to what the current editor supports
                    try:
                        action = editor.calc_usable_action(action_key)
                    except:
                        print(f"action {action_key} not used in this editor")
                        pass
                    else:
                        # a single action can create multiple entries
                        try:
                            action_keys = action.calc_menu_sub_keys(editor)
                            print(f"action {action_key} created subkeys {action_keys}")
                        except AttributeError:
                            action_keys = [action_key]
                        for action_key in action_keys:
                            id = get_action_id(action_key)
                            valid_id_map[id] = (action_key, action)
                            action.append_to_menu(self.menu, id, action_key)
            else:
                submenu = MenuDescription(action_key, editor, valid_id_map)
                if submenu.count > 0:
                    self.menu.AppendSubMenu(submenu.menu, submenu.name)

    @property
    def count(self):
        return self.menu.GetMenuItemCount()


class MenubarDescription:
    def __init__(self, parent, editor):
        self.menus = []
        self.valid_id_map = collections.OrderedDict()
        num_old_menus = parent.raw_menubar.GetMenuCount()
        num_new_menus = 0
        for desc in editor.menubar_desc:
            menu = MenuDescription(desc, editor, self.valid_id_map)
            if menu.count > 0:
                if num_new_menus < num_old_menus:
                    parent.raw_menubar.Replace(num_new_menus, menu.menu, menu.name)
                else:
                    parent.raw_menubar.Append(menu.menu, menu.name)
                self.menus.append(menu)
                num_new_menus += 1
        while num_new_menus < num_old_menus:
            parent.raw_menubar.Remove(num_new_menus)
            num_old_menus -= 1

    def sync_with_editor(self, menubar_control):
        for id, (action_key, action) in self.valid_id_map.items():
#            print(f"syncing {id}: {action_key}, {action}")
            menu_item = menubar_control.FindItemById(id)
            action.sync_menu_item_from_editor(action_key, menu_item)


class ToolbarDescription:
    def __init__(self, parent, editor):
        tb = parent.raw_toolbar
        tb.ClearTools()
        self.valid_id_map = collections.OrderedDict()
        for action_key in editor.toolbar_desc:
            if action_key is None:
                tb.AddSeparator()
            else:
                if action_key.startswith("-"):
                    tb.AddSeparator()
                else:
                    # usable_actions limit the visible actions to what the current editor supports
                    try:
                        action = editor.calc_usable_action(action_key)
                    except:
                        print(f"action {action_key} not used in this editor")
                        pass
                    else:
                        # a single action can create multiple entries
                        try:
                            action_keys = action.calc_tool_sub_keys(editor)
                            print(f"action {action_key} created subkeys {action_keys}")
                        except AttributeError:
                            action_keys = [action_key]
                        for action_key in action_keys:
                            id = get_action_id(action_key)
                            self.valid_id_map[id] = (action_key, action)
                            action.append_to_toolbar(tb, id, action_key)

    def sync_with_editor(self, toolbar_control):
        for id, (action_key, action) in self.valid_id_map.items():
            print(f"syncing tool {id}: {action_key}, {action}")
            item = toolbar_control.FindById(id)
            action.sync_tool_item_from_editor(action_key, toolbar_control, id)


class SimpleFrame(wx.Frame):
    clipboard_check_interval = 1.0

    def __init__(self, editor):
        wx.Frame.__init__(self, None , -1, editor.title)

        self.raw_menubar = wx.MenuBar()
        self.SetMenuBar(self.raw_menubar)
        self.Bind(wx.EVT_MENU, self.on_menu)

        self.raw_toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)

        self.toolbar_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self.Bind(wx.EVT_ACTIVATE, self.on_activate)

        if wx.Platform == "__WXMAC__":
            self.Bind(wx.EVT_MENU_OPEN, self.on_menu_open_mac)
        elif wx.Platform == "__WXMSW__":
            self.Bind(wx.EVT_MENU_OPEN, self.on_menu_open_win)
        else:
            self.Bind(wx.EVT_MENU_OPEN, self.on_menu_open_linux)

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.notebook = aui.AuiNotebook(self, -1)
        sizer.Add(self.notebook, 1, wx.GROW)
        self.SetSizer(sizer)

        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.on_page_changed)
        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSED, self.on_page_closed)

        self.active_editor = None
        self.add_editor(editor)

    def create_menubar(self):
        print(f"create_menubar: active editor={self.active_editor}")
        self.menubar = MenubarDescription(self, self.active_editor)

    def sync_menubar(self):
        try:
            self.menubar.sync_with_editor(self.raw_menubar)
        except RecreateDynamicMenuBar:
            self.create_menubar()
            self.menubar.sync_with_editor(self.raw_menubar)

    def create_toolbar(self):
        print(f"create_toolbar: active editor={self.active_editor}")
        self.toolbar = ToolbarDescription(self, self.active_editor)

    def sync_toolbar(self):
        try:
            self.toolbar.sync_with_editor(self.raw_toolbar)
        except RecreateDynamicMenuBar:
            self.create_toolbar()
            self.toolbar.sync_with_editor(self.raw_toolbar)

    def add_editor(self, editor):
        editor.attached_to_frame = self
        control = editor.create_control(self.notebook)
        editor.control = control
        control.editor = editor
        self.notebook.AddPage(control, editor.tab_name)
        self.make_active(editor)

    def make_active(self, editor, force=False):
        last = self.active_editor
        self.active_editor = editor
        if force or last != editor or self.raw_menubar.GetMenuCount() == 0:
            self.create_menubar()
            self.sync_menubar()
            self.create_toolbar()
            self.sync_toolbar()
            index = self.find_index_from_control(editor.control)
            print(f"setting tab focus to {index}")
            self.notebook.SetSelection(index)
            editor.control.SetFocus()

    def find_tab_number_of_editor(self, editor):
        return self.notebook.FindPage(editor.control)

    def find_editor_from_control(self, control):
        for index in range(self.notebook.GetPageCount()):
            if control == self.notebook.GetPage(index):
                return control.editor
        raise EditorNotFound

    def find_index_from_control(self, control):
        for index in range(self.notebook.GetPageCount()):
            if control == self.notebook.GetPage(index):
                return index
        raise EditorNotFound

    def find_editor_from_index(self, index):
        control = self.notebook.GetPage(index)
        return self.find_editor_from_control(control)

    def on_menu_open_win(self, evt):
        # windows only works when updating the menu during the event call
        print(f"on_menu_open_win: syncing menubar. From {evt.GetMenu()}")
        self.sync_menubar()

    def on_menu_open_linux(self, evt):
        # workaround for linux which crashes updating the menu bar during an event
        print(f"on_menu_open: syncing menubar. From {evt.GetMenu()}")
        wx.CallAfter(self.sync_menubar)

    def on_menu_open_mac(self, evt):
        # workaround for Mac which sends the EVT_MENU_OPEN for lots of stuff unrelated to menus
        state = wx.GetMouseState()
        if state.LeftIsDown():
            print(f"on_menu_open_mac: syncing menubar. From {evt.GetMenu()}")
            wx.CallAfter(self.sync_menubar)
        else:
            print(f"on_menu_open_mac: skipping menubar sync because mouse isn't down. From {evt.GetMenu()}")

    def on_menu(self, evt):
        action_id = evt.GetId()
        print(f"on_menu: menu id: {action_id}")
        try:
            action_key, action = self.menubar.valid_id_map[action_id]
            try:
                action.execute()
            except AttributeError:
                print(f"no execute method for {action}")
        except:
            print(f"menu id: {action_id} not found!")
        else:
            print(f"found action {action}")

    def on_page_changed(self, evt):
        index = evt.GetSelection()
        editor = self.find_editor_from_index(index)
        print(f"on_page_changed: page id: {index}, {editor}")
        self.make_active(editor, True)
        evt.Skip()

    def on_page_closed(self, evt):
        index = evt.GetSelection()
        print(f"on_page_closed: page id: {index}")
        editor = self.find_editor_from_index(index)
        control = editor.control
        editor.prepare_destroy()
        self.notebook.RemovePage(index)
        del control
        evt.Skip()

    def on_timer(self, evt):
        evt.Skip()
        print("timer")
        wx.CallAfter(self.sync_toolbar)

    def on_activate(self, evt):
        if evt.GetActive():
            print("restarting toolbar timer")
            self.toolbar_timer.Start(self.clipboard_check_interval * 1000)
        else:
            print("halting toolbar timer")
            self.toolbar_timer.Stop()
        wx.CallAfter(self.sync_toolbar)

class ActionBase:
    def __init__(self, editor):
        self.editor = editor
        self.init_from_editor()

    def append_to_menu(self, menu, id, action_key):
        menu.Append(id, self.calc_name(action_key))

    def append_to_toolbar(self, tb, id, action_key):
        name = self.calc_name(action_key)
        tb.AddTool(id, name, self.calc_bitmap(action_key), wx.NullBitmap, wx.ITEM_NORMAL, name, f"Long help for '{name}'", None)

    def calc_bitmap(self, action_key):
        return wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, self.editor.tool_bitmap_size)

    def init_from_editor(self):
        pass

    def sync_menu_item_from_editor(self, action_key, menu_item):
        pass

    def sync_tool_item_from_editor(self, action_key, toolbar_control, id):
        pass

class ActionBaseRadioMixin:
    def append_to_menu(self, menu, id, action_key):
        menu.AppendRadioItem(id, self.calc_name(action_key))

    def append_to_toolbar(self, tb, id, action_key):
        name = self.calc_name(action_key)
        tb.AddTool(id, name, self.calc_bitmap(action_key), wx.NullBitmap, wx.ITEM_RADIO, name, f"Long help for '{name}'", None)

class new_file(ActionBase):
    def calc_name(self, action_key):
        return "&New"

    def execute(self):
        new_editor = Editor()
        wx.CallAfter(self.editor.attached_to_frame.add_editor, new_editor)

class open_file(ActionBase):
    def calc_name(self, action_key):
        return "&Open"

class save(ActionBase):
    def calc_name(self, action_key):
        return "&Save"

    def sync_menu_item_from_editor(self, action_key, menu_item):
        menu_item.Enable(not self.editor.control.IsEmpty())

class save_as(ActionBase):
    def calc_name(self, action_key):
        return "Save &As"

class application_quit(ActionBase):
    def calc_name(self, action_key):
        return "&Quit"

    def execute(self):
        self.editor.attached_to_frame.Destroy()

class copy(ActionBase):
    def calc_name(self, action_key):
        return "&Copy"

    def sync_menu_item_from_editor(self, action_key, menu_item):
        menu_item.Enable(self.editor.control.CanCopy())

    def sync_tool_item_from_editor(self, action_key, toolbar_control, id):
        state = self.editor.control.CanCopy()
        print(f"tool item {id}, {state}, {self.editor.tab_name}")
        toolbar_control.EnableTool(id, state)

class paste(ActionBase):
    def calc_name(self, action_key):
        return "&Paste"

    def sync_menu_item_from_editor(self, action_key, menu_item):
        menu_item.Enable(self.editor.control.CanPaste())

class paste_as_text(ActionBase):
    def calc_name(self, action_key):
        return "Paste As Text"

class prefs(ActionBase):
    def calc_name(self, action_key):
        return "&Preferences"

class about(ActionBase):
    def calc_name(self, action_key):
        return "&About"

class document_list(ActionBase):
    def calc_name(self, action_key):
        return action_key.replace("_", " ").title()

    def calc_menu_sub_keys(self, action_key):
        return ["document_list1", "document_list2", "document_list3"]

class text_counting(ActionBase):
    def init_from_editor(self):
        self.counts = list(range(5, 25, 5))

    def calc_name(self, action_key):
        return action_key.replace("_", " ").title()

    def calc_menu_sub_keys(self, action_key):
        self.count_map = {f"text_count_{c}":c for c in self.counts}
        return [f"text_count_{c}" for c in self.counts]

    def sync_menu_item_from_editor(self, action_key, menu_item):
        count = self.editor.control.GetLastPosition()
        menu_item.Enable(count >= self.count_map[action_key])

class text_last_digit(ActionBaseRadioMixin, ActionBase):
    def calc_name(self, action_key):
        return action_key.replace("_", " ").title()

    def calc_menu_sub_keys(self, action_key):
        self.count_map = {f"text_last_digit_{c}":c for c in range(10)}
        return [f"text_last_digit_{c}" for c in range(10)]

    def sync_menu_item_from_editor(self, action_key, menu_item):
        count = self.editor.control.GetLastPosition()
        divisor = self.count_map[action_key]
        menu_item.Check(count % 10 == divisor)

    calc_tool_sub_keys = calc_menu_sub_keys

    def sync_tool_item_from_editor(self, action_key, toolbar_control, id):
        count = self.editor.control.GetLastPosition()
        divisor = self.count_map[action_key]
        toolbar_control.ToggleTool(id, count % 10 == divisor)

class text_last_digit_dyn(ActionBase):
    def init_from_editor(self):
        self.count = (self.editor.control.GetLastPosition() % 10) + 1

    def calc_name(self, action_key):
        return action_key.replace("_", " ").title()

    def calc_menu_sub_keys(self, action_key):
        self.count_map = {f"text_last_digit_dyn{c}":c for c in range(self.count)}
        return [f"text_last_digit_dyn{c}" for c in range(self.count)]

    def sync_menu_item_from_editor(self, action_key, menu_item):
        count = (self.editor.control.GetLastPosition() % 10) + 1
        if count != self.count:
            raise RecreateDynamicMenuBar

class text_size(ActionBase):
    def init_from_editor(self):
        self.counts = list(range(5, 25, 5))

    def calc_name(self, action_key):
        size = self.editor.control.GetLastPosition()
        return f"Text Size: {size}"

    def sync_menu_item_from_editor(self, action_key, menu_item):
        name = self.calc_name(action_key)
        menu_item.SetItemLabel(name)


class Editor:
    menubar_desc = [
    ["File", ["New", "new_file"], "open_file", None, "save", "save_as", None, "quit"],
    ["Edit", "copy", "paste", "paste_rectangular", ["Paste Special", "paste_as_text", "paste_as_hex"], None, "prefs"],
    ["Text", "text_counting", None, "text_last_digit", None, "text_size"],
    ["Dynamic", "text_last_digit_dyn"],
    ["Document", "document_list"],
    ["Help", "about"],
    ]

    toolbar_desc = [
    "new_file", "open_file", "save", None, "copy", "paste", "paste_as_text", "paste_as_hex",
    ]

    usable_actions = {
         "new_file": new_file,
         "open_file": open_file,
         "save": save,
         "save_as": save_as,
         "quit": application_quit,
         "copy": copy,
         "paste": paste,
         "paste_as_text": paste_as_text,
         "prefs": prefs,
         "about": about,
         "document_list": document_list,
         "text_counting": text_counting,
         "text_last_digit": text_last_digit,
         "text_last_digit_dyn": text_last_digit_dyn,
         "text_size": text_size,
    }

    tool_bitmap_size = (24, 24)

    def __init__(self):
        self.title = "Sample Editor"
        self.tab_name = "Text"
        self.attached_to_frame = None

    def prepare_destroy(self):
        print(f"prepare_destroy: {self.tab_name}")
        self.control = None
        self.attached_to_frame = None

    def create_control(self, parent):
        return wx.TextCtrl(parent, -1, style=wx.TE_MULTILINE)

    def calc_usable_action(self, action_key):
        action_factory = self.usable_actions[action_key]
        return action_factory(self)


class DemoFrame(SimpleFrame):
    """ This window displays a button """
    def __init__(self, editor):
        SimpleFrame.__init__(self, editor)


if __name__ == "__main__":
    app = wx.App(False)
    editor = Editor()
    editor2 = Editor()
    editor2.usable_actions = {
         "new_file": new_file,
         "open_file": open_file,
         "save": save,
         "save_as": save_as,
         "quit": application_quit,
         "copy": copy,
         "paste": paste,
         "prefs": prefs,
         "about": about,
         "text_counting": text_counting,
         "text_last_digit": text_last_digit,
         "text_last_digit_dyn": text_last_digit_dyn,
         "text_size": text_size,
    }
    editor2.toolbar_desc = [
    "new_file", "open_file", "save", None, "text_last_digit",
    ]
    editor2.tab_name = "Editor 2"
    editor3 = Editor()
    editor3.tab_name = "Editor 3"
    editor4 = Editor()
    editor4.tab_name = "Editor 4"
    editor5 = Editor()
    editor5.tab_name = "Editor 5"
    frame = DemoFrame(editor)
    frame.add_editor(editor2)
    frame.add_editor(editor3)
    frame.add_editor(editor4)
    frame.add_editor(editor5)
    frame.Show()
    app.MainLoop()
