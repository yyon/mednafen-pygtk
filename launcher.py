import pygtk
import sys
import os
import gtk
import subprocess
import shutil

#A symple mednafen launcher in pygtk
#Copyright (C) 2012 Ian Campbell

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

alreadybackedup = False

def makedir(dir):
	if not os.path.exists(dir):
		os.makedirs(dir)

class pathsave():
	def __init__(self):
		self.filename = os.path.join(os.getenv("HOME"), ".mednafen/paths.txt")
		self.savenumbers = {"rom":0, "romdir":1, "mcsdir":2, "bakdir":3, "backup":4}
		
		defaultfile = ""
		defaultpath = os.getenv("HOME")
		romdir = os.path.join(os.getenv("HOME"), ".mednafen/rom")
		mcsdir = os.path.join(os.getenv("HOME"), ".mednafen/mcs")
		mcsbakdir = os.path.join(os.getenv("HOME"), ".mednafen/mcs/backup")
		
		if os.path.exists(self.filename) == False:
			self.setfile([defaultfile, romdir, mcsdir, mcsbakdir, str(True)])
	
	def getfile(self):
		file = open(self.filename, "r")
		save = file.read()
		save = save.split("\n")
		file.close()
		
		return save
	
	def setfile(self, save):
		file = open(self.filename, "w")
		contents = "\n".join(save)
		file.write(contents)
		file.close()

	def get(self, name):
		savenumber = self.savenumbers[name]
				
		save = self.getfile()
		
		return save[savenumber]
	
	def set(self, name, value):
		save = self.getfile()
		savenumber = self.savenumbers[name]
		save[savenumber] = value
		
		self.setfile(save)

def getbackupdir(romfile, mcsbakdir):
	name = getromname(romfile)
	
	backupdir = os.path.join(mcsbakdir, name)
	makedir(backupdir)

	return backupdir

def getncqfile(mcsdir, name):
	ncqfile = os.listdir(mcsdir)

	filestoberemoved = []

	for file in ncqfile:
		if file.split(".")[0] != name:
			filestoberemoved.append(file)

	for file in filestoberemoved:
		ncqfile.remove(file)

	if len(ncqfile) == 1:
		#can be backed up
		return os.path.join(mcsdir, ncqfile[0])
	elif len(ncqfile) == 0:
		#no file
		return []
		md = gtk.MessageDialog(self, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE, "No save file")
		md.run()
		md.destroy()
		print "Warning: no file!"
	else:
		#many files
		print "Error: too many files!"
		md = gtk.MessageDialog(self, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, "Multiple Save Files")
		md.run()
		md.destroy()
		
		filter = gtk.FileFilter()
		filter.set_name("Mednafen saved states")
		filter.add_pattern("*.ncq")
		
		new_ncqfile = SelectFile(main_window.window, mcsdir, [filter])
		
		if new_ncqfile == None:
			return None
		else:
			return new_ncqfile

def dobackup(romfile, mcsdir, mcsbakdir):
	global alreadybackedup
	
	if alreadybackedup == False:
		error = False
		
		name = getromname(romfile)
		
		backupdir = getbackupdir(romfile, mcsbakdir)

		backupfiles = sorted(os.listdir(backupdir))
		if backupfiles == []:
			newnumber = 0
		else:
			number = int(backupfiles[-1].split(".")[0])
			newnumber = number + 1
		newnumber = str(newnumber).zfill(4)
		newnumberfile = newnumber + ".ncq"
		
		ncqfile = getncqfile(mcsdir, name)
		
		if ncqfile == None:
			error = True
		elif ncqfile == []:
			pass #No file
		else:
			shutil.copy(ncqfile, os.path.join(backupdir, newnumberfile))
		
		alreadybackedup = True
		
		return error

