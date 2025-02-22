#!/usr/bin/env python3

# Help from https://github.com/alwaysai/video-streamer on  client-server setup

# web_interface.py

import json
import time
import os
from flask_socketio import SocketIO
from flask import Flask, render_template, request
import sys

from logger import *
from globals import owner, VERSION
from keymap import add_keymap, searchKeyMap, modify_keymap, del_keymap
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode, version=VERSION)

@app.route('/log')
def log():
    return render_template('log.html', async_mode=socketio.async_mode, version=VERSION, log=loadLog(), logLevel=getLogLevel())

@app.route('/settings')
def settings():
    return render_template('settings.html', async_mode=socketio.async_mode, version=VERSION)

@app.route('/keymap', methods=['GET'])
def keymap():
    return render_template('keymap.html', async_mode=socketio.async_mode, version=VERSION)



################## APP SOCKETS ################################
@socketio.on('connect')
def connect_web():
    print('[INFO] Web client connected: {}'.format(request.sid))


@socketio.on('disconnect')
def disconnect_web():
    print('[INFO] Web client disconnected: {}'.format(request.sid))


@socketio.on('connect')
def connect_midi():
    socketio.emit('my_response', {'data': f'Client {request.sid} Connected', 'count': 0})
    print('[INFO] client connected: {}'.format(request.sid))

@socketio.on('disconnect')
def disconnect_midi():
    socketio.emit('my_response', {'data': f'Client {request.sid} Disconnected', 'count': 0})
    print('[INFO] client disconnected: {}'.format(request.sid))


@socketio.on('get_settings')
def get_settings(data):
    load_settings(settingsFile)
    send_settings()

@socketio.on('save_settings')
def save_settings(data):
    saveServerSettings(data, settingsFile)
    socketio.emit('save_settings',data)

def send_settings():
    socketio.emit('settings', {'match_device':match_device,'midi_mode':midi_mode, 'availableInputs':availableInputs, 'availableOutputs':availableOutputs, \
                    'activeInput':activeInput, 'activeOutput':activeOutput, 'settings':settings, 'keymap':keymap, 'keyMapFile':keyMapFile})

################# forward main app to web interface #########################

@socketio.on('midi_restarted')
def midi_restarted():
    client_msg('MIDI has been restarted')

@socketio.on('server_restarted')
def server_restarted():
    client_msg('Server has been restarted')

####################  forward web interface to main app #####################

@socketio.on('restart_midi')
def restart_midi():
    client_msg('Sent Restart MIDI')
    socketio.emit('restart_midi')

@socketio.on('restart_server')
def restart_server():
    client_msg('Sent Restart Server')
    socketio.emit('restart_server')

@socketio.on('quit')
def quit():
    client_msg('Quitting')
    time.sleep(1)
    socketio.emit('quit')

####################### forward web interface to keymap.py ########################3

@socketio.on('new_mapping')
def new_mapping(keymap, map):
    add_keymap(keymap, map)

@socketio.on('modify_mapping')
def modify_mapping(keymap, map):
    modify_keymap(keymap, map)

@socketio.on('delete_mapping')
def delete_mapping(keymap, note, device):
    del_keymap(keymap, note, device)

@socketio.on('search_keymap')
def search_keymap(keymap, device, note):
    socketio.emit('search_keymap_return', searchKeyMap(keymap, device, note, False))

################# forward midi_mapper to logger ######################

@socketio.on('newLogLevel')
def newLogLevel(message):
    setLogLevel(message)
    socketio.emit('loglevel', getLogLevel())

@socketio.on('clear_log')
def clear_log():
    clearLog()

################# forward midi_mapper to web interface ######################
@socketio.on('client_msg')
def client_msg(message):
    socketio.emit('my_response', {'data': message})

@socketio.on('setup')
def setup(message):
    global midi_mode, availableInputs, activeOutput, availableOutputs, activeInput, settings, keymap, match_device, keyMapFile
    availableInputs = message['inputs']
    activeOutput = message['activeOutput']
    availableOutputs = message['outputs']
    activeInput = message['activeInput']
    settings = message['settings']
    keymap = message['keymap']
    midi_mode = message['midi_mode']
    match_device = message['match_device']
    keyMapFile = message['keyMapFile']
    send_settings()

@socketio.on('io_set')
def io_set(message):
    activeInput = message['data']['input']
    activeOutput = message['data']['output']
    socketio.emit('confirm_io', {'data': {'input':activeInput, 'output':activeOutput}})


#################### forward web_interface to midi_mapper ##################

@socketio.on('midi_msg')
def handle_midi_message(message):
    socketio.emit('midi_msg', {'data': message['data']})
    # print(message['data'])

@socketio.on('midi_sent')
def handle_midi_sent(message):
    socketio.emit('midi_sent', {'data': message['data']})
    # print(message['data'])

@socketio.on('midi_sent')
def handle_midi_sent(message):
    socketio.emit('midi_sent', {'data': message['data']})
    # print(message['data'])

@socketio.on('set_mode')
def set_mode(message):
    socketio.emit('set_mode',message)

@socketio.on('exact_match')
def exact_match(message):
    socketio.emit('exact_match',message)

@socketio.on('rescan_io')
def rescan_io():
    socketio.emit('rescan_io',)

@socketio.on('get_keymap')
def get_keymap():
    socketio.emit('reload_keymap',)

@socketio.on('apply_settings')
def apply_settings():
    socketio.emit('apply_settings',)

@socketio.event
def select_io(message):
    socketio.emit('select_io', {'data': message['data']})

@socketio.event
def webMidiNoteIn(message):
    socketio.emit('webMidiNoteIn', {'data': message['data']})

@socketio.event
def webPCIn(message):
    socketio.emit('webPCIn', {'data': message['data']})

################ OSC to Web Interface ###################################

@socketio.on('incomingOSC')
def incomingOSC(address):
    # socketio.emit('my_response', {'data': address})
    socketio.emit('incomingOSC', address)
    pass

@socketio.on('outgoingOSC')
def outgoingOSC(message):
    # socketio.emit('my_response', {'data': f'{message}'})
    socketio.emit('outgoingOSC', message)
    pass

@socketio.on('OSC2MIDI_out')
def OSC2MIDI_out(message):
    socketio.emit('OSC2MIDI_in', message)

################ Main Functions ###################################

def load_settings(settings_file):
    global settings, socket_port, settingsFile
    settingsFile = settings_file
    file = open(settings_file)
    settings = json.loads(file.read())
    socket_port = settings['socket_port']
    file.close()

def saveServerSettings(data, settings_file):
    file = open(settings_file)
    settings = json.loads(file.read())
    settings['socket_port'] = data['socket_port']
    # file.write(json.dumps(settings))
    file.close()
    socketio.emit('my_response', {'data': 'Server Settings Saved'})
    print('Settings Saved')

def server_main(settings_file):
    logs.debug(f'web_interface.py running as PID: {os.getpid()} as User: {owner(os.getpid())}')
    load_settings(settings_file)
    print('Server Main')
    print(f'[INFO] Starting server at http://localhost:{socket_port}')
    logs.info(f"{__name__} started")
    socketio.run(app=app, host='0.0.0.0', port=socket_port)

if __name__ == "__main__":
    server_main()
