#!/usr/bin/env python

import wx

import os
import sys


import wx.lib.agw.cubecolourdialog as CCD

class AlwaysAlphaCCD(CCD.CubeColourDialog):
    def DoLayout(self):
        CCD.CubeColourDialog.DoLayout(self)
        self.mainSizer.Hide(self.showAlpha)
       

#----------------------------------------------------------------------
if __name__ == "__main__":
    app = wx.App(False)
    colourData = wx.ColourData()
    colourData.SetColour(wx.Colour(12,34,56,78))
    dlg = wx.ColourDialog(None, colourData)
#    dlg = AlwaysAlphaCCD(None, colourData)
    if dlg.ShowModal() == wx.ID_OK:
        # If the user selected OK, then the dialog's wx.ColourData will
        # contain valid information. Fetch the data ...
        new_colourData = dlg.GetColourData()

        # ... then do something with it. The actual colour data will be
        # returned as a three-tuple (r, g, b) in this particular case.
        colour = new_colourData.GetColour()
        print('You selected: %s: %d, %s: %d, %s: %d, %s: %d\n' % ("Red", colour.Red(),
                                                                               "Green", colour.Green(),
                                                                               "Blue", colour.Blue(),
                                                                               "Alpha", colour.Alpha()))
    dlg.Destroy()
    app.MainLoop()
