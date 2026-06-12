import socket
import threading
import random
import string
import ast
import json
import time

# Chargement de la configuration
with open('config.json', 'r') as f:
    config = json.load(f)

HOST = config.get("host", "127.0.0.1")
PORT = config.get("port", 28282)
BOATS_CONFIG = config.get("boats", {})
TOTAL_BOATS = sum(info["count"] for info in BOATS_CONFIG.values())
MAX_HITS = sum(info["length"] * info["count"] for info in BOATS_CONFIG.values())

current_games = {}   # Salon -> Données du jeu
active_players = {}  # Pseudo -> Client Socket (Joueurs connectés)
disconnected_players = {} # Pseudo -> { "game": code, "expiry": timestamp, "data": ... }

print("-----------------------------------------")
print("|                                       |")
print("|       Serveur Bataille Navale Pro      |")
print(f"|  Touches pour gagner : {MAX_HITS:<15}|")
print("-----------------------------------------")

def nettoyer_deconnexions():
    """Supprime les sessions expirées après les 30 secondes de grâce."""
    while True:
        time.sleep(5)
        now = time.time()
        to_delete = []
        for pseudo, info in list(disconnected_players.items()):
            if now > info["expiry"]:
                to_delete.append(pseudo)
                game = info["game"]
                # Si le joueur ne revient pas, on ferme la partie associée
                if game in current_games:
                    for p_sock in current_games[game]["players"]:
                        try:
                            p_sock.sendall("OPPONENT_TIMEOUT_DISCONNECTED\n".encode())
                        except:
                            pass
                    del current_games[game]
        for pseudo in to_delete:
            if pseudo in disconnected_players:
                del disconnected_players[pseudo]

threading.Thread(target=nettoyer_deconnexions, daemon=True).start()

def get_boat_coords(name, boat):
    x, y, orientation = boat
    base_name = "_".join(name.split("_")[:2])
    size = BOATS_CONFIG.get(base_name, {}).get("length", 1)
    coords = []
    for i in range(size):
        if orientation == "n": coords.append((x, y - i))
        elif orientation == "s": coords.append((x, y + i))
        elif orientation == "e": coords.append((x + i, y))
        elif orientation == "o": coords.append((x - i, y))
    return coords

