# This file is part of the daspos-umbrella package.
#
# For copyright and licensing information about this package, see the
# NOTICE.txt and LICENSE.txt files in its top-level directory; they are
# available at https://github.com/crcresearch/daspos-umbrella
#
# Licensed under the MIT License (MIT);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import hashlib
import json
import urllib2
from Tkinter import *
from os import path
from tkFileDialog import askopenfilename

try:
    ttk_imported = True
    from ttk import Button, Style
except ImportError:
    print "Umbrella Spec Validator: ttk module not installed"
    ttk_imported = False

class ValidatorUI(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent)

        self.parent = parent
        self.width = 400
        self.height = 200
        self.center_window()
        self.msg_str_line1 = StringVar()
        self.msg_str_line2 = StringVar()
        self.msg_str_line3 = StringVar()
        self.errors = dict()
        self.err_flag = False
        self.filename_entry = None
        self.filename_str = StringVar()
        self.err_popup = None

        self.init_ui()

    def init_ui(self):
        self.parent.title("Umbrella Spec Validator")

        if ttk_imported:
            self.parent.resizable(0, 0)
            self.style = Style()

            try:
                self.style.theme_use("vista")
            except _tkinter.TclError:
                self.style.theme_use("default")
        else:
            self.parent.resizable(1, 0)

        self.pack(fill=BOTH, expand=1)

        self.init_entry()
        self.init_bttns()

    def center_window(self):
        sw = self.parent.winfo_screenwidth()
        sh = self.parent.winfo_screenheight()


        x = (sw - self.width)/2
        y = (sh - self.height)/2
        self.parent.geometry('%dx%d+%d+%d' % (self.width, self.height, x, y))

    def init_bttns(self):
        bttn_frame = Frame(self.parent)

        Button(bttn_frame, text='Validate', command=self.check_validity).pack(side=LEFT, pady=10, padx=3)
        Button(bttn_frame, text='Exit', command=root.quit).pack(side=LEFT, pady=10, padx=3)

        bttn_frame.pack(side=BOTTOM)

    def init_entry(self):
        # Filepath entry field
        entry_frame = Frame(self.parent)

        # Message Label
        Label(entry_frame, text="", textvariable=self.msg_str_line1, width=self.width, font="Arial 10 bold").pack(side=TOP)
        Label(entry_frame, text="", textvariable=self.msg_str_line2, width=self.width).pack(side=TOP)
        Label(entry_frame, text="", textvariable=self.msg_str_line3, width=self.width).pack(side=TOP)

        self.update_label("Welcome to the Umbrella Spec Validator!")

        # File Entry
        Label(entry_frame, text='Spec File Path: ').pack(side=LEFT, padx=10, pady=10)
        self.filename_entry = Entry(entry_frame, textvariable=self.filename_str, width=33)
        self.filename_entry.pack(side=LEFT, pady=20)
        Button(entry_frame, text="Search", command=self.browse_for_spec).pack(side=LEFT, padx=10, pady=10)

        entry_frame.pack(side=TOP)

    def browse_for_spec(self):
        Tk().withdraw()
        filename = askopenfilename()
        self.filename_str.set(filename)

    def popup_err(self):
        # Initialize new popup window
        self.err_popup = Tk()
        self.err_popup.title("Errors Found")

        # Add Scrollbar
        scrollbar = Scrollbar(self.err_popup)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Initialize Error Messages
        err_count = 0
        max_len = 0
        listbox = Listbox(self.err_popup)
        listbox.pack(side=LEFT, fill=BOTH, expand=1)

        for filename, source_list in self.errors.iteritems():
            filename_written = False
            for source, error_list in source_list.iteritems():
                if len(error_list) is not 0:
                    err_count += len(error_list)
                    file_line = " " + filename + ":"
                    source_line = "    " + source + ":"

                    # Write filename
                    if not filename_written:
                        filename_written = True
                        listbox.insert(END, "\n")
                        listbox.insert(END, file_line)

                    # Write url
                    listbox.insert(END, source_line)

                    # Write Errors
                    for err_line in error_list:
                        listbox.insert(END, err_line)

                    # Update required width of window
                    if max_len < max(len(file_line), len(source_line), len(err_line)):
                        max_len = max(len(file_line), len(source_line), len(err_line)) + 5

        # Write Title
        listbox.insert(0, " " + str(err_count) + " ERRORS FOUND:")

        # Add Error Message
        listbox.config(width=max_len, height=20)
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)

        # Pop up the window
        self.err_popup.mainloop()

        # Reset the error dictionary and flag
        self.errors = dict()
        self.err_flag = False

    def calculate_md5(self, url, data):
        filename = data["filename"]
        url_index = data["sources"].index(url)
        reported_size = data["size"]

        try:
            remote = urllib2.urlopen(url)
        except urllib2.HTTPError:
            self.err_flag = True
            self.errors[filename][url].append("       HTTP Error 404: Not Found")
            return None

        try:
            f_size = float(remote.headers['content-length'])
        except KeyError:
            f_size = reported_size

        hash = hashlib.md5()
        size_downloaded = 0.0
        size_prev_downloaded = float(f_size*url_index)
        tot_size_to_download = float(f_size*len(data["sources"]))

        while True:
            data = remote.read(10240)
            if not data:
                percent_downloaded = int((f_size + size_prev_downloaded)/tot_size_to_download * 100)
                self.update_label("Validating MD5 checksums...", filename + ": " + str(percent_downloaded) + "%")
                break
            else:
                size_downloaded += 10240.0

            hash.update(data)
            percent_downloaded = int((size_downloaded + size_prev_downloaded)/ tot_size_to_download * 100)
            self.update_label("Validating MD5 checksums...", filename + ": " + str(percent_downloaded) + "%")

        if int(f_size) != int(reported_size):
            self.err_flag = True
            self.errors[filename][url].append("       Incorrect file size. True size: " + str(f_size) + " B")

        return hash.hexdigest()

    def update_label(self, l1, l2=None, l3=None):
        self.msg_str_line1.set(" ")
        self.msg_str_line2.set(" ")
        self.msg_str_line3.set(" ")

        if l1:
            self.msg_str_line1.set(l1)
        if l2:
            self.msg_str_line2.set(l2)
        if l3:
            self.msg_str_line3.set(l3)

        self.parent.update_idletasks()

    def truncate_path(self, path, size=36):
        trunc_beginning = str()
        trunc_end = str()
        directory_list = path.split("/") if "/" in path else path.split("\\")

        char_ct = 0
        i = 0

        if len(path) > size:
            while char_ct < size:
                trunc_beginning += directory_list[i] + "/"

                if directory_list[-(i+1)] is not directory_list[i]:
                    trunc_end = "/" + directory_list[-(i+1)] + trunc_end
                    i += 1
                    char_ct = len(trunc_beginning) + 3 + len(trunc_end)
                else:
                    break

            return trunc_beginning + "... " + trunc_end
        else:
            return path

    def open_file(self, filename):
        if len(filename.strip()) is 0:
            return None

        # Incorrect File Path
        if not path.isfile(filename):
            self.update_label("File not found.")

            return None

        # Open File
        with open(str(filename)) as fp:
            try:
                spec = json.load(fp)
            # Can't Load the Spec
            except ValueError:
                self.update_label("Can't load file %s" % self.truncate_path(filename))
                self.filename_entry.delete(0, END)
                spec = None

        # Can't Load the Spec
        if spec is None:
            self.update_label("Can't load file %s" % self.truncate_path(filename))
            self.filename_entry.delete(0, END)

        return spec

    def check_validity(self):
        # Open Spec
        filename = self.filename_entry.get()
        spec = self.open_file(filename)
        if spec is None:
            return

        self.update_label("Validating...")

        # Read Spec Contents
        files = list()
        missing = list()
        if "package_manager" in spec:
            for name, config in spec["package_manager"]["config"].iteritems():
                files.append({"filename": name,
                              "sources": config["source"],
                              "md5": config["checksum"],
                              "size": config["size"]})

        if "software" in spec:
            for name, software in spec["software"].iteritems():
                files.append({"filename": name,
                              "sources": software["source"],
                              "md5": software["checksum"],
                              "size": software["size"]})
        if "data" in spec:
            for name, data in spec["data"].iteritems():
                files.append({"filename": name,
                              "sources": data["source"],
                              "md5": data["checksum"],
                              "size": data["size"]})

        if "os" in spec:
            files.append({"filename": spec["os"]["name"],
                          "sources": spec["os"]["source"],
                          "md5": spec["os"]["checksum"],
                          "size": spec["os"]["size"]})
        else:
            missing.append("os")

        if "hardware" not in spec:
            missing.append("hardware")

        if "kernel" not in spec:
            missing.append("kernel")



        if len(missing) is not 0:
            self.update_label("File is not umbrella spec:", self.truncate_path(filename), "Missing " + ", ".join(missing))
            self.filename_entry.delete(0, END)
            return

        for data in files:
            filename = data["filename"]
            self.errors[filename] = dict()
            for url in data["sources"]:
                self.errors[filename][url] = list()
                md5 = self.calculate_md5(url, data)
                if md5 and md5 != data["md5"]:
                    self.err_flag = True
                    self.errors[filename][url].append("       Hash incorrect. Given: " + data["md5"] + ", Calculated: " + md5)

        if not self.err_flag:
            self.update_label("Validation successful")
            self.parent.bell()

        else:
            self.update_label("Validation unsuccessful")
            self.filename_entry.delete(0, END)
            self.popup_err()

if __name__ == "__main__":
    root = Tk()
    root.geometry("250x150+300+300")
    app = ValidatorUI(root)
    root.mainloop()

