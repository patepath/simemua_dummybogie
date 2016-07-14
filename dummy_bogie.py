#!/usr/bin/env python

import pygtk
import gtk
import pango
#import smbus
import threading
import time
import os
import RPi.GPIO as GPIO
import socket


GPIO.setmode(GPIO.BCM)
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(26, GPIO.OUT)
GPIO.setup(20, GPIO.OUT)

pw1 = GPIO.PWM(26, 1000)
pw2 = GPIO.PWM(20, 1000)

pw1.start(0)
pw2.start(0)

clear_list = (26, 20)
GPIO.output(clear_list, GPIO.LOW)

gtk.gdk.threads_init()
window = gtk.Window(gtk.WINDOW_TOPLEVEL)
normal_font = pango.FontDescription("Tahoma 16")
normal_entry = pango.FontDescription("Tahoma 16")
status_font = pango.FontDescription("Tahoma 25")

label_RPM = gtk.Label()
label_speed = gtk.Label()
label_lv_drive = gtk.Label()
label_lv_brake = gtk.Label()
label_lv_load = gtk.Label()
entry_ft_drive = gtk.Entry(max=3)
entry_ft_brake = gtk.Entry(max=3)
entry_ft_load = gtk.Entry(max=3)
label_at_drive = gtk.Label('0.0')
label_at_brake = gtk.Label('0.0')

class DummyBogie:

    vbox = gtk.VBox(False, 0)
    count = 0
    ts = 0
    te = 0

    def __init__(self):
        GPIO.add_event_detect(5, GPIO.FALLING, callback=self.interrupt_count)
        threading.Thread(target=self.thread_socket_server).start()
        threading.Thread(target=self.pooling).start()

        window.connect("delete_event", self.delete_event)

        window.set_border_width(10)
        window.resize(800, 600)
        window.set_title("Dummy Bogie")

#        action_box = gtk.HBox(True, 0)
#        bttn_key = gtk.Button('Keyboard')
#        bttn_key.modify_font(normal_font)
#        bttn_key.connect('clicked' , self.bttn_key_clicked, '')
#        action_box.pack_start(bttn_key)
#        self.vbox.pack_start(action_box)

        self.create_config_frame()
        self.create_status_frame()

        window.add(self.vbox)
        window.show_all()

    def bttn_key_clicked(self, widget, event, data=None):
        os.system('./toggle-matchbox-key.sh')

    def interrupt_count(self, channel):
        self.count += 1
        self.te = int(round(time.time() * 1000))

    def thread_socket_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('', 2515))
        server.listen(1)

        while True:
                    c, addr = server.accept()

            while True:
                data = c.recv(64)

                if data:
                    actual = 0.0

                    try:
                        duty = float(data)
                    except ValueError:
                        duty = 0.0

                    if duty >=0:
                        label_lv_drive.set_text("%.1f" %duty)
                        label_lv_brake.set_text('0.0')

                        try:
                            factor = float(entry_ft_drive.get_text())
                        except ValueError:
                            factor = 0.0

                        actual = duty * factor
                        label_at_drive.set_text("%.1f" %actual)
                        label_at_brake.set_text('0.0')

                        pw1.ChangeDutyCycle(actual)
                        pw2.ChangeDutyCycle(actual)

                    else:
                        label_lv_brake.set_text("%.1f" %duty)
                        label_lv_drive.set_text('0.0')

                        try:
                            factor = float(entry_ft_brake.get_text())
                        except ValueError:
                            factor = 0.0

                        actual = duty * factor
                        label_at_brake.set_text("%.1f" %actual)
                        label_at_drive.set_text('0.0')

                else:
                    c.close()
                    break

        server.close()

    def pooling(self):
        period = 0.0
        cycle = 0.0

        while True:
            if self.count != 0:
                period = float((self.te-self.ts)/self.count)
            else:
                period = 0

            if period != 0:
                cycle = float(1/period) * 1000

            else:
                cycle = 0

            rpm = cycle * 60

            label_RPM.set_text("Wheel = %d rpm" %(rpm/4))
            label_speed.set_text("Speed = %d km/hr" %(rpm * 0.1602/4)) # 60*2.67/1000
            self.count = 0
            self.ts = self.te
            time.sleep(0.5)

    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

    def create_config_frame(self):
        config_box = gtk.HBox(False, 0)
        config_frame = gtk.Frame()
        config_frame.set_label("Configuration")
        config_frame.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FFFFFF'))
        config_table = gtk.Table(4, 5, False)
        config_table.set_border_width(10)

