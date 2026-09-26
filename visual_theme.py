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


class StripedTreeview(ttk.Treeview):
    """Alternância visual sem substituir tags de alertas das linhas."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._stripe_job=None
        self._hovered=''
        self._sort_column=None
        self._sort_reverse=False
        self.tag_configure('_hover',background='#E1C699')
        self.tag_configure('_even',background=SURFACE)
        self.tag_configure('_odd',background='#E8DECE')
        self.bind('<Motion>',self._hover,add='+')
        self.bind('<Leave>',lambda _:self._set_hover(''),add='+')
        self.bind('<Destroy>',self._cleanup,add='+')

    def _cleanup(self,event):
        if event.widget is self and self._stripe_job:
            self.after_cancel(self._stripe_job)
            self._stripe_job=None

    def _queue_stripes(self):
        if self._stripe_job is None:self._stripe_job=self.after_idle(self._stripe)

    def insert(self,*args,**kwargs):
        result=super().insert(*args,**kwargs)
        self._queue_stripes()
        return result

    def delete(self,*items):
        super().delete(*items)
        self._queue_stripes()

    def move(self,*args):
        super().move(*args)
        self._queue_stripes()

    def heading(self,column,option=None,**kwargs):
        if 'text' in kwargs and 'command' not in kwargs:
            kwargs['command']=lambda:self.sort_by(column)
        return super().heading(column,option,**kwargs)

    def sort_by(self,column):
        self._sort_reverse=not self._sort_reverse if self._sort_column==column else False
        self._sort_column=column
        self._queue_stripes()

    def _sort_key(self,iid):
        import re,unicodedata
        value=unicodedata.normalize('NFKD',self.set(iid,self._sort_column)).casefold()
        value=''.join(c for c in value if not unicodedata.combining(c))
        return tuple((1,int(part)) if part.isdigit() else (0,part) for part in re.split(r'(\d+)',value))

    def _stripe(self):
        self._stripe_job=None
        if self._sort_column is not None:
            for index,iid in enumerate(sorted(self.get_children(),key=self._sort_key,reverse=self._sort_reverse)):
                super().move(iid,'',index)
        for index,iid in enumerate(self.get_children()):
            tags=[t for t in self.item(iid,'tags') if t not in ('_even','_odd')]
            self.item(iid,tags=tags+['_odd' if index%2 else '_even'])

    def _set_hover(self,iid):
        if iid==self._hovered:return
        if self._hovered and self.exists(self._hovered):
            self.item(self._hovered,tags=[t for t in self.item(self._hovered,'tags') if t!='_hover'])
        self._hovered=iid
        if iid and self.exists(iid):self.item(iid,tags=list(self.item(iid,'tags'))+['_hover'])

    def _hover(self,event):
        self._set_hover(self.identify_row(event.y))
