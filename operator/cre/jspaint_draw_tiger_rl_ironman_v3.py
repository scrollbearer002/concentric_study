#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import subprocess
import time
from pathlib import Path

import Quartz

from art_geometry import strokes_bbox
from reference_board import build_generic_reference_board

ROOT = Path(__file__).resolve().parent
FINAL_SCREENSHOT = ROOT / 'jspaint_tiger_rl_ironman_v3_final.png'

BLACK='rgb(0,0,0)'; RED='rgb(255,0,0)'; GOLD='rgb(255,255,0)'; ORANGE='rgb(255,128,64)'; BROWN='rgb(128,64,0)'; SILVER='rgb(192,192,192)'; CYAN='rgb(0,255,255)'; WHITE='rgb(255,255,255)'


def _osascript(script:str)->str:
    r=subprocess.run(['osascript','-e',script],capture_output=True,text=True,timeout=25,check=False)
    return (r.stdout or '').strip()

def _do_js(js:str)->str:
    one=' '.join(js.split())
    esc=one.replace('\\','\\\\').replace('"','\\"')
    return _osascript(f'tell application "Safari" to do JavaScript "{esc}" in current tab of front window')

def _open():
    subprocess.run(['open','-a','Safari','https://jspaint.app/'],check=True,timeout=5)
    subprocess.run(['osascript','-e','tell application "Safari" to activate'],check=True)
    time.sleep(3)

def _maximize():
    _osascript('''tell application "Safari" to activate
    tell application "System Events"
      tell process "Safari"
        try
          click menu item "Fill" of menu "Window" of menu bar 1
        end try
      end tell
    end tell''')
    time.sleep(0.8)

def _bounds()->tuple[int,int,int,int]:
    out=_osascript('tell application "Safari" to get bounds of front window')
    parts=[int(p.strip()) for p in out.split(',')]
    return tuple(parts)  # type: ignore[return-value]

def _canvas_info()->dict[str,float]:
    out=_do_js("""(function(){const c=document.querySelectorAll('canvas')[0]; if(!c) return ''; const r=c.getBoundingClientRect(); return JSON.stringify({url:location.href,width:c.width,height:c.height,left:r.left,top:r.top,cssWidth:r.width,cssHeight:r.height,innerWidth:window.innerWidth,innerHeight:window.innerHeight});})();""")
    return json.loads(out)

def _palette_info()->dict[str,tuple[float,float]]:
    out=_do_js("""(function(){return JSON.stringify(Array.from(document.querySelectorAll('.swatch.color-button')).map((el)=>{const r=el.getBoundingClientRect(); return {color:el.getAttribute('data-color'),cx:r.left+r.width/2,cy:r.top+r.height/2};}));})();""")
    payload=json.loads(out)
    return {e['color']:(float(e['cx']),float(e['cy'])) for e in payload}

def _tool_info()->dict[str,tuple[float,float]]:
    out=_do_js("""(function(){return JSON.stringify(Array.from(document.querySelectorAll('.tool')).map((el)=>{const r=el.getBoundingClientRect(); return {title:el.title,cx:r.left+r.width/2,cy:r.top+r.height/2};}));})();""")
    payload=json.loads(out)
    return {e['title']:(float(e['cx']),float(e['cy'])) for e in payload}

def _clear():
    _do_js("""(function(){const c=document.querySelectorAll('canvas')[0]; const ctx=c.getContext('2d'); ctx.fillStyle='white'; ctx.fillRect(0,0,c.width,c.height); return 'ok';})();""")

def _gp(x:float,y:float,origin:tuple[float,float])->tuple[float,float]:
    return (origin[0]+x,origin[1]+y)

def _click(pt:tuple[float,float]):
    x,y=pt
    d=Quartz.CGEventCreateMouseEvent(None,Quartz.kCGEventLeftMouseDown,Quartz.CGPointMake(x,y),Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap,d); time.sleep(0.03)
    u=Quartz.CGEventCreateMouseEvent(None,Quartz.kCGEventLeftMouseUp,Quartz.CGPointMake(x,y),Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap,u); time.sleep(0.1)

def _choose_tool(title:str,win_origin:tuple[float,float],tools:dict[str,tuple[float,float]]):
    _click(_gp(*tools[title],win_origin))

def _choose_color(color:str,win_origin:tuple[float,float],palette:dict[str,tuple[float,float]]):
    _click(_gp(*palette[color],win_origin))

