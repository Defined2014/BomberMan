from collections import namedtuple
import os
try:
    from PyQt5 import QtGui, QtCore
    from PyQt5.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsView, QApplication
    from PyQt5.QtMultimedia import QSound
    from PyQt5.QtGui import QPainter, QPen, QColor, QFont
except ImportError:
    from PyQt4 import  tGui, QtCore
    from PyQt4.QtGui import QGraphicsItem, QGraphicsScene, QGraphicsView, QApplication, QSound
    from PyQt4.QtGui import QPainter, QPen, QColor, QFont

DEBUG = False


class Frames:
    """Container for all the image frames in an animation"""
    def __init__(self, img_file_paths, on_timeout=None, interval=500, repeat=1,
                 horizontal_flip=False, vertical_flip=False, non_stop=True):
        self.frames = []
        self.max_width = 0
        self.max_height = 0
        for file_path in img_file_paths:
            img = QtGui.QImage(file_path)
            if img.height() > self.max_height:
                self.max_height = img.height()
            if img.width() > self.max_width:
                self.max_width = img.width()
            if horizontal_flip or vertical_flip:
                img = img.mirrored(horizontal_flip, vertical_flip)
            self.frames.append(img)

        # copy frames 'repeat' times
        self.frames *= repeat
        # current frame index
        self.index = 0
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timeout)
        self.interval = interval
        self.timeout_callback = on_timeout
        self.non_stop = non_stop  # whether to start the animation immediately (by calling timeout() before timeout)
        self.transition_callback = None
        self.completion_callback = None

    def set_transition_callback(self, callback):
        self.transition_callback = callback

    def set_completion_callback(self, callback):
        self.completion_callback = callback

    def start(self):
        if not self.timer.isActive():
            self.index = 0
            self.timer.start(self.interval)
        if self.non_stop:
            self.timeout()  # no more waiting at the beginning!

    def next(self):
        if self.index == len(self.frames):  # end of animation
            if self.completion_callback:
                self.completion_callback()
            self.index = 0
            return None
        frame = self.frames[self.index]
        self.index += 1
        if self.transition_callback:
            self.transition_callback()
        return frame

    def timeout(self):
        frame = self.next()
        self.timeout_callback(frame)
        if not frame:
            self.timer.stop()

    def get_static_frame(self, frame_index=0):
        return self.frames[frame_index]


class Animations:
    """Class for managing the behavior of the animations"""
    def __init__(self, on_update_frame):
        self.animation_dict = {}
        self.is_playing = False
        self.on_update_frame = on_update_frame
        self.completion_callback = None
        self.max_width = 0
        self.max_height = 0

    def add(self, name, image_file_names, interval=500, repeat=1, horizontal_flip=False,
            vertical_flip=False, non_stop=True):
        frames = Frames(image_file_names, on_timeout=self.update_frame, interval=interval, repeat=repeat,
                        horizontal_flip=horizontal_flip, vertical_flip=vertical_flip, non_stop=non_stop)
        self.animation_dict[name] = frames
        if frames.max_width > self.max_width:
            self.max_width = frames.max_width
        if frames.max_height > self.max_height:
            self.max_height = frames.max_height

    def get_item(self, animation_name):
        return self.animation_dict[animation_name]

    def play(self, name, on_transition=None, on_completion=None):
        """
        on_transition is a function to be called when a new frame is played in the animation
        on_completion is a function to be called when the animation has finished playing
        """
        frames = self.animation_dict[name]
        if not self.is_playing:
            if on_transition:
                frames.set_transition_callback(on_transition)
            if on_completion:
                self.completion_callback = on_completion
            frames.start()
            self.is_playing = True

    def update_frame(self, frame):
        if not frame:
            self.is_playing = False
            if self.completion_callback:
                self.completion_callback()
                self.completion_callback = None  # callback only executed once
        else:
            self.on_update_frame(frame)


