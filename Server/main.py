from struct import pack, unpack
from threading import Thread
from socket import socket, AF_INET, SOCK_STREAM
import json

PORT = 0x4BAE
games = []

class PlayerLeftException(Exception):
    pass

class Player():
#---------------------------------------------------------------
    def __sendJsonrpc(self, method: str = None, params: list|dict = None, error: list|dict = None):
        jsonRPC = [{"jsonrpc":"2.0"}]
        if method is not None:
            jsonRPC.append({"method":method})
        if params is not None:
            jsonRPC.append({"params":params})
        else:
            jsonRPC.append({"params":[]})
        if error is not None:
            jsonRPC.append({"error":error})
        messageEncoded = json.loads(jsonRPC).encode(encoding="utf-8")
        self._sock.send(pack("!i",len(messageEncoded)))
        self._sock.send(messageEncoded)

    def __sendAndReceiveJsonrpc(self,id: int, method: str = None, params: list|dict = None, error: list|dict = None):
        jsonRPC = [{"jsonrpc":"2.0"}]
        jsonRPC.append({"id":id})
        if method is not None:
            jsonRPC.append({"method":method})
        if params is not None:
            jsonRPC.append({"params":params})
        else:
            jsonRPC.append({"params":[]})
        if error is not None:
            jsonRPC.append({"error":params})
        # encode
        messageEncoded = json.loads(jsonRPC).encode(encoding="utf-8")
        # send
        self._sock.send(pack("!i",len(messageEncoded)))
        self._sock.send(messageEncoded)
        # prepare receive
        binaryLen = self._sock.recv(4)
        len = unpack("!i",binaryLen)[0]
        # receive
        data = self._sock.recv(len).decode('utf-8')
        #return response
        return data

    def __receiveJsonrpc(self) -> list:
        # prepare receive
        binaryLen = self._sock.recv(4)
        len = unpack("!i",binaryLen)[0]
        # receive
        data: str = self._sock.recv(len).decode('utf-8')
        jsonrpc = json.loads(data)
        #return response
        return jsonrpc
#---------------------------------------------------------------

    def __init__(self,num: int,sock: socket):
        self._num = num
        self._sock = sock
        #self._sock.send(pack("!i",num))
        self.__sendJsonrpc(method="player_number",params={"player_number":num})

    def get_choice(self):
        self.__sendJsonrpc(method="play")
        jsonObj = self.__receiveJsonrpc()
        try:
            method = jsonObj["method"]
            caseStr = jsonObj["params"]["case"]
            id = jsonObj["id"]
        except Exception:
            raise Exception # malformed request
        if method != "process_move":
            raise Exception # wrong method
        try:
            case = int(caseStr)
        except ValueError:
            raise Exception # invalid value type (not an int)
        return case,id

    def get_num(self):
        return self._num

    def end_game(self, code):
        if code==1:
            self.__sendJsonrpc(method="end_game",params=[{"winner":True,"player":1}])
        elif code==1:
            self.__sendJsonrpc(method="end_game",params=[{"winner":True,"player":2}])
        elif code==1:
            self.__sendJsonrpc(method="end_game",params=[{"winner":False,"player":None}])