def _draw(points:list[tuple[float,float]],canvas_origin:tuple[float,float],delay:float=0.004):
    if len(points)<2: return
    pts=[_gp(x,y,canvas_origin) for x,y in points]
    x0,y0=pts[0]
    d=Quartz.CGEventCreateMouseEvent(None,Quartz.kCGEventLeftMouseDown,Quartz.CGPointMake(x0,y0),Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap,d); time.sleep(0.04)
    for x,y in pts[1:]:
        ev=Quartz.CGEventCreateMouseEvent(None,Quartz.kCGEventLeftMouseDragged,Quartz.CGPointMake(x,y),Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap,ev); time.sleep(delay)
    xe,ye=pts[-1]
    u=Quartz.CGEventCreateMouseEvent(None,Quartz.kCGEventLeftMouseUp,Quartz.CGPointMake(xe,ye),Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap,u); time.sleep(0.05)

def _smooth(points:list[tuple[float,float]],n:int=8)->list[tuple[float,float]]:
    if len(points)<2: return points
    out=[points[0]]
    for i in range(len(points)-1):
        ax,ay=points[i]; bx,by=points[i+1]
        for k in range(1,n+1):
            t=k/n; out.append((ax+(bx-ax)*t, ay+(by-ay)*t))
    return out

def _oval(cx:float,cy:float,rx:float,ry:float,n:int=30):
    return [(cx+rx*math.cos(2*math.pi*i/n), cy+ry*math.sin(2*math.pi*i/n)) for i in range(n+1)]

def _line(x1:float,y1:float,x2:float,y2:float):
    return [(x1,y1),(x2,y2)]

def _arc(cx:float,cy:float,rx:float,ry:float,a0:float,a1:float,n:int=18):
    pts=[]
    for i in range(n+1):
        t=i/n; ang=math.radians(a0+(a1-a0)*t)
        pts.append((cx+rx*math.cos(ang), cy+ry*math.sin(ang)))
    return pts

def _transform_groups(groups, cw:float, ch:float):
    all_strokes=[]
    for _,items in groups:
        for item in items:
            all_strokes.append(item['points'])
    min_x,min_y,max_x,max_y=strokes_bbox(all_strokes)
    bw=max_x-min_x; bh=max_y-min_y
    left,right,top,bottom=cw*0.24,cw*0.24,ch*0.05,ch*0.06
    uw,uh=cw-left-right, ch-top-bottom
    scale=min(uw/bw, uh/bh)
    tx0=left+(uw-bw*scale)/2; ty0=top+(uh-bh*scale)/2
    def tx(p): return (tx0+(p[0]-min_x)*scale, ty0+(p[1]-min_y)*scale)
    out=[]
    for color,items in groups:
        g=[]
        for item in items:
            d={'kind':item['kind'],'points':[tx(p) for p in item['points']]}
            if 'fill_point' in item: d['fill_point']=tx(item['fill_point'])
            g.append(d)
        out.append((color,g))
    return out

