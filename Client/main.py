from ursina import *
from random import *
from ursinanetworking import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina import shaders
import random

BLOCKS = [
    "Grass",
    "Stone",
    "Dirt",
    "Tnt"
]

packs = open("settings/packs.txt","r")
pack = packs.read()

App = Ursina()

Client = UrsinaNetworkingClient("26.89.203.102", 25565)
Easy = EasyUrsinaNetworkingClient(Client)

window.exit_button.visible = False
window.fps_counter.enabled = False
window.show_ursina_splash = True

Ad = Audio("")
sky = Sky()

Blocks = {}
Players = {}
PlayersTargetPos = {}

SelfId = -1

@Client.event
def Explode(Position):
    E = Explosion(Position)

@Client.event
def GetId(Id):
    global SelfId
    SelfId = Id
    print(f"My ID is : {SelfId}")

@Easy.event
def onReplicatedVariableCreated(variable):
    global Client
    variable_name = variable.name
    variable_type = variable.content["type"]
    if variable_type == "block":
        block_type = variable.content["block_type"]
        if block_type == "Grass": new_block = Grass()
        elif block_type == "Stone": new_block = Stone()
        elif block_type == "Dirt": new_block = Dirt()
        elif block_type == "Tnt": new_block = Tnt()
        else:
            print("Block not found.")
            return

        new_block.name = variable_name
        new_block.position = variable.content["position"]
        new_block.client = Client
        Blocks[variable_name] = new_block
        if variable.content["investigator"] == "client":
            Ad.clip = new_block.sound
            Ad.pitch = uniform(0.8, 1.2)
            Ad.play()
    elif variable_type == "player":
        PlayersTargetPos[variable_name] = Vec3(0, 0, 0)
        Players[variable_name] = PlayerRepresentation()
        if SelfId == int(variable.content["id"]):
            Players[variable_name].color = color.red
            Players[variable_name].visible = False

@Easy.event
def onReplicatedVariableUpdated(variable):
    PlayersTargetPos[variable.name] = variable.content["position"]

@Easy.event
def onReplicatedVariableRemoved(variable):
    variable_name = variable.name
    variable_type = variable.content["type"]
    if variable_type == "block":
        Ad.clip = Blocks[variable_name].break_sound if Blocks[variable_name].break_sound != None else Blocks[variable_name].sound
        Ad.pitch = uniform(0.5, 0.9)
        Ad.play()

        for i in range(randrange(2, 4)):
            BreakParticle(Blocks[variable_name].texture, Blocks[variable_name].position)

        destroy(Blocks[variable_name])
        del Blocks[variable_name]
    elif variable_type == "player":
        destroy(Players[variable_name])
        del Players[variable_name]

MAX = len(BLOCKS)
INDEX = 1
SELECTED_BLOCK = ""

Inventory = Text(text = "", origin = (-5, 0), background = False,color = color.black)

def updateHud():
    global SELECTED_BLOCK
    SELECTED_BLOCK = BLOCKS[INDEX % MAX]

    Ad.clip = "sounds/click1.ogg"
    Ad.play()

    txt = "Inventory: \n"
    for b in BLOCKS:
        if b == SELECTED_BLOCK:
            txt += f"> {b}\n"
        else:
            txt += f"{b}\n"
    Inventory.text = txt

updateHud()

def input(key):

    global INDEX, SELECTED_BLOCK

    if key == "right mouse down":
        A = raycast(player.position + (0, 2, 0), camera.forward, distance = 8, traverse_target = scene)
        E = A.entity
        if E:
            pos = E.position + mouse.normal
            Client.send_message("request_place_block", { "block_type" : SELECTED_BLOCK, "position" : tuple(pos)})

    if key == "left mouse down":
        A = raycast(player.position + (0, 2, 0), camera.forward, distance = 8, traverse_target = scene)
        E = A.entity
        if E and E.breakable:
            Client.send_message("request_destroy_block", E.name)

    if key == "scroll up":
        INDEX -= 1
        updateHud()

    elif key == "scroll down":
        INDEX += 1
        updateHud()


    Client.send_message("MyPosition", tuple(player.position + (0, 1, 0)))