#----------------------------------------------------------
# row 1

        label = gtk.Label("DRIVE")
        label.modify_font(normal_font)
        config_table.attach(label, 0, 1, 1, 2)

        label_lv_drive.set_alignment(xalign=0.5, yalign=0.5)
        label_lv_drive.modify_font(normal_entry)
        label_lv_drive.set_text('0.0')
        config_table.attach(label_lv_drive, 1, 2, 1, 2)

        entry_ft_drive.set_alignment(xalign=0.5)
        entry_ft_drive.modify_font(normal_entry)
        entry_ft_drive.set_text('1.0')
        config_table.attach(entry_ft_drive, 2, 3, 1, 2)

        entry = gtk.Entry()
        entry.set_alignment(xalign=0.5)
        entry.modify_font(normal_entry)
        entry.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse('#7FFFD4'))
        config_table.attach(entry, 3, 4, 1, 2)

        label_at_drive.set_alignment(xalign=0.5, yalign=0.5)
        label_at_drive.modify_font(normal_entry)
        label_at_drive.set_text('0.0')
        config_table.attach(label_at_drive, 4, 5, 1, 2)

#----------------------------------------------------------
# row 2

        label = gtk.Label("BRAKE")
        label.modify_font(normal_font)
        config_table.attach(label, 0, 1, 2, 3)

        label_lv_brake.set_alignment(xalign=0.5, yalign=0.5)
        label_lv_brake.modify_font(normal_entry)
        label_lv_brake.set_text('0.0')
        config_table.attach(label_lv_brake, 1, 2, 2, 3)

        entry_ft_brake.set_alignment(xalign=0.5)
        entry_ft_brake.modify_font(normal_entry)
        entry_ft_brake.set_text('1.0')
        config_table.attach(entry_ft_brake, 2, 3, 2, 3)

        entry = gtk.Entry()
        entry.set_alignment(xalign=0.5)
        entry.modify_font(normal_font)
        entry.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse('#7FFFD4'))
        config_table.attach(entry, 3, 4, 2, 3)

        label_at_brake.set_alignment(xalign=0.5, yalign=0.5)
        label_at_brake.modify_font(normal_entry)
        label_at_brake.set_text('0.0')
        config_table.attach(label_at_brake, 4, 5, 2, 3)

#----------------------------------------------------------
# row 3

        label = gtk.Label("LOAD")
        label.modify_font(normal_font)
        config_table.attach(label, 0, 1, 3, 4)

        label_lv_load.set_alignment(xalign=0.5, yalign=0.5)
        label_lv_load.modify_font(normal_entry)
        label_lv_load.set_text('0.0')
        config_table.attach(label_lv_load, 1, 2, 3, 4)

        entry_ft_load.set_alignment(xalign=0.5)
        entry_ft_load.modify_font(normal_entry)
        entry_ft_load.set_text('1.0')
        config_table.attach(entry_ft_load, 2, 3, 3, 4)

        entry = gtk.Entry()
        entry.set_alignment(xalign=0.5)
        entry.modify_font(normal_entry)
        entry.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse('#7FFFD4'))
        config_table.attach(entry, 3, 4, 3, 4)

        label = gtk.Label("0.0")
        label.modify_font(normal_entry)
        config_table.attach(label, 4, 5, 3, 4)

#----------------------------------------------------------

        label = gtk.Label("LEVEL (%)")
        label.modify_font(normal_font)
        config_table.attach(label, 1, 2, 0, 1)

        label = gtk.Label("FACTOR")
        label.modify_font(normal_font)
        config_table.attach(label, 2, 3, 0, 1)

        label = gtk.Label('FUNCTION')
        label.modify_font(normal_font)
        config_table.attach(label, 3, 4, 0, 1)

        label = gtk.Label("ACTUAL (%)")
        label.modify_font(normal_font)
        config_table.attach(label, 4, 5, 0, 1)

        config_frame.add(config_table)
        config_box.pack_start(config_frame)
        self.vbox.pack_start(config_box, False, False, 0)

    def create_status_frame(self):
        status_box = gtk.HBox(False, 0)
        status_frame = gtk.Frame()
        status_frame.set_label("STATUS")
        status_table = gtk.Table(1, 2, True)
        status_table.set_border_width(10)

        label_RPM.modify_font(status_font)
        label_RPM.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#0000FF'))
        label_RPM.set_text('Wheel = 0 rpm')
        status_table.attach(label_RPM, 0, 1, 0, 1)

        label_speed.modify_font(status_font)
        label_speed.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#0000FF'))
        label_speed.set_text('Speed = 0 km/hr')
        status_table.attach(label_speed, 1, 2, 0, 1)

        status_frame.add(status_table)
        status_box.pack_start(status_frame)
        self.vbox.pack_start(status_box)

def main():
    gtk.main()
    return 0

if __name__ == "__main__":
    DummyBogie()

    #gtk.gdk.threads_enter()
    main()
    #gtk.gdk.threads_leave()

