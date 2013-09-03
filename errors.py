#!/usr/bin/python
#
# This file is part of Bargate.
#
# Bargate is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Bargate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Bargate.  If not, see <http://www.gnu.org/licenses/>.

from bargate import app
import bargate.core
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
import smbc
import traceback

def debugError(msg):
	return output_error("Debug Message",msg,"Debug")

#### Output error handler
## outputs a template error page, or if redirect is set, redirects with a popup
## error set on the users' session so it pops up a modal dialog after redirect
def output_error(title,message,errstr,redirect=None):
	"""This function is called by other error functions to show the error to the
	end user. It takes a title, message and a further error type. If redirect
	is set then rather than show an error it will return the 'redirect' after
	setting the popup error flags so that after the redirect a popup error is 
	shown to the user. Redirect should be a string returned from flask redirect().
	"""

	if redirect == None:

		## Render an error page
		return render_template('error.html',error=errstr,
			title=title,
			message=message,
		), 200

	else:

		## Set error popup and return
		bargate.core.poperr_set(title,message)
		return redirect


#### Generic fatal error
def fatal(ex):
	"""Call this when a fatal exception has occured and you want Bargate to stop
	executing further. This function will abort with a 500 HTTP error and will
	display a message about the 'ex' exception passed to it.
	"""
	g.fault_message = "An unexpected error occured. The error was of type " + str(type(ex)) + " and the message was: " + ex.__str__()
	abort(500)

#### Exception handler when running smbc functions
## handler for all exceptions generated by pysmbc
def smbc_handler(ex,uri="Unknown",redirect=None):
	"""Handles exceptions generated by pysmbc functions. It currently deals with
	all known smbc exceptions. This will generate fancy formatted messages
	for each smbc type.
	"""

	# PERMISSION DENIED
	if isinstance(ex,smbc.PermissionError):
		return smbc_PermissionDenied(redirect)

	# NO ENTRY (doesn't exist)
	elif isinstance(ex,smbc.NoEntryError):
		return smbc_NoEntryError(uri,redirect)

	# NO SPACE LEFT ON DEVICE
	elif isinstance(ex,smbc.NoSpaceError):
		return smbc_NoSpaceError(redirect)

	# FILE OR DIR ALREADY EXISTS
	elif isinstance(ex,smbc.ExistsError):
		return smbc_ExistsError(uri,redirect)

	# DIRECTORY NOT EMPTY
	elif isinstance(ex,smbc.NotEmptyError):
		return smbc_NotEmptyError(uri,redirect)

	# TIMED OUT
	elif isinstance(ex,smbc.TimedOutError):
		return smbc_TimedOutError(redirect)

	# ALL OTHER EXCEPTIONS
	else:
		fatal(ex)

#### SMBC Engine faults
## exceptions generated by pysmbc
def smbc_NoEntryError(uri,redirect=None):
	"""Prints out a nice error for smbc.NoEntryError exceptions
	"""
	return output_error("No such file or directory","The file or directory '" + uri + "' was not found.","smbc.NoEntryError",redirect)

def smbc_NotEmptyError(uri,redirect=None):
	"""Prints out a nice error for smbc.NotEmptyError exceptions
	"""
	return output_error("The directory is not empty","The directory '" + uri + "' is not empty so cannot be deleted.","smbc.NotEmptyError",redirect)

def smbc_PermissionDenied(redirect=None):
	"""Prints out a nice error for smbc.PermissionDenied exceptions
	"""
	return output_error("Permission Denied","You do not have permission to perform the action.","smbc.PermissionError",redirect)

def smbc_ExistsError(uri,redirect=None):
	"""Prints out a nice error for smbc.ExistsError exceptions
	"""
	return output_error("File or directory already exists","The file or directory '" + uri + "' which you attempted to create already exists.","smbc.ExistsError",redirect)

def smbc_NoSpaceError(redirect=None):
	"""Prints out a nice error for smbc.NoSpaceError exceptions
	"""
	return output_error("No space left on device","There is no space left on the server. You may have exceeded your usage allowance/quota",'smbc.NoSpaceError',redirect)

