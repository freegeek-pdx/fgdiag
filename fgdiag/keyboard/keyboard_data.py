# constants for color pairs

DEBUG_COLOR = 7
KEYBOARD = 1
STATUSLINE = 2
KEY_NORMAL = 3
KEY_HILITE = 4
MENU_UNSELECT = 5
MENU_SELECT = 6
KEYGROUP = 8

# ratio of menu / keyboard widths

RATIO = 0.8

# margins on the edges of the keyboard 

TOP_MARGIN = 0
SIDE_MARGIN = 7

# smallest key sizes possible, any smaller and the
# labels don't fit into the keys properly

KEY_WIDTH = 5
KEY_HEIGHT = 3

# The sets of dictionaries of all the keys on at least a 104/105 
# keyboard.  The dict entry has the following structure:
#     scan code: [label string,[row,col],[height, width]]
#  where scan codes are the 'make' scan codes (where the key
# has just been pressed down) in decimal and row,col and
# height, width are relative numbers, not curses y,x 
# coordinates/sizes.  See class Keyboard, function
# make_keys() for more details.
 
# the alphanumeric or main group of keys:
alnum_data  = {  
               30:    ["A",[3,1],[1,1]],
               48:    ["B",[4,5],[1,1]],
               46:    ["C",[4,3],[1,1]],
               32:    ["D",[3,3],[1,1]],
               18:    ["E",[2,3],[1,1]],
               33:    ["F",[3,4],[1,1]],
               34:    ["G",[3,5],[1,1]],
               35:    ["H",[3,6],[1,1]],
               23:    ["I",[2,8],[1,1]],
               36:    ["J",[3,7],[1,1]],
               37:    ["K",[3,8],[1,1]],
               38:    ["L",[3,9],[1,1]],
               50:    ["M",[4,7],[1,1]],
               49:    ["N",[4,6],[1,1]],
               24:    ["O",[2,9],[1,1]],
               25:    ["P",[2,10],[1,1]],
               16:    ["Q",[2,1],[1,1]],
               19:    ["R",[2,4],[1,1]],
               31:    ["S",[3,2],[1,1]],
               20:    ["T",[2,5],[1,1]],
               22:    ["U",[2,7],[1,1]],
               47:    ["V",[4,4],[1,1]],
               17:    ["W",[2,2],[1,1]],
               45:    ["X",[4,2],[1,1]],
               21:    ["Y",[2,6],[1,1]],
               44:    ["Z",[4,1],[1,1]],
               2:     ["1",[1,1],[1,1]],
               3:     ["2",[1,2],[1,1]],
               4:     ["3",[1,3],[1,1]],
               5:     ["4",[1,4],[1,1]],
               6:     ["5",[1,5],[1,1]],
               7:     ["6",[1,6],[1,1]],
               8:     ["7",[1,7],[1,1]],
               9:     ["8",[1,8],[1,1]],
               # needed to use the 'break' code because the 'make' code is
               # same as key '=' (???)
               138:   ["9",[1,9],[1,1]],
               11:    ["0",[1,10],[1,1]],
               41:    ["`",[1,0],[1,1]],
               15:    ["TAB",[2,0],[1,1.7]],
               58:    ["CAP",[3,0],[1,1.8]],
               42:    ["SHIFT",[4,0],[1,2.5]],  #left shift
               29:    ["CTRL",[5,0],[1,1.5]],   #left ctrl
               125:   ["WIN", [5,1],[1,1]],   #left win
               56:    ["ALT", [5,2],[1,1]],   #left alt
               57:    ["SPACE", [5,3],[1,7]],
               100:   ["ALT", [5,10],[1,1]],  #right alt
               126:   ["WIN", [5,11],[1,1]],  #right win
               263:   ["MNU",[5,12],[1,1]],   
               97:    ["CTRL", [5,13],[1,1.5]], #right ctrl
               51:    [",", [4,8],[1,1]],
               52:    [".", [4,9],[1,1]],
               53:    ["?", [4,10],[1,1]],
               54:    ["SHIFT", [4,11], [1,2.5]],  #right shift
               39:    [";", [3,10],[1,1]],
               40:    ["'", [3,11],[1,1]],
               28:    ["ENTER", [3,12],[1,2.15]],
               # This is NOT the make code listed in the table (???)
               407:   ["[", [2,11],[1,1]],
               27:    ["]", [2,12],[1,1]],
               43:    ["\\", [2,13],[1,1.2]],
               12:    ["-", [1,11],[1,1]],
               # needed to use the 'break' code because the 'make' code is
               # same as key '9' (???)
               141:   ["=", [1,12],[1,1]],  
               14:    ["BACK", [1,13],[1,1.9]]
    }
    
