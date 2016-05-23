from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QGraphicsItem, QApplication, QGraphicsScene, QGraphicsView
import glob
import os
from animations import AnimatedItem, AnimatedScene, CollisionManager, MessageItem
import random

class Fire(AnimatedItem):
    def __init__(self,scene,x=0,y=0):
        super().__init__(scene,x,y)
        self.animations.add("fire",glob.glob(r"sprites/Flame/*.png"),interval = 200)
        self.set_default_image("fire")
        self.animations.play("fire",on_transition=None, on_completion=self.destroy)

    def on_collision(self,other):
        if(type(other)==Bomb):
            other.blast()

class Creep(AnimatedItem):
    def __init__(self,scene,x=0,y=0):
        super().__init__(scene,x,y)
        self.animations.add("down",glob.glob(r"sprites/creep/front/*.png"),interval = 50)
        self.animations.add("up",glob.glob(r"sprites/creep/back/*.png"),interval = 50)
        self.animations.add("right",glob.glob(r"sprites/creep/side/*.png"),interval = 50)
        self.animations.add("left",glob.glob(r"sprites/creep/side/*.png"),interval = 50,horizontal_flip = True)
        self.set_default_image("down")
        self.speed = 8
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timeout)
        self.collision_rect = QtCore.QRect(8,8,48,48)

    def start(self):
        self.timer.start(1000)

    def timeout(self):
        direction = random.randint(0,3)
        if(direction==0) and (self.y()+64) < self.scene.height():
            self.animations.play("down", self.move_down)
        if(direction==1) and (self.y()-8*self.speed) >= 0:
            self.animations.play("up", self.move_up)
        if(direction==2) and (self.x() > 0):
            self.animations.play("left", self.move_left)
        if(direction==3) and self.x()+64 < self.scene.width():
            self.animations.play("right", self.move_right)
        
    def move_down(self):
        self.setY(self.y() + self.speed)
    
    def move_up(self):
        self.setY(self.y() - self.speed)
    
    def move_left(self):
        self.setX(self.x() - self.speed)
    
    def move_right(self):
        self.setX(self.x() + self.speed)

    def on_collision(self,other):
        if(type(other)==Fire):
            self.destroy()
        if(type(other)==Block):
            if(other.blocktype != "portal"):
                self.setX((self.x()+32)//64*64)
                self.setY((self.y()+32)//64*64)
        if(type(other)==Bomb):
            self.setX((self.x()+32)//64*64)
            self.setY((self.y()+32)//64*64)

class Powerup(AnimatedItem):
    def __init__(self,scene,x=0,y=0,uptype="BombPower"):
        super().__init__(scene,x,y)
        self.animations.add("BombPower",['sprites/powerups/BombPowerup.png'],non_stop=False)
        self.animations.add("FlamePower",['sprites/powerups/FlamePowerup.png'],non_stop=False)
        self.animations.add("SpeedPower",['sprites/powerups/SpeedPowerup.png'],non_stop=False)
        self.uptype=uptype
        self.set_default_image(self.uptype)

class Bomb(AnimatedItem):
    def __init__(self,scene,power=1,x=0,y=0):
        super().__init__(scene,x,y)
        self.animations.add("bomb",glob.glob(r"sprites/Bomb/*.png"),interval = 200,repeat=4)
        self.set_default_image("bomb")
        self.power=power
        self.animations.play("bomb",None,self.blast)
        self.setZValue(100)

    def blast(self):
        self.destroy()
        man=None
        for i,item in enumerate(self.scene.items()):
            if(type(item)==Bomberman):
                man=item
        man.now=man.now-1
        f = Fire(self.scene,self.x(),self.y())
        b1=True
        b2=True
        b3=True
        b4=True
        for i in range(1,self.power+1):
            if self.x()+64*i+32<self.scene.width() and b1==True:
                if(self.checkBolck(self.x()+64*i,self.y())==True):
                    f = Fire(self.scene,self.x()+64*i,self.y())
                else:
                    b1=False
            if self.x()-64*i>0 and b2==True:
                if(self.checkBolck(self.x()-64*i,self.y())==True):
                    f = Fire(self.scene,self.x()-64*i,self.y())
                else:
                    b2=False
            if self.y()-64*i>0 and b3==True:
                if(self.checkBolck(self.x(),self.y()-64*i)==True):  
                    f = Fire(self.scene,self.x(),self.y()-64*i)
                else:
                    b3=False
            if self.y()+64*i+32<self.scene.height() and b4==True:
                if(self.checkBolck(self.x(),self.y()+64*i)==True):
                    f = Fire(self.scene,self.x(),self.y()+64*i)
                else:
                    b4=False

    def checkBolck(self,x,y):
        pd=True
        for i, item in enumerate(self.scene.items()):
            if(type(item)==Block):
                bx=item.x()+8
                by=item.y()+8
                if bx==x and by==y:
                    pd=False
                    if item.can_Destory==True:
                        item.destroy()
                        z=random.randint(0,100)
                        if(z<=10):
                            up = Powerup(self.scene,bx+8,by+8)
                        elif(z<=20):
                            up = Powerup(self.scene,bx+8,by+8,"SpeedPower")
                        elif(z<=30):
                            up = Powerup(self.scene,bx+8,by+8,"FlamePower")
        return pd

class Block(AnimatedItem):
    def __init__(self,scene,x=0,y=0,blocktype="soildblock"):
        super().__init__(scene,x,y)
        self.animations.add("soildblock",['sprites/blocks/SolidBlock.png'],non_stop=False)
        self.animations.add("explodableblock",['sprites/blocks/explodableblock.png'],non_stop=False)
        self.animations.add("portal",['sprites/blocks/portal.png'],non_stop=False)
        self.blocktype=blocktype
        self.set_default_image(self.blocktype)
        self.can_Destory=False
        if(blocktype=="explodableblock"):
            self.can_Destory=True

class Ground(AnimatedItem):
    def __init__(self,scene,x,y):
        super().__init__(scene,x,y)
        self.animations.add("background",['sprites/blocks/BackgroundTile.png'],non_stop=False)
        self.set_default_image("background")


class Bomberman(AnimatedItem):
    def __init__(self,scene,x=0,y=0):
        super().__init__(scene,x,y)
        self.animations.add("down",glob.glob(r"sprites/bomberman/front/*.png"),interval = 50)
        self.animations.add("up",glob.glob(r"sprites/bomberman/back/*.png"),interval = 50)
        self.animations.add("right",glob.glob(r"sprites/bomberman/side/*.png"),interval = 50)
        self.animations.add("left",glob.glob(r"sprites/bomberman/side/*.png"),interval = 50,horizontal_flip = True)
        self.set_default_image("down")
        self.collision_rect = QtCore.QRect(8,72,48,48)
        self.setZValue(100)
        self.power=1
        self.speed = 8
        self.count=1
        self.now=0
        
    def move_down(self):
        self.setY(self.y() + self.speed)
    
    def move_up(self):
        self.setY(self.y() - self.speed)
    
    def move_left(self):
        self.setX(self.x() - self.speed)
    
    def move_right(self):
        self.setX(self.x() + self.speed)
                
    def keyPressEvent(self,event):
        key = event.key()
        if key == QtCore.Qt.Key_Down:
            if (self.y()+128) < self.scene.height():
                self.animations.play("down", self.move_down)
        if key == QtCore.Qt.Key_Up:
            if (self.y()+64-8*self.speed) >= 0:
                self.animations.play("up",self.move_up)
        if key == QtCore.Qt.Key_Left:
            if (self.x() > 0):
                self.animations.play("left",self.move_left)
        if key == QtCore.Qt.Key_Right:
            if self.x()+64 < self.scene.width():
                self.animations.play("right",self.move_right)
        if key == 32:
            if(self.now<self.count):
                xc=(self.x()+32)//64*64+8
                yc=(self.y()+self.height())//64*64-56
                self.now=self.now+1
                bomb = Bomb(self.scene,power=self.power,x=xc,y=yc)

    def on_collision(self,other):
        if(type(other)==Fire or type(other)==Creep):
            m=MessageItem(self.scene)
            m.add("Mission Fail!")
            self.destroy()
        if(type(other)==Block):
            if(other.blocktype != "portal"):
                self.setX((self.x()+32)//64*64)
                self.setY((self.y()+32)//64*64)
            else:
                m=MessageItem(self.scene)
                m.add("Mission Complete!")
                self.destroy()
        if(type(other)==Powerup):
            if(other.uptype=="BombPower"):
                self.count=self.count+1
                other.destroy()
            if(other.uptype=="FlamePower"):
                self.power=self.power+1
                other.destroy()
            if(other.uptype=="SpeedPower"):
                if(self.animations.animation_dict['down'].interval >=10):
                    self.animations.animation_dict['down'].interval-=10
                    self.animations.animation_dict['up'].interval-=10
                    self.animations.animation_dict['right'].interval-=10
                    self.animations.animation_dict['left'].interval-=10
                other.destroy()

class Button(AnimatedItem):
    def __init__(self,scene,x=0,y=0):
        super().__init__(scene,x,y)
        self.animations.add("normal",["sprites/menu/One_Player_Normal.png"],interval=1,non_stop = False)
        self.animations.add("hover",["sprites/menu/One_Player_Hover.png"],interval=1,non_stop = False)
        self.set_default_image("normal")
        self.setAcceptHoverEvents(True)
        self.con=0

    def hoverEnterEvent(self, event):
        self.con=1
        self.animations.play("hover", None)

    def hoverLeaveEvent(self,event):
        self.con=0
        self.animations.play("normal", None)

    def mousePressEvent(self,event):
        if self.con==1:
            for i,item in enumerate(self.scene.items()):
                if(item!=self):
                    item.destroy()
            for i in range(0,9):
                for j in range(0,9):
                    Ground(scene,i*64,j*64)
                    continue
            Block(scene,64*5,64*3)
            Block(scene,64*7,64*1,'explodableblock')
            Block(scene,64*7,64*2,'explodableblock')
            Block(scene,64*7,64*3,'explodableblock')
            Block(scene,64*2,64*3,'portal')
            creep = Creep(scene,4*64,3*64)
            creep.start()
            Bomberman(scene,0,0)
            self.destroy()

class Image(QGraphicsItem):
    def __init__(self, scene, x=0, y=0, path=None):
        super().__init__()
        self.scene = scene
        self.scene.addItem(self)
        self.image = QtGui.QImage(path)
        self.width=self.image.width()
        self.height=self.image.height()
        self.setX(x)
        self.setY(y)

    def paint(self, painter, option, widget=None):
        if self.image:
            painter.drawImage(0, 0, self.image)

    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.width, self.height) 

    def destroy(self):
        if self in self.scene.items():
            self.scene.removeItem(self)

if __name__ == "__main__":
    app = QApplication([])
    scene = AnimatedScene(576,576)
    collision = CollisionManager(scene)
    img = Image(scene,0,0,"sprites/title_flat.jpg")
    a = Button(scene,222,320)
    app.exec()