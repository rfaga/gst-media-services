# name of your binary
bin_PROGRAMS = gst-app

# list of source files
# the prefix is the name of the binary
gst_app_SOURCES = main.c gstms.c

# list of headers we're not going to install
noinst_HEADERS = gstms.h

# our CFLAGS and LDFLAGS used for compiling and linking
# make sure you prefix these with the name of your binary
gst_app_CFLAGS = $(GST_CFLAGS) $(GST_PLUGINS_BASE_CFLAGS) -Wall -g -O2
gst_app_LDFLAGS = $(GST_LIBS) $(GST_PLUGINS_BASE_LIBS)
