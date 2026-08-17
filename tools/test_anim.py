import os
import sys

import simplepbr

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from panda3d.core import MouseButton, KeyboardButton, ClockObject, Vec3, AmbientLight, DirectionalLight, TextNode
from direct.gui.OnscreenText import OnscreenText

# Переходим в корень проекта, чтобы работали относительные пути к assets | Change to project root for relative asset paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

globalClock = ClockObject.getGlobalClock()


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        simplepbr.init()
        self.disableMouse()

        alight = AmbientLight("ambient")
        alight.setColor((0.2, 0.2, 0.2, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)

        dlight = DirectionalLight("directional")
        dlight.setColor((0.8, 0.8, 0.8, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(45, -60, 0)
        self.render.setLight(dlnp)

        self.actor = Actor(os.path.join(PROJECT_ROOT, "assets/models/house.bam"))
        self.actor.setScale(0.5)

        bounds = self.actor.getBounds()
        self.center = bounds.getCenter()

        self.pivot = self.render.attachNewNode("pivot")
        self.pivot.setPos(self.center)

        self.actor.reparentTo(self.pivot)
        self.actor.setPos(-self.center)

        self.anims = list(self.actor.getAnimNames())
        self.animIndex = 0
        self.frameMode = False
        self.currentFrame = 0
        self.holdTimer = 0
        self.keyWasDown = False

        font = self.loader.loadFont("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

        self.controlsText = OnscreenText(
            text="LMB: rotation  |  CMB: zoom  |  ↑/↓: next/previous anim  |  Tab: by frame  |  R: reset",
            pos=(-1.3, 0.94),
            scale=0.045,
            fg=(1, 1, 1, 0.7),
            align=TextNode.ALeft,
            font=font,
        )

        self.controlsText2 = OnscreenText(
            text="Shift+↑/↓: tilt 90°  |  Shift+←/→: rotate 90°",
            pos=(-1.3, 0.87),
            scale=0.045,
            fg=(1, 1, 1, 0.7),
            align=TextNode.ALeft,
            font=font,
        )

        self.infoText = OnscreenText(
            text="",
            pos=(-1.3, 0.80),
            scale=0.045,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            font=font,
        )

        if self.anims:
            self.actor.loop(self.anims[self.animIndex])
            self.updateAnimInfo()

        self.rotSpeed = 1
        self.isRotating = False
        self.lastMousePos = Vec3(0, 0, 0)

        self.shiftUpWasDown = False
        self.shiftDownWasDown = False
        self.shiftLeftWasDown = False
        self.shiftRightWasDown = False

        self.zoomDist = 5
        self.camera.setPos(0, -self.zoomDist, self.center.z)
        self.camera.lookAt(self.center)

        self.accept("wheel_up", self.zoom, extraArgs=[-1])
        self.accept("wheel_down", self.zoom, extraArgs=[1])

        self.accept("arrow_up", self.arrowUp)
        self.accept("arrow_down", self.arrowDown)
        self.accept("r", self.resetView)
        self.accept("tab", self.toggleFrameMode)

        self.taskMgr.add(self.rotateTask, "RotateTask")

    def arrowUp(self):
        if not self.frameMode:
            self.nextAnim()

    def arrowDown(self):
        if not self.frameMode:
            self.prevAnim()

    def toggleFrameMode(self):
        self.frameMode = not self.frameMode
        if self.frameMode:
            self.actor.stop()
            self.currentFrame = 0
            self.poseFrame()
        else:
            name = self.anims[self.animIndex]
            self.actor.loop(name)
        self.updateAnimInfo()

    def stepFrame(self, delta):
        if not self.frameMode or not self.anims:
            return
        name = self.anims[self.animIndex]
        ctrl = self.actor.getAnimControl(name)
        if ctrl:
            anim = ctrl.getAnim()
            if anim:
                total = anim.getNumFrames()
                self.currentFrame = (self.currentFrame + delta) % total
                self.poseFrame()
                self.updateAnimInfo()

    def poseFrame(self):
        name = self.anims[self.animIndex]
        ctrl = self.actor.getAnimControl(name)
        if ctrl:
            ctrl.pose(float(self.currentFrame))

    def updateAnimInfo(self):
        name = self.anims[self.animIndex]
        ctrl = self.actor.getAnimControl(name)
        info = ""
        if ctrl:
            anim = ctrl.getAnim()
            if anim:
                frames = anim.getNumFrames()
                fps = anim.getBaseFrameRate()
                dur = frames / fps if fps > 0 else 0
                total = len(self.anims)
                info = f"{self.animIndex+1}/{total}: {name}  |  {frames} frames  |  {dur:.2f}s"
                if self.frameMode:
                    info += f"  |  ←/→: previous/next frame  |  Frame: {self.currentFrame}/{frames-1}"
        self.infoText.setText(info)

    def nextAnim(self):
        if not self.anims:
            return
        self.animIndex = (self.animIndex + 1) % len(self.anims)
        name = self.anims[self.animIndex]
        self.actor.stop()
        self.actor.loop(name)
        self.updateAnimInfo()

    def prevAnim(self):
        if not self.anims:
            return
        self.animIndex = (self.animIndex - 1) % len(self.anims)
        name = self.anims[self.animIndex]
        self.actor.stop()
        self.actor.loop(name)
        self.updateAnimInfo()

    def resetView(self):
        self.pivot.setHpr(0, 0, 0)

    def zoom(self, direction):
        self.zoomDist = max(2, min(10, self.zoomDist + direction))
        self.camera.setPos(0, -self.zoomDist, self.center.z)
        self.camera.lookAt(self.center)

    def rotateTask(self, task):
        dt = globalClock.getDt()
        mw = self.mouseWatcherNode

        if mw.hasMouse():
            mx = mw.getMouseX()
            my = mw.getMouseY()

            if mw.isButtonDown(MouseButton.one()) and not self.isRotating:
                self.isRotating = True
                self.lastMousePos = Vec3(mx, my, 0)

            elif mw.isButtonDown(MouseButton.one()) and self.isRotating:
                dx = mx - self.lastMousePos.x
                dy = my - self.lastMousePos.y

                if abs(dx) > 0.001 or abs(dy) > 0.001:

                    current_hpr = self.pivot.getHpr()
                    new_h = current_hpr.x - dx * self.rotSpeed * 100
                    new_p = current_hpr.y + dy * self.rotSpeed * 100

                    self.pivot.setHpr(new_h, new_p, current_hpr.z)

                self.lastMousePos = Vec3(mx, my, 0)

            else:
                self.isRotating = False

        shiftDown = mw.isButtonDown(KeyboardButton.shift()) or mw.isButtonDown(KeyboardButton.rshift())

        if shiftDown and mw.isButtonDown(KeyboardButton.up()):
            if not self.shiftUpWasDown:
                hpr = self.pivot.getHpr()
                self.pivot.setHpr(hpr.x, hpr.y - 90, hpr.z)
                self.shiftUpWasDown = True
        elif shiftDown and mw.isButtonDown(KeyboardButton.down()):
            if not self.shiftDownWasDown:
                hpr = self.pivot.getHpr()
                self.pivot.setHpr(hpr.x, hpr.y + 90, hpr.z)
                self.shiftDownWasDown = True
        elif shiftDown and mw.isButtonDown(KeyboardButton.left()):
            if not self.shiftLeftWasDown:
                hpr = self.pivot.getHpr()
                self.pivot.setHpr(hpr.x - 90, hpr.y, hpr.z)
                self.shiftLeftWasDown = True
        elif shiftDown and mw.isButtonDown(KeyboardButton.right()):
            if not self.shiftRightWasDown:
                hpr = self.pivot.getHpr()
                self.pivot.setHpr(hpr.x + 90, hpr.y, hpr.z)
                self.shiftRightWasDown = True
        else:
            self.shiftUpWasDown = False
            self.shiftDownWasDown = False
            self.shiftLeftWasDown = False
            self.shiftRightWasDown = False

        if self.frameMode and self.anims:
            keyDown = mw.isButtonDown(KeyboardButton.left()) or mw.isButtonDown(KeyboardButton.right())
            if keyDown:
                if not self.keyWasDown:
                    dir = -1 if mw.isButtonDown(KeyboardButton.left()) else 1
                    self.stepFrame(dir)
                    self.holdTimer = 0
                else:
                    self.holdTimer += dt
                    if self.holdTimer > 0.15:
                        dir = -1 if mw.isButtonDown(KeyboardButton.left()) else 1
                        self.stepFrame(dir)
                        self.holdTimer = 0
            self.keyWasDown = keyDown

        return Task.cont


app = MyApp()
app.run()