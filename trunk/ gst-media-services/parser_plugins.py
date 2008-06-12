#!/usr/bin/env python
import gst

class Pad:
	def __init__(self, plugin, element_factory, pad_template):
		self.plugin = plugin
		self.feature = element_factory
		self.template = pad_template
		caps = self.template.get_caps().to_string().split(",")
		self.mimetype = caps[0]
		self.build_properties(caps[1:])
		self.klasses = self.feature.get_klass().split("/")
	
	def build_properties(self, caps):
		#TODO: parse caps
		self.properties = caps
	



#read registry
reg = gst.registry_get_default()

#read plugins from registry
plugins = reg.get_plugin_list()

pads = []

#build pad_template list
for plugin in plugins:
	features = reg.get_feature_list_by_plugin(plugin.get_name())
	for feature in features:
		#tags = feature.get_klass().split("/")
		#feature.get_description(), feature.get_longname
		try:
			pads_templates = feature.get_static_pad_templates()
			for pad in pads_templates:
				pads += [Pad(plugin, feature, pad)]
				#[ [plugin.get_name(), feature.get_name(), pad.name_template, pad.get_caps().to_string().split(",")[0]] ]
		except:
			pass
		#	print "'%20s' - f.'%20s', '%s'"%(plugin.get_name(), feature.get_name(), type(feature))

#print pads

