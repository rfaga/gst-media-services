#!/usr/bin/env python

from parser_plugins import *


###############################################################################

# UI for testing only

############
COLUMNS = 5
import gtk
def build_table(sort=None):
	global table
	table = gtk.Table(len(pads)+1,COLUMNS)
	pads.sort(sort)
	i=0
	j=0
	pluginbutton = gtk.Button("Plugin")
	pluginbutton.connect('clicked', plugin_event)
	elementbutton = gtk.Button("Element")
	elementbutton.connect('clicked', element_event)
	padbutton = gtk.Button("Pad")
	padbutton.connect('clicked', pad_event)
	mimetypebutton = gtk.Button("Mimetype")
	mimetypebutton.connect('clicked', mimetype_event)
	klassbutton = gtk.Button("Klass")
	klassbutton.connect('clicked', klass_event)
	for button in [pluginbutton, elementbutton, padbutton, mimetypebutton, klassbutton]:
		button.show()
		table.attach(button, j, j+1, 0, 1)
		j += 1
	i+=1

	for pad in pads:
		j = 0
		for text in [pad.plugin.get_name(), pad.feature.get_name(), pad.template.name_template, pad.mimetype, pad.klasses]:
			label = gtk.Label(text)
			#label.set_selectable(True)
			label.set_line_wrap(True)
			label.set_width_chars(50)
			label.show()
			table.attach(label, j, j+1, i, i+1)
			j += 1
		i += 1
	table.show()



def rebuild(sort):
	global table, scroll, window
	window.remove(scroll)
	table.destroy()
	scroll.destroy()
	scroll = gtk.ScrolledWindow()
	build_table(sort)
	scroll.add_with_viewport(table)
	scroll.show()
	window.add(scroll)	

def plugin_event(trash):
	rebuild(plugin_sort)
def plugin_sort(x, y):
	if   x.plugin.get_name() >  y.plugin.get_name(): return 1
	elif x.plugin.get_name() == y.plugin.get_name(): return 0
	elif x.plugin.get_name() <  y.plugin.get_name(): return -1

def element_event(trash):
	rebuild(element_sort)
def element_sort(x, y):
	if   x.feature.get_name() >  y.feature.get_name(): return 1
	elif x.feature.get_name() == y.feature.get_name(): return 0
	elif x.feature.get_name() <  y.feature.get_name(): return -1

def pad_event(trash):
	rebuild(pad_sort)
def pad_sort(x, y):
	if   x.template.name_template >  y.template.name_template: return 1
	elif x.template.name_template == y.template.name_template: return 0
	elif x.template.name_template <  y.template.name_template: return -1

def mimetype_event(trash):
	rebuild(mimetype_sort)
def mimetype_sort(x, y):
	if   x.mimetype >  y.mimetype: return 1
	elif x.mimetype == y.mimetype: return 0
	elif x.mimetype <  y.mimetype: return -1

def klass_event(trash):
	rebuild(klass_sort)
def klass_sort(x, y):
	if   x.klasses >  y.klasses: return 1
	elif x.klasses == y.klasses: return 0
	elif x.klasses <  y.klasses: return -1

scroll = gtk.ScrolledWindow()
build_table()

scroll.add_with_viewport(table)
scroll.show()
window = gtk.Window()
window.show()
window.add(scroll)
window.connect('destroy', gtk.main_quit)
window.maximize()
gtk.main()
