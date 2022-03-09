from struct import pack, unpack
import struct
from threading import Thread
from socket import socket, AF_INET, SOCK_STREAM

PORT = 0x4BAE
games = []

class PlayerLeftException(Exception):
    pass

class Player():
    def __init__(self,num: int,sock: socket):
        self._num = num
        self._sock = sock
        self._sock.send(pack("!i",num))

    def show(self,string_to_display: str):
        self._sock.send(pack("!i",1))
        encoded_string = string_to_display.encode(encoding="utf-8")
        self._sock.send(pack("!i",len(encoded_string)))
        self._sock.send(encoded_string)

    def get_choice(self):
        self._sock.send(pack("!i",2))
        data = self._sock.recv(4)
        try:
            choice = unpack("!i",data)[0]
        except struct.error:
            raise PlayerLeftException
        return choice

    def get_num(self):
        return self._num

    def end_game(self):
        self._sock.send(pack("!i",3))

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
            # while the game hasn't ended
            while self._status == 0:
                # get the playing player's instance
                #
                if self._turn == 1:
                    current_player = self._player1
                elif self._turn == 2:
                    current_player = self._player2
                current_player.show(self.__drawGrid())
                # get the player choice (the case)
                choice = current_player.get_choice()
                if(not(-1<choice<9)):
                    current_player.show("Erreur, réessayez")
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
                        current_player.show(self.__drawGrid())
                        # and a message
                        current_player.show("Au tour de l'autre joueur")
                # if not valid then:
                else:
                    # show error message
                    current_player.show("Erreur, réessayez")
                    # player will play again the playing player wasn't modified
            # end of the game
            self._player1.show("Fin de la partie")
            self._player2.show("Fin de la partie")
            # final grid state
            self._player1.show(self.__drawGrid())
            self._player2.show(self.__drawGrid())
            if self._status == 1:
                self._player1.show("Victoire du joueur 1")
                self._player2.show("Victoire du joueur 1")
            elif self._status == 2:
                self._player1.show("Victoire du joueur 2")
                self._player2.show("Victoire du joueur 2")
            elif self._status == 3:
                self._player1.show("Egalité, pas vainqueur (ni de perdant)")
                self._player2.show("Egalité, pas vainqueur (ni de perdant)")
            self._player1.end_game()
            self._player2.end_game()
        # if a plyer left mid-game
        except PlayerLeftException:
            # using try because the one who left will raise errors (and I did not bother to search who is still there)
            try:
                self._player1.show("A player has left")
                self._player1.end_game()
            except ConnectionError:
                pass
            try:
                self._player2.show("A player has left")
                self._player2.end_game()
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
            player.show("En attente d'un autre joueur...")
            tmp_players.append(player)
            if len(tmp_players) == 2:
                game = Game(tmp_players[0],tmp_players[1])
                games.append(game)
                game.start()
                tmp_players = []
            games = [game for game in games if not game.get_status()==10]