class main():
	def __init__(self, pathsaver):
		self.pathsaver = pathsaver
		
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_border_width(10)
		self.window.set_title("Mednafen Launcher")
		
		self.window.connect("delete_event", self.windowdelete)
		self.window.connect("destroy", self.windowdestroy)
		
		self.vlayout = gtk.VBox(False, 10)
		
		self.rombox, self.romlabel, self.romentry, self.rombutton = self.createbrowseset(self.vlayout, "Rom", self.browserom, self.pathsaver.get("rom"))
		self.romdirbox, self.romdirlabel, self.romdirentry, self.romdirbutton = self.createbrowseset(self.vlayout, "Rom Dir", self.browseromdir, self.pathsaver.get("romdir"))
		self.mcsbox, self.mcslabel, self.mcsentry, self.mcsbutton = self.createbrowseset(self.vlayout, "Mcs Dir", self.browsemcsdir, self.pathsaver.get("mcsdir"))
		self.bakbox, self.baklabel, self.bakentry, self.bakbutton = self.createbrowseset(self.vlayout, "Backup Dir", self.browsebakdir, self.pathsaver.get("bakdir"))
		
		self.baktogglebox = gtk.HBox(False, 10)
		
		self.baktoggleswitch = gtk.CheckButton("Backup")
		self.baktoggleswitch.set_active(self.pathsaver.get("backup") in ["True", "true"])
		self.baktoggleswitch.connect('notify::active', self.setbaktoggle) 
		self.baktogglebox.pack_start(self.baktoggleswitch)
		self.baktoggleswitch.show()
		
		self.restorebutton = gtk.Button("Restore Backup")
		self.restorebutton.connect("clicked", self.browserestore, None)
		self.baktogglebox.pack_start(self.restorebutton)
		self.restorebutton.show()
		
		self.vlayout.pack_start(self.baktogglebox)
		self.baktogglebox.show()

		self.launchbutton = gtk.Button("Launch")
		self.launchbutton.connect("clicked", self.launch, None)
		self.vlayout.pack_start(self.launchbutton)
		self.launchbutton.show()

		self.window.add(self.vlayout)
		self.vlayout.show()

		self.window.show()
	
	def windowdelete(self, widget, event, data=None):
		return False
	
	def windowdestroy(self, widget, data=None):
		gtk.main_quit()
	
	def getromfile(self):
		romdir = self.romdirentry.get_text()
		romname = self.romentry.get_text()
		romfile = os.path.join(romdir, romname)
		
		return romfile
	
	def getbackupdata(self):
		mcsdir = self.mcsentry.get_text()
		mcsbakdir = self.bakentry.get_text()
		backup = self.baktoggleswitch.get_active()
		romfile = self.getromfile()
		
		return romfile, mcsdir, mcsbakdir, backup
	
	def launch(self, widget, data=None):
		romfile, mcsdir, mcsbakdir, backup = self.getbackupdata()
		self.window.destroy()
		
		launchMednafen(romfile, mcsdir, mcsbakdir, backup)
	
	def createbrowseset(self, container, name, method, default = ""):
		box = gtk.HBox(False, 10)
		
		label = gtk.Label(name + ": ")
		label.set_size_request(100, -1)
		label.set_alignment(0, 0.5)
		box.pack_start(label)
		label.show()
		
		entry = gtk.Entry()
		entry.set_size_request(400, -1)
		entry.connect("activate", method, None)
		entry.set_text(default)
		box.pack_start(entry)
		entry.show()
		
		button = gtk.Button("Browse")
		button.connect("clicked", method, None)	
		box.pack_start(button)
		button.show()
		
		container.pack_start(box)
		box.show()
		
		return box, label, entry, button
	
	def browserom(self, widget, data=None):
		filter = gtk.FileFilter()
		filter.set_name("Gameboy Advanced Rom")
		filter.add_pattern("*.gba")
		
		self.browse("roms", self.getrom, self.romdirentry.get_text(), [filter])
	
	def browserestore(self, widget, data=None):
		filter = gtk.FileFilter()
		filter.set_name("Mednafen saved states")
		filter.add_pattern("*.ncq")
		
		romfile, mcsdir, mcsbakdir, backup = self.getbackupdata()
		dobackup(romfile, mcsdir, mcsbakdir)
		
		self.browse("backups", self.restore, getbackupdir(romfile, mcsbakdir), [filter])
	
	def browseromdir(self, widget, data=None):
		self.browsedir("Rom", self.getromdir, upLevel(self.romdirentry.get_text()))
		
	def browsemcsdir(self, widget, data=None):
		self.browsedir("Mcs", self.getmcsdir, upLevel(self.mcsentry.get_text()))
	
	def browsebakdir(self, widget, data=None):
		self.browsedir("Backup", self.getbakdir, upLevel(self.bakentry.get_text()))
	
	def browse(self, name, method, lookin, filters):
		file = SelectFile(self.window, lookin, filters)
		if file != None:
			method(file)
	
	def browsedir(self, name, method, lookin):
		dir = SelectDir(self.window, lookin, name)
		if dir != None:
			method(dir)
	
	def getrom(self, file):
		romname = file.split("/")[-1]
		self.romentry.set_text(romname)
		self.pathsaver.set("rom", romname)
		
		self.getromdir(upLevel(file))

	def restore(self, file):
		romfile, mcsdir, mcsbakdir, backup = self.getbackupdata()
		name = getromname(romfile)
		ncqfile = getncqfile(mcsdir, name)
		
		shutil.copy(file, ncqfile)
		print file, ncqfile

	def getromdir(self, dir):
		self.romdirentry.set_text(dir)
		self.pathsaver.set("romdir", dir)

	def getmcsdir(self, dir):
		self.mcsentry.set_text(dir)
		self.pathsaver.set("mcsdir", dir)

	def getbakdir(self, bakdir):
		self.bakentry.set_text(dir)
		self.pathsaver.set("bakdir", dir)

	def setbaktoggle(self, widget, data=None):
		self.pathsaver.set("backup", str(self.baktoggleswitch.get_active()))

	def loop(self):
		gtk.main()