def _groups():
    cx=500.0; hy=210.0
    orange=[]; red=[]; gold=[]; silver=[]; black=[]; cyan=[]; brown=[]
    head=_smooth(_oval(cx,hy,118,102),4)
    l_ear=_smooth(_oval(cx-72,hy-85,30,38),4)
    r_ear=_smooth(_oval(cx+72,hy-85,30,38),4)
    muzzle=_smooth(_oval(cx,hy+44,54,36),4)
    torso=_smooth([(370,320),(630,320),(680,500),(645,860),(355,860),(320,500),(370,320)],8)
    l_arm=_smooth([(370,390),(255,455),(225,665),(300,760),(380,695),(370,390)],8)
    r_arm=_smooth([(630,390),(745,455),(775,665),(700,760),(620,695),(630,390)],8)
    l_leg=_smooth([(435,860),(405,1040),(490,1040),(505,860),(435,860)],8)
    r_leg=_smooth([(565,860),(510,1040),(595,1040),(565,860)],8)
    l_boot=_smooth([(390,1040),(505,1040),(515,1072),(378,1072),(390,1040)],8)
    r_boot=_smooth([(495,1040),(610,1040),(622,1072),(485,1072),(495,1040)],8)
    l_shoulder=_smooth([(372,338),(300,372),(340,430),(402,388),(372,338)],8)
    r_shoulder=_smooth([(628,338),(700,372),(660,430),(598,388),(628,338)],8)
    tail=_smooth([(668,785),(745,760),(807,807),(816,873),(753,895),(685,865),(668,785)],8)
    faceplate=_smooth([(450,145),(474,118),(526,118),(550,145),(540,190),(460,190),(450,145)],8)
    badge=_smooth(_oval(590,430,22,20),4)
    reactor=_smooth(_oval(500,495,34,34),4)
    collar_l=_smooth([(430,322),(468,388),(470,505),(432,430),(430,322)],8)
    collar_r=_smooth([(570,322),(532,388),(530,505),(568,430),(570,322)],8)
    orange += [
        {'kind':'closed','points':head,'fill_point':(500,210)},
        {'kind':'closed','points':l_ear,'fill_point':(428,128)},
        {'kind':'closed','points':r_ear,'fill_point':(572,128)},
        {'kind':'closed','points':tail,'fill_point':(750,835)},
    ]
    silver += [{'kind':'closed','points':muzzle,'fill_point':(500,255)}]
    red += [
        {'kind':'closed','points':torso,'fill_point':(500,585)},
        {'kind':'closed','points':l_arm,'fill_point':(286,566)},
        {'kind':'closed','points':r_arm,'fill_point':(714,566)},
        {'kind':'closed','points':l_leg,'fill_point':(448,955)},
        {'kind':'closed','points':r_leg,'fill_point':(555,955)},
        {'kind':'closed','points':l_boot,'fill_point':(450,1055)},
        {'kind':'closed','points':r_boot,'fill_point':(555,1055)},
        {'kind':'closed','points':faceplate,'fill_point':(500,150)},
    ]
    gold += [
        {'kind':'closed','points':l_shoulder,'fill_point':(348,380)},
        {'kind':'closed','points':r_shoulder,'fill_point':(652,380)},
        {'kind':'closed','points':badge,'fill_point':(590,430)},
    ]
    cyan += [{'kind':'closed','points':reactor,'fill_point':(500,495)}]
    brown += [
        {'kind':'closed','points':_smooth([(450,325),(550,325),(530,370),(470,370),(450,325)],8),'fill_point':(500,340)}
    ]
    black += [
        {'kind':'stroke','points':head},{'kind':'stroke','points':l_ear},{'kind':'stroke','points':r_ear},{'kind':'stroke','points':muzzle},
        {'kind':'stroke','points':_smooth(_arc(cx-34,hy+2,18,10,205,340),5)},
        {'kind':'stroke','points':_smooth(_arc(cx+34,hy+2,18,10,200,335),5)},
        {'kind':'stroke','points':_smooth(_line(489,252,500,274),5)},{'kind':'stroke','points':_smooth(_line(500,274,511,252),5)},{'kind':'stroke','points':_smooth(_line(500,274,500,297),5)},
        {'kind':'stroke','points':_smooth(_line(500,297,475,309),5)},{'kind':'stroke','points':_smooth(_line(500,297,525,309),5)},
        {'kind':'stroke','points':_smooth(_line(463,276,406,268),5)},{'kind':'stroke','points':_smooth(_line(463,292,404,296),5)},
        {'kind':'stroke','points':_smooth(_line(537,276,594,268),5)},{'kind':'stroke','points':_smooth(_line(537,292,596,296),5)},
        {'kind':'stroke','points':_smooth(_line(500,118,500,78),5)},{'kind':'stroke','points':_smooth(_line(473,136,458,90),5)},{'kind':'stroke','points':_smooth(_line(527,136,542,90),5)},
        {'kind':'stroke','points':_smooth([(430,150),(394,188),(420,215)],8)},{'kind':'stroke','points':_smooth([(570,150),(606,188),(580,215)],8)},
        {'kind':'stroke','points':_smooth([(452,194),(425,230),(448,254)],8)},{'kind':'stroke','points':_smooth([(548,194),(575,230),(552,254)],8)},
        {'kind':'stroke','points':_smooth([(477,118),(468,150),(481,174)],8)},{'kind':'stroke','points':_smooth([(523,118),(532,150),(519,174)],8)},
        {'kind':'stroke','points':torso},{'kind':'stroke','points':l_arm},{'kind':'stroke','points':r_arm},{'kind':'stroke','points':l_leg},{'kind':'stroke','points':r_leg},{'kind':'stroke','points':l_boot},{'kind':'stroke','points':r_boot},{'kind':'stroke','points':l_shoulder},{'kind':'stroke','points':r_shoulder},{'kind':'stroke','points':tail},
        {'kind':'stroke','points':badge},{'kind':'stroke','points':reactor},{'kind':'stroke','points':collar_l},{'kind':'stroke','points':collar_r},
        {'kind':'stroke','points':_smooth(_line(500,322,500,860),8)},{'kind':'stroke','points':_smooth([(430,323),(468,420),(494,610),(505,860)],9)},{'kind':'stroke','points':_smooth([(570,323),(532,420),(506,610),(495,860)],9)},
        {'kind':'stroke','points':_smooth([(385,470),(455,446),(472,500),(401,522),(385,470)],8)},{'kind':'stroke','points':_smooth([(615,470),(545,446),(528,500),(599,522),(615,470)],8)},
        {'kind':'stroke','points':_smooth(_line(590,420,607,420),4)},{'kind':'stroke','points':_smooth(_line(599,412,599,440),4)},{'kind':'stroke','points':_smooth(_line(484,495,516,495),4)},{'kind':'stroke','points':_smooth(_line(500,479,500,511),4)},
        {'kind':'stroke','points':_smooth([(705,800),(767,782),(792,804)],8)},
    ]
    return [(ORANGE,orange),(SILVER,silver),(RED,red),(GOLD,gold),(CYAN,cyan),(BROWN,brown),(BLACK,black)]

