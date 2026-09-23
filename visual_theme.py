"""Identidade Papéis de Marte e superfícies adaptáveis à área disponível."""
import tkinter as tk
from tkinter import ttk, font

BG='#F6F1E8'
SURFACE='#FFFCF7'
CREAM='#EADCC8'
RED='#7A2E3A'
RED_DARK='#59212B'
OLIVE='#55613F'
GOLD='#C79A5A'
MUTED='#716355'
COFFEE='#3A2417'
ROSE='#D8B08C'
BODY='Segoe UI'
HEADING='Georgia'


def configure_fonts(root):
    global BODY, HEADING
    available=set(font.families(root))
    BODY=next((f for f in ('Libre Franklin','Montserrat','Segoe UI','DejaVu Sans') if f in available),'TkDefaultFont')
    HEADING=next((f for f in ('Cormorant Garamond','Garamond','Georgia','DejaVu Serif') if f in available),'TkDefaultFont')
    root.option_add('*Font',(BODY,10))
    return BODY,HEADING


def maximize(window):
    """Use the Windows work area, preserving taskbar and close controls."""
    try:window.state('zoomed')
    except tk.TclError:
        try:window.attributes('-zoomed',True)
        except tk.TclError:
            window.geometry(f'{window.winfo_screenwidth()}x{max(300,window.winfo_screenheight()-60)}+0+0')


class ScrollArea(tk.Frame):
    """Keep minimum content dimensions reachable rather than clipping controls."""
    def __init__(self,parent,*,background=BG,min_width=900,min_height=720):
        super().__init__(parent,bg=background)
        self.columnconfigure(0,weight=1);self.rowconfigure(0,weight=1)
        self.canvas=tk.Canvas(self,bg=background,highlightthickness=0)
        self.canvas.grid(row=0,column=0,sticky='nsew')
        self.vertical=ttk.Scrollbar(self,orient='vertical',command=self.canvas.yview)
        self.horizontal=ttk.Scrollbar(self,orient='horizontal',command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vertical.set,xscrollcommand=self.horizontal.set)
        self.content=tk.Frame(self.canvas,bg=background)
        self.window=self.canvas.create_window((0,0),window=self.content,anchor='nw')
        self.min_width=min_width;self.min_height=min_height
        self.canvas.bind('<Configure>',self.resize)
        self.content.bind('<Configure>',lambda _:self.refresh())
        self.canvas.bind('<MouseWheel>',self.wheel)
        self.canvas.bind('<Button-4>',lambda _:self.canvas.yview_scroll(-3,'units'))
        self.canvas.bind('<Button-5>',lambda _:self.canvas.yview_scroll(3,'units'))

    def wheel(self,event):
        self.canvas.yview_scroll(-1 if event.delta>0 else 1,'units')

    def refresh(self):
        class Size:pass
        size=Size();size.width=self.canvas.winfo_width();size.height=self.canvas.winfo_height()
        self.resize(size)

    def resize(self,event):
        required_height=max(self.min_height,self.content.winfo_reqheight())
        width=max(event.width,self.min_width);height=max(event.height,required_height)
        self.canvas.itemconfigure(self.window,width=width,height=height)
        self.canvas.configure(scrollregion=(0,0,width,height))
        if event.height<required_height:self.vertical.grid(row=0,column=1,sticky='ns')
        else:self.vertical.grid_remove()
        if event.width<self.min_width:self.horizontal.grid(row=1,column=0,sticky='ew')
        else:self.horizontal.grid_remove()

    def reset(self):
        self.canvas.xview_moveto(0);self.canvas.yview_moveto(0)