def upLevel(path):
	path = path.split("/")
	path = path[:-1]
	path = "/".join(path)
	return path

def SelectFile(parent, directory, filters):
	dialog_buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
						gtk.STOCK_OPEN, gtk.RESPONSE_OK)
	dialog_title = "Select File"
	dialog = gtk.FileChooserDialog(parent=parent, title=dialog_title,
									action=gtk.FILE_CHOOSER_ACTION_OPEN,
									buttons=dialog_buttons, )
	dialog.set_current_folder(directory)
	
	for filter in filters:
		dialog.add_filter(filter)
	
	allfilter = gtk.FileFilter()
	allfilter.set_name("All files")
	allfilter.add_pattern("*")
	dialog.add_filter(allfilter)

	result = None
	
	if dialog.run() == gtk.RESPONSE_OK:
		result = dialog.get_filename()
	
	dialog.destroy()
	
	return result

def SelectDir(parent, directory, name):
	dialog_buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
						gtk.STOCK_OPEN, gtk.RESPONSE_OK)
	dialog_title = "Select "+name+" Directory"
	dialog = gtk.FileChooserDialog(parent=parent, title=dialog_title,
									action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
									buttons=dialog_buttons, )
	dialog.set_current_folder(directory)
	
	result = None
	
	if dialog.run() == gtk.RESPONSE_OK:
		result = dialog.get_filename()
	
	dialog.destroy()
	
	return result

def getromname(romfile):
	return ".".join(romfile.split("/")[-1].split(".")[:-1])

def launchMednafen(romfile, mcsdir, mcsbakdir, backup):
	if romfile != None and romfile != "":
		launch = True
		
		name = getromname(romfile)
		
		if backup:
			backuperror = dobackup(romfile, mcsdir, mcsbakdir)
			if backuperror:
				launch = False
		
		if launch:
			subprocess.call(["mednafen", romfile])

if __name__ == "__main__":
	pathsaver = pathsave()
	for dir in [pathsaver.get("romdir"), pathsaver.get("mcsdir"), pathsaver.get("bakdir")]:
		makedir(dir)
	
	main_window = main(pathsaver)
	main_window.loop()
