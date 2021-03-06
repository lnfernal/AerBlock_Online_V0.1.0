#Made by Aermoss Yusuf Rençber
from asyncio.tasks import sleep
from time import *
from ursinanetworking import *
from opensimplex import OpenSimplex
from ursina import Vec3, distance

print("Hello from the server !")

Server = UrsinaNetworkingServer("26.89.203.102", 25565)
Easy = EasyUrsinaNetworkingServer(Server)
Blocks = {}

def Explosion(position):
    Server.broadcast("Explode", position)
    sleep(1)
    to_destroy = []
    for x in Blocks:
        a = (Blocks[x]["position"])
        b = (position)
        if distance(Vec3(a), Vec3(b)) < 2:
            to_destroy.append(x)
    for x in to_destroy:
        destroy_block(x)

def destroy_block(Block_name):
    del Blocks[Block_name]
    Easy.remove_replicated_variable_by_name(Block_name)

i = 0
def spawn_block(block_type, position, investigator = "client"):
    global i
    block_name = f"blocks_{i}"
    Easy.create_replicated_variable(
        block_name,
        { "type" : "block", "block_type" : block_type, "position" : position, "investigator" : investigator}
    )
    
    if block_type == "Tnt":
        threading.Thread(target = Explosion, args=(position,)).start()

    Blocks[block_name] = {
        "name" : block_name,
        "position" : position
    }
    i += 1

@Server.event
def onClientConnected(Client):
    Easy.create_replicated_variable(
        f"player_{Client.id}",
        { "type" : "player", "id" : Client.id, "position" : (0, 0, 0) }
    )
    print(f"{Client} connected !")
    Client.send_message("GetId", Client.id)

@Server.event
def onClientDisconnected(Client):
    Easy.remove_replicated_variable_by_name(f"player_{Client.id}")

@Server.event
def request_destroy_block(Client, Block_name):
    destroy_block(Block_name)

@Server.event
def request_place_block(Client, Content):
    spawn_block(Content["block_type"], Content["position"])

@Server.event
def MyPosition(Client, NewPos):
    Easy.update_replicated_variable_by_name(f"player_{Client.id}", "position", NewPos)

tmp = OpenSimplex()
for x in range(24):
    for z in range(24):

        l = round(tmp.noise2d(x = x / 5, y = z / 5))

        if l == -1: spawn_block("Stone", (x, l, z), investigator = "server")
        if l == 0: spawn_block("Grass", (x, l, z), investigator = "server")
        if l == 1: spawn_block("Grass", (x, l, z), investigator = "server")

while True:
    Easy.process_net_events()
