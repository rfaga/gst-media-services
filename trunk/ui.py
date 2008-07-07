#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import gtk, gtk.glade, gobject

GLADE_PATH = "convert_anything.glade"

#TAGS
PIPELINE_ONLY = 1
INPUT_OFF = 2
TARGET_OFF = 3

widgets = gtk.glade.XML(GLADE_PATH)

class FileChooserDialog:
    def __init__(self, parent):
        self.parent = parent
        self.widget = widgets.get_widget("widget_fc")
        self.dialog = widgets.get_widget("dialog_filechooser")
        self.check = widgets.get_widget("checkbutton_fc")
        widgets.signal_autoconnect(self)

    def show(self):
        self.dialog.show()

    def hide(self):
        self.dialog.hide()

    def on_button_fc_add_clicked(self, widget):
        self.parent.add_files(self.widget.get_uris())
        self.widget.unselect_all()
        if self.check.get_active():
            self.hide()

    def on_button_fc_cancel_clicked(self, widget):
        self.hide()

class InputObject():
    """
    A file / input stream
    """

    def __init__(self, uri):
        """
        Constructor.
        
        uri -- URI path, based in GnomeVFS
        """
        self.uri = uri
    
    def __str__(self):
        return "<b>%s</b>"%self.uri

class FileList(object):
    """
    Manipulates gtk.TreeView from glade file to manage files
    """

    def __init__(self, parent):
        """
        Constructor.
        
        parent -- parent dialog
        """
        self.parent = parent
        self.widget = widgets.get_widget("filelist")
        self.widget.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.model = gtk.ListStore(gobject.TYPE_STRING)
        self.widget.set_model(self.model)
        column = gtk.TreeViewColumn("File name", gtk.CellRendererText(), text=0)
        self.widget.append_column(column)


    def add_files(self, files):
        """
        Add files to the FileList
        ---
        files -- input files, in GnomeVFS format (URI)
        """
        self.files = files
        for f in files:
            self.model.append([InputObject(f)])

    def remove_files(self):
        """
        remove files in the FileList
        """
        rows = self.widget.get_selection().get_selected_rows()[1]
        rows.reverse()
        for row in rows:
            self.model.remove(self.model.get_iter(row))


class MainDialog:
    def __init__(self, *category):
        """
        
        category -- What category(ies) is(are) this(ese) conversion. Values can be:
            PIPELINE_ONLY -- constructs only the pipeline and give it back to
                the application which called GSTMS
            INPUT_OFF -- disable possibility to user add or remove files. If
                you choose it, don't forget to add files manually.
            TARGET_OFF -- disable possibility to user choose where to save the
                transcoded files/streams. If you don't specify manually a path,
                the original path will be assumed as the target folder.
            No values -- a default dialog app will appear.

        """
        self.category = category

        self.dialog = widgets.get_widget("dialog_gstms")
        self.filechooserdialog = FileChooserDialog(self)
        self.filelist = FileList(self)

        self.area_input = widgets.get_widget("table_input")
        self.area_video = widgets.get_widget("hbox_video")
        self.area_audio = widgets.get_widget("hbox_audio")
        self.area_subtitle = widgets.get_widget("hbox_subtitle")
        self.area_target = widgets.get_widget("hbox_target")

        self.button_transcode = widgets.get_widget("button_transcode")
        self.button_ok = widgets.get_widget("button_ok")
        
        self.dialog_preferences = widgets.get_widget("dialog_preferences")
       
        if PIPELINE_ONLY in self.category:
            self.button_ok.show()
            self.button_transcode.hide()

        if INPUT_OFF in self.category:
            self.area_input.hide()

        if TARGET_OFF in self.category:
            self.area_target.hide()
        
        widgets.signal_autoconnect(self)
        self.dialog.show()

    ### Catching signals ###

    def close_maindialog(self, widget):
        """
        Closes the dialog and the convertion service
        """
        gtk.main_quit()

    def on_button_add_clicked(self, widget):
        self.filechooserdialog.show()

    def on_button_remove_clicked(self, widget):
        self.filelist.remove_files()

    ### Operations ###

    def add_files(self, files):
        """
        files -- A python list of files, in URI format. This URI uses GnomeVFS.
        """
        self.filelist.add_files(files)

main = MainDialog(PIPELINE_ONLY)
gtk.main()
