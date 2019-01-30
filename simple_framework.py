""" Simple menubar & tabbed window framework
"""
import collections

import wx
import numpy as np
import numpy.random as rand

class RecreateDynamicMenuBar(RuntimeError):
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
                            action_keys = action.calc_sub_keys(editor)
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
            menu_item = menubar_control.FindItemById(id)
            action.sync_from_editor(action_key, menu_item)


class SimpleFrame(wx.Frame):
    def __init__(self, editor):
        wx.Frame.__init__(self, None , -1, editor.title)
        self.editors = []
        self.raw_menubar = wx.MenuBar()
        self.SetMenuBar(self.raw_menubar)
        self.Bind(wx.EVT_MENU, self.on_menu)
        self.Bind(wx.EVT_MENU_OPEN, self.on_menu_open)

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.notebook = wx.Notebook(self, -1)
        sizer.Add(self.notebook, 1, wx.GROW)
        self.SetSizer(sizer)

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_changed)

        self.add_editor(editor)

    def create_menubar(self):
        self.menubar = MenubarDescription(self, self.active_editor)

    def sync_menubar(self):
        try:
            self.menubar.sync_with_editor(self.raw_menubar)
        except RecreateDynamicMenuBar:
            self.create_menubar()
            self.menubar.sync_with_editor(self.raw_menubar)

    def add_editor(self, editor):
        self.editors.append(editor)
        editor.attached_to_frame = self
        control = editor.create_control(self.notebook)
        editor.control = control
        self.notebook.AddPage(control, editor.tab_name)
        self.make_active(editor)

    def make_active(self, editor, force=False):
        self.active_editor = editor
        i = self.find_tab_number_of_editor(editor)
        if force or i != self.notebook.GetSelection() or self.raw_menubar.GetMenuCount() == 0:
            self.create_menubar()
            self.sync_menubar()
            self.notebook.ChangeSelection(i)

    def find_tab_number_of_editor(self, editor):
        return self.notebook.FindPage(editor.control)

    def on_menu_open(self, evt):
        print(f"syncing menubar")
        wx.CallAfter(self.sync_menubar)

    def on_menu(self, evt):
        action_id = evt.GetId()
        print(f"menu id: {action_id}")
        try:
            action = self.menubar.valid_id_map[action_id]
            try:
                action.execute(self.active_editor)
            except AttributeError:
                print(f"no execute method for {action}")
        except:
            print(f"menu id: {action_id} not found!")
        else:
            print(f"found action {action}")

    def on_page_changed(self, evt):
        print(f"page changed id: {evt.GetSelection()}")
        editor = self.editors[evt.GetSelection()]
        self.make_active(editor, True)


class ActionBase:
    def __init__(self, editor):
        self.editor = editor
        self.init_from_editor()

    def append_to_menu(self, menu, id, action_key):
        menu.Append(id, self.calc_name(action_key))

    def init_from_editor(self):
        pass

    def sync_from_editor(self, action_key, menu_item):
        pass

class ActionBaseRadioMixin:
    def append_to_menu(self, menu, id, action_key):
        menu.AppendRadioItem(id, self.calc_name(action_key))

class new_file(ActionBase):
    def calc_name(self, action_key):
        return "&New"

class open_file(ActionBase):
    def calc_name(self, action_key):
        return "&Open"

class save(ActionBase):
    def calc_name(self, action_key):
        return "&Save"

    def sync_from_editor(self, action_key, menu_item):
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

    def sync_from_editor(self, action_key, menu_item):
        menu_item.Enable(self.editor.control.CanCopy())

class paste(ActionBase):
    def calc_name(self, action_key):
        return "&Paste"

    def sync_from_editor(self, action_key, menu_item):
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

    def calc_sub_keys(self, action_key):
        return ["document_list1", "document_list2", "document_list3"]

class text_counting(ActionBase):
    def init_from_editor(self):
        self.counts = list(range(5, 25, 5))

    def calc_name(self, action_key):
        return action_key.replace("_", " ").title()

    def calc_sub_keys(self, action_key):
        self.count_map = {f"text_count_{c}":c for c in self.counts}
        return [f"text_count_{c}" for c in self.counts]

    def sync_from_editor(self, action_key, menu_item):
        count = self.editor.control.GetLastPosition()
        menu_item.Enable(count >= self.count_map[action_key])

class text_last_digit(ActionBaseRadioMixin, ActionBase):
    def calc_name(self, action_key):
        return action_key.replace("_", " ").title()

    def calc_sub_keys(self, action_key):
        self.count_map = {f"text_last_digit_{c}":c for c in range(10)}
        return [f"text_last_digit_{c}" for c in range(10)]

    def sync_from_editor(self, action_key, menu_item):
        count = self.editor.control.GetLastPosition()
        divisor = self.count_map[action_key]
        menu_item.Check(count % 10 == divisor)

class text_last_digit_dyn(ActionBase):
    def init_from_editor(self):
        self.count = (self.editor.control.GetLastPosition() % 10) + 1

    def calc_name(self, action_key):
        return action_key.replace("_", " ").title()

    def calc_sub_keys(self, action_key):
        self.count_map = {f"text_last_digit_dyn{c}":c for c in range(self.count)}
        return [f"text_last_digit_dyn{c}" for c in range(self.count)]

    def sync_from_editor(self, action_key, menu_item):
        count = (self.editor.control.GetLastPosition() % 10) + 1
        if count != self.count:
            raise RecreateDynamicMenuBar
        divisor = self.count_map[action_key]
        menu_item.Check(count % 10 == divisor)

class text_size(ActionBase):
    def init_from_editor(self):
        self.counts = list(range(5, 25, 5))

    def calc_name(self, action_key):
        size = self.editor.control.GetLastPosition()
        return f"Text Size: {size}"

    def sync_from_editor(self, action_key, menu_item):
        name = self.calc_name(action_key)
        menu_item.SetItemLabel(name)


class Editor:
    menubar_desc = [
    ["File", "new_file", "open_file", None, "save", "save_as", None, "quit"],
    ["Edit", "copy", "paste", "paste_rectangular", ["Paste Special", "paste_as_text", "paste_as_hex"], None, "prefs"],
    ["Text", "text_counting", None, "text_last_digit", None, "text_size"],
    ["Dynamic", "text_last_digit_dyn"],
    ["Document", "document_list"],
    ["Help", "about"],
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

    def __init__(self):
        self.title = "Sample Editor"
        self.tab_name = "Text"
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
    editor2.tab_name = "Empty"
    frame = DemoFrame(editor)
    frame.add_editor(editor2)
    frame.Show()
    app.MainLoop()
