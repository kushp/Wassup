#!/usr/bin/python

'''
Authors: Michael Terry, Edith Law, and Gary and Ku$h and Josh, for CS349, Winter 2015

This file is the backend to the Wassup app. You should not need
to modify anything in this file. However, you may need to refer
to it to understand the communications protocol between the client
and the server.

You may also find it instructional to understand how backend servers work.

Note that this server performs minimal error checking, and does
not securely transmit data, and does not authenticate users.

The server is a very simple implementation. It uses a pickled file
for storing data. You can use ./print_db.py to print out the contents
of the DB at any time.
'''

import os
import pickle
import base64
from bottle import route, run, static_file, template, request, redirect, response

# File names
DEFAULT_DB_FILE_NAME = 'wassup_app_db.bin'
WASSUP_APP_FILE_NAME = 'wassup_app.html'
WASSUP_LOGIN_FILE_NAME = 'wassup_login.html'

# DB constants
USERS_KEY = 'users'
USER_ID_KEY = 'user_id'
EXISTS_KEY = 'exists'
SENDER_ID_KEY = 'sender_id'
FULL_NAME_KEY = 'full_name'
FRIEND_ADDED_KEY = 'friend_added'
SENDER_FULL_NAME_KEY = 'sender_full_name'
FRIENDS_LIST_KEY = 'friends_list'
SUPS_KEY = 'sups'
SUP_ID_KEY = 'sup_id'
DATE_KEY = 'date'

# Communication constants
PROTOCOL_VERSION = '1.3'
PROTOCOL_VERSION_KEY = 'protocol_version'
MESSAGE_ID_KEY = 'message_id'
COMMAND_KEY = 'command'
COMMAND_DATA_KEY = 'command_data'
ERROR_KEY = 'error'
REPLY_DATA_KEY = 'reply_data'

# Commands
CREATE_USER_COMMAND = 'create_user'
USER_EXISTS_COMMAND = 'user_exists'
ADD_FRIEND_COMMAND = 'add_friend'
ADD_FRIEND_IF_EXISTS_COMMAND = 'add_friend_if_exists'
REMOVE_FRIEND_COMMAND = 'remove_friend'
GET_FRIENDS_COMMAND = 'get_friends'
SEND_SUP_COMMAND = 'send_sup'
REMOVE_SUP_COMMAND = 'remove_sup'
CLEAR_SUPS_COMMAND = 'clear_sups'
GET_SUPS_COMMAND = 'get_sups'

'''
Data structures:
- The app DB is a dictionary with the following key/value pairs:
-- 'users': user DB object
- The user DB is a dictionary with the following key/value pairs:
-- 'user_id': user ID
-- 'full_name': user's full name
-- 'friends_list': a list of user IDs representing the user's friends
-- 'sups': a list of objects with the following key/value pairs:
--- 'sender_id': The ID of the user who sent the sup
--- 'date': The time the sup was sent
'''

# The server application DB, that manages all individual user DBs
def app_db_write_to_file(app_db, file_name=DEFAULT_DB_FILE_NAME):
  '''
  Will write the DB out to the file specified
  '''
  fout = open(file_name, 'wb')
  pickle.dump(app_db, fout)
  fout.close()

def app_db_load_from_file(file_name=DEFAULT_DB_FILE_NAME):
  '''
  Will load the DB from the file given. If the file doesn't exist,
  then it will create a new DB object (but not write it to disk)
  '''
  if not os.path.exists(file_name):
    return app_db_create()
  fin = open(file_name, 'rb')
  app_db = pickle.load(fin)
  fin.close()
  return app_db

def app_db_create():
  '''
  Creates the app DB
  '''
  return {
    USERS_KEY: {}
  }

def app_db_add_user(app_db, user_id, full_name):
  '''
  Adds the user to the DB. Does not write to disk. If the user
  already exists, does nothing.
  '''
  if not user_id in app_db[USERS_KEY]:
    app_db[USERS_KEY][user_id] = user_db_create(user_id, full_name)

def app_db_get_user_db(app_db, user_id):
  '''
  Gets the DB for the given user
  '''
  if not user_id in app_db[USERS_KEY]:
    raise Exception("user_id not in DB: " + user_id)
  return app_db[USERS_KEY][user_id]

def app_db_user_exists(app_db, user_id):
  '''
  Checks whether the given user_id exists in the user DB or not
  '''
  return user_id in app_db[USERS_KEY]