class AnimatedItem(QGraphicsItem):
    """Any movable graphics item that can be animated in the window"""
    def __init__(self, scene, x=0, y=0):
        super().__init__()
        self.animations = Animations(self.on_update_frame)
        self.scene = scene
        self.scene.addItem(self)
        self.image = None
        self.setX(x)
        self.setY(y)
        self.collidable = True  # has the potential to be hit by another item; implies implementation of on_collision
        self.collision_rect = None  # collision_rect is the area of the item that can possibly collide with other items

    def set_default_image(self, animation_name, frame_index=0):
        self.image = self.animations.get_item(animation_name).get_static_frame(frame_index)

    def width(self):
        return self.animations.max_width

    def height(self):
        return self.animations.max_height

    def paint(self, painter, option, widget):
        if self.image:
            painter.drawImage(0, 0, self.image)
        if not DEBUG:
            return
        pen = QtGui.QPen(QtCore.Qt.black, 1, QtCore.Qt.DashDotLine)
        painter.setPen(pen)
        if self.collision_rect:
            painter.drawRect(self.collision_rect.x(), self.collision_rect.y(),
                             self.collision_rect.width(), self.collision_rect.height())
        else:
            painter.drawRect(0, 0, self.width(), self.height())

    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.width(), self.height())

    def on_update_frame(self, frame):
        self.image = frame
        self.update()

    @staticmethod
    def point_inside_rect(point, rect):
        return rect.x() < point.x() < rect.x() + rect.width() and rect.y() < point.y() < rect.y() + rect.height()

    def collides_with(self, other):
        if self.collision_rect:
            self_left, self_top = self.x() + self.collision_rect.x(), self.y() + self.collision_rect.y()
            self_right, self_bottom = self_left + self.collision_rect.width(), self_top + self.collision_rect.height()
        else:
            self_left, self_top = self.x(), self.y()
            self_right, self_bottom = self.x() + self.width(), self.y() + self.height()

        if other.collision_rect:
            other_left, other_top = other.x() + other.collision_rect.x(), other.y() + other.collision_rect.y()
            other_right, other_bottom = other_left + other.collision_rect.width(), \
                                        other_top + other.collision_rect.height()
        else:
            other_left, other_top = other.x(), other.y()
            other_right, other_bottom = other_left + other.width(), other_top + other.height()
        return self_left < other_right and self_right > other_left and \
               self_top < other_bottom and self_bottom > other_top

    def on_collision(self, other):
        """This method will be invoked when self collides with another AnimatedItem in the scene"""
        pass

    def destroy(self):
        if self in self.scene.items():
            self.scene.removeItem(self)

class MessageItem(QGraphicsItem):
    """A message board at the top of the screen"""
    Item = namedtuple("Item", ['message', 'seconds'])

    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self.setX(0)
        self.setY(200)
        self.scene.addItem(self)
        self.items = []
        self.current_item = MessageItem.Item("", 0)
        self.current_seconds = 0

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_timer)
        self.timer.start(1000)
        self.setOpacity(0.6)
        self.setZValue(99999)

    def add(self, message, last_for_seconds=3, is_urgent=False):
        item = MessageItem.Item(message=message, seconds=last_for_seconds)
        if is_urgent:
            self.items.insert(0, item)
        else:
            self.items.append(item)

    def check_timer(self):
        self.current_seconds += 1
        if self.current_seconds >= self.current_item.seconds:
            if not self.items:
                self.current_item = MessageItem.Item("", 0)
            else:
                self.current_item = self.items.pop(0)
            self.current_seconds = 0
            self.update()

    def paint(self, painter, option, widget):
        if not self.current_item.message:
            return
        painter.setPen(QPen(QtCore.Qt.red, 3, QtCore.Qt.SolidLine))
        painter.setFont(QFont('Simsun', 25))
        painter.drawRect(self.boundingRect())
        painter.drawText(self.boundingRect(), QtCore.Qt.AlignCenter, self.current_item.message)

    def boundingRect(self):
        # only the size of the view (not the scene) changes on window resize
        return QtCore.QRectF(10, 10, self.scene.view.width()-20, 50)


class CollisionManager:
    """A manager that constantly checks whether collisions have happened and notifies the colliding items"""
    def __init__(self, scene):
        self.scene = scene
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_collisions)
        self.timer.start(50)

    def check_collisions(self):
        for i, item1 in enumerate(self.scene.items()):
            for item2 in self.scene.items()[i+1:]:
                if not isinstance(item1, AnimatedItem) or not isinstance(item2, AnimatedItem):
                    continue
                if not item1.collidable and not item2.collidable:
                    continue
                if item1.collides_with(item2):    # if the two items collide, notify them
                    if item1.collidable:
                        item1.on_collision(item2)
                    if item2.collidable:
                        item2.on_collision(item1)


class AnimatedScene(QGraphicsScene):
    """The window containing all the animated items"""
    def __init__(self, width, height):
        super().__init__(0, 0, width, height)
        self.view = QGraphicsView(self)
        self.view.resizeEvent = self.resizeEvent  # necessary for the view to receive resize events
        self.view.show()
        self.collision_manager = CollisionManager(self)

    def keyPressEvent(self, event):
        """Notify all items in the scene about the keys pressed"""
        for item in self.items():
            item.keyPressEvent(event)

    def mousePressEvent(self,event):
        for item in self.items():
            item.mousePressEvent(event)

    def resizeEvent(self, event):
        pass