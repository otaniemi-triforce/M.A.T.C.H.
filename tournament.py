import random
import math
import time
import mugenoperator as mo



WINNER1 = 1
WINNER2 = 2
POW2 = [0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]


class Tournament:
    def __init__(self):
        self.running = 0
        self.tournament_state = {"Div": 0, "Round": 1, "Match": 1, "Fight": [], "Order" : []}

    def is_running(self):
        return self.running
    
    # Update the state of the running tournament
    def __update_tournament_state(self, id, value):
        try:
            if self.running:
                self.tournament_state[id] = value
        except KeyError:
            print("Incorrect key")
            
    def get_state(self, id):
        try:
            if self.running:
                return self.tournament_state[id]
        except KeyError:
            print("Incorrect key")

    # Prints out the ranking of the given division
    def rankings(self, players, division):
        print("Rankings being generated for: " + str(division + 1))
        count = 12
        position = 1
        message = ("---------\n")
        message += ("Division " + str(division + 1) + " finished!\n")
        message += ("Rankings:\n---------\n")
        while(count):
            for player in players:
                if player["Rank"][division] == count:
                    message += str(position) + '. ' + player["Name"] + ' - made it to round ' + str(player["Rank"][division]) + "\n"
                    position += 1
            count -= 1
        return message

    def final_rankings(self, players, div):
        score = []
        print("Final rankings")
        tmp = 0
        for player in players:
            score.append(0)
            for i in range(div):
                score[tmp] += player["Rank"][i]
            tmp += 1
        count = 10 * div
        position = 1
        message = "FINAL STANDINGS:\n----------------\n"
        while(count):
            for i in range(len(players)):
                if score[i] == count:
                    rank = [str(i) for i in players[i]["Rank"]]
                    message += str(position) + '. ' + players[i]["Name"] + ' - Total score: ' + str(score[i]) + "  Division scores: " + ','.join(rank) + "\n"
                    position += 1
            count -= 1
        return message

    def player_order(self, order):
        message = "Player order for next round:"
        for i in order:
            message += players[i]["Name"] + "\n"
        return message

    def run_tournament(self, players, divisions, mugen):
        self.running = 1
        print("Tournament Thread starting!")
        self.__update_tournament_state("Div", 0)
        self.__update_tournament_state("Round", 1)
        self.__update_tournament_state("Match", 1)
        self.__update_tournament_state("Fight", "")
        self.__update_tournament_state("Order", [])
        for i in range(divisions):
            # Update state
            self.__update_tournament_state("Div", i)
            # Play division i
            self.tournament(players, i, mugen)
                
        self.__update_tournament_state("Div", divisions + 1)
        self.running = 0
        print ("TOURNAMENT THREAD FINISHED")
        
    # Play match function currently simulates a battle for the tournament system
    # This should be implemented by game control side of things.
    def play_match(self, player1, player2, division, mugen):
        self.__update_tournament_state("Fight", [[player1["Name"], player1["Characters"][division]],[player2["Name"], player2["Characters"][division]]])
        while(1):
            winner = -1
            mugen.scan()
            time.sleep(0.5)
            mugen.scan()
            time.sleep(0.5)
            print("DEAD OR ALIVE")
            if mugen.get_state() == mo.DEAD_STATE:
                print("Tournament: Mugen was dead from the get go, waiting for reset")
                mugen.reset(True)
                time.sleep(60)
            if mugen.get_state() == mo.LOADING_STATE:
                print("...mugen is still loading")
                time.sleep(30)
            else:
                print("MENU CHECK")
                if mugen.get_state() == mo.MENU_STATE:
                    mugen.scan()
                print("SELECT CHECK")
                if mugen.get_state() == mo.SELECT_STATE:
                    while mugen.get_queue_size(mo.PLAYER1) != 0 and mugen.get_queue_size(mo.PLAYER2) != 0:
                        mugen.scan()
                    print("TOURNAMENT: Insert chars")
                    print("CHAR ID1: " + str(player1["Characters"][division]))
                    print("CHAR ID2: " + str(player2["Characters"][division]))
                    mugen.add_character(player1["Characters"][division], mo.PLAYER1)
                    mugen.add_character(player2["Characters"][division], mo.PLAYER2)
                    print("Inserted, waiting for result.")
                    while(mugen.get_state != mo.DEAD_STATE):
                        winner = mugen.scan()
                        if(winner == -1):
                            pass
                        else:
                            break
                        time.sleep(2)
                    print("TOURNAMENT: Match finished")
                    # Ties are unacceptable
                    if (mugen.get_state() != mo.DEAD_STATE and winner > 0):
                        break
                    else:
                        print("Tournament: Mugen is dead, waiting for reset")
                        mugen.reset(True)
                        time.sleep(60)
        return winner
        
        
    def tournament(self, players, division, mugen):
        
        # Calculate the rounds needed based on finding the power of two bigger than and closest to number of players
        for r in range(len(POW2)):
            if POW2[r] >= len(players):
                rounds = r
                break
        print("ROUNDS NEEDED: " + str(rounds))
            
        order = [i for i in range(len(players))]
        random.shuffle(order)
        print("Seeded order: ")
        
        ranking = []
        
        #Play tournament
        while(order):
        
            # Play each round
            for round in range(1, rounds, 1):
                self.__update_tournament_state("Round", round)
                self.__update_tournament_state("Order", order)
                print("\n------\nROUND : " + str(round))
                # Play starting from the "bottom" of the order
                match = 0
                while(len(order) - 1 > match):
                    time.sleep(0.5)
                    print("\nMATCH :" + str(match + 1))
                    if len(order) - match > 1:
                        result = self.play_match(players[order[match]], players[order[match + 1]], division, mugen)
                        print("\nRESULT : " + str(result) + '.')
                        if result == WINNER1:
                            # Player 2 lost, mark the achieved rank in division to player rank data
                            players[order[match + 1]]["Rank"][division] = round
                            ranking.insert(0,order.pop(match + 1))
                            
                        if result == WINNER2:
                            # Player 1 lost, mark the achieved rank in division to player rank data
                            players[order[match]]["Rank"][division] = round
                            ranking.insert(0,order.pop(match))
                    match += 1
                    
                if len(order) == 1: 
                    print("WE GOT A CLEAR WINNER")
                    print(players[order[0]]["Name"])
                    # We have a winner
                    players[order[0]]["Rank"][division] = round + 1
                    ranking.insert(0,order.pop(0))
            
       
        return ranking