# The user DB
def user_db_create(user_id, full_name):
  '''
  Creates the user DB for the given user
  '''
  return {
    USER_ID_KEY: user_id,
    FULL_NAME_KEY: full_name,
    FRIENDS_LIST_KEY: [],
    SUPS_KEY: []
  }

def user_db_get_user_id(user_db):
  return user_db[USER_ID_KEY]

def user_db_get_user_full_name(user_db):
  return user_db[FULL_NAME_KEY]

def user_db_get_friends_list(user_db):
  '''
  Returns a copy of the user's friend's list.
  '''
  return user_db[FRIENDS_LIST_KEY][:]

def user_db_add_friend(user_db, user_id):
  '''
  Adds the given user to the friend's list. Does nothing
  if the friend is already in the friends list
  '''
  friends_list = user_db[FRIENDS_LIST_KEY]
  if not user_id in friends_list:
    friends_list.append(user_id)

def user_db_remove_friend(user_db, user_id):
  '''
  Removes the given user from the friend's list.
  '''
  friends_list = user_db[FRIENDS_LIST_KEY]
  if user_id in friends_list:
    friends_list.remove(user_id)

def user_db_get_sups(user_db):
  '''
  Returns a copy of the user's sups list
  '''
  return user_db[SUPS_KEY][:]

def user_db_add_sup(user_db, sender_id, sup_id, date):
  '''
  Adds a sup to the user's sups list
  '''
  sups = user_db[SUPS_KEY]
  sups.append({
    SENDER_ID_KEY: sender_id,
    SUP_ID_KEY: sup_id,
    DATE_KEY: date
  })

def user_db_remove_sup(user_db, sup_id):
  '''
  Removes a sup from the user's sups list
  '''
  sups = user_db[SUPS_KEY]
  sups = [sup for sup in sups if sup[SUP_ID_KEY] != sup_id]
  user_db[SUPS_KEY] = sups

def user_db_clear_sups(user_db):
  '''
  Clears all sups from a user's sups list
  '''
  user_db[SUPS_KEY] = []


# Routing code
'''
Client-Server Protocol
- A request to the server is a JSON object with the following properties (all required):
-- protocol_version: A version number indicating the protocol version
-- message_id: The ID of the message being sent
-- command: The actual command to execute
-- command_data: Command-specific data. This should be null if there is no command data.
- We assume the user ID is set in a cookie. If it is not set, users will be redirected to
  a login page.

- A response JSON object will be returned with the following key-value pairs (all fields
  will be present in every response):
-- protocol_version: The protocol version the server is using
-- error: If no error, this field is an empty string. Otherwise, it is a string with the error
          encountered, server-side
-- command: The command this object is a response to
-- message_id: The ID of the original request/message
-- reply_data: The return data for executing the command. Undefined if an error. The type
               of data returned is command-specific, and noted below
'''

@route('/post', method="POST")
def handle_post():
  '''
  This handles all the AJAX requests.
  '''
  try:
    message_id = ''
    user_id = ''
    command = ''
    command_data = ''

    json_data = request.json
    print
    print "JSON object received via POST:", str(json_data)

    if not MESSAGE_ID_KEY in json_data:
      if COMMAND_KEY in json_data:
        command = json_data[COMMAND_KEY]
        return generate_error('missing message ID', command, 'Missing message ID field in JSON object')

    message_id = json_data[MESSAGE_ID_KEY]

    if not COMMAND_KEY in json_data:
      return generate_error(message_id, 'command missing', 'Missing command field in JSON object')

    command = json_data[COMMAND_KEY].lower()

    if not PROTOCOL_VERSION_KEY in json_data:
      return generate_error(message_id, command, 'Missing protocol version in JSON object')

    if not COMMAND_DATA_KEY in json_data:
      return generate_error(message_id, command, 'Missing command_data field in JSON object')

    protocol_version = json_data[PROTOCOL_VERSION_KEY]
    command_data = json_data[COMMAND_DATA_KEY]

    if request.get_cookie(USER_ID_KEY):
      user_id = request.get_cookie(USER_ID_KEY)
    else:
      # To allow command-line tests, you can specify the user ID via the user_id field
      if USER_ID_KEY in json_data:
        user_id = json_data[USER_ID_KEY]
      else:
        redirect('/login')
        return

    # The actual commands that handle the requests
    command_handlers = {
      CREATE_USER_COMMAND: handle_create_user,
      USER_EXISTS_COMMAND: handle_user_exists,
      ADD_FRIEND_COMMAND: handle_add_friend,
      ADD_FRIEND_IF_EXISTS_COMMAND: handle_add_friend_if_exists,
      REMOVE_FRIEND_COMMAND: handle_remove_friend,
      GET_FRIENDS_COMMAND: handle_get_friends,
      SEND_SUP_COMMAND: handle_send_sup,
      REMOVE_SUP_COMMAND: handle_remove_sup,
      CLEAR_SUPS_COMMAND: handle_clear_sups,
      GET_SUPS_COMMAND: handle_get_sups
    }

    if not command in command_handlers:
      return generate_error(message_id, command, 'Unknown command: ' + command)

    return command_handlers[command](protocol_version, user_id, message_id, command, command_data)
  except Exception as e:
    return generate_error(message_id, command, 'Error caught processing input: ' + str(e))