def update():
    global INDEX

    if player.position[1] < -5:
        player.position = (randrange(0, 15), 10, randrange(0, 15))

    for p in Players:
        try:
            Players[p].position += (Vec3(PlayersTargetPos[p]) - Players[p].position) / 25
        except Exception as e: print(e)

    if held_keys["shift"]:
        sprint()
    else:
        normal()
    
    if held_keys["c"]:
        zoom()
    
    Easy.process_net_events()

class PlayerRepresentation(Entity):
    def __init__(self, position = (5,5,5)):
        super().__init__(
            parent = scene,
            position = position,
            model = "cube",
            texture = "white_cube",
            origin_y = .5,
            color = color.white,
            highlight_color = color.white,
            scale = (0.5, 1, 0.5)
        )

class BreakParticle(Entity):

    def __init__(self, texture, position = (0,0,0)):
        super().__init__(
            position = position,
            model = "models/block",
            texture = texture,
            origin_y = .5,
            billboard = True,
            color = color.white,
            highlight_color = color.white,
            scale = (
                uniform(0.10, 0.20),
                uniform(0.10, 0.20),
                uniform(0.0, 0.0)
            ),
            shader = shaders.lit_with_shadows_shader
        )

        self.s = 0.05
        self.velx = uniform(-self.s, self.s)
        self.vely = uniform(0, 0.1)
        self.velz = uniform(-self.s, self.s)
        self.animate_scale(0, uniform(0.75, 1))
        destroy(self, 1)
    
    def update(self):
        r = raycast(self.position , (0, -1, 0), ignore=(self,), distance=0.1, debug=False).hit
        if not r:
            self.position += (self.velx, self.vely, self.velz)
            self.vely -= 0.009

class Explosion(Entity):
    def __init__(self, position) -> None:
        super().__init__(
            model = "quad",
            texture = f"assets/{pack}/explosion",
            origin_y = -0.25,
            scale = (0, 0, 0),
            billboard = True,
            position = position
        )
        self.ad = Audio("sounds/explosion.mp3")
        self.ad.volume = 2
        self.ad.play()

        self.animate_scale((3, 3, 3), 1)
        self.animate_color(color.rgba(0, 0, 0, 0), 1)

        destroy(self, 1)

BLOCKS_PARENT = Entity()

class Block(Button):
    def __init__(self, position = (0,0,0)):
        super().__init__(
            parent = BLOCKS_PARENT,
            position = position,
            model = "models/block",
            origin_y = .5,
            color = color.white,
            highlight_color = color.white,
            scale = .5,
            shader = shaders.lit_with_shadows_shader
        )
        self.name = "unnamed_block"
        self.sound = None
        self.break_sound = None
        self.client = None
        self.breakable = True

class Grass(Block):
    def __init__(self, position = (0, 0, 0)):
        super().__init__(position)
        self.texture = f"assets/{pack}/grass_block.png"
        self.sound = "sounds/grass1.ogg"

class Stone(Block):
    def __init__(self, position = (0, 0, 0)):
        super().__init__(position)
        self.texture = f"assets/{pack}/stone_block.png"
        self.sound = "sounds/stone1.ogg"

class Dirt(Block):
    def __init__(self, position = (0, 0, 0)):
        super().__init__(position)
        self.texture = f"assets/{pack}/dirt_block.png"
        self.sound = "sounds/dirt1.ogg"

class Tnt(Block):
    def __init__(self, position = (0, 0, 0)):
        super().__init__(position)
        self.texture = f"assets/{pack}/tnt_block.png"
        self.sound = "sounds/grass1.ogg"
        self.i = 0
        self.s = 0
        self.breakable = False

    def update(self):
        self.scale = (self.s, self.s, self.s)
        self.s = 0.5 + math.fabs(math.sin(self.i) * 0.05)
        self.i += 0.5

def sprint():
    player.speed = 10
    camera.fov =  150

def zoom():
    camera.fov = 20
    player.mouse_sensitivity = (30, 30)

def normal():
    player.speed = 5
    camera.fov = 130
    player.mouse_sensitivity = (100, 100)

player = FirstPersonController()
player.gravity = 0.6
player.jump_height = 1.1
player.jump_duration = 0.28
player.scale = 0.9
player.mouse_sensitivity = (100, 100)
player.x = random.randint(5,15)
player.z = random.randint(5,15)
player.y = 10

App.run()