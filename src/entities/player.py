import os

from direct.actor.Actor import Actor
from src.config import (
    JUMP_POWER,
    MOVE_SPEED,
    SPRINT_SPEED_MULTIPLIER,
    GRAVITY,
    MAP_SIZE,
    SHOW_BOUNDS,
    PLAYER_SCALE,
    PLAYER_HEADING,
    PLAYER_MODEL,
    MODELS_DIR,
)


class Player:
    def __init__(
        self,
        render,
        with_model=True,
        move_speed=MOVE_SPEED,
        sprint_multiplier=SPRINT_SPEED_MULTIPLIER,
        gravity=GRAVITY,
        map_size=MAP_SIZE,
    ):
        """Создаёт игрока: модель, анимации, параметры движения | Create player: model, animations, movement params"""
        self.render = render

        self.move_speed = move_speed
        self.sprint_multiplier = sprint_multiplier
        self.gravity = gravity
        self.map_size = map_size

        self.root = render.attachNewNode("player_root")

        self.actor = None
        if with_model:
            self.actor = Actor(os.path.join(MODELS_DIR, PLAYER_MODEL))
            self.actor.reparentTo(self.root)
            self.actor.setScale(PLAYER_SCALE)
            self.actor.setPos(0, 0, 0)
            self.actor.setH(PLAYER_HEADING)
            if SHOW_BOUNDS:
                self.actor.showBounds()
            self.actor.loop("Idle_Loop")

        self.velocity_z = 0
        self.is_grounded = True

        self.current_anim = None
        self.oneshot_anim = None
        self.jump_state = None
        self.spell_state = None

        self.keys = {"w": False, "a": False, "s": False, "d": False}
        self.shift_down = False

    def set_key(self, key, value):
        """Устанавливает состояние клавиши движения | Set movement key state"""
        self.keys[key] = value

    def jump(self):
        """Прыжок | Jump"""
        if self.spell_state is not None:
            if self.spell_state == "loop" and self.is_grounded:
                if self.actor is not None:
                    self.actor.stop()
                self.spell_state = None
                self.current_anim = None
                self.velocity_z = JUMP_POWER
                self.is_grounded = False
                self.play_animation("Jump_Start")
                self.jump_state = "start"
            return
        if self.is_grounded:
            self.velocity_z = JUMP_POWER
            self.is_grounded = False
            self.play_animation("Jump_Start")
            self.jump_state = "start"

    def shoot(self, on_spell_hit=None):
        """Выстрел | Shoot"""
        if self.actor is None or self.jump_state in ("start", "loop"):
            return

        if self.spell_state == "loop":
            self.actor.stop()
            self.actor.play("Spell_Simple_Shoot")
            self.spell_state = "shoot"
            if on_spell_hit:
                on_spell_hit()
        elif self.spell_state is None:
            self.spell_state = "enter"
            self.actor.stop()
            self.actor.play("Spell_Simple_Enter")
            self.current_anim = None

    def play_animation(self, anim_name):
        """Однократное воспроизведение анимации | Play one-shot animation"""
        if self.actor is None:
            return
        self.actor.stop()
        self.actor.play(anim_name)
        self.oneshot_anim = anim_name
        self.current_anim = None

    def update_movement(self, dt):
        """Перемещение игрока клавишами WASD | Move player from WASD keys"""
        move_x = 0
        move_y = 0

        if self.keys["w"]:
            move_y += 1
        if self.keys["s"]:
            move_y -= 1
        if self.keys["a"]:
            move_x -= 1
        if self.keys["d"]:
            move_x += 1

        forward = self.root.getQuat(self.render).getForward()
        right = self.root.getQuat(self.render).getRight()

        forward.setZ(0)
        right.setZ(0)
        forward.normalize()
        right.normalize()

        direction = forward * move_y + right * move_x

        if direction.lengthSquared() > 0:
            direction.normalize()
            speed = self.move_speed * (self.sprint_multiplier if self.shift_down else 1)
            self.root.setPos(self.root.getPos() + direction * speed * dt)

    def apply_gravity(self, dt):
        """Применяет гравитацию и приземление | Apply gravity and landing"""
        if not self.is_grounded:
            self.velocity_z += self.gravity * dt

        new_z = self.root.getZ() + self.velocity_z * dt

        if new_z <= 0:
            new_z = 0
            self.velocity_z = 0
            self.is_grounded = True

        self.root.setZ(new_z)

    def clamp_position(self):
        """Ограничение перемещения по границам карты | Constrain movement within map boundaries"""
        limit = self.map_size
        self.root.setX(max(-limit, min(limit, self.root.getX())))
        self.root.setY(max(-limit, min(limit, self.root.getY())))

    def resolve_animation(self, on_spell_hit=None):
        """Разрешение состояний анимации: заклинание, прыжок, бег | Resolve animation states: spell, jump, run"""
        if self.actor is None:
            return

        if self.spell_state:
            if self.spell_state == "loop" and (self.keys["w"] or self.keys["a"] or self.keys["s"] or self.keys["d"]):
                self.actor.stop()
                self.current_anim = None
                self.actor.play("Spell_Simple_Exit")
                self.spell_state = "exit"

            if self.spell_state == "enter":
                ctrl = self.actor.getAnimControl("Spell_Simple_Enter")
                if not ctrl or not ctrl.isPlaying():
                    self.actor.stop()
                    self.actor.play("Spell_Simple_Shoot")
                    self.spell_state = "shoot"
                    if on_spell_hit:
                        on_spell_hit()
            elif self.spell_state == "shoot":
                ctrl = self.actor.getAnimControl("Spell_Simple_Shoot")
                if not ctrl or not ctrl.isPlaying():
                    self.actor.stop()
                    self.actor.loop("Spell_Simple_Loop")
                    self.spell_state = "loop"
                    self.current_anim = None
            elif self.spell_state == "exit":
                ctrl = self.actor.getAnimControl("Spell_Simple_Exit")
                if not ctrl or not ctrl.isPlaying():
                    self.spell_state = None
                    self.current_anim = None

            if self.spell_state:
                return

        if self.oneshot_anim:
            ctrl = self.actor.getAnimControl(self.oneshot_anim)
            if ctrl and ctrl.isPlaying():
                if self.jump_state == "start" and self.is_grounded:
                    self.actor.stop()
                    self.actor.play("Jump_Land")
                    self.jump_state = "land"
                    self.oneshot_anim = None
                else:
                    return
            self.oneshot_anim = None

        if self.jump_state == "start":
            ctrl = self.actor.getAnimControl("Jump_Start")
            if not ctrl or not ctrl.isPlaying():
                self.actor.stop()
                self.actor.loop("Jump_Loop")
                self.jump_state = "loop"

        if self.jump_state == "loop" and self.is_grounded:
            self.actor.stop()
            self.actor.play("Jump_Land")
            self.jump_state = "land"

        if self.jump_state == "land":
            ctrl = self.actor.getAnimControl("Jump_Land")
            if not ctrl or not ctrl.isPlaying():
                self.jump_state = None

        if self.jump_state is None and self.oneshot_anim is None:
            moving = self.keys["w"] or self.keys["a"] or self.keys["s"] or self.keys["d"]
            sprinting = moving and self.shift_down
            target = "Sprint_Loop" if sprinting else ("Walk_Loop" if moving else "Idle_Loop")
            if target != self.current_anim:
                self.actor.stop()
                self.actor.loop(target)
                self.current_anim = target