def handle_create_user(
    protocol_version,
    user_id,
    message_id,
    command,
    command_data):
  '''
  command_data is a dictionary with the following key-value pairs:
  - user_id: The user ID
  - full_name: The user's full name

  Returns a string on success
  '''
  if not (USER_ID_KEY in command_data and FULL_NAME_KEY in command_data):
    return generate_error(message_id, command, 'Missing user_id and/or full_name in ' + command + ' request')
  new_user_id = command_data[USER_ID_KEY]
  full_name = command_data[FULL_NAME_KEY]
  app_db = app_db_load_from_file()
  app_db_add_user(app_db, new_user_id, full_name)
  app_db_write_to_file(app_db)
  return generate_reply(message_id, command, 'Created user')

def handle_user_exists(
    protocol_version,
    user_id,
    message_id,
    command,
    command_data):
  '''
  command_data is a dictionary with the following key-value pairs:
  - user_id: The user ID

  Returns a dictionary with the following key/value pairs:
  - user_id: The user ID
  - exists: Boolean
  - full_name: User's full name, empty string if they don't exist
  '''
  if not (USER_ID_KEY in command_data):
    return generate_error(message_id, command, 'Missing user_id in ' + command + ' request')
  user_id = command_data[USER_ID_KEY]
  app_db = app_db_load_from_file()
  user_exists = app_db_user_exists(app_db, user_id)

  user_db = app_db_get_user_db(app_db, user_id) if user_exists else None
  user_full_name = user_db_get_user_full_name(user_db) if user_exists else ""
  return generate_reply(message_id, command, {
    USER_ID_KEY: user_id,
    EXISTS_KEY: user_exists,
    FULL_NAME_KEY: user_full_name
  })

def handle_add_friend_if_exists(
    protocol_version,
    user_id,
    message_id,
    command,
    command_data):
  '''
  command_data is a dictionary with the following key-value pairs:
  - user_id The ID of the user to add, if they already exist

  Returns an object with the following key-value pairs:
  - user_id: The ID of the user to add
  - exists: A Boolean indicating whether they actually exist
  - full_name: Their full name
  - friend_added: Whether the add operation was successful
  '''
  if not USER_ID_KEY in command_data:
    return generate_error(message_id, command, 'Missing user_id in ' + command + ' request')
  friend_id = command_data[USER_ID_KEY]
  app_db = app_db_load_from_file()
  user_db = app_db_get_user_db(app_db, user_id)
  if app_db_user_exists(app_db, friend_id):
    user_db_add_friend(user_db, friend_id)
    app_db_write_to_file(app_db)

    friend_db = app_db_get_user_db(app_db, friend_id)
    friend_full_name = user_db_get_user_full_name(friend_db)
    return generate_reply(message_id, command, {
      USER_ID_KEY: friend_id,
      EXISTS_KEY: True,
      FULL_NAME_KEY: friend_full_name,
      FRIEND_ADDED_KEY: True
      })
  else:
    return generate_reply(message_id, command, {
      USER_ID_KEY: friend_id,
      EXISTS_KEY: False,
      FULL_NAME_KEY: '',
      FRIEND_ADDED_KEY: False
      })
      