def main():
    board=build_generic_reference_board(
        request='Draw a Tiger Wearing Ralph Lauren everything inspired by Iron Man from Marvel comics.',
        primary_subject='tiger', anatomy_anchor='tiger anatomy', identity_anchor='Ralph Lauren Polo visual identity', style_anchor='Iron Man armor from Marvel comics',
        must_have_parts=['full tiger figure','recognizable tiger face and stripes','Ralph Lauren cue','red and gold armor tailoring','smaller centered composition'],
        must_avoid=['canvas clipping','generic cat drift','missing lower body','scanline fill artifacts'],
        style_notes=['Use tiger anatomy first and keep the head connected to the body.','Use fill tool for solid masses and pencil for detail.','Keep generous canvas margins for the full figure.'],
        pose='connected full-body hero pose with compact centered composition', camera_angle='straight-on character poster view', passes=['outline','fill masses','detail','verification'])
    board.save_split_artifacts(ROOT,'jspaint_tiger_rl_ironman_v3')
    _open(); _maximize(); time.sleep(1)
    b=_bounds(); info=_canvas_info(); palette=_palette_info(); tools=_tool_info(); _clear(); time.sleep(0.2)
    x1,y1,x2,y2=b; aw=x2-x1; ah=y2-y1; cl=max(0.0,(aw-info['innerWidth'])/2.0); ct=max(0.0,ah-info['innerHeight'])
    canvas_origin=(x1+cl+info['left'], y1+ct+info['top']); win_origin=(x1+cl,y1+ct)
    groups=_transform_groups(_groups(), float(info['cssWidth']), float(info['cssHeight']))
    print(f"[jspaint-tiger-v3] url={info['url']}")
    print(f"[jspaint-tiger-v3] bounds={b}")
    print(f"[jspaint-tiger-v3] canvas_origin_pt=({canvas_origin[0]:.1f}, {canvas_origin[1]:.1f})")
    print(f"[jspaint-tiger-v3] canvas_size_pt=({float(info['cssWidth']):.1f}, {float(info['cssHeight']):.1f})")
    _choose_color(BLACK,win_origin,palette); _choose_tool('Pencil',win_origin,tools)
    for color,items in groups:
        if color!=BLACK:
            for item in items: _draw(item['points'],canvas_origin,0.0038)
    _choose_tool('Fill With Color',win_origin,tools)
    for color,items in groups:
        if color==BLACK: continue
        _choose_color(color,win_origin,palette)
        for item in items:
            if 'fill_point' in item: _click(_gp(item['fill_point'][0], item['fill_point'][1], canvas_origin))
        time.sleep(0.08)
    _choose_color(BLACK,win_origin,palette); _choose_tool('Pencil',win_origin,tools)
    for color,items in groups:
        if color==BLACK:
            for i,item in enumerate(items,1):
                _draw(item['points'],canvas_origin,0.0038 if len(item['points'])>20 else 0.0045)
                if i%10==0: time.sleep(0.08)
    time.sleep(1.0)
    subprocess.run(['screencapture','-x',str(FINAL_SCREENSHOT)],check=True)
    print(f'[done] {FINAL_SCREENSHOT}')

if __name__=='__main__':
    main()