def handle_client(client):
    global current_games, active_players, disconnected_players
    my_pseudo = None

    try:
        # 1. Étape d'authentification par pseudo
        while not my_pseudo:
            data = client.recv(1024)
            if not data: return
            msg = data.decode().strip()
            if msg.startswith("AUTH "):
                pseudo = msg.split(" ", 1)[1]
                if pseudo in active_players:
                    client.sendall("AUTH_ERR_ALREADY_CONNECTED\n".encode())
                else:
                    my_pseudo = pseudo
                    active_players[my_pseudo] = client
                    
                    # Vérifier si c'est une reconnexion
                    if my_pseudo in disconnected_players:
                        old_info = disconnected_players[my_pseudo]
                        game = old_info["game"]
                        del disconnected_players[my_pseudo]
                        
                        # Remplacement du socket dans la partie existante
                        game_data = current_games[game]
                        game_data["players"] = [client if p == old_info["socket"] else p for p in game_data["players"]]
                        if game_data.get("turn") == old_info["socket"]:
                            game_data["turn"] = client
                        
                        client.sendall(f"RECONNECT_OK {game}\n".encode())
                        
                        # Informer l'adversaire de son retour
                        enemy = game_data["players"][0] if game_data["players"][1] == client else game_data["players"][1]
                        enemy.sendall(f"CHAT Système: {my_pseudo} s'est reconnecté.\n".encode())
                        enemy.sendall("OPPONENT_BACK\n".encode())
                        
                        # Renvoyer l'état actuel pour reconstruire l'interface graphique du client
                        shots_taken = list(game_data["shots"].get(client, set()))
                        shots_received = list(game_data["shots"].get(enemy, set()))
                        
                        # Calcul des stats intermédiaires
                        hits_taken = game_data["hits"].get(client, 0)
                        miss_taken = len(shots_taken) - hits_taken
                        
                        client.sendall(f"RESTORE_STATE {game_data['grids'][client]} | {shots_taken} | {shots_received} | {game_data['turn'] == client}\n".encode())
                    else:
                        client.sendall("AUTH_OK\n".encode())

        # 2. Boucle principale de messages
        while True:
            data = client.recv(1024)
            if not data: break
            msg_list = data.decode().split("\n")
            
            for raw_msg in msg_list:
                msg = raw_msg.strip()
                if not msg: continue

                if msg == 'Create':
                    game = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
                    current_games[game] = {
                        "players": [client],
                        "pseudos": {client: my_pseudo},
                        "started": False,
                        "shots": {client: set()},
                        "hits": {client: 0},
                        "miss": {client: 0},
                        "boats_health": {},
                        "grids": {}
                    }
                    client.sendall(f"Code {game}\n".encode())
                    continue

                if msg.startswith("Join "):
                    target_game = msg.split(" ", 1)[1]
                    if target_game in current_games:
                        game_data = current_games[target_game]
                        if len(game_data["players"]) >= 2:
                            client.sendall("GAME_FULL\n".encode())
                        else:
                            game_data["players"].append(client)
                            game_data["pseudos"][client] = my_pseudo
                            game_data["shots"][client] = set()
                            game_data["hits"][client] = 0
                            game_data["miss"][client] = 0
                            
                            list_pseudos = [game_data["pseudos"][p] for p in game_data["players"]]
                            for p in game_data["players"]:
                                p.sendall(f"PLAYERS_LIST {','.join(list_pseudos)}\n".encode())
                            client.sendall("JOIN_OK\n".encode())
                    else:
                        client.sendall("GAME_NOT_FOUND\n".encode())
                    continue

                # Vérifications de sécurité pour les commandes en jeu
                if my_pseudo not in active_players: continue

                # Extraction de la partie courante
                current_game_code = None
                for code, g_data in current_games.items():
                    if client in g_data["players"]:
                        current_game_code = code
                        break
                
                if not current_game_code: continue
                game_data = current_games[current_game_code]

                if msg.startswith("START "):
                    game_data["started"] = True
                    for p in game_data["players"]:
                        p.sendall(f"START {current_game_code}\n".encode())
                    continue

                if msg.startswith("GRID "):
                    grid_content = msg.split("GRID ", 1)[1]
                    game_data["grids"][client] = grid_content
                    
                    if len(game_data["grids"]) == 2:
                        turn = random.choice(game_data["players"])
                        game_data["turn"] = turn
                        
                        for p in game_data["players"]:
                            game_data["boats_health"][p] = {}
                            p_grid = ast.literal_eval(game_data["grids"][p])
                            for b_id, b_info in p_grid.items():
                                game_data["boats_health"][p][b_id] = get_boat_coords(b_id, b_info)

                        for p in game_data["players"]: p.sendall("GAME_START\n".encode())
                        turn.sendall("YOUR_TURN\n".encode())
                    continue

                if msg.startswith("CHAT "):
                    chat_payload = msg.split("CHAT ", 1)[1]
                    for p in game_data["players"]:
                        p.sendall(f"CHAT {my_pseudo}: {chat_payload}\n".encode())
                    continue

                if msg.startswith("SHOOT "):
                    if game_data["turn"] != client:
                        client.sendall("NOT_YOUR_TURN\n".encode())
                        continue

                    _, x_str, y_str = msg.split()
                    x, y = int(x_str), int(y_str)

                    if (x, y) in game_data["shots"][client]:
                        client.sendall("ALREADY_SHOT\n".encode())
                        continue

                    game_data["shots"][client].add((x, y))
                    enemy = game_data["players"][0] if game_data["players"][1] == client else game_data["players"][1]
                    
                    hit = False
                    sunk_boat_id = None

                    for b_id, coords in game_data["boats_health"][enemy].items():
                        if (x, y) in coords:
                            hit = True
                            coords.remove((x, y))
                            if len(coords) == 0:
                                sunk_boat_id = b_id
                            break

                    if hit:
                        game_data["hits"][client] += 1
                        client.sendall(f"HIT {x} {y}\n".encode())
                        enemy.sendall(f"HIT_BY {x} {y}\n".encode())

                        if sunk_boat_id:
                            enemy_boats_alive = sum(1 for c in game_data["boats_health"][enemy].values() if len(c) > 0)
                            client.sendall(f"SUNK_ENEMY {sunk_boat_id} {enemy_boats_alive}\n".encode())
                            enemy.sendall(f"SUNK_YOU {sunk_boat_id}\n".encode())

                        if game_data["hits"][client] >= MAX_HITS:
                            # Calcul des statistiques de fin de match
                            for player_sock in game_data["players"]:
                                p_pseudo = game_data["pseudos"][player_sock]
                                t_shots = len(game_data["shots"][player_sock])
                                t_hits = game_data["hits"][player_sock]
                                t_miss = t_shots - t_hits
                                precision = int((t_hits / t_shots) * 100) if t_shots > 0 else 0
                                
                                # Trouver le navire ayant le plus de PV restants
                                max_hp = -1
                                best_boat = "Aucun"
                                for b_id, coords in game_data["boats_health"][player_sock].items():
                                    b_name = "_".join(b_id.split("_")[:2])
                                    orig_len = BOATS_CONFIG[b_name]["length"]
                                    rem_hp = len(coords)
                                    if rem_hp > max_hp and orig_len > 0:
                                        max_hp = rem_hp
                                        best_boat = b_id.split("_")[1]
                                
                                stats_msg = f"STATS {precision} {t_miss} Bateau_{best_boat}({max_hp}PV)\n"
                                player_sock.sendall(stats_msg.encode())

                            client.sendall("WIN\n".encode())
                            enemy.sendall("LOSE\n".encode())
                            continue
                    else:
                        game_data["miss"][client] += 1
                        client.sendall(f"MISS {x} {y}\n".encode())
                        enemy.sendall(f"MISS_BY {x} {y}\n".encode())

                    game_data["turn"] = enemy
                    enemy.sendall("YOUR_TURN\n".encode())

    except:
        pass
    finally:
        # Traitement de la déconnexion avec l'immunité des 30 secondes
        if my_pseudo:
            if my_pseudo in active_players:
                del active_players[my_pseudo]
            
            # Trouver si le joueur était engagé dans une partie
            for code, g_data in list(current_games.items()):
                if client in g_data["players"]:
                    print(f"📡 {my_pseudo} a perdu sa connexion. Rétention de session : 30s.")
                    disconnected_players[my_pseudo] = {
                        "game": code,
                        "socket": client,
                        "expiry": time.time() + 30.0
                    }
                    # Prévenir l'adversaire qu'il doit temporiser
                    for p in g_data["players"]:
                        if p != client:
                            try:
                                p.sendall("OPPONENT_TEMPORARY_DISCONNECTED\n".encode())
                                p.sendall(f"CHAT Système: {my_pseudo} a déco. Attente de 30s...\n".encode())
                            except: pass
                    break
        try: client.close()
        except: pass

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen()

while True:
    client_sock, _ = s.accept()
    threading.Thread(target=handle_client, args=(client_sock,), daemon=True).start()