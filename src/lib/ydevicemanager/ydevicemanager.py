#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Copyright (C) 2011 YLMF(www.ylmf.org) Ltd.

# This application is released under the GNU General Public License
# v3 (or, at your option, any later version). You can find the full
# text of the license under http://www.gnu.org/licenses/gpl.txt.
# By using, editing and/or distributing this software you agree to
# the terms and conditions of this license.
# Thank you for using free software!
#
#(c) Whise 2010,2011 <hechao@115.com>
#
# Ylmf Device Manager
# This is free software made available under the GNU public license.

__author__ = "hechao"
__date__ = "$2011-11-14 13:25:06$"

import os
import gtk
import ctypes
import gettext
import gobject
try:
    has_udev = True
    import pyudev
    import pyudev.glib
except:
    has_udev = False
try:
    libc = ctypes.CDLL('libc.so.6')
    libc.prctl(15, 'ydm', 0, 0, 0)
except:pass
from globals import *
from widgets import *
from dbuscall import call_signal
from libdevice import DeviceThread
from libdriver import DriverThread

gettext.textdomain('ydm')
def _(s):
    return gettext.gettext(s)


class DeviceManger(BaseFucn):

    def __init__(self):
        gtk.gdk.threads_init()
        call_signal(self.status_changed)

        self.pcid = {}
        self.has_tap = None
        self.mainbox = gtk.VBox()

        # Init gtk window
        self.window = self.initwindow()
        
        # Create toolbar
        self.toolbar = ToolBar(self)
        self.mainbox.pack_start(self.toolbar, False)

        self.framebox = gtk.VBox()
        self.mainbox.pack_start(self.framebox)

        # statusbar
        self.status_bar = StatusBar()
        self.mainbox.pack_start(self.status_bar, False)

        # device change
        if has_udev:
            self.device_changed()

        self.window.add(self.mainbox)
        self.window.show_all()

        self.device_thread = DeviceThread(self)
        self.device_thread.start()

        '''test'''
        self.driver_thread = DriverThread(self)
        self.driver_thread.start()

        if os.path.isfile(HW_XML):
            self.device_thread.join()

        gtk.gdk.threads_enter()
        try:
            gtk.main()
        finally:
            gtk.gdk.threads_leave()

    def device_changed(self):
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='usb')
        observer = pyudev.glib.GUDevMonitorObserver(monitor)
        observer.connect('device-added', self.device_added)
        observer.connect('device-removed', self.device_removed)
        monitor.enable_receiving()

    def device_added(self, observer, device):
        self.status_bar.set_status(_("Found a new device is added, you can re-test in order to obtain the latest hardware information."))

    def device_removed(self, observer, device):
        self.status_bar.set_status(_("Found that the device is removed, you can re-test in order to get the change information after of the hardware."))

    def status_changed(self, msg):
        if msg == "ABI":
            self.status_bar.set_status(_("Loading Finished"))
        else:
            self.set_status(_("Loading:") + msg)
            self.status_bar.set_status(_("Loading:") + msg)

    def set_status(self, status):
        self.statelabel.set_markup("<span foreground='#0092CE' font_desc='10'>%s</span>" % status)

    def select_page(self, pageid):
        self.clean_widget(pageid)

        def driver_page(*arg):
            self.clean_widget(pageid)
            self.framebox.pack_start(self.driver_page)

	if pageid == DEV_ID:
            if hasattr(self, 'device_page'):
                self.framebox.pack_start(self.device_page)
            else:
                self.framebox.pack_start(self.load_wait(self, "Loading, please wait ..."))
                self.device_thread.connect('load-wait', self.wait_page, pageid)

        elif pageid == DRI_ID:
            if hasattr(self, 'driver_page'):
                if self.has_tap == "RETRY":
                    self.framebox.pack_start(self.load_wait(self, "Loading, please wait ..."))
                    gobject.timeout_add(2000, driver_page)
                else:
                    self.framebox.pack_start(self.driver_page)
            else:
                self.framebox.pack_start(self.load_wait(self, "Loading, please wait ..."))
                self.driver_thread.connect('load-wait', self.wait_page, pageid)

        elif pageid == TEST_ID:
            self.framebox.add(self.load_wait(self, "Developing, please wait ..."))

    def clean_widget(self, pageid):
        self.framebox.foreach(lambda widget: self.framebox.remove(widget))
        self.toolbar.tool_button.pageid = pageid
        #Image change, queue_draw() trigger expose()
        self.toolbar.tool_button.queue_draw()

    def wait_page(self, event, pageid):
        self.select_page(pageid)

if __name__ == "__main__":
    DeviceManger()