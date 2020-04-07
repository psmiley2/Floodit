#!/usr/bin/python

# Assistive Algorithms Assignment 8: Intelligent Tutoring Systems
# Some code to get you started
# (c) 2020 Elaine Short

import tkinter as tk
import threading
import time
import argparse
from random import randrange, choice
import numpy as np
from queue import Queue 

BORDER=10
TEXT_H=150
TEXT_W=300

class GridGame:
    
    #builds a grid of a given width and height
    def __init__(self, width, height, size):
        self.root = tk.Tk()

        self.c = tk.Canvas(self.root, width=width*size+4*BORDER+TEXT_W,
                               height=max(height*size+2*BORDER,TEXT_H+2*BORDER))

        self.gridsize = size
        self.c.pack()

        self.cells = {}
        self.edges = {}
        self.corners = {}
        self.centers = {}

        self.children = {}
        
        self.last_click=None
        self.in_tutorial=True

        ## Start of my game's variables
        self.game_type = "easy"
        self.width = width
        self.height = height

        self.flood_idxs = [2]
        self.flood_color = ""
        self.board_colors = [[]]

        self.keylist = []
        self.move_count = 0
        self.total_moves = 0
        ## End of my game's variables


        self.textbox = self.c.create_text(width*size+TEXT_W/2.+BORDER*2, BORDER+height*size/2., text="",width=TEXT_W,justify=tk.LEFT)
        self.change_text("Hello!")
        
        
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

        self.root.bind("<Button 2>", self.right_click_cb)
        self.root.bind("<Button 1>", self.left_click_cb)
        self.root.bind("/",self.get_hint)
        self.root.bind("<space>", self.start_game)

    def start(self):
        tk.mainloop()
        

    

    def right_click_cb(self, pos):
        self.handle_click(pos.x,pos.y,False)           
            
    def left_click_cb(self, pos):
        self.handle_click(pos.x,pos.y,True)

    def handle_click(self, x, y, is_left):
        items = self.c.find_overlapping(x,y,x+5,y+5)
        if len(items)==0:
            return

        corner = False
        corner_idx = None
        for nearby in items:
            if nearby in self.corners:
                corner = True
                self.last_click=(nearby, "corner", is_left)
                self.handle_corner_click(nearby, is_left)

        edge = False
        if not corner:
            for nearby in items:
                if nearby in self.edges:
                    edge = True
                    self.last_click=(nearby, "edge", is_left)
                    self.handle_edge_click(nearby, is_left)
                    
        center = False
        if not edge and not corner:
            for nearby in items:
                if nearby in self.centers:
                    center=True
                    self.last_click=(nearby, "center", is_left)
                    self.handle_center_click(nearby, is_left)
            

            
    #add a circle to the center of an item
    def add_circle(self, item, radius, fill="white"):
        bbox = self.c.bbox(item)
        x = bbox[0]+(bbox[2]-bbox[0])/2.
        y = bbox[1]+(bbox[3]-bbox[1])/2.

        circle = self.c.create_oval(x-radius,y-radius,x+radius,y+radius,fill=fill)
        self.add_child_to_grid(item, circle)

    #add a character to the center of an item
    def add_text(self, item, text, color="black"):
        bbox = self.c.bbox(item)
        x = bbox[0]+(bbox[2]-bbox[0])/2.
        y = bbox[1]+(bbox[3]-bbox[1])/2.

        text = self.c.create_text(x,y, text=text,justify=tk.CENTER, fill=color)
        self.add_child_to_grid(item, text)
        

    def add_child_to_grid(self, item, child):
        if item in self.children:
            self.children[item].append(child)
        else:
            self.children[item]=[child]
   
    #returns (x,y) tuple of the corner of the grid cell (row,col)
    def get_grid_corner(self,row,col):
        return (BORDER+self.gridsize*col,BORDER+self.gridsize*row)
    
    #item must be id of parent corner/edge/center; removes all children
    def remove_children(self, item):
        if item not in self.children:
            return
        children = self.children[item]
        self.children[item]=[]
        for child in children:
            self.c.delete(child)
        
    def change_text(self, new_text):
        self.c.itemconfigure(self.textbox,text=new_text,justify=tk.LEFT)

    #edge weights are light, medium, and heavy
    def change_edge_weight(self, idx, edge_type):
        if weight=="light":
            self.c.itemconfigure(idx, width=1)
        elif weight=="medium":
            self.c.itemconfigure(idx, width=2)
        elif weight=="heavy":
            self.c.itemconfigure(idx, width=4)
        self.c.tag_raise(idx)
        
    #standard color names (blue, yellow, black, etc.) will work, as well as
    #hex colors as strings (#000000)
    def change_edge_color(self, idx, color):
        self.c.itemconfigure(idx,fill=color)
        self.c.tag_raise(idx)
        
    def get_cell_from_center(self, center_idx):
        i,j = self.centers[center_idx][0][0:2]
        return self.cells[(i,j)]

    #standard color names (blue, yellow, black, etc.) will work, as well as
    #hex colors as strings (#000000)
    #you can see names of colors here:
    #https://www.tcl.tk/man/tcl8.6/TkCmd/colors.htm
    def change_cell_color(self, idx, color):
        self.c.itemconfigure(idx,fill=color)

        #make sure edges are on top of fill:
        cell_info = self.get_cell_from_center(idx)

        edges = ["N","S","W","E"]
        for e in edges:
            self.c.tag_raise(cell_info[e])

    def wait_for_click(self,timeout=120):
        self.last_click=None
        elapsed=0
        while self.last_click is None:
            time.sleep(0.1)
            elapsed=elapsed+0.1
            if elapsed > timeout:
                break
        return self.last_click

    def check_win(self):
        if not np.any(self.part_of_flood == False):
            self.change_text("Congratulations. You have won the game!")
            print ("YOU HAVE WON THE GAME !!!!!!\n\n\n\n\n\n\n")
            exit()
        elif self.move_count == self.total_moves:
            self.change_text("You have lost the game.")
            print ("YOU HAVE LOST THE GAME !!!!!!\n\n\n\n\n\n\n")
            exit()
            
    def handle_edge_click(self, idx, is_left):
        # self.change_text("You {} clicked on edge {}.\n The adjacent cells are:\n {}".format("left" if is_left else "right", idx,"\n".join(map(lambda s: str(s),self.edges[idx]))))
        # self.remove_children(idx)
        # self.add_circle(idx, 10, "orange")
        # self.add_text(idx,str(idx),"blue")
        # self.change_edge_color(idx, "#BD15C4")
        pass
    
    def handle_corner_click(self, idx, is_left):
        # self.change_text("You {} clicked on corner {}.\n The adjacent cells are:\n {}".format("left" if is_left else "right", idx,"\n".join(map(lambda s: str(s),self.corners[idx]))))
        # self.remove_children(idx)
        # self.add_circle(idx, 10, "orange")
        # self.add_text(idx,str(idx),"green")
        pass

    def handle_center_click(self, idx, is_left):
        
        (xpos, ypos, discard) = self.centers[idx][0]

        #clicked on a piece that is already part of the flood
        if (self.part_of_flood[xpos, ypos] == True and self.move_count > 0):
            return

        self.flood_color = self.board_colors[xpos][ypos]

        q = Queue(maxsize = (self.width * self.height))

        indices = np.where(self.part_of_flood == True) 
        x, y = indices[0], indices[1]
        for i in range(len(x)):
            q.put((x[i], y[i]))

        while not q.empty():
            piece = q.get()
            if (not piece[0] == 0):
                if (not self.part_of_flood[piece[0] - 1, piece[1]]) and (self.board_colors[piece[0] - 1][piece[1]] == self.flood_color):
                    self.board_colors[piece[0] - 1][piece[1]] = self.flood_color
                    self.part_of_flood[piece[0] - 1, piece[1]] = True
                    q.put(((piece[0] - 1), piece[1]))

            if (not piece[0] == self.width - 1):
                if not self.part_of_flood[piece[0] + 1, piece[1]] and self.board_colors[piece[0] + 1][piece[1]] == self.flood_color:
                    self.board_colors[piece[0] + 1][piece[1]] = self.flood_color
                    self.part_of_flood[piece[0] + 1, piece[1]] = True
                    q.put(((piece[0] + 1), piece[1]))

            if (not piece[1] == 0):
                if not self.part_of_flood[piece[0], piece[1] - 1] and self.board_colors[piece[0]][piece[1] - 1] == self.flood_color:
                    self.board_colors[piece[0]][piece[1] - 1] = self.flood_color
                    self.part_of_flood[piece[0], piece[1] - 1] = True
                    q.put(((piece[0]), piece[1] - 1))

            if (not piece[1] == self.height - 1):
                if not self.part_of_flood[piece[0], piece[1] + 1] and self.board_colors[piece[0]][piece[1] + 1] == self.flood_color:
                    self.board_colors[piece[0]][piece[1] + 1] = self.flood_color
                    self.part_of_flood[piece[0], piece[1] + 1] = True
                    q.put(((piece[0]), piece[1] + 1))

        for i in range(self.width * self.height):
            if self.part_of_flood[int(i / self.width), int(i % self.height)] == True:
                self.change_cell_color(self.keylist[i], self.flood_color)

        if (not self.in_tutorial):
            self.move_count += 1
            self.change_text(("Moves: ", self.move_count, " / ", self.total_moves))

            self.check_win()
        # self.change_cell_color(idx,"yellow")
        # self.add_circle(idx, 10, "orange")
        pass

    ##########################################################s
    # Start Of My Functions                                  #
    ##########################################################

    def initialize_colors(self):
        index = 0
        for idx in self.centers.keys():
            self.change_cell_color(idx, self.board_colors[int(index / self.width)][index % self.width])
            index += 1

        self.flood_color = self.board_colors[0][0]

    ##########################################################
    # End Of My Functions                                    #
    ##########################################################

    def tutorial_board(self):
        y = "yellow"
        p = "purple"
        r = "red"
        g = "green"
        o = "orange"
        b = "blue"

        palette = [y,p,r,g,o,b]

        self.board_colors = [[choice(palette) for i in range(self.width)] for j in range(self.height)]

        self.part_of_flood = np.full((self.width, self.height), False)
        self.part_of_flood[0, 0] = True
        self.initialize_colors()
        self.keylist = list(self.centers.keys())
        self.handle_center_click(2, True) #call handle function on top left corner 


    def new_easy_game(self):
        #runs before starting the game; you can use this to set up the game

        if self.in_tutorial == True:
            self.tutorial_board()
            return

        self.total_moves = 23
        y = "yellow"
        p = "purple"
        r = "red"
        g = "green"
        o = "orange"
        b = "blue"

        if (randrange(2) == 1):
            self.board_colors = [[p,y,y,p,p,y,b,y,p,r,p,g],
                                [r,b,b,g,p,o,o,r,g,p,p,g],
                                [y,p,b,y,b,r,o,o,g,y,b,r],
                                [o,b,o,g,o,o,b,r,p,r,y,g],
                                [b,g,y,o,r,g,r,p,y,o,g,g],
                                [o,o,y,y,y,b,y,r,y,b,y,b],
                                [y,p,y,o,r,b,b,o,g,o,r,y],
                                [r,g,o,r,g,r,g,o,y,p,y,b],
                                [r,o,g,p,y,g,p,g,g,r,o,r],
                                [o,y,r,b,p,g,y,b,p,b,r,p],
                                [o,b,o,r,g,g,b,y,g,b,y,p],
                                [b,o,b,g,r,r,p,g,o,y,o,g]]
        else:
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
        self.handle_center_click(2, True) #call handle function on top left corner 
        self.move_count -= 1

    def new_hard_game(self):
        #runs before starting the game; you can use this to set up the game
        self.game_type = "hard"

        if self.in_tutorial == True:
            self.tutorial_board()
            return

        self.total_moves = 19

        y = "yellow"
        p = "purple"
        r = "red"
        g = "green"
        o = "orange"
        b = "blue"
                   
        if (randrange(2) == 1):
            self.board_colors = [
                [b,b,p,y,y,p,y,o,b,p,y,b],
                [y,b,r,y,r,o,o,b,g,p,y,o],
                [y,p,o,o,y,r,o,o,y,g,p,g],
                [y,b,o,p,r,p,y,p,o,r,p,r],
                [g,p,g,b,b,r,o,o,g,g,b,p],
                [g,y,y,y,p,r,b,y,b,r,o,b],
                [y,y,o,b,g,b,r,o,r,p,p,p],
                [r,p,y,p,b,y,b,o,g,o,o,g],
                [p,r,r,b,y,o,y,o,p,g,r,r],
                [g,b,g,p,y,p,r,y,r,g,o,y],
                [o,r,r,p,g,o,g,g,o,g,y,y],
                [b,o,r,g,g,p,y,y,g,b,p,r]
            ]
        else:
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

        self.handle_center_click(2, True) #call handle function on top left corner 
        self.move_count -= 1

    def get_hint(self,key):
        hint = ""
        if self.move_count < 4:
            hint = "EARLY GAME: Try to reach the center of the board in as few moves as possible.\n"
        elif self.move_count < 9:
            hint = "EARLY MID GAME: Look for moves that add the greatest amount of surface area to your flood.\n"
        elif self.move_count < 14:
            hint = "LATE MID GAME: Try to branch out to all four corners of the board.\n"
        else:
            hint = "LATE GAME: Your main priority now should be to eliminate colors from the board.\n"
        self.change_text((hint, "\nMoves: ", self.move_count, " / ", self.total_moves))

    def start_game(self, key):
        self.move_count = 0
        self.in_tutorial = False
        if self.game_type == "easy":
            self.new_easy_game()  
        else:
            self.new_hard_game()
        self.change_text(("Moves: ", self.move_count, " / ", self.total_moves))

    def tutorial(self):
        # add your tutorial code here
        self.change_text("TUTORIAL:\nWelcome to Flood\nThe colored tile in the top left corner of the board is part of your flood\nIf you click a colored tile on the screen that is a different color than your flood, your flood will become that color\nAny pieces that bordered your flood and that are the same color as your flood are now also part of your flood\nYour goal is to add all of the tiles to your flood without using the max number of moves\nUse the practice board to the left to get a feel for how to play the game.\nYou may also press space to reset the game\n\nPress '/' to recieve a hint.\n\nPress the Space Bar to exit the tutorial and start playing the game!")
        self.wait_for_click(120)

if __name__=="__main__":
    ap = argparse.ArgumentParser(description='Play a game; choose your difficulty')
    ap.add_argument("--hard", dest="hardmode", action="store_true",default=False, help="Play a harder version of the game.")

    args = ap.parse_args()

    g = GridGame(12, 12, 50) #rows,columns,cell size

    if args.hardmode:
        g.new_hard_game()
    else:
        g.new_easy_game()
    
    t = threading.Thread(target=g.tutorial)
    t.start()
    g.start()
    t.join()
