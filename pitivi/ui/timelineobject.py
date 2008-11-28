import goocanvas
import gobject
import gtk
import os.path
import pango
import pitivi.instance as instance
from urllib import unquote
from pitivi.receiver import receiver, handler
from view import View
import controller
from complexinterface import Zoomable

LEFT_SIDE = gtk.gdk.Cursor(gtk.gdk.LEFT_SIDE)
RIGHT_SIDE = gtk.gdk.Cursor(gtk.gdk.RIGHT_SIDE)

class TrimHandle(View, goocanvas.Rect, Zoomable):

    """A component of a TimelineObject which manage's the source's edit
    points"""

    element = receiver()

    def __init__(self, element, **kwargs):
        self.element = element
        goocanvas.Rect.__init__(self,
            width=5,
            fill_color_rgba=0x00000022,
            line_width=0,
            **kwargs
        )
        View.__init__(self)

class StartHandle(TrimHandle):

    """Subclass of TrimHandle wich sets the object's start time"""

    class Controller(controller.Controller):

        def set_pos(self, obj, pos):
            self._view.element.snapInTime(
                self._view.pixelToNs(pos[0]))

class EndHandle(TrimHandle):

    """Subclass of TrimHandle which sets the objects's end time"""

    class Controller(controller.Controller):

        def set_pos(self, obj, pos):
            self._view.element.snapOutTime(
                self._view.pixelToNs(pos[0]))

class TimelineObject(View, goocanvas.Group, Zoomable):

    element = receiver()

    __HEIGHT__ = 50
    __NORMAL__ = 0x709fb899
    __SELECTED__ = 0xa6cee3AA

    class Controller(controller.Controller):

        def drag_start(self):
            instance.PiTiVi.current.timeline.disableEdgeUpdates()

        def drag_end(self):
            instance.PiTiVi.current.timeline.enableEdgeUpdates()

        def set_pos(self, item, pos):
            self._view.element.snapStartDurationTime(max(
                self._view.pixelToNs(pos[0]), 0))

    def __init__(self, element, composition):
        goocanvas.Group.__init__(self)
        View.__init__(self)

        self.element = element
        self.comp = composition

        self.bg = goocanvas.Rect(
            height=self.__HEIGHT__, 
            line_width=0)

        self.name = goocanvas.Text(
            x=10,
            y=10,
            text=os.path.basename(unquote(element.factory.name)),
            font="Sans 9",
            fill_color_rgba=0x000000FF,
            alignment=pango.ALIGN_LEFT)
 
        self.start_handle = StartHandle(element,
            height=self.__HEIGHT__)
        self.start_handle.setZoomAdjustment(self.getZoomAdjustment())
        self.end_handle = EndHandle(element,
            height=self.__HEIGHT__)
        self.end_handle.setZoomAdjustment(self.getZoomAdjustment())

        for thing in (self.bg, self.start_handle, self.end_handle, self.name):
            self.add_child(thing)
        self.normal()

    def select(self):
        self.bg.props.fill_color_rgba = self.__SELECTED__

    def normal(self):
        self.bg.props.fill_color_rgba = self.__NORMAL__

    def zoomChanged(self):
        self._start_duration_cb(self.element, self.element.start,
            self.element.duration)

    def setChildZoomAdjustment(self, adj):
        self.start_handle.setZoomAdjustment(adj)
        self.end_handle.setZoomAdjustment(adj)

    @handler(element, "start-duration-changed")
    def _start_duration_cb(self, obj, start, duration):
        self.set_simple_transform(self.nsToPixel(start), 0, 1, 0)
        width = self.nsToPixel(duration)
        w = width - self.end_handle.props.width
        self.name.props.clip_path = "M%g,%g h%g v%g h-%g z" % (
            0, 0, w, self.__HEIGHT__, w)
        self.bg.props.width = width
        # place end handle at appropriate distance
        self.end_handle.props.x = w
