import socket
import threading
import random
import string
import ast

HOST = "127.0.0.1"
PORT = 28282
nb_joueur = 0
players = []
current_games = {}
data_players = {}
grids = {}

print("-----------------------------------------")
print("|                                       |")
print("|               Serveur prêt            |")
print("|                                       |")
print("-----------------------------------------")


def handle_client(client, lock):
    global nb_joueur
    global players
    global current_games
    global data_players
    global grids

    numero_player = random.randint(0, 100)
    with lock:
        while numero_player in players:
            numero_player = random.randint(0, 10)
        players.append(numero_player)

    def clrm():
        try:
            client.close()
            print(f"Joueur {numero_player} déconnecté")
            with lock:
                if numero_player in players:
                    nb_joueur -= 1
                    players.remove(numero_player)
        except:
            pass

    def get_boat_coords(name, boat):
        x, y, orientation = boat
        if "three" in name:
            size = 3
        elif "two" in name:
            size = 2
        else:
            size = 1

        coords = []

        for i in range(size):
            if orientation == "n":
                coords.append((x, y - i))
            elif orientation == "s":
                coords.append((x, y + i))
            elif orientation == "e":
                coords.append((x + i, y))
            elif orientation == "o":
                coords.append((x - i, y))

        return coords
    
    try:
        client.sendall(f"Player {numero_player}\n".encode())
        print(f"Player {numero_player} online")
        while True:
            data = client.recv(1024)
            if not data:
                break
            data = data.decode()
            print(data)

            if data == 'Create':
                game = join_game()
                print(f"New game created : {game}")

                current_games[game] = {
                    "host": client,
                    "players": [client],
                    "started": False
                }

                data_players[client] = {"id": "Unknown", "game": game}
                client.sendall(f"Code {game}\n".encode())
                continue

            if data.startswith("GRID"):
                if client not in data_players or data_players[client]["game"] == "":
                    continue

                game = data_players[client]["game"]
                grid_data = data.split("GRID ", 1)[1]
                if "grids" not in current_games[game]:
                    current_games[game]["grids"] = {}

                current_games[game]["grids"][client] = grid_data
                if len(current_games[game]["grids"]) == 2:
                    print("Les deux joueurs sont prêts")

                    game_players = current_games[game]["players"]
                    turn = random.choice(game_players)
                    current_games[game]["turn"] = turn

                    for p in game_players:
                        p.sendall("GAME_START\n".encode())
                    turn.sendall("YOUR_TURN\n".encode())

                continue
            if " " in data:
                mode = data.split(" ", 2)
                
                if mode[0] == 'Join' and len(mode) > 1:
                    if mode[1] in current_games:
                        if len(current_games[mode[1]]["players"]) >= 2 and client not in current_games[mode[1]]["players"]:
                            data = "GAME_FULL"
                        else:
                            if client not in current_games[mode[1]]["players"]:
                                current_games[mode[1]]["players"].append(client)
                            if client not in data_players:
                                data_players[client] = {"id": f"Player_{numero_player}", "game": mode[1]}
                            else:
                                data_players[client]["game"] = mode[1]
                            all_players_in_game = current_games[mode[1]]["players"]
                            list_ids = [data_players.get(p, {"id": "Unknown"})["id"] for p in all_players_in_game]
                            players_msg = f"PLAYERS_LIST {','.join(list_ids)}\n"
                            
                            for p in all_players_in_game:
                                    p.sendall(players_msg.encode())
                            
                            data = "JOIN_OK\n"
                            client.sendall(data.encode())
                            continue

                    else:
                        client.sendall("GAME_NOT_FOUND\n".encode())
                        continue
                if client not in data_players or data_players[client]["game"] == "":
                    continue

                game = data_players[client]["game"]

                if mode[0] == 'ID' and len(mode) > 1:
                    already_exist = False
                    for player in data_players.values():
                        if player["id"] == mode[1]:
                            already_exist = True
                            break

                    if not already_exist:
                        data = "ID_g"
                        data_players.update({client: {"id": mode[1], "game": ''}})
                        client.sendall(data.encode())
                        continue

                    else:
                        data = "ID_b\n"
                        client.sendall(data.encode())
                        continue
                if mode[0] == 'START' and len(mode) > 1:
                    if mode[1] in current_games:
                            current_games[mode[1]]["started"] = True
                            # A remettre lors de la phase production
                            
                            all_players_in_game = current_games[mode[1]]["players"]

                            for p in all_players_in_game:
                                p.sendall(f"START {mode[1]}\n".encode())
                    continue

                if mode[0] == "SHOOT" and len(mode) >= 3:

                    game = data_players[client]["game"]
                    game_data = current_games[game]

                    if game_data["turn"] != client:
                        client.sendall("NOT_YOUR_TURN\n".encode())
                        continue

                    game_players = game_data["players"]
                    enemy = game_players[0] if game_players[1] == client else game_players[1]

                    # INIT hits une seule fois
                    if "hits" not in game_data:
                        game_data["hits"] = {}
                        for p in game_players:
                            game_data["hits"][p] = 0

                    x = int(mode[1])
                    y = int(mode[2])

                    grid = ast.literal_eval(game_data["grids"][enemy])

                    hit = False


                    for name, boat in grid.items():
                        coords = get_boat_coords(name, boat)
                        if (x, y) in coords:
                            hit = True
                            break


                    if hit:
                        client.sendall("HIT\n".encode())
                        enemy.sendall(f"HIT_BY {x} {y}\n".encode())

                        game_data["hits"][client] += 1

                        if game_data["hits"][client] >= 10:
                            client.sendall("WIN\n".encode())
                            enemy.sendall("LOSE\n".encode())
                            continue
                    else:
                        client.sendall("MISS\n".encode())
                        enemy.sendall(f"MISS_BY {x} {y}\n".encode())

                    game_data["turn"] = enemy
                    enemy.sendall("YOUR_TURN\n".encode())

                

        clrm()

    except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
        clrm()

def join_game():
    def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))
    
    return id_generator()
    
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen()
lock = threading.Lock()

while True:
    client, addr = s.accept()
    threading.Thread(target=handle_client, args=(client, lock)).start()
    with lock:
        nb_joueur += 1

# grids
grid_j1 = {"three_boat": (0,0,"n"), "two_boat1": (0,0,"n"), "two_boat2": (0,0,"n"),
           "boat1": (0,0,"n"), "boat2": (0,0,"n"), "boat3": (0,0,"n")}

grid_j2 = {"three_boat": (0,0,"n"), "two_boat1": (0,0,"n"), "two_boat2": (0,0,"n"),
           "boat1": (0,0,"n"), "boat2": (0,0,"n"), "boat3": (0,0,"n")}