"""Safe, portable formatting for the recipe's Tk text editor."""
import json
import re

TAGS=('bold','highlight')

def normalize_format(value):
    if not value:return '{}'
    try:
        data=json.loads(value) if isinstance(value,str) else value
        if not isinstance(data,dict) or any(k not in TAGS for k in data):raise ValueError()
        clean={}
        for tag,ranges in data.items():
            if not isinstance(ranges,list):raise ValueError()
            checked=[]
            for pair in ranges:
                if not isinstance(pair,(list,tuple)) or len(pair)!=2:raise ValueError()
                if any(not isinstance(v,str) or not re.fullmatch(r'[1-9][0-9]*\.[0-9]+',v) for v in pair):raise ValueError()
                if tuple(map(int,pair[0].split('.')))>=tuple(map(int,pair[1].split('.'))):raise ValueError()
                checked.append(list(pair))
            if checked:clean[tag]=checked
        return json.dumps(clean,sort_keys=True,separators=(',',':'))
    except (ValueError,TypeError,OverflowError) as exc:
        raise ValueError('Formatação da receita inválida.') from exc

def read_format(editor):
    data={}
    for tag in TAGS:
        ranges=list(map(str,editor.tag_ranges(tag)))
        pairs=[]
        for a,b in zip(ranges[::2],ranges[1::2]):
            end=editor.index('end-1c')
            if editor.compare(b,'>',end):b=end
            if editor.compare(a,'<',b):pairs.append([a,b])
        data[tag]=pairs
    return normalize_format(data)

def load_format(editor,value):
    try:data=json.loads(normalize_format(value))
    except ValueError:data={}
    for tag in TAGS:
        editor.tag_remove(tag,'1.0','end')
        for a,b in data.get(tag,[]):editor.tag_add(tag,a,b)

def toggle_selection(editor,tag):
    if tag not in TAGS:raise ValueError('Formato desconhecido.')
    selected=editor.tag_ranges('sel')
    if len(selected)!=2:return False
    a,b=selected
    # Remove only when the whole selection already has the requested style.
    ranges=editor.tag_ranges(tag)
    covered=any(editor.compare(start,'<=',a) and editor.compare(end,'>=',b)
                for start,end in zip(ranges[::2],ranges[1::2]))
    if covered:editor.tag_remove(tag,a,b)
    else:editor.tag_add(tag,a,b)
    editor.focus_set()
    return True