# escape key group
esc_data = {               
               1:     ["ESC", [0,0],[1,1]]
	}
	
#the first function key group
funct1_data = {
               59:    ["F1", [0,0], [1,1]],
               60:    ["F2", [0,1], [1,1]],
               61:    ["F3", [0,2], [1,1]],
               62:    ["F4", [0,3], [1,1]]
       }
       
#the second function key group
funct2_data = {	       
               63:    ["F5", [0,0], [1,1]],
               64:    ["F6", [0,1], [1,1]],
               65:    ["F7", [0,2], [1,1]],
               66:    ["F8", [0,3], [1,1]]
	}
	
#the third function key group
funct3_data = {
               67:    ["F9", [0,0], [1,1]],
               68:    ["F10", [0,1], [1,1]],
               87:    ["F11", [0,2], [1,1]],
               88:    ["F12", [0,3], [1,1]]
         }
	 
# the lock keys and print screen group
lock_data = { 
              99:  ["PRINT", [0, 0], [1,1]],
	      70:  ["SCROLL", [0,1],[1,1]],
	      247:  ["PAUSE", [0,2],[1,1]]
	    }
	    
# the navigation key group
navig_data = {
	      110:   ["INS",[0,0],[1,1]],
	      102:   ["HOME",[0,1],[1,1]],
	      104:   ["UP",[0,2],[1,1]],
	      111:  ["DEL",[1,0],[1,1]],
	      107:  ["END",[1,1],[1,1]],
	      109:  ["DOWN",[1,2],[1,1]]
	    }
	    
# this is the arrow key group
arrow_data = {
	      103: ["|",[0,1],[1,1]],
	      105: ["<-",[1,0],[1,1]],
	      108: ["|",[1,1],[1,1]],
	      106: ["->",[1,2],[1,1]]
	    }
	    	      
# this is the numeric pad key group
numer_data = {
	      69:    ["NUM", [0,0],[1,1]],
	      98:   ["/",[0,1],[1,1]],
	      55:  ["*",[0,2],[1,1]],
	      74:  ["-",[0,3],[1,1]],
	      71: ["7",[1,0],[1,1]],
	      72: ["8",[1,1],[1,1]],
	      73: ["9",[1,2],[1,1]],
	      78:   ["+",[.5,3],[2,1]],
	      75: ["4",[2,0],[1,1]],
	      76: ["5",[2,1],[1,1]],
	      77: ["6",[2,2],[1,1]],
	      79: ["1",[3,0],[1,1]],
	      80: ["2",[3,1],[1,1]],
	      81: ["3",[3,2],[1,1]],
	      96: ["ETR",[1.5,3],[2,1]],
	      82: ["0",[4,.5],[1,2]],
	      83: [".",[4,2],[1,1]]
           }
	   
# key offsets for the alnum group
alnum_offsets = {
		 1: alnum_data[41][2][1],
		 2: alnum_data[15][2][1],
		 3: alnum_data[58][2][1],
		 4: alnum_data[42][2][1],
		 5: alnum_data[29][2][1]
	  }

