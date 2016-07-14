#!/usr/bin/evn python

import pygtk
import gtk
import pango
import socket

class dummybogie:

    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.connect('delete_event', self.delete_event)
        window.set_border_width(10)
        window.resize(800, 600)
        window.set_title('Dummy Bogie')
        window.show_all()

    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

def main():
    gtk.main()
    return 0

if __name__ == '__main__':
    dummybogie()

    main()
