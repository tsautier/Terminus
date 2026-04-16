#!/usr/bin/env python3
# encoding: utf-8
"""
   Wrapper for nodejs
   License : GPL
"""
import os
from os import system, symlink, chdir, getcwd
from os.path import join, realpath, dirname, islink, isdir, isfile, relpath
from shutil import which
import subprocess
from .utils import concatenated, copy
from .build_params import BUILD_TOOLS
from .logging import print_info, print_err

DEBUG_SKIP = os.environ.get('DEBUG_SKIP', '').split(',')
NODEJS = '' if 'nodejs' in DEBUG_SKIP else which("nodejs") or which("node")
NODEJS_INIT = {'useable': False}
CSSLINT = which("csslint")

if NODEJS:
    # NODEJS_VERSION = subprocess.getoutput(NODEJS + ' --version')
    # print('using %s %s' % (NODEJS, NODEJS_VERSION))
    NODEJS_INIT['modules_dir'] = join(realpath(BUILD_TOOLS), "node_modules")
    NODEJS_INIT['bin_dir'] = join(NODEJS_INIT['modules_dir'], ".bin")
else:
    DEBUG_SKIP = ['npm', 'babel', 'uglifyjs', 'postcss']


def install_deps(force=False, update=True):
    """ Install or update NODEJS tools"""
    if 'npm' in DEBUG_SKIP:
        return
    d = getcwd()
    chdir(BUILD_TOOLS)
    NODEJS_INIT['useable'] = True
    if force or not isfile('package-lock.json'):
        err = subprocess.call('npm install'.split())
        NODEJS_INIT['useable'] = err == 0
    if update:
        err = subprocess.call('npm update'.split())
        NODEJS_INIT['useable'] = err == 0
    chdir(d)


def _nodebin(cmd, *args):
    if not NODEJS_INIT['useable']:
        print('npm install incomplete : abort')
        return False
    cmd_path = cmd if cmd.startswith('./') else join(NODEJS_INIT['bin_dir'], cmd)
    return system(f"{NODEJS} {cmd_path} {' '.join(args)}")


def transpile(files, target):
    """ Transpile """
    complete = concatenated(files)
    # specific to babeljs... preset env is not found without that
    nodemodules_local = join(dirname(complete), "node_modules")
    if not (islink(nodemodules_local) or isdir(nodemodules_local)):
        symlink(NODEJS_INIT['modules_dir'], nodemodules_local)
    #

    if 'babel' in DEBUG_SKIP:
        print_info("%14s > %s", 'Copy (no babel)', relpath(target))
        copy(complete, target)
        return True

    print_info("%14s > %s", 'Transpile JS', relpath(target))
    return _nodebin('babel', '--presets env', '-o', target, complete)


def minify(src, target):
    """ Minify """

    if 'uglifyjs' in DEBUG_SKIP:
        print_info("%14s > %s", 'Copy (no uglifyjs)', relpath(target))
        copy(src, target)
        return True

    print_info("%14s > %s", 'Minify JS', relpath(target))

    return _nodebin('uglifyjs', '-o',  target, src, '-c', '-m')


def postcss(files, target):
    """ Autoprefix """

    if CSSLINT and 'csslint' not in DEBUG_SKIP:
        for f in files:
            with subprocess.Popen([CSSLINT, f], stdout=subprocess.PIPE) as p:
                p.communicate()
                if p.returncode != 0:
                    print_err('CSS LINT failed for %s', f)

    complete = concatenated(files)

    if 'postcss' in DEBUG_SKIP:
        print_info("%14s > %s", 'Copy (no postcss)', relpath(target))
        copy(complete, target)
        return True

    print_info("%14s > %s", 'Autoprefix CSS', target)
    return _nodebin(join(BUILD_TOOLS, 'postcss.js'), complete, target)
