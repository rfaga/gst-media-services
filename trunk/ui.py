#!/usr/bin/env python

# this file is a glade test for now, just to get a screenshot


import gtk, gtk.glade, gobject

glade_file = gtk.glade.XML("convert_anything.glade")

dialog = glade_file.get_widget("dialog_gstms")

tree = glade_file.get_widget("filelist")

treelist = gtk.ListStore(gobject.TYPE_STRING)

treelist.append(["Test1"])
tree.set_model(treelist)

dialog.show()

gtk.main()
