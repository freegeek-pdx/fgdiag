"""Handles and standardizes user output."""

import sys, curses

# Spice these up once the module is working

def error_exit(reason):
    """Print the reason for an unrecoverable error and exit."""
    error(reason)
    sys.exit()

def notice(body):
    """Print a noncritical notice."""
    print "Notice"
    print body

def warning(body):
    """Print a warning."""
    print "Warning!"
    print body

def error(body):
    """Print an error."""
    print "Error!"
    print body
    
def prompt(title, body):
    """Prompt for something."""
    print title
    return raw_input(body + " ")

def yesno(title, body):
    while 1:
        answer = prompt(title, body + " (yes/no):")
        if answer == "yes":
            return True
        if answer == "no":
            return False
