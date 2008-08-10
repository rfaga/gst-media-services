# -*- coding: UTF-8 -*-
#
###############################################################################
# This file is part of gst-media-services.                                    #
# Copyright (C) 2008 Roberto Faga Jr, Stefan Kost and Gstreamer team.         #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, version 3.                                    #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  See LICENSE file.                                 #
###############################################################################

import gobject; gobject.threads_init()

import gst, os, sys
from gst.extend.discoverer import Discoverer
import time
import xml.dom.minidom as xmldom

#media types
VIDEO_TYPE = 1
AUDIO_TYPE = 2
DATA_TYPE = 3

#messages about conversion
CONVERSION_FINISHED = 31
CONVERSION_FAILED = 32
CONVERSION_RUNNING = 33

EMPTY = gst.caps_from_string('EMPTY')
ANY = 'ANY'

FILE_SOURCE = "filesrc"
FILE_SINK = "filesink"
DECODEBIN = "decodebin"

################################# Misc #######################################

class File(object):
    """
    A Media object, a file object with its properties
    """

    def __init__(self, path):
        """
        Constructor.
        
        path -- file path
        """
        self.path = path
        self.decoder = Discoverer(path)
        self.decoder.connect("discovered", self.on_discover)
        self.decoder.discover()
        self.mimetype = None
    
    def on_discover(self, discover, success):
        try:
            self.set_mimetype(discover.mimetype.split(",")[0])
        except:
            #if ocurred an error, file is data file, unrecognized by discoverer
            pass
        if discover.is_video:
            self.mediatype = VIDEO_TYPE
        elif discover.is_audio:
            self.mediatype = AUDIO_TYPE
        else:
            self.mediatype = DATA_TYPE
        #print discover.is_video, discover.is_audio, success

    def set_mimetype(self, mimetype):
        """
        
        mimetype -- Mimetype string of this file
        """
        self.mimetype = mimetype
        #print mimetype


def error(message):
    print "error: %s"%message

################################ Registry ####################################

class ElementFactory:
    """
    GSTMS Element Factory model, to use in a database of possible elements.
    these possible elements can be used in pipeline.
    """

    def __init__(self, element_factory):
        self.element_factory = element_factory
        pads = element_factory.get_static_pad_templates()
        self.name = element_factory.get_name()
        self.sinks = EMPTY.copy()
        self.sources = EMPTY.copy()
        self.klass = element_factory.get_klass().lower()
        if not pads:
            return None

        #now, for each pad template, classify as SINK or SOURCE
        for pad in pads:
            if pad.direction == gst.PAD_SINK:
                self.sinks = self.sinks.union(pad.get_caps())
            elif pad.direction == gst.PAD_SRC:
                self.sources = self.sources.union(pad.get_caps())
            #if, for any unknown reason, it is another type of direction, ignore it.

    def check(self, sink_caps, source_caps, klasses):
        """
        checks if this ElementFactory can generate a gst element for desired
        pipeline

        sink_caps -- sink caps which element must have, at least
        source_caps -- source caps which elements must have, at least
        klasses -- a list of klasses which this element must have. empty lists
            to accept any element.

        returns True or False, if this EF can be used or not.
        """
        sink_condition, source_condition = False, False

        #XXX: I'm not sure about this, but I can't see why uniting sinks with
        # themselves can not work, as different sinks normally are different.

        #check gst klasses, if False I can discard this element right now
        for klass in klasses:
            if klass not in self.klass:
                return False

        if source_caps == EMPTY:
            source_condition = True
        elif self.sources.intersect(source_caps) != EMPTY:
            source_condition = True

        if sink_caps == EMPTY:
            sink_condition = True
        elif self.sinks.intersect(sink_caps) != EMPTY:
            sink_condition = True

        return sink_condition and source_condition

registry = None

def load_registry():
    """
    Init registry list. 
    """
    #XXX: Is reading all registry at start too much to process? Also, isn't so much to load on memory?
    global registry, elements_factory
    
    #init elements_factory available for use
    elements_factory = []

    #read registry only once
    registry = gst.registry_get_default()
    #read plugins from registry
    plugins = registry.get_plugin_list()
    
    #build pad_template list
    for plugin in plugins:
        features = registry.get_feature_list_by_plugin(plugin.get_name())
        for feature in features:
            try:
                element_factory = ElementFactory(feature)
                if element_factory:
                    elements_factory += [element_factory]
            except:
                pass

load_registry()


