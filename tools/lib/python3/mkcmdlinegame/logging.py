#!/usr/bin/env python3
# encoding: utf-8
"""
   Contains logging functions for buildsystem
   License : GPL
"""
from __future__ import print_function
import sys
from time import sleep
try:
    import colorama
    RED, ORANGE, GREY, RESET = (
        colorama.Fore.RED,
        colorama.Fore.YELLOW,
        colorama.Fore.LIGHTGREEN_EX,
        colorama.Fore.RESET
    )
except ImportError:
    RED, ORANGE, GREY, RESET = ['']*4

REDIR = {
    'error': sys.stderr,
    'warning': sys.stderr,
    'info': sys.stderr
}
ERROR_REDIR = sys.stderr
WARNING_REDIR = sys.stderr
INFO_REDIR = sys.stderr


def silent_log():
    """ disable info and warnings logs """
    REDIR['info'] = None
    REDIR['waring'] = None


def print_err(msg, *keys):
    """ print an error (formatstr, keys,...) """
    if REDIR['error']:
        REDIR['error'].write(RED + "›o‹ nooo : " +
                             (msg % keys) + RESET + "\n")
        sleep(2)


def print_warn(msg, *keys):
    """ print a warning (formatstr, keys,...) """
    if REDIR['warning']:
        REDIR['warning'].write(ORANGE + "! " + (msg % keys) + RESET + "\n")


def print_info(msg, *keys):
    """ print an info (formatstr, keys,...) """
    if REDIR['info']:
        REDIR['info'].write(GREY + (msg % keys) + RESET + "\n")