def smbc_TimedOutError(redirect=None):
	"""Prints out a nice error for smbc.TimedOutError exceptions
	"""
	return output_error("Timed out","The current operation timed out. Please try again later.",'smbc.TimedOutError',redirect)

#### Other application faults / user faults
### exceptions generated by bargate

def banned_file(redirect=None):
	"""Returns a template or redirect to return from the view for when a banned file is uploaded.
	"""
	return output_error("Banned File Type","The file type you are trying to upload is banned from being uploaded.","User Error",redirect)

def no_file_attached(redirect=None):
	"""Returns a template or redirect to return from the view for when no file is attached during an upload.
	"""
	return output_error("No file attached","You did not attach a file when attempting to upload","User Error",redirect)

def upload_overwrite_directory(redirect=None):
	"""Returns a template or redirect to return from the view for when a user tries to upload a file over the top of a directory.
	"""
	return output_error("Unable to upload file","A directory already exists with the same name as the file you are trying to upload.","",redirect)

def invalid_item_type(redirect=None):
	"""Returns a template or redirect to return from the view for when an action is performed on an invalid item type.
	"""
	return output_error("Invalid item type","You tried to perform an action on an invalid item type - i.e. a share or printer.","User Error",redirect);

def invalid_item_download(redirect=None):
	"""Returns a template or redirect to return from the view for when an item is downloaded which isn't a file.
	"""
	return output_error("Invalid item type","You tried to download an item other than a file.","User Error",redirect);

def invalid_item_copy(redirect=None):
	"""Returns a template or redirect to return from the view for when a user tries to copy an item other than a file.
	"""
	return output_error("Invalid item type","You tried to copy an item other than a file.","User Error",redirect);

def invalid_path(redirect=None):
	"""Returns a template or redirect to return from the view for when a user navigates to an invalid path.
	"""
	return output_error("Invalid path","You tried to navigate to an invalid or illegal path.","User Error",redirect);

################################################################################
#### Flask error handlers - captures "abort" calls from within flask and our code

@app.errorhandler(500)
def error500(error):
	"""Handles abort(500) calls in code.
	"""
	if not hasattr(g, 'fault_message'):
			g.fault_message = "An unexpected error occured. The error was of type " + str(type(error)) + " and the message was: " + error.__str__()
	if not hasattr(g, 'fault_title'):
		g.fault_title = "Sorry, something went wrong!"


	if 'username' in session:
		usr = session['username']
	else:
		usr = 'Not logged in'

	## send a log aobut this as flask doesn't seem to catch it?
	app.logger.error("""Bargate 500 handler called.

Title:                %s
Message:              %s
HTTP Path:            %s
HTTP Method:          %s
Client IP Address:    %s
User Agent:           %s
User Platform:        %s
User Browser:         %s
User Browser Version: %s
Username:             %s

""" % (
			g.fault_title,
			g.fault_message,
			request.path,
			request.method,
			request.remote_addr,
			request.user_agent.string,
			request.user_agent.platform,
			request.user_agent.browser,
			request.user_agent.version,
			usr,
			
		))

	debug = traceback.format_exc()
	return render_template('error.html',error=error,title=g.fault_title,message=g.fault_message,debug=debug), 500

@app.errorhandler(400)
def error400(error):
	"""Handles abort(400) calls in code.
	"""
	debug = traceback.format_exc()
	return render_template('error.html',error=error,title="Bad Request",message='Your request was invalid, please try again.',debug=debug), 400

@app.errorhandler(403)
def error403(error):
	"""Handles abort(403) calls in code.
	"""
	return render_template('error.html',error=error,title="Permission Denied",message='You do not have permission to access this resource. If you have changed your password recently you must log out and log back in again.'), 403

@app.errorhandler(404)
def error404(error):
	"""Handles abort(404) calls in code.
	"""
	return render_template('error.html',error=error,title="Not found",message="Sorry, I couldn't find what you were after. It might have been eaten."), 404

@app.errorhandler(405)
def error405(error):
	"""Handles abort(405) calls in code.
	"""
	return render_template('error.html',error=error,title="Not allowed",message="Method not allowed. This usually happens when your browser sent a POST rather than a GET, or vice versa"), 405

