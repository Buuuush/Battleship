import socket
import threading
import random
import string

HOST = "127.0.0.1"
PORT = 28282
nb_joueur = 0
players = []
current_games = {}
data_players = {}

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

    try:
        client.send((f"Player {numero_player}").encode())
        print(f"Player {numero_player} online")
        while True:
            data = client.recv(1024)
            if not data:
                break
            data = data.decode()

            if data == 'Create':
                game = join_game()
                data = f"Code {game}"
                print(f"New game created : {game}")
                current_games.update({game: {"host": client, "players": [client], "started": False}})
                if client not in data_players:
                    data_players[client] = {"id": "Unknown", "game": game}
                else:
                    data_players[client]["game"] = game

            if " " in data:
                mode = data.split(" ")
                
                if mode[0] == 'Join' and len(mode) > 1:
                    print(f"[DEBUG] Commande Join recue pour la partie: {mode[1]}")
                    if mode[1] in current_games:
                        if len(current_games[mode[1]]["players"]) >= 2 and client not in current_games[mode[1]]["players"]:
                            print(f"[DEBUG] Partie {mode[1]} pleine (deja 2 joueurs)")
                            data = "GAME_FULL"
                        else:
                            if client not in current_games[mode[1]]["players"]:
                                current_games[mode[1]]["players"].append(client)
                                print(f"[DEBUG] Player {numero_player} ajoute a la partie {mode[1]}")
                            
                            if client not in data_players:
                                data_players[client] = {"id": f"Player_{numero_player}", "game": mode[1]}
                            else:
                                data_players[client]["game"] = mode[1]

                            all_players_in_game = current_games[mode[1]]["players"]
                            list_ids = [data_players.get(p, {"id": "Unknown"})["id"] for p in all_players_in_game]
                            players_msg = f"PLAYERS_LIST {','.join(list_ids)}"
                            
                            print(f"[DEBUG] Diffusion de la liste des joueurs : {players_msg}")
                            for p in all_players_in_game:
                                try:
                                    p.sendall(players_msg.encode())
                                except:
                                    pass
                            
                            data = f"JOIN_OK"
                    else:
                        print(f"[DEBUG] Partie introuvable: {mode[1]}")

                if mode[0] == 'ID' and len(mode) > 1:
                    already_exist = False
                    for player in data_players.values():
                        if player["id"] == mode[1]:
                            already_exist = True
                            break

                    if not already_exist:
                        data = "ID_g"
                        data_players.update({client: {"id": mode[1], "game": ''}})
                    else:
                        data = "ID_b"

                if mode[0] == 'START' and len(mode) > 1:
                    if mode[1] in current_games:
                        current_games[mode[1]]["started"] = True

            if isinstance(data, str):
                data = data.encode()
            client.sendall(data)
            
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