class Game(Thread):
    def __init__(self,player1: Player, player2: Player):
        Thread.__init__(self)
        #link to player 1
        self._player1 = player1
        #link to player 2
        self._player2 = player2
        #who plays next ?
        self._turn = 1
        #current status of the game
        #0 = going
        #1 = victory player 1
        #2 = victory player 2
        #3 = tie
        self._status = 0
        self._grille = [[" "," "," "],[" "," "," "],[" "," "," "]]

    def get_status(self):
        return self._status

    # à appeler à chaque modification de la grille
    # return 0 = game goes on
    # return 1 = victory player 1
    # return 2 = victory player 2
    # return 3 = tie
    def __check(self):
        #on verifie les colonnes
        for i in range(0,3):
            if(self._grille[i][0]==self._grille[i][1]==self._grille[i][2]!=" "):
                return self._grille[i][0]

        #on verifie les lignes
        for i in range(0,3):
            if(self._grille[0][i]==self._grille[1][i]==self._grille[2][i]!=" "):
                return self._grille[0][i]

        #on verifie les diagonales
        if(self._grille[0][0]==self._grille[1][1]==self._grille[2][2]!=" "):
            return self._grille[1][1]

        if(self._grille[0][2]==self._grille[1][1]==self._grille[2][0]!=" "):
            return self._grille[1][1]

        #on verifie qu'il reste des cases a reself._grilleplir
        for i in range(0,3):
            for j in range(0,3):
                if(self._grille[i][j]==" "):
                    return 0
        return 3

    def __switch_player(self):
        if self._turn==1:
            self._turn=2
        else:
            self._turn=1

    def __convert_case(self,val):
        if val==1:
            return "X"
        elif val==2:
            return "O"
        else:
            return str(val)


    # create a render of the grid
    # "-----------"
    # "|  |   |  |"
    # "|  |   |  |"
    # "|  |   |  |"
    # "-----------"
    def __drawGrid(self):
        grille = "-------"+"\n"
        for i in range(0,3):
            grille += "|"+self.__convert_case(self._grille[i][0])+"|"+self.__convert_case(self._grille[i][1])+"|"+self.__convert_case(self._grille[i][2])+"|\n"
            grille += "-------\n"
        return grille

    def run(self):
        try:
            last_player = None
            # while the game hasn't ended
            while self._status == 0:
                # get the playing player's instance
                #
                if self._turn == 1:
                    current_player = self._player1
                elif self._turn == 2:
                    current_player = self._player2

                if current_player != last_player:
                    current_player.__sendJsonrpc(method="update_grid",params=[{"grid":self._grille}])

                # get the player choice (the case)
                choice,id = current_player.get_choice()
                if(not(-1<choice<9)):
                    current_player.__sendJsonrpc(error=[{"code":1},{"message":"Value out of bounds"}])
                    continue
                # process this move
                x=choice%3
                y=int((choice-x)/3)
                # if valid then:
                if(self._grille[y][x]==' '):
                    # set the case
                    self._grille[y][x]=current_player.get_num()
                    self._status = self.__check()
                    # if game wasn't ended with this move
                    if(self._status==0):
                        # other player plays next
                        self.__switch_player()
                        # show updated grid
                        current_player.__sendJsonrpc(method="update_grid",params=[{"grid":self._grille}])
                        # and a message
                        current_player.__sendJsonrpc(method="next_player")
                # if not valid then:
                else:
                    # show error message
                    current_player.__sendJsonrpc(error=[{"code":2},{"message":"Position already taken"}])
                    # player will play again the playing player wasn't modified

            # final grid state
            self._player1.__sendJsonrpc(method="update_grid",params=[{"grid":self._grille}])
            self._player2.__sendJsonrpc(method="update_grid",params=[{"grid":self._grille}])
            if self._status == 1:
                self._player1.end_game(1)
                self._player2.end_game(1)
            elif self._status == 2:
                self._player1.end_game(2)
                self._player2.end_game(2)
            elif self._status == 3:
                self._player1.end_game(3)
                self._player2.end_game(3)
        # if a plyer left mid-game
        except PlayerLeftException:
            # using try because the one who left will raise errors (and I did not bother to search who is still there)
            try:
                self._player1.__sendJsonrpc(method="player_left")
            except ConnectionError:
                pass
            try:
                self._player1.__sendJsonrpc(method="player_left")
            except ConnectionError:
                pass
        # flag for deletion
        self._status = 10
        return


if __name__ == '__main__':
    with socket(AF_INET, SOCK_STREAM) as sock_listen:
        sock_listen.bind(('', PORT))
        sock_listen.listen(5)
        print(f"Listening on port {PORT}")
        tmp_players = []
        while True:
            sock_service, client_addr = sock_listen.accept()

            player = Player(len(tmp_players)+1,sock_service)
            player.__sendJsonrpc(method="wait")
            tmp_players.append(player)
            if len(tmp_players) == 2:
                game = Game(tmp_players[0],tmp_players[1])
                games.append(game)
                game.start()
                tmp_players = []
            games = [game for game in games if not game.get_status()==10]