def handle_add_friend(
    protocol_version,
    user_id,
    message_id,
    command,
    command_data):
  '''
  command_data is a dictionary with the following key-value pairs:
  - user_id The ID of the user to add

  Returns a string on success
  '''
  if not USER_ID_KEY in command_data:
    return generate_error(message_id, command, 'Missing user_id in ' + command + ' request')
  friend_id = command_data[USER_ID_KEY]
  app_db = app_db_load_from_file()
  user_db = app_db_get_user_db(app_db, user_id)
  user_db_add_friend(user_db, friend_id)
  app_db_write_to_file(app_db)
  return generate_reply(message_id, command, 'Added friend')

def handle_remove_friend(
    protocol_version,
    user_id,
    message_id,
    command,
    command_data):
  '''
  command_data is a dictionary with the following key-value pairs:
  - user_id The ID of the user to add

  Returns a string on success
  '''
  if not USER_ID_KEY in command_data:
    return generate_error(message_id, command, 'Missing user_id in ' + command + ' request')
  friend_id = command_data[USER_ID_KEY]
  app_db = app_db_load_from_file()
  user_db = app_db_get_user_db(app_db, user_id)
  user_db_remove_friend(user_db, friend_id)
  app_db_write_to_file(app_db)
  return generate_reply(message_id, command, 'Removed friend')

def handle_get_friends(
    protocol_version,
    user_id,
    message_id,
    command,
    command_data):
  '''
  command_data is not needed for this command, and is ignored.

  Returns a list of objects with the following key-value pairs:
  - user_id: The ID of the friend
  - full_name: The full name of the friend
  '''
  app_db = app_db_load_from_file()
  user_db = app_db_get_user_db(app_db, user_id)
  friends_list = user_db_get_friends_list(user_db)
  return_list = []
  for friend_id in friends_list:
    if app_db_user_exists(app_db, friend_id):
      friend_db = app_db_get_user_db(app_db, friend_id)
      return_list.append({
        USER_ID_KEY: friend_id,
        FULL_NAME_KEY: user_db_get_user_full_name(friend_db)
        })
    else:
      return_list.append({
        USER_ID_KEY: friend_id,
        FULL_NAME_KEY: ''
      })
  return generate_reply(message_id, command, return_list)

def handle_send_sup(
    protocol_version,
    user_id,
    message_id,
    command,
    command_data):
  '''
  command_data is a dictionary with the following key-value pairs:
  - user_id: The ID of the user to send the sup to
  - sup_id: The ID of the sup message
  - date: The date of the sup message

  Returns a string on success
  '''
  if not (USER_ID_KEY in command_data and SUP_ID_KEY in command_data and DATE_KEY in command_data):
    return generate_error(message_id, command, 'Missing user_id, sup_id, and/or date in ' + command + ' request')
  friend_id = command_data[USER_ID_KEY]
  sup_id = command_data[SUP_ID_KEY]
  date = command_data[DATE_KEY]
  app_db = app_db_load_from_file()
  friend_db = app_db_get_user_db(app_db, friend_id)
  user_db_add_sup(friend_db, user_id, sup_id, date)
  app_db_write_to_file(app_db)
  return generate_reply(message_id, command, 'Sent sup')

def handle_remove_sup(
    protocol_version,
    user_id,
    message_id,
    command,
    command_data):
  '''
  command_data is a dictionary with the following key-value pairs:
  - sup_id: The ID of the sup message to remove

  Returns a string on success
  '''
  if not SUP_ID_KEY in command_data:
    return generate_error(message_id, command, 'Missing sup_id in ' + command + ' request')
  sup_id = command_data[SUP_ID_KEY]
  app_db = app_db_load_from_file()
  user_db = app_db_get_user_db(app_db, user_id)
  user_db_remove_sup(user_db, sup_id)
  app_db_write_to_file(app_db)
  return generate_reply(message_id, command, 'Removed sup')

def handle_clear_sups(
    protocol_version,
    user_id,
    message_id,
    command,
    command_data):
  '''
  command_data is ignored for this command

  Returns a string on success
  '''
  app_db = app_db_load_from_file()
  user_db = app_db_get_user_db(app_db, user_id)
  user_db_clear_sups(user_db)
  app_db_write_to_file(app_db)
  return generate_reply(message_id, command, 'Cleared sups')

