#!/usr/bin/python2.2
""" program for testing keyboards.  Uses the ncurses library for a GUI interface.
    MUST BE RUNNED IN A 120 COLUMN WIDE CONSOLE (AND NOT IN AN XTERMINAL)
"""

import curses, sys, os
#import curses.textpad
from keyboard_data import *

class Window:
    """ Generic base class for all window objects such as keys, keygroups, keyboard 
        and options window.
    """
    global DEBUG_COLOR

    def __init__(self, parent, size, pos, color):
        self.parent = parent
        self.size = size
        self.pos = pos
        self.color = color
	self.recreate_window()

    def debug(self, line):
        """ for showing debug information.  It writes a line in the upper left corner of
	    this window.
	"""
        self.win.attron(curses.color_pair(DEBUG_COLOR))
	self.win.addstr(0, 0, line) 
        self.win.refresh()
        self.win.attroff(curses.color_pair(DEBUG_COLOR))

    def recreate_window(self):
        self.win = curses.newwin(self.size[0], self.size[1], self.pos[0], self.pos[1])
        self.win.bkgd(ord(' '), curses.color_pair(self.color))
    

    def width(self):
        return self.size[1]
	
    def set_width(self, w):
        self.size[1] = w

    def height(self):
        return self.size[0]
	
    def set_height(self, h):
        self.size[0] = h

    def row_pos(self):
        return self.pos[0]
	
    def set_row_pos(self, r):
        self.pos[0] = r
	
    def col_pos(self):
        return self.pos[1]
	
    def set_col_pos(self, c):
        self.pos[1] = c
	
    def color_pair(self):
        return self.color

    def refresh(self):
        if self.win:
            self.win.refresh()

class Options(Window):
    """ This is a window in the lower half of the screen for showing information
        and changing options (such as type of keyboard shown).  Also, may 
        ask for feedback from user (although this might be better done in a 
        popup window?)
    """

    def __init__(self, parent, size, pos, color):
        Window.__init__(self, parent, size, pos, color)
        
    def draw(self):
        if self.win:
            self.win.box()
            self.make_statusline("<no key pressed>")
            self.refresh()

    def showChoices(self):
        """ shows a list of menu choices to choose from 
	    NOT IMPLEMENTED YET
	"""
        self.win.addstr(2,2,"1 - 104 keys")
        self.win.addstr(2,1,"2 - 101 keys")
        self.win.refresh()

    def make_statusline(self, msg):
        """ this line is put at the very bottom of the options window
	    Only the last part of the line is erased to avoid 'flicker'
	    problems which occur when the entire line is refreshed
	"""
        y = self.size[0]-2
        line = "--- hold down <ctrl> key and hit the <esc> key to quit --- "
	start = len(line)
	line += msg
        self.win.attron(curses.color_pair(STATUSLINE))
	self.win.addstr(y,start,"      ")
        self.win.addstr(y, 0, line) 
        self.win.refresh()
        self.win.attron(curses.color_pair(self.color))

    def show_code(self, c):
        """ shows in the statusline the scan code generated from the last key hit.
	"""
        line = "last key hit: %d" % c
        self.make_statusline(line)     

class Key(Window):
    """ This is a class for one individual key.
    """
    def __init__(self, parent, size, pos, color, name):
        Window.__init__(self, parent, size, pos, color)
        self.name = name
	
    def get_name(self):
        return self.name
	
    def set_name(self, name):
        self.name = name

    def draw(self):
        self.draw_label()
        self.draw_border()
	self.refresh()

    def draw_border(self):
        if self.win:
            self.win.border()

    def draw_label(self):
        if self.win:
	    # need to center label horizontally
	    name = self.name.center(self.width())
	    # been centered horizontally in __init__()). 
	    centr = (self.height()/2)
	    for row in range(0, self.height()):
                if row == centr:
		    self.win.addstr(row, 0, name)
		else:
		    self.win.addstr(row, 0, "    ")

    def hilight(self):
        if self.win:
            self.win.attron(curses.A_BOLD | curses.color_pair(KEY_HILITE))
            self.draw()

class JShapedKey(Key):

    def __init__(self, parent, size, pos, color, name, upperpos, uppersize):
        Key.__init__(self, parent, size, pos, color, name) 
	self.upperpart = Key(parent, uppersize, upperpos, color, " ")
        
    def draw(self):
        self.draw_label()
	self.upperpart.draw_label()
        self.draw_lower_border()
	self.draw_upper_border()
	self.upperpart.refresh()
	self.refresh()
	
    def draw_lower_border(self):
        self.win.border(0,0,' ',0,0,curses.ACS_VLINE,0,0)
	self.win.hline(0,1,curses.ACS_HLINE,3)
	self.win.vline(0,4,curses.ACS_LRCORNER,1)
 
    def draw_upper_border(self):
        self.upperpart.win.border(0,0,0,' ',0,0,curses.ACS_VLINE,curses.ACS_VLINE)

    def hilight(self):
        self.win.attron(curses.A_BOLD | curses.color_pair(KEY_HILITE))
	self.upperpart.win.attron(curses.A_BOLD | curses.color_pair(KEY_HILITE))
        self.draw()
	
class Keygroup:
    """ a keygroup is a set of keys which are 'group' together on the 
        keyboard.  It is mainly used to help space out
	entire groups of keys without having to move each and every
	key.
    """
    def __init__(self, pos):
	self.pos = pos
	self.keys = {}

    def draw(self):
        self.draw_keys()

    def make_keys(self, kparent, group):
        for asc in group.keys():
            list = group[asc]
            ksize = [0,0]
            ksize[0] = list[2][0]*KEY_HEIGHT
            ksize[1] = list[2][1]*KEY_WIDTH
            krow = TOP_MARGIN + self.pos[0] + (list[1][0]*(ksize[0]))
            kcol = SIDE_MARGIN + self.pos[1] + (list[1][1]-1)*(ksize[1])
	    key = Key(parent=kparent, size=ksize, pos=[krow,kcol],
                      color=KEY_NORMAL, name=list[0])
            self.keys[asc] = key
	

    def draw_keys(self):
        for (code, key) in self.keys.iteritems():
             key.draw() 

    def get_key(self, code):
        if self.keys.has_key(code):
            key = self.keys[code]
            return key
        return None

