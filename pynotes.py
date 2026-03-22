# pyNotes - a python notepad
# Copyright (C) 2026 mrbartix [bartixalt@gmail.com]
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import customtkinter as ctk, tkinter as tk, sys, subprocess
from PIL import ImageTk, Image
from pathlib import *
from tkinter import filedialog
# pdfs for printing
from reportlab.platypus import SimpleDocTemplate, Preformatted
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
if sys.platform == "win32":
    import win32print, win32api

class InfoBox(ctk.CTkToplevel):
    def __init__(self, parent, txt=str, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.geometry("300x80")
        self.title("Info")
        if sys.platform != "win32":
            self.img_path = Path(__file__).resolve().parent / "icon.png"
            self.img = ImageTk.PhotoImage(Image.open(f"{self.img_path}"))
            self.wm_iconphoto(False, self.img)
        else: 
            self.img_path = Path(__file__).resolve().parent / "icon.ico"
            self.iconbitmap(str(self.img_path))
            # fix a bug in CTk which resets the icon after 200ms
            self.after(201, lambda: self.iconbitmap(str(self.img_path)))
        self.label = ctk.CTkLabel(self, text=txt)
        self.label.pack(padx=20, pady=20)
        #
        self.transient(parent)
        self.lift()
        self.attributes("-topmost", True)
        self.after(10, lambda: self.attributes("-topmost", False))
        self.focus_force()

class YesNoPopup(ctk.CTkToplevel):
    def __init__(self, parent, title=str, labelTxt=str, yesAction=None, noAction=None):
        super().__init__(parent)
        self.geometry("250x90")
        if sys.platform != "win32":
            self.img_path = Path(__file__).resolve().parent / "icon.png"
            self.img = ImageTk.PhotoImage(Image.open(f"{self.img_path}"))
            self.wm_iconphoto(False, self.img)
        else: 
            self.img_path = Path(__file__).resolve().parent / "icon.ico"
            self.iconbitmap(self.img_path)
            # fix a bug in CTk which resets the icon after 200ms
            self.after(201, lambda: self.iconbitmap(str(self.img_path)))
        self.title(title)
        self.resizable(False,False)
        self.transient(parent)
        self.focus_force()
        self.Label = ctk.CTkLabel(self, text=labelTxt)
        self.Label.pack()
        self.yes = ctk.CTkButton(self, text="Yes", width=80, fg_color="transparent", command=lambda: [yesAction(), self.destroy()], corner_radius=0, border_width=1, border_color="black", text_color="black")
        self.yes.place(x=30, y=40)
        self.cancel = ctk.CTkButton(self, text="No", width=80, fg_color="transparent", command=lambda: [noAction(), self.destroy()], corner_radius=0, border_width=1, border_color="black", text_color="black")
        self.cancel.place(x=140, y=40)

class PyNotes:
    def __init__(self):
        ctk.set_appearance_mode("light")
        self.filepath = None
        self.modified = False
        self.root = ctk.CTk()
        self.root.resizable(False,False)
        self.root.protocol('WM_DELETE_WINDOW', self.exitapp)
        self.root.geometry("750x650")
        self.root.title("pyNotes")
        self.root.bind("<Button-1>", self.hidemenus) # for closing menus *stupid way*
        if sys.platform != "win32":
            self.img_path = Path(__file__).resolve().parent / "icon.png"
            self.img = ImageTk.PhotoImage(Image.open(f"{self.img_path}"))
            self.root.wm_iconphoto(False, self.img)
        else: 
            self.img_path = Path(__file__).resolve().parent / "icon.ico"
            self.root.iconbitmap(self.img_path)
        ### args
        if len(sys.argv) > 1:
            p = Path(str(sys.argv[1]))
            if p.exists():
                self.filepath = p
            else: raise ValueError("[ERR] This path either doesn't exist, is invalid or something else")
        ###
        self.main_bar = ctk.CTkFrame(self.root, 750, 25, corner_radius=0)
        self.main_bar.pack_propagate(0)
        self.main_bar.grid_propagate(0)
        self.main_bar.pack()
        ##
        # define the 'file' men -> bind all of the functions to it
        self.fmenu = tk.Menu(self.root, tearoff=0)
        self.fmenu.add_command(label="    New                       Ctrl+N", command=self.new)
        self.fmenu.add_command(label="    Open...                 Ctrl+O", command=self.openfile)
        self.fmenu.add_command(label="    Save                      Ctrl+S", command=self.save)
        self.fmenu.add_command(label="    Save As...      Ctrl+Shift+S", command=self.saveas)
        self.fmenu.add_command(label="    Print...                  Ctrl+P", command=self.print)
        self.fmenu.add_command(label="    Exit", command=self.exitapp)
        ##
        self.file_button = ctk.CTkButton(self.main_bar, 40, 25, text="File", fg_color="transparent", corner_radius=0, text_color="black")
        self.file_button.bind("<Button-1>", lambda event: self.showmenu(self.fmenu, self.file_button, event))
        self.file_button.grid(column=0, row=0)
        self.info_button = ctk.CTkButton(self.main_bar, 40, 25, text="Info", fg_color="transparent", corner_radius=0, text_color="black", command=self.openInfo)
        self.info_button.grid(column=1, row=0)
        ###
        self.mtextbox = ctk.CTkTextbox(self.root, 750, 625)
        if self.filepath:
            with open(self.filepath, "r") as f:
                txt = f.read()
            self.mtextbox.insert("1.0", txt)
            self.mtextbox.edit_modified(False)
            self.modified = False
        self.mtextbox.bind("<<Modified>>", self._on_modified)
        self.mtextbox.pack()
        ###
        self.toplevel_window = None

        ### keyboard
        self.root.bind("<Control-n>", lambda e: self.new())
        self.root.bind("<Control-o>", lambda e: self.openfile())
        self.root.bind("<Control-s>", lambda e: self.save())
        self.root.bind("<Control-Shift-S>", lambda e: self.saveas())
        self.root.bind("<Control-p>", lambda e: self.print())

    def execute(self):
        self.root.mainloop()
    def showmenu(self, menuvar, buttonvar, event):
        x = buttonvar.winfo_rootx()
        y = buttonvar.winfo_rooty() + buttonvar.winfo_height()
        menuvar.post(x, y)
        if sys.platform != "win32": menuvar.grab_set()
    def hidemenus(self, *args, **kwargs):
        try:
            self.fmenu.unpost()
            if sys.platform != "win32": self.fmenu.grab_release()
        except: pass
    def openInfo(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = InfoBox(self.root, txt="pyNotes - a notepad app made in python\n(C) mrbartix 2026 (GPL v3.0)")  # create window if its None or destroyed
        else:
            self.toplevel_window.focus()  # if window exists focus it
    def saveas(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            with open(path, "w") as f:
                f.write(self.mtextbox.get("1.0", "end"))
            self.modified = False
    def save(self):
        if not self.filepath:
            self.saveas()
            return
        with open(self.filepath, "w") as f:
            f.write(self.mtextbox.get("1.0", "end"))
        self.modified = False
    def exitapp(self):
        if self.modified:
            YesNoPopup(self.root, "Are you sure?", "Are you sure you want to exit?", yesAction=lambda: exit(0), noAction=lambda: self.ppass)
        else: exit(0)
    def _load_file_openfile(self, path):
        with open(path, "r") as f:
            self.mtextbox.delete("1.0", "end")
            self.mtextbox.insert("1.0", f.read())
        self.mtextbox.edit_modified(False)
        self.modified = False
    def _on_modified(self, event):
        if self.mtextbox.edit_modified():
            self.modified = True
            self.mtextbox.edit_modified(False)
    def openfile(self):
        path = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not path: return
        if self.modified == True:
            YesNoPopup(self.root, "Are you sure?", "Are you sure you want to\noverride your unsaved file?", yesAction=lambda: self._load_file_openfile(path), noAction=lambda: self.ppass)
        else: self._load_file_openfile(path)
    def new(self):
        if self.modified == True:
            YesNoPopup(self.root, "Are you sure?", "Are you sure you want to\noverride your unsaved file?", yesAction=lambda: self.mtextbox.delete("1.0", "end"), noAction=lambda: self.ppass)
        else: self.mtextbox.delete("1.0", "end")
    ### PRINTING
    def print(self):
        text = self.mtextbox.get("1.0", "end-1c")
        filename = Path(__file__).resolve().parent / ".tempn.pdf"
        pdfmetrics.registerFont(TTFont("Mono", "DejaVuSansMono.ttf"))
        doc = SimpleDocTemplate(str(filename))
        styles = getSampleStyleSheet()
        style = styles["Normal"]
        style.fontName = "Mono"
        text = text.replace("\t", "    ")
        story = [Preformatted(text, style)]
        doc.build(story)
        ###
        if sys.platform == "linux" or sys.platform == "darwin": # darwin -> macos
            try:
                subprocess.run(["lpr", str(filename)], check=True)
                printwindow = InfoBox(self.root, txt="Printing...")
                printwindow.after(3000, printwindow.destroy)
                subprocess.run(["rm", str(filename)], check=True)
            except Exception as e: 
                print(f"[ERR]: Printing failed, either something is wrong, you don't have a printer or something else; {e}")
        elif sys.platform == "win32":
            try:
                printer_name = win32print.GetDefaultPrinter()
                win32api.ShellExecute(0, "printto", str(filename), f'"{printer_name}"', ".", 0)
                printwindow = InfoBox(self.root, txt="Printing...")
                printwindow.after(3000, printwindow.destroy())
                subprocess.run(["del", str(filename)], check=True)
            except Exception as e: 
                print(f"[ERR]: Printing failed, either something is wrong, you don't have a printer or something else; {e}")
        else: print("You aren't on linux, macos or windows - sorry!")
    def ppass(self):
        pass # this exists because im lazy and its the fastest way to get around a problem (i can't pass 'pass' to lambda)

if __name__ == "__main__":
    pyNotes = PyNotes()
    pyNotes.execute()