def handle_get_sups(
    protocol_version,
    user_id,
    message_id,
    command,
    command_data):
  '''
  command_data is ignored for this command

  Returns a list of sup objects, each with the following key-value pairs:
  - sender_id: The user ID of the person who sent the sup
  - sup_id: The ID of the sup message
  - sender_full_name: The full name of the sender
  - date: The date of the sup message
  '''
  app_db = app_db_load_from_file()
  user_db = app_db_get_user_db(app_db, user_id)
  sups = user_db_get_sups(user_db)
  for sup in sups:
    if app_db_user_exists(app_db, sup[SENDER_ID_KEY]):
      sup_sender_user_db = app_db_get_user_db(app_db, sup[SENDER_ID_KEY])
      sup[SENDER_FULL_NAME_KEY] = user_db_get_user_full_name(sup_sender_user_db)
    else:
      sup[SENDER_FULL_NAME_KEY] = ''
  return generate_reply(message_id, command, sups)

def generate_error(
    message_id,
    command,
    error_message):
  return {
    PROTOCOL_VERSION_KEY: PROTOCOL_VERSION,
    MESSAGE_ID_KEY: message_id,
    COMMAND_KEY: command,
    ERROR_KEY: error_message,
    REPLY_DATA_KEY: ''
  }

def generate_reply(
    message_id,
    command,
    reply_object):
  return {
    PROTOCOL_VERSION_KEY: PROTOCOL_VERSION,
    MESSAGE_ID_KEY: message_id,
    COMMAND_KEY: command,
    ERROR_KEY: '',
    REPLY_DATA_KEY: reply_object
  }

##################################################################
###################       Other Routing         ##################
##################################################################
@route('/')
def main():
  '''
  The primary page for the app.
  '''
  if not request.get_cookie(USER_ID_KEY):
    redirect('/login')
    return
  return template(WASSUP_APP_FILE_NAME)

@route('/login', method='GET')
def login(error_message=''):
  '''
  The login page
  '''
  return template(WASSUP_LOGIN_FILE_NAME, error_message=error_message)

@route('/logged_in', method='POST')
def logged_in():
  '''
  The page the user is sent to when posting their login info
  '''
  try:
    user_id = request.forms.get(USER_ID_KEY)
    full_name = request.forms.get(FULL_NAME_KEY)
    if not (user_id and full_name):
      return login("Invalid or missing user ID and name")
    app_db = app_db_load_from_file()
    app_db_add_user(app_db, user_id, full_name)
    app_db_write_to_file(app_db)
    response.set_cookie(USER_ID_KEY, user_id)
  except Exception as e:
    return login("Error logging in. Please try again. (Error: " + str(e) + ")")
  redirect('/')

@route('/logout', method='POST')
def logout():
  try:
    response.delete_cookie(USER_ID_KEY)
  except Exception as e:
    return generate_error('', '', 'Error logging out: ' + str(e))
  redirect('/login')

@route('/egg')
def egg():
  return base64.b64decode("PCFET0NUWVBFIGh0bUw+PGh0bWw+PGhlYWQ+PGxpbmsgcmVsPSJzdHlsZXNoZWV0IiBocmVmPSJodHRwczovL21heGNkbi5ib290c3RyYXBjZG4uY29tL2Jvb3RzdHJhcC8zLjMuMS9jc3MvYm9vdHN0cmFwLm1pbi5jc3MiLz48L2hlYWQ+PGJvZHk+PGRpdiBjbGFzcz0iY29udGFpbmVyIj48cD48Y2VudGVyPjxpbWcgc3JjPSJodHRwOi8vaS5pbWd1ci5jb20vRmdRM21Zay5qcGciIGNsYXNzPSJpbWctcmVzcG9uc2l2ZSI+PC9jZW50ZXI+PC9wPjxwPjxjZW50ZXI+R29vZCBsdWNrITwvY2VudGVyPjwvcD48cD4oSW1hZ2Ugc291cmNlOiA8YSBocmVmPSJodHRwOi8vaW1ndXIuY29tL0ZnUTNtWWsiPmh0dHA6Ly9pbWd1ci5jb20vRmdRM21ZazwvYT4pPC9wPjwvZGl2PjwvYm9keT48L2h0bWw+")


##################################################################
################### Do not modify the following ##################
##################################################################
@route('/static/<filename:path>')
def server_static(filename):
  base_dir = os.path.abspath(os.path.dirname(__file__))
  return static_file(filename, root='%s/static'%(base_dir))

if __name__ == '__main__':
  run(host='localhost', port=8080, debug=True, reloader=True)