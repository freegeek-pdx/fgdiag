"""Handles and standardizes user output."""

import sys

# Spice these up once the module is working

def error_exit(reason):
    """Print the reason for an unrecoverable error and exit."""
    print reason
    sys.exit()

def notice(text):
    """Print a noncritical notice."""
    print text

def warning(text):
    """Print a warning."""
    print text
    
def prompt(title):
    """Prompt for something."""
    return raw_input(title)

def yesno(title):
    while 1:
        answer = prompt(title + " (yes/no): ")
        if answer == "yes":
            return True
        if answer == "no":
            return False

def db_fallback_notice(filename):
    """Alert about fallback if database fails."""
    notice("Unable to establish a connection with the FreeGeek Database. Outputting test results to a file named %s. " % (filename))