class Alnum_group(Keygroup):
    """ This the 'main' group of the keyboard where the alphanumeric
        characters are (among other keys).  I needed to override the
	make_keys() function because I needed to customize spacing
	for the first column of keys (they are all of different 
	sizes).
    """

    def __init__(self,  pos):
        Keygroup.__init__(self, pos)

    def make_keys(self, kparent, group):
        for asc in alnum_data.keys():
            list = alnum_data[asc]
            ksize = [0,0]
            ksize[0] = list[2][0]*(KEY_HEIGHT)
            ksize[1] = list[2][1]*(KEY_WIDTH)
            krow = TOP_MARGIN + self.pos[0] + (list[1][0]*(ksize[0]))
            if list[1][1] == 0:
                kcol = SIDE_MARGIN + self.pos[1]
            else:
                kcol = self.mid_col_pos(list[1][0], list[1][1])
	     
            key = Key(parent=kparent, size=ksize, pos=[krow,kcol],
                      color=KEY_NORMAL, name=list[0])
            self.keys[asc] = key
	if Keyboard_type == KB_TYPE_104B:
	    self.adjustKeysFor104B(kparent)
	if Keyboard_type == KB_TYPE_101:
	    self.adjustKeysFor101(kparent)
	    
    def mid_col_pos(self, rpos, cpos):
        begin = SIDE_MARGIN + self.pos[1] + alnum_offsets[rpos]*(KEY_WIDTH)
        return begin + (cpos-1)*(KEY_WIDTH)
 
    def adjustKeysFor104B(self, kparent):
        # enter key is J shaped
        oldkey = self.keys.get(28, None)
        if oldkey:
            ht = oldkey.height()
     	    wd = oldkey.width()
            row = oldkey.row_pos()
	    col = oldkey.col_pos()
	    oldname = oldkey.get_name()
	    key = JShapedKey(parent=kparent, size=[ht,wd], pos=[row,col], color=KEY_NORMAL,
		           name=oldname, upperpos=[row-KEY_HEIGHT,col+KEY_WIDTH-1],
		           uppersize = [ht, (wd/2)+1])
	    self.keys[28] = key
	    # the \ key is up on the 1st row 
	oldkey = self.keys.get(43, None)
	if oldkey:
	    row = oldkey.row_pos() - KEY_HEIGHT
	    col = SIDE_MARGIN + 13*KEY_WIDTH
	    width = KEY_WIDTH
	    oldkey.set_row_pos(row)
	    oldkey.set_col_pos(col)
	    oldkey.set_width(width)
	    oldkey.recreate_window()
	    # the backspace key is smaller and over one more space
	    oldkey = self.keys.get(14, None)
	    if oldkey:
	        width = 1*KEY_WIDTH
		cpos = self.mid_col_pos(1,14)
	        oldkey.set_width(width)
		oldkey.set_name("BCK")
	    	oldkey.set_col_pos(cpos)
		oldkey.recreate_window()

    def adjustKeysFor101(self, kparent):
	#remove win keys
	key = self.keys.get(125, None)
	if key:
	    del self.keys[125]
	key = self.keys.get(126, None)
	if key:
	    del self.keys[126]
	key = self.keys.get(263, None)
	if key:
	    del self.keys[263]
	# move over left alt key and make it bigger,
	key = self.keys.get(100, None)
	if key:
	    cpos = SIDE_MARGIN + 11*KEY_WIDTH
	    key.set_col_pos(cpos)
	    width = 1.5*KEY_WIDTH
	    key.set_width(width)
	    key.recreate_window()
	# make space key longer
	key = self.keys.get(57, None)
	if key:
	    width = 7.5*KEY_WIDTH
	    key.set_width(width)
	    key.recreate_window()
	    
		      
class Keyboard(Window):
    """ This is the upper window that holds all the keys.
    """
    
    def __init__(self, parent, size, pos, color):
        Window.__init__(self, parent, size, pos, color)
        self.groups = None  # a list of keygroups to be added later

    def draw(self):
        self.draw_board()
	self.refresh()
        if not self.groups:
            self.make_keygroups()
        self.draw_keygroups()

    def draw_board(self):
        if self.win:
            self.win.border()
	
	    
    def make_group(self, gpos, data):
        group = Keygroup(gpos)
	group.make_keys(self, data)
	self.groups.append(group) 

    def make_keygroups(self):
        self.groups = []
	# aphanumeric keys (main part)
        group = Alnum_group(pos=[1,0])
        group.make_keys(self, alnum_data)
        self.groups.append(group)
	# navigation keys (HOME, END, PAGEDOWN, etc.)
	gpos = [4, 83]
	self.make_group(gpos, navig_data)
	# numeric keypad
	gpos = [4, 101]
	self.make_group(gpos, numer_data)
	# arrow keypad
	gpos = [13, 83]
	self.make_group(gpos, arrow_data)
	# the keygroup with the NUM LOCK, SCREEN PRINT, etc.
	gpos = [0, 83]
	self.make_group(gpos, lock_data)
	# the keygroup with the escape key
	gpos = [0,5]
	self.make_group(gpos, esc_data)
	# the keygroup with F1-4 keys
	gpos = [0,13]
	self.make_group(gpos, funct1_data)
	# the keygroup with the F5-8 keys
	gpos = [0,36]
	self.make_group(gpos, funct2_data)
	# the keygroup with the F9-12 keys
	gpos = [0,59]
	self.make_group(gpos, funct3_data)

    def draw_keygroups(self):
        for group in self.groups:
            group.draw()

    def get_key(self, c):
        """ given a scan code, find the corresponding key
	    by searching all the keygroups
	"""
        for group in self.groups:
            key = group.get_key(c)
	    if key:  break
        return key

