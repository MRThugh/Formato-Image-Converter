"""
Separate GUI widgets used in app.py
"""
import tkinter as tk
from tkinter import ttk

class FileListFrame(tk.Frame):
    """Frame to show selected files with simple columns."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.tree = ttk.Treeview(self, columns=("name","format","size"), show="headings", height=8)
        self.tree.heading("name", text="Name")
        self.tree.heading("format", text="Format")
        self.tree.heading("size", text="Size")
        self.tree.pack(fill="both", expand=True)
    def add(self, filename, fmt, size):
        self.tree.insert("", "end", values=(filename, fmt, size))
    def clear(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