def get_possible_elements(sink_caps, source_caps, favorites, klasses, elements_list=elements_factory):
    """
    get all possible elements, considering the caps and trying 
    first the favorites

    sink_caps -- sink caps
    source_caps -- source caps
    favorites -- what are the favorites elements
    klasses -- gst klasses which elements must be
    elements_list -- list of possible elements to test

    returns a list of possible elements, considering the order as the best
    option in first place and worst in last.
    """
    possible_list = []
    favorites.sort(None,None,True) #reverse sort
    for ef in elements_list:
        if ef.check(sink_caps, source_caps, klasses):
            possible_list += [ef]
    for pe in possible_list:
        if pe.name in favorites:
            possible_list.remove(pe)
            possible_list.insert(0, pe)
    return possible_list
    #TODO: correctly construction of possible_elements
    #return favorites

########################### XML Profile Parser ###############################
class Profile:
    """
    A profile class, with helpful properties and methods.
    This profile means variables and pipeline to a Gstreamer conversion.
    """

    id = None
    name = None
    output_file_extension = None
    elements_needed = []
    mimetypes = []
    pipeline_process = None
    variables = []
    type = DATA_TYPE

    def __init__(self, xmlnode):
        """
        Constructor.
        
        xmlnode -- the node in dom format, from xml.dom library.
        """
        if xmlnode.nodeName == "audio-profile":
            self.type = AUDIO_TYPE
        elif xmlnode.nodeName == "video-profile":
            self.type = VIDEO_TYPE

        self.id = xmlnode.getAttribute("id")
        self.name = xmlnode.getElementsByTagName("name")[0].firstChild.nodeValue
        self.description = xmlnode.getElementsByTagName("description")[0].firstChild.nodeValue
        self.output_file_extension = xmlnode.getElementsByTagName("output-file-extension")[0].firstChild.nodeValue

        self.elements = []
        elementsxml= xmlnode.getElementsByTagName("element")
        for e in elementsxml:
            element = self.probe_element(e)
            if not element:
               error("no element found for '%s'"%e.getAttribute("id"))
            else:
                element.name = e.getAttribute("id")
                self.elements += [element]

        #TODO: check conditions to link or not
        self.links = []
        linksxml= xmlnode.getElementsByTagName("link")
        for link in linksxml:
            self.links += [ ( link.getAttribute("origin") , link.getAttribute("destiny") ) ]

    def probe_element(self, elementxml):
        """
        elementxml -- element to be probed, in XML format

        return element in gstms.Element format
        """
        source_caps = gst.caps_from_string(elementxml.getElementsByTagName("source")[0].firstChild.nodeValue)
        sink_caps = gst.caps_from_string(elementxml.getElementsByTagName("sink")[0].firstChild.nodeValue)

        #let's read recommended-elements, this can help our element finder
        recommendedsxml = elementxml.getElementsByTagName("recommended-element")
        favorites = []
        for r in recommendedsxml:
            favorites += [r.firstChild.nodeValue]
 
        klasses = []
        klassesxml = elementxml.getElementsByTagName("klass")
        for klass in klassesxml:
            klasses += [klass.firstChild.nodeValue.lower()]

        #now we get the possible element in gstms.Element format.
        # oh, and this element can be None if no element was found
        elements = get_possible_elements(sink_caps, source_caps, favorites, klasses)
        if not elements:
            return None
        
        element = elements[0] #XXX: for now, the first of list is the chosen one
        element.type = elementxml.getAttribute("type")
        
        #TODO: parse properties options from elementxml
        return element
    
    def __str__(self):
        return self.name

    def transcode(self, file_path, updater=None):
        transcode = Transcode(self.id, self.elements, self.links, updater)
        #TODO: correct destiny
        transcode.convert_file(file_path, \
                file_path[:file_path.rfind(".")]+"."+self.output_file_extension)

    #XXX: In the future, do a write method to write a profile into a file, so editing will be easier.


def get_profiles():
    """
    Get all possible profiles from XML databases.

    return: a tuple with audio profiles and video profiles lists.
    """
    #TODO: I need to read XMLs from the /usr/share folder (or some other system folder) and from a home folder (like ~/.gstms in UNIX-like)
    HOME_PATH = os.path.expanduser("~/.gstms")
    SYSTEM_PATH = "profiles/" #local path, same of source file, for now...

    profiles_path = os.listdir(SYSTEM_PATH)
    profiles_audio, profiles_video = [], []
    for path in profiles_path:
        fullpath = os.path.join(os.path.abspath(SYSTEM_PATH), path)
        try:
            doc = xmldom.parse(fullpath)
        except:
            error("file %s is not a valid XML file"%fullpath)
            continue

        #try:
        possible_profiles = doc.firstChild.childNodes
        for profile in possible_profiles:
                #if node is a child
            if profile.nodeType == 1:
                p = Profile(profile)
                if p.type == VIDEO_TYPE:
                    profiles_video += [p]
                elif p.type == AUDIO_TYPE:
                    profiles_audio += [p]
        #except:
        #    error("xml file at '%s' is not in EncodingProfiles format. \n\
        #            Python error: '%s'"%(fullpath, str(sys.exc_info()[0])))
    return profiles_audio, profiles_video