#Global functions:

def init_color_pairs():
    """ initializes color pairs used throughout the script"""
    curses.init_pair(KEYBOARD, curses.COLOR_CYAN, curses.COLOR_CYAN)
    curses.init_pair(STATUSLINE, curses.COLOR_BLUE, curses.COLOR_YELLOW)
    curses.init_pair(KEY_NORMAL, curses.COLOR_YELLOW, curses.COLOR_BLUE)
    curses.init_pair(KEY_HILITE, curses.COLOR_BLUE, curses.COLOR_YELLOW)
    curses.init_pair(MENU_UNSELECT, curses.COLOR_BLUE, curses.COLOR_BLUE)
    curses.init_pair(MENU_SELECT, curses.COLOR_MAGENTA,
                     curses.COLOR_MAGENTA)
    curses.init_pair(DEBUG_COLOR, curses.COLOR_RED, curses.COLOR_BLACK)

def setup_windows(stdscr, max_row, max_col):
    """ Initialize the keyboard window and the options window """
    kb_width = max_col
    kb_height = int(max_row*RATIO)
    kb_beginrow = 0
    kb_begincol = 0
    keyboard = Keyboard(parent=stdscr, size=[kb_height, kb_width],
                        pos=[kb_beginrow, kb_begincol], color=KEYBOARD)
    if keyboard:
        keyboard.draw()
    m_height =int(max_row*(1-RATIO))+1
    m_width = max_col
    m_col = kb_begincol
    m_row = kb_height
    options = None
    options = Options(parent=stdscr, size=[m_height, m_width],
                pos=[m_row, m_col], color=MENU_UNSELECT)
    if options:
        options.draw()
    return (keyboard, options)

# to make it static, make it global (is there a better way to do this in Python?)
ctrl_down = False
def setCtrlKeyState(c):
    """ for keeping track of whether the ctrl key is down or up. """
    global ctrl_down
    if (c == 97) | (c == 29):
        ctrl_down = True
    if (c == 157) | (c == 225):
        ctrl_down = False

def toggleToOptions(options, stdscr):
    """ This is when the user wants to 'toogle' to the options window.
        NOT IMPLEMENTED YET.
    """
    options.debug("in options")
    options.showChoices()
    c = stdscr.getch()
    if c == 1:
        options.debug("pressed 1")
    if c == 2:
        options.debug("pressed 2")
        
def main(stdscr):
    """ this creates the keyboard and then goes
        into a loop which listens for input from 
	the keyboard
    """
    stdscr = curses.initscr()
    (max_row, max_col) = stdscr.getmaxyx()
    if max_col < 120:
        print "need to run from a 120 column (or wider) screen"
	sys.exit(-1)
    curses.raw()
    curses.noecho()
    curses.curs_set(0) # turn off cursor
    init_color_pairs()
    (keyboard, options) = setup_windows(stdscr, max_row, max_col)
    try:
        os.system('kbd_mode -k')
        while 1:
            c = stdscr.getch()
            setCtrlKeyState(c) 
            if ctrl_down and (c == 1): break
            #if ctrl_down and (c == 15): toggleToOptions(options, stdscr)
            #if c == 57: break
            options.show_code(c)
            key = keyboard.get_key(c)
            if key:
                key.hilight()
    finally:
        os.system('kbd_mode -a')

# begin program:
if __name__ == '__main__':
    curses.wrapper(main)
else:
    print "this needs to be runned from the prompt"

