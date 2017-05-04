# Functions to run a single trial and write to a file their choices polling every 1/10th of a second
from __future__ import division
import sys,os,random
import pygame as pg
from pygame.locals import *

sharepath = os.path.join(os.path.dirname(__file__),'..','SharedCode')
trpath = os.path.join(os.path.dirname(__file__),'..','Trials')
sys.path.insert(1,sharepath)
sys.path.insert(1,trpath)

pg.font.init()
FONT_L = pg.font.SysFont(None,48)

from dynamicTable import *
from dynamicTrial import *
from ReadExpInputs import *

def quitevent(quit_k = [K_LSHIFT,K_ESCAPE]):
    keys = pg.key.get_pressed()
    for k in quit_k:
        if keys[k] == 0:
            return False
    return True

def runTrial(trial,screen, wrtfl = None, redbarpos = RIGHT, score = 0,subjID = 'None', switch = random.random() < 0.5, ord = 0, dispscore = True):
    
    # Make a junk file if wrtfl is not given, then delete
    if wrtfl is None: wrtfl = os.tmpfile()
    
    # Randomize red/green
    if switch: trial.switchRedGreen()
    # Calculate number of steps per frame or polling
    stepperframe = int(1000/FPS)
    stepperpoll = int(1000/POLLPS)
    
    # File partial lines
    trhdr = subjID + ',' + trial.name + ',' + str(ord) + ','
    if switch: trhdr += 'Rev,'
    else: trhdr += 'Reg,'
    
    # Set up the screen and dimensions
    dims = (trial.dim[0], trial.dim[1]+100)
    scoff = (int((screen.get_width() - dims[0])/2),int((screen.get_height() - dims[1])/2))
    if scoff[0] < 0 or scoff[1] < 0: raise Exception('Screen too small for the trial')
    screen.fill(WHITE)
    
    trsc = pg.Surface(dims)
    ctr1off = (0,trial.dim[1]+25)
    ctr2off = (dims[0] - 400, trial.dim[1]+25)
    
    # Make the rectangles displaying the red/green buttons
    key1 = pg.Surface((50,50))
    if redbarpos == RIGHT: key1.fill(GREEN); k1txt = FONT_L.render('z',True,BLACK,GREEN)
    elif redbarpos == LEFT: key1.fill(RED); k1txt = FONT_L.render('z',True,BLACK,RED)
    else: raise Exception('Need to provide RIGHT or LEFT to redbarpos argument')
    k1txtsize = FONT_L.size('z')
    key1.blit(k1txt, (int((50-k1txtsize[0])/2),int((50-k1txtsize[1])/2)))
    k1pos = (400,trial.dim[1]+25)
    
    key2 = pg.Surface((50,50))
    if redbarpos == RIGHT: key2.fill(RED); k2txt = FONT_L.render('m',True,BLACK,RED)
    elif redbarpos == LEFT: key2.fill(GREEN); k2txt = FONT_L.render('m',True,BLACK,GREEN)
    else: raise Exception('Need to provide RIGHT or LEFT to redbarpos argument')
    k2txtsize = FONT_L.size('m')
    key2.blit(k2txt, (int((50-k2txtsize[0])/2),int((50-k2txtsize[1])/2)))
    k2pos = (dims[0] - 450,trial.dim[1]+25)
    
    # Make the part of the screen that displays the score
    scsz1 = FONT_L.size('Score:')
    scsz2 = FONT_L.size(str(score))
    #scsz = (max(scsz1[0],scsz2[0]), scsz1[1] + scsz2[1])
    scsz = (180,scsz1[1] + scsz2[1])
    scoresc = pg.Surface(scsz)
    scoresc.fill(WHITE)
    scp1 = (int((scsz[0] - scsz1[0])/2),0)
    scp2 = (int((scsz[0] - scsz2[0])/2),scsz1[1])
    scoresc.blit(FONT_L.render('Score:',True,BLACK,WHITE),scp1)
    scoresc.blit(FONT_L.render(str(score),True,BLACK,WHITE),scp2)
    scorepos = (int((trsc.get_width() - scsz[0])/2), trial.dim[1] + int((100 - scsz[1])/2))
    
    # Run through the trial once, counting steps and correct answer
    tb = trial.makeTable()
    polls = 0
    steps = 0
    winner = None
    
    running = True
    while running:
        r = tb.physicsstep()
        steps += 1
        if steps % stepperpoll == 0: polls += 1
        if r == RED: winner = RED; running = False
        elif r == GREEN: winner = GREEN; running = False
    
    # Set up the trial screen, greying out field until spacebar click
    if redbarpos == RIGHT:
        ctr1 = ScoreCounter(GREEN,MAXTIME*POLLPS,LEFT)
        ctr2 = ScoreCounter(RED,MAXTIME*POLLPS,RIGHT)
    else:
        ctr1 = ScoreCounter(RED,MAXTIME*POLLPS,LEFT)
        ctr2 = ScoreCounter(GREEN,MAXTIME*POLLPS,RIGHT)
    
    trsc.fill(WHITE)
    pg.draw.rect(trsc,LIGHTGREY,pg.Rect((0,0),trial.dim))
    trsc.blit(ctr1.draw(),ctr1off)
    trsc.blit(ctr2.draw(),ctr2off)
    trsc.blit(key1,k1pos)
    trsc.blit(key2,k2pos)
    trsc.blit(scoresc,scorepos)
    
    moveontxt = FONT_L.render('Press spacebar to start the trial',True,BLACK,LIGHTGREY)
    trsc.blit(moveontxt, (int((trial.dim[0] - moveontxt.get_width())/2), int((trial.dim[1] - moveontxt.get_height())/2)))
    
    screen.blit(trsc,scoff)
    pg.display.flip()
    
    running = True
    while running:
        for event in pg.event.get():
            if event.type == QUIT: sys.exit(0)
            elif quitevent(): sys.exit(0)
            elif event.type == KEYDOWN and event.key == K_SPACE: running = False
            
    # Reset and run the trial
    tb = trial.makeTable()
    trsc.fill(WHITE)
    trsc.blit(tb.draw(),(0,0))
    trsc.blit(ctr1.draw(),ctr1off)
    trsc.blit(ctr2.draw(),ctr2off)
    trsc.blit(key1,k1pos)
    trsc.blit(key2,k2pos)
    trsc.blit(scoresc,scorepos)
    screen.blit(trsc,scoff)
    pg.display.flip()
    
    
    trsteps = 0
    running = True
    clk = pg.time.Clock()
    while running:
        r = tb.physicsstep()
        trsteps += 1
        
        if trsteps % stepperpoll == 0:
            keys = pg.key.get_pressed()
            wrtfl.write(trhdr + str(trsteps) + ',')
            if keys[K_z] == True and keys[K_m] == False:
                ctr1.add()
                if redbarpos == RIGHT:
                    wrtfl.write('Green,')
                    if switch: wrtfl.write('Red\n')
                    else: wrtfl.write('Green\n')
                else:
                    wrtfl.write('Red,')
                    if switch: wrtfl.write('Green\n')
                    else: wrtfl.write('Red\n')
            elif keys[K_m] == True and keys[K_z] == False:
                ctr2.add()
                if redbarpos == RIGHT:
                    wrtfl.write('Red,')
                    if switch: wrtfl.write('Green\n')
                    else: wrtfl.write('Red\n')
                else:
                    wrtfl.write('Green,')
                    if switch: wrtfl.write('Red\n')
                    else: wrtfl.write('Green\n')
            else:
                wrtfl.write('None,None\n')
        
        if trsteps % stepperframe == 0:
            trsc.fill(WHITE)
            trsc.blit(tb.draw(),(0,0))
            trsc.blit(ctr1.draw(),ctr1off)
            trsc.blit(ctr2.draw(),ctr2off)
            trsc.blit(key1,k1pos)
            trsc.blit(key2,k2pos)
            trsc.blit(scoresc,scorepos)
            screen.blit(trsc,scoff)
            pg.display.flip()
            clk.tick(FPS)
        
        for event in pg.event.get():
            if event.type == QUIT: sys.exit(0)
            elif quitevent(): sys.exit(0)
            
        if r == RED or r == GREEN: running = False
    
    # Count up the amount of red/green and assign a score
    if redbarpos == RIGHT:
        redpct = ctr2.count / polls
        greenpct = ctr1.count / polls
    else:
        redpct = ctr1.count / polls
        greenpct = ctr2.count / polls
    
    if winner == RED: points = DEFPPT + (MAXPPT - DEFPPT)*redpct - (MAXPPT - DEFPPT)*greenpct
    else: points = DEFPPT + (MAXPPT - DEFPPT)*greenpct - (MAXPPT - DEFPPT)*redpct
    
    points = int(points)
    
    score += points
    scoresc.fill(WHITE)
    scoresc.blit(FONT_L.render('Score:',True,BLACK,WHITE),scp1)
    scp2 = (int((scsz[0] - FONT_L.size(str(score))[0])/2),scsz1[1])
    scoresc.blit(FONT_L.render(str(score),True,BLACK,WHITE),scp2)
    
    tb = trial.makeTable()
    trsc.fill(WHITE)
    trsc.blit(tb.draw(),(0,0))
    trsc.blit(ctr1.draw(),ctr1off)
    trsc.blit(ctr2.draw(),ctr2off)
    trsc.blit(key1,k1pos)
    trsc.blit(key2,k2pos)
    trsc.blit(scoresc,scorepos)
    
    if dispscore:
        disptxt = 'You earned {0!s} points on this trial'
    else:
        disptxt = '  '
    txsz1 = FONT_L.size(disptxt.format(points))
    txsz2 = FONT_L.size('Press spacebar to continue')
    txsc = pg.Surface((max(txsz1[0],txsz2[0])+10,txsz1[1] + txsz2[1] + 10))
    txsc.fill(WHITE)
    pg.draw.rect(txsc,BLACK,txsc.get_rect(),2)
    txp1 = (int((txsc.get_width() - txsz1[0])/2)+3,5)
    txp2 = (int((txsc.get_width() - txsz2[0])/2)+3,txsz1[1]+5)
    txsc.blit(FONT_L.render(disptxt.format(points),True,BLACK),txp1)
    txsc.blit(FONT_L.render('Press spacebar to continue',True,BLACK),txp2)
        
    trsc.blit(txsc,(int((trsc.get_width()-txsc.get_width())/2),int((trsc.get_height()-txsc.get_height())/2)))
    
    screen.blit(trsc,scoff)
    pg.display.flip()
    
    
    running = True
    while running:
        for event in pg.event.get():
            if event.type == QUIT: sys.exit(0)
            elif quitevent(): sys.exit(0)
            elif event.type == KEYDOWN and event.key == K_SPACE: running = False
            
    return trial.name, winner, points, redpct, greenpct
    
    