##################### Pipeline model #######################
class Pipeline:
    """
    Pipeline class, to simplify other pipeline uses
    """

    def __init__(self, name):
        """
        Constructor, don't forget to construct the pipeline before using it
        """
        self.pipeline = gst.Pipeline(name)
        #self.stop()
        

    def on_message(self, bus, message):
        """
        Message from bus!
        """
        t = message.type
        #print "Incoming message! - '%s'"%t
        # If process ended
        if t == gst.MESSAGE_EOS:
            #print message.parse_eos()
            self.finish()
        elif t == gst.MESSAGE_STATE_CHANGED:
            #print "CHANGED: ",message.parse_state_changed()
            pass
        
        elif t == gst.MESSAGE_ERROR:
            #TODO: send error message to a right place
            print message.parse_error()

        elif t == gst.MESSAGE_NEW_CLOCK:
            print message.parse_new_clock()

        elif t == gst.MESSAGE_TAG:
            self.found_tag(message.parse_tag()) 

    def found_tag(self, message):
        pass#print message.keys()

    def play(self):
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        self.watch_id = bus.connect("message", self.on_message)
        
        self.pipeline.set_state(gst.STATE_PLAYING)

    def stop(self):
        try:
            bus = self.pipeline.get_bus()
            bus.disconnect(self.watch_id)
            bus.remove_signal_watch()
            del self.watch_id
        except:
            pass #do nothing
        self.pipeline.set_state(gst.STATE_NULL)

    def finish(self):
        #implement it!
        pass

# I don't like the idea of probing raw converters, as I can get some filter
# element which changes something of original stream
RAW_CONVERTERS = [
        ElementFactory(gst.element_factory_find("ffmpegcolorspace")),
        ElementFactory(gst.element_factory_find("audioconvert"))]

class Transcode(Pipeline):

    def __init__(self, name, elements_list, links, updater=None):
        """
        Generates a transcode object, capable to transcode a media file 
        according to elements and link given

        name -- a string name to the object, must be unique
        elements_list -- list of gstms.ElementFactory to be used to convert
        links - tuple of pairs, containing source and sink of connections
        """
        Pipeline.__init__(self, name)
        self.filesource = gst.element_factory_make(FILE_SOURCE, "filesource")
        self.decode = gst.element_factory_make(DECODEBIN, "decodebin")
        self.decode.connect("new-decoded-pad", self.new_decoded_pad)
        self.pipeline.add(self.filesource, self.decode)
        self.filesource.link(self.decode)

        self.filesink = gst.element_factory_make(FILE_SINK, "filesink")
        elements = {}
        elements.update( {"end": self.filesink})
        for e in elements_list:
            elements.update( {e.name: e.element_factory.create()} )
        self.pipeline.add(*elements.values())

        self.starts = []
        for (source, destiny) in links:
            if source == "start":
                pad = elements[destiny].get_static_pad("sink")
                self.starts += [(elements[destiny], pad)]
            else:
                try:
                    elements[source].link(elements[destiny])
                except:
                    error("element '%s' couldn't link to '%s'"%(source, destiny))
        self.updater = updater

    def new_decoded_pad(self, decodebin, pad, last):
        #print "decoded! %s"%pad.get_caps().to_string()

        for element, spad in self.starts:
            conv = get_possible_elements(pad.get_caps(), spad.get_caps() ,\
                    RAW_CONVERTERS, [], RAW_CONVERTERS)
            if not conv:
                return
            conv = conv[0].element_factory.create()
            self.pipeline.add(conv)

            cpad = conv.get_static_pad("src")
            cpad.link(spad)            

            cpad = conv.get_static_pad("sink")
            pad.link(cpad)
            
            self.starts.remove((element, spad))

            #XXX: code below is helping debug
            for i in self.pipeline.elements():
                for p in i.src_pads():
                    print p.is_linked()
                    if not p.is_linked():
                        print "not_linked source: ",i, p.get_caps().to_string()
                for p in i.sink_pads():
                    print p.is_linked()
                    if not p.is_linked():
                        print "not_linked sink: ",i, p.get_caps().to_string()

    def convert_file(self, file_source, file_destiny):
        self.filesource.set_property("location", file_source)
        self.filesink.set_property("location", file_destiny)
        self.play()

    def finish(self):
        self.stop()
        print "***** File finished *****"
        if self.updater:
            self.updater(CONVERSION_FINISHED)

#import gtk, sys
#file = sys.argv[-1]
#t = Transcoder("a"); t.play_file(file)
#gtk.main()
