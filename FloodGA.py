#!/usr/bin/python

# Assistive Algorithms Assignment 8: Intelligent Tutoring Systems
# Starter Code by (c) 2020 Elaine Short: http://eshort.tech 
# Non Tkinter related code by (c) 2020 Peter Smiley

import tkinter as tk
import threading
import time
import argparse
from random import randrange, choice, random
import numpy as np
from queue import Queue 
import time
import math

BORDER=10
TEXT_H=150
TEXT_W=300

class GridGame:
    
    #builds a grid of a given width and height
    def __init__(self, width, height, size):

        # Variable to build board skeleton
        self.root = tk.Tk()
        self.c = tk.Canvas(self.root, width=width*size+4*BORDER+TEXT_W,
                               height=max(height*size+2*BORDER,TEXT_H+2*BORDER))
        self.gridsize = size
        self.c.pack()
        self.cells = {}
        self.edges = {}
        self.corners = {}
        self.centers = {}
        self.width = width
        self.height = height
        self.textbox = self.c.create_text(width*size+TEXT_W/2.+BORDER*2, BORDER+height*size/2., text="",width=TEXT_W,justify=tk.LEFT)

        # Variables to build FloodIt Game + Solve Algorithm
        self.board_colors = [[]]
        self.keylist = []
        self.board_size = self.height * self.width

        # Game State
        self.high_score = 0
        self.won = False
        self.generation = 1
        self.flood_size = 1
        self.first_run = True
        self.move_count = 0
        self.total_moves = 0
        self.flood_color = ""
        self.agent_number = 1

        # Variables that can be tuned to optimize performance
        self.population_size = 20
        self.mutation_rate = .05
        self.max_generations = 300

        
        # Builds board skeleton
        for i in range(0,height):
            for j in range(0,width):
                x,y = self.get_grid_corner(i,j)
                cell = {}
                cell["C"]=self.c.create_rectangle(x, y,
                                        x+self.gridsize, y+self.gridsize,
                                                      fill="#eeeeee",
                                                      outline="#ffffff")
                self.centers[cell["C"]]=[(i,j,"C")]

                edge_dirs = {
                    "N":(-1,0,"S",0,0,1,0),
                    "S":(1,0,"N",0,1,1,1),
                    "E":(0,1,"W",1,0,1,1),
                    "W":(0,-1,"E",0,0,0,1)}
                corner_dirs={
                    "NE":([(-1,0,"N"),(0,1,"E"),(-1,1,"NE")],"SW",1,0),
                    "NW":([(-1,0,"N"),(0,-1,"W"),(-1,-1,"NW")],"SE",0,0),
                    "SE":([(1,0,"S"),(0,1,"E"),(1,1,"SE")],"NW",1,1),
                    "SW":([(1,0,"S"),(0,-1,"W"),(1,-1,"SW")],"NE",0,1)}

                colors={"NE":"red",
                        "SW":"green",
                        "SE":"blue",
                        "NW":"yellow"}


                #add edges, making sure not to create edges that already exist
                for name,direction in edge_dirs.items():
                    neighbor_idx = (i+direction[0],j+direction[1])
                    nb_edge_dir = direction[2]
                    if not neighbor_idx in self.cells:
                        cell[name]=self.c.create_line(
                            x+self.gridsize*direction[3],
                            y+self.gridsize*direction[4],
                            x+self.gridsize*direction[5],
                            y+self.gridsize*direction[6],
                            width=2,
                            fill="grey")
                        self.edges[cell[name]]=[(i,j,nb_edge_dir)]
                        self.c.tag_raise(cell[name])
                    else:
                        cell[name]=self.cells[neighbor_idx][nb_edge_dir]
                        self.c.tag_raise(cell[name])
                        self.edges[cell[name]].append((i,j,nb_edge_dir))

                #add corners, invisibly small at first, making sure not to
                #add duplicates            
                for name,direction in corner_dirs.items():
                    neighbors = direction[0]
                    corner_to_cell_dir = direction[1]

                    found_nb = False
                    nb_idx = None
                    nb_dir = None
                    for neighbor in neighbors:
                        idx = (i+neighbor[0],j+neighbor[1])
                        if idx in self.cells:
                            found_nb = True
                            nb_idx = idx
                            nb_dir = neighbor[2]
                            break

    
                    if found_nb:
                        #which of the neighbor's corners do we want to grab?
                        nbs_corner = name
                        #reverse the direction we went to get to the neighbor
                        if "N" in nb_dir:
                            nbs_corner = nbs_corner.replace("N","S")
                        if "S" in nb_dir:
                            nbs_corner = nbs_corner.replace("S","N")
                        if "E" in nb_dir:
                            nbs_corner = nbs_corner.replace("E","W")
                        if "W" in nb_dir:
                            nbs_corner = nbs_corner.replace("W","E")    
                            
                        #grab that corner
                        cell[name]=self.cells[nb_idx][nbs_corner]
                        self.c.tag_raise(cell[name])
                        self.corners[cell[name]].append((i,j,corner_to_cell_dir))
                    else: #didn't find a neighbor; just make the corner
                        cx = x+self.gridsize*direction[2]
                        cy = y+self.gridsize*direction[3]
                        cell[name]=self.c.create_oval(cx-1,cy-1,
                                                             cx+1,cy+1,
                                                             fill="grey",
                                                          outline="grey")
                        self.corners[cell[name]]=[(i,j,corner_to_cell_dir)]
                        self.c.tag_raise(cell[name])

                #to see cell (i,j) for debug, uncomment the below line
                #self.c.create_text(x+20,y+20,text="{},{}".format(i,j))
                    
                self.cells[(i,j)]=cell

    def start(self):
        tk.mainloop()
        
    #returns (x,y) tuple of the corner of the grid cell (row,col)
    def get_grid_corner(self,row,col):
        return (BORDER+self.gridsize*col,BORDER+self.gridsize*row)
    
    def change_text(self, new_text):
        self.c.itemconfigure(self.textbox,text=new_text,justify=tk.LEFT)
    
    def get_cell_from_center(self, center_idx):
        i,j = self.centers[center_idx][0][0:2]
        return self.cells[(i,j)]

    def change_cell_color(self, idx, color):
        self.c.itemconfigure(idx,fill=color)

        #make sure edges are on top of fill:
        cell_info = self.get_cell_from_center(idx)

        edges = ["N","S","W","E"]
        for e in edges:
            self.c.tag_raise(cell_info[e])

    def check_win(self):
        if self.flood_size == self.board_size:
            if (self.won == False):
                self.change_text("Congratulations. You have won the game!")
                self.won = True
            else:
                if self.move_count < self.high_score:
                    self.high_score = self.move_count
            return True
        elif self.move_count == self.total_moves:
            self.change_text("You have lost the game.")
        return False 

    def mutate(self, child):
        possible_clicks = list(self.centers.keys())
        for i in range(len(child)):
            if random() < self.mutation_rate:
                # Will change click to a random click
                child[i] = choice(possible_clicks)
        return child
                
    def crossover(self, agent_A, agent_B):
        chop = randrange(0, self.total_moves)
        child = agent_A[:chop]
        b = agent_B[chop:]
        # Merge the parts from both agents
        for i in b:
            child.append(i)        
        child = self.mutate(child)
        return child

    # If the agent clicks the flood, it will find the non-flood tile that is closest and
    # click on that instead
    def transform_click_to_closest(self, xpos, ypos):
        already_checked = []
        q = Queue(maxsize = (self.width * self.height) * 1000)
        x = 0 
        y = 0
        
        q.put((xpos, ypos))
        already_checked.append((xpos, ypos))

        while (True):
            (x, y) = q.get()

            if self.part_of_flood[x, y] == False:
                return (x, y)               

            if (x != self.width - 1 and (x + 1, y) not in already_checked):
                q.put((x + 1, y))
                already_checked.append((x + 1, y))
            if (y != self.height - 1 and (x, y + 1) not in already_checked):
                q.put((x, y + 1))
                already_checked.append((x, y + 1))
            if (y != 0 and (x, y - 1) not in already_checked):
                q.put((x, y - 1))
                already_checked.append((x, y - 1))
            if (x != 0 and (x - 1, y) not in already_checked):
                q.put((x - 1, y))
                already_checked.append((x - 1, y))


    def population(self, new_agents):
        agents = []
        gen_pool = []
        next_gen = []
        first = True
        left_over_moves = 0

        best_agent = []
        best_agent_flood_size = 0

        if self.generation == 1:
            for i in range(self.population_size):
                agent = []
                for j in range(self.total_moves):
                    agent.append(choice(list(self.centers.keys())))
                agents.append(agent)
        else:
            agents = new_agents

        for agent in agents:
            for click in agent:
                self.handle_center_click(click)
                self.change_text(("Moves: ", self.move_count, " / ", self.total_moves, "\nGeneration = ", self.generation, "\nFlood Size = ", self.flood_size, "\nAgent #", self.agent_number))
                
                # Prints the best agents from each generation
                if first == True:
                    self.root.update()
                    time.sleep(.1)

                if self.check_win() == True:
                    left_over_moves = self.total_moves - self.move_count
                    break

            #Collect Info
            if self.flood_size > best_agent_flood_size:
                best_agent = agent
                best_agent_flood_size = self.flood_size
                if best_agent_flood_size > self.high_score and self.won == False:
                    self.high_score = best_agent_flood_size

                
            #rewards for block elimination
            fitness = (self.flood_size / 12) * (self.flood_size / 12)
            fitness *= 1 + (left_over_moves * 1.3)

            for i in range(int(fitness)):
                gen_pool.append(agent)


            #Reset board
            self.move_count = 0
            self.flood_size = 1
            self.agent_number += 1
            first = False
            left_over_moves = 0
            self.new_game() 

        print("high_score: ", self.high_score)

        #Make new population
        next_gen.append(best_agent)
        for i in range(1, self.population_size):
            agent_A = choice(gen_pool) 
            agent_B = choice(gen_pool) 
            child = self.crossover(agent_A, agent_B)
            next_gen.append(child)
        
        #Reset Game with new population
        self.generation += 1
        print ("Generation: ", self.generation, "\n\n")
        if (self.generation < self.max_generations):
            self.agent_number = 1
            self.population(next_gen)

    def handle_center_click(self, idx):
        (xpos, ypos, discard) = self.centers[idx][0]
        #clicked on a piece that is already part of the flood
        if (self.move_count > 0):
            if self.part_of_flood[xpos, ypos] == True:
                (xpos, ypos) = self.transform_click_to_closest(xpos, ypos)

        self.flood_color = self.board_colors[xpos][ypos]

        q = Queue(maxsize = (self.width * self.height))

        indices = np.where(self.part_of_flood == True) 
        x, y = indices[0], indices[1]
        for i in range(len(x)):
            q.put((x[i], y[i]))

        # Uses a queue to simulate recursion. Finds all chained connected colors
        while not q.empty():
            piece = q.get()
            if (not piece[0] == 0):
                if (not self.part_of_flood[piece[0] - 1, piece[1]]) and (self.board_colors[piece[0] - 1][piece[1]] == self.flood_color):
                    self.board_colors[piece[0] - 1][piece[1]] = self.flood_color
                    self.part_of_flood[piece[0] - 1, piece[1]] = True
                    q.put(((piece[0] - 1), piece[1]))
                    self.flood_size += 1

            if (not piece[0] == self.width - 1):
                if not self.part_of_flood[piece[0] + 1, piece[1]] and self.board_colors[piece[0] + 1][piece[1]] == self.flood_color:
                    self.board_colors[piece[0] + 1][piece[1]] = self.flood_color
                    self.part_of_flood[piece[0] + 1, piece[1]] = True
                    q.put(((piece[0] + 1), piece[1]))
                    self.flood_size += 1

            if (not piece[1] == 0):
                if not self.part_of_flood[piece[0], piece[1] - 1] and self.board_colors[piece[0]][piece[1] - 1] == self.flood_color:
                    self.board_colors[piece[0]][piece[1] - 1] = self.flood_color
                    self.part_of_flood[piece[0], piece[1] - 1] = True
                    q.put(((piece[0]), piece[1] - 1))
                    self.flood_size += 1

            if (not piece[1] == self.height - 1):
                if not self.part_of_flood[piece[0], piece[1] + 1] and self.board_colors[piece[0]][piece[1] + 1] == self.flood_color:
                    self.board_colors[piece[0]][piece[1] + 1] = self.flood_color
                    self.part_of_flood[piece[0], piece[1] + 1] = True
                    q.put(((piece[0]), piece[1] + 1))
                    self.flood_size += 1

        for i in range(self.width * self.height):
            if self.part_of_flood[int(i / self.width), int(i % self.height)] == True:
                self.change_cell_color(self.keylist[i], self.flood_color)

        self.move_count += 1
        self.change_text(("Moves: ", self.move_count, " / ", self.total_moves))

    # Sets the actual colors in the tkinter board to the selected board colors
    def initialize_colors(self):
        index = 0
        for idx in self.centers.keys():
            self.change_cell_color(idx, self.board_colors[int(index / self.width)][index % self.width])
            index += 1

        self.flood_color = self.board_colors[0][0]

    def new_game(self):
        self.total_moves = 23

        y = "yellow"
        p = "purple"
        r = "red"
        g = "green"
        o = "orange"
        b = "blue"

        # Hard Coded sample board
        self.board_colors = [[y,o,p,b,o,y,o,o,g,r,g,y],
                            [g,y,o,r,y,p,r,p,p,b,p,y],
                            [b,o,o,o,b,o,r,g,r,b,r,o],
                            [b,g,g,r,r,y,p,g,r,p,r,p],
                            [p,p,g,g,y,b,p,r,g,y,o,r],
                            [b,o,r,y,r,r,r,r,g,y,p,p],
                            [o,b,r,r,o,g,g,g,y,y,b,p],
                            [g,r,b,o,y,g,p,o,o,g,p,b],
                            [r,g,o,p,b,p,b,p,g,b,y,b],
                            [o,b,o,r,o,o,b,g,y,r,b,r],
                            [r,o,o,g,g,y,o,r,o,o,y,g],
                            [o,p,g,r,b,g,y,o,p,y,y,y]]

        self.part_of_flood = np.full((self.width, self.height), False)
        self.part_of_flood[0, 0] = True
        self.initialize_colors()
        self.keylist = list(self.centers.keys())
        self.handle_center_click(2) #call handle function on top left corner 
        self.move_count -= 1

        if self.first_run == True:
            self.first_run = False
            self.population([])
        
if __name__=="__main__":
    ap = argparse.ArgumentParser(description='Play a game; choose your difficulty')
    ap.add_argument("--hard", dest="hardmode", action="store_true",default=False, help="Play a harder version of the game.")

    args = ap.parse_args()

    g = GridGame(12, 12, 50) #rows,columns,cell size

    g.new_game()
    g.start()
    