class ScoreCounter(object):
    
    def __init__(self,color, maxcount,direction = RIGHT, size = (400,50)):
        self.barcol = color
        self.dir = direction
        self.maxcount = maxcount
        self.size = size
        self.count = 0
        self.sc = pg.Surface(self.size)
        
    def add(self, inc = 1): self.count += inc
    
    def draw(self):
        self.sc.fill(WHITE)
        pg.draw.rect(self.sc,self.barcol,pg.Rect((0,0),(self.size[0]-1,self.size[1]-1)),2)
        
        rembars = self.size[0] - 4
        propfill = self.count / self.maxcount
        
        fbars = propfill * rembars
        
        if self.dir == RIGHT: begpt = (2,2)
        elif self.dir == LEFT: begpt = (self.size[0] - 1 - fbars,2)
        else: raise Exception('Not right direction in Score Counter')
        
        if self.count > 0: pg.draw.rect(self.sc,self.barcol,pg.Rect(begpt,(fbars,self.size[1]-4)))
        
        return self.sc
    
    
if __name__ == '__main__':
    
    pg.init()
    sc = pg.display.set_mode((1280,1024))
    score = 0
    
    fl = open('test.csv','w')
    fl.write('SubjID,TrialName,TrialOrder,RegRev,Timestep,Choice,NormChoice\n')
    
    if random.random() < 0.5: rpos = RIGHT
    else: rpos = LEFT
    
    if len(sys.argv) == 1:
        score += (runTrial(tr1,sc,fl,redbarpos = rpos,score = score))[2]
        score += (runTrial(tr2,sc,fl,redbarpos = rpos,score = score))[2]
        score += (runTrial(tr3,sc,fl,redbarpos = rpos,score = score))[2]
        score += (runTrial(tr5,sc,fl,redbarpos = rpos,score = score))[2]
    else:
        trnm = sys.argv[1]
        trpth = os.path.join('..','Trials',trnm + '.ptr')
        tr = loadTrial(trpth)
        runTrial(tr,sc,fl,redbarpos = rpos,score=score,switch = False)
    