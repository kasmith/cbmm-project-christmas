# Functions to run a single trial and write to a file their choices polling every 1/10th of a second
from __future__ import division
import sys,os,random
from physicsTable import *
from physicsTable.constants import *
import pygame as pg
from pygame.locals import *
from pygaze import libscreen, libinput, liblog, libtime
from constants import *
from setup import *
from textParse import *

FRAMEMS = int(1000/FPS)
SCOREWID = 200
BUTTONWID = 400


fixScreen = libscreen.Screen()
fixScreen.draw_fixation(fixtype='cross',pw=3)
def checkFixationDrift(display, tracker):
    checked = False
    while not checked:
        display.fill(fixScreen)
        display.show()
        checked = tracker.drift_correction()

def calcScore(rt, resp, goal):
    if resp == 'NA':
        return 0
    elif resp == goal:
        tdiff = SCORE_MAX - SCORE_MIN
        return max(min(int(100*(SCORE_MAX - rt)/tdiff),100),0)
    else:
        return -10

def drawTable(table, redOnRight, score, fillButton = True, dispScore = True):
    tabledims = table.dim
    midx = int(DISPSIZE[0]/2.)
    assert tabledims[0] < DISPSIZE[0] and tabledims[1] < (DISPSIZE[1] - 100), "Table too big for the screen"
    sc = pg.Surface(DISPSIZE)
    # Find offsets and draw the table
    tboffset = (int((DISPSIZE[0]-tabledims[0])/2.), int((DISPSIZE[1]-tabledims[1]-100)/2.))
    tbdraw = table.draw()
    sc.fill(WHITE)
    bkr = pg.Rect(tboffset[0]-2,tboffset[1]-2,tabledims[0]+4,tabledims[1]+4)
    pg.draw.rect(sc, BLACK, bkr)
    sc.blit(tbdraw, tboffset)
    # Draw the score
    if dispScore:
        scoretop = justifyText("Score:", FONT_L, (midx, tboffset[1] + tabledims[1]+20), CENTER, TOP)
        scorebottom = justifyText(str(score), FONT_L, (midx, tboffset[1] + tabledims[1] + 60), CENTER, TOP)
        sc.blit(scoretop[0], scoretop[1])
        sc.blit(scorebottom[0], scorebottom[1])
    # Draw the buttons
    if redOnRight:
        rcol = RED
        lcol = GREEN
    else:
        rcol = GREEN
        lcol = RED
    lbrect = pg.Rect(int(midx - SCOREWID/2. - BUTTONWID), tboffset[1] + tabledims[1] + 20, BUTTONWID, 60)
    rbrect = pg.Rect(int(midx + SCOREWID/2.), tboffset[1] + tabledims[1] + 20, BUTTONWID, 60)
    if fillButton:
        pg.draw.rect(sc,rcol,rbrect)
        pg.draw.rect(sc,lcol,lbrect)
        rto, rtr = justifyText("m", FONT_VL, (int(midx + SCOREWID/2. + BUTTONWID/2.), tboffset[1] + tabledims[1]+50))
        sc.blit(rto, rtr)
        lto, ltr = justifyText("z", FONT_VL, (int(midx - SCOREWID/2. - BUTTONWID/2.), tboffset[1] + tabledims[1]+50))
        sc.blit(lto, ltr)
    else:
        pg.draw.rect(sc, rcol, rbrect, 4)
        pg.draw.rect(sc, lcol, lbrect, 4)
    return sc

def run(trial, display, pgscreen, tracker, ofl, trackfl, motionType, redOnRight = True, score = 0, subjID = 'None', switch = random.random() < 0.5, trorder = 0, dispscore = True):
    assert motionType in ['Fwd','Rev','None'], "Illegal motion type"

    assert tracker.connected(), "Error: tracker is no longer connected to controller"

    # Make a junk file if ofl is not given, then delete
    if ofl is None:
        ofl = os.tmpfile()
    # Make a junk file if the track file is not given, then delete
    if trackfl is None:
        trackfl = os.tmpfile()

    # Randomize whether this is red or green
    if switch:
        trial.switchRedGreen()

    # Create partial lines (summary and track):
    sum_hdr = subjID + ',' + trial.name + ',' + str(trorder) + ',' + motionType + ','
    if switch:
        sum_hdr += "Switched,"
    else:
        sum_hdr += "Forward,"
    track_hdr = subjID + ',' + trial.name + ','

    # Check for fixation drift
    checkFixationDrift(display, tracker)

    # Set up the trial
    table = trial.makeTable()
    origvel = table.balls.getvel()
    if motionType == 'Rev':
        table.balls.setvel((-origvel[0],-origvel[1]))
    if motionType == 'None':
        table.balls.setvel((0,0))

    runtime = 0
    steps = 0
    atresp = False
    atshow = False
    running = True
    rawresp = None
    rawgoal = None
    rt = -1
    clk = pg.time.Clock()

    tracker.start_recording()
    pgscreen.blit(drawTable(table,redOnRight,score,atresp,True),(0,0))
    display.show()
    pg.event.clear()
    clk.tick()

    while running:
        if DUMMYMODE:
            initpress = pg.event.get(KEYDOWN)
        # Get the sample
        ex, ey = tracker.sample()
        pup = tracker.pupil_size()
        ttime = libtime.get_time()
        trackfl.write(track_hdr + str(runtime) + ',' + str(ttime) + ',' + str(steps) + ',' + str(ex) + ',' + \
                      str(ey) + ',' + str(pup) + ',' + str(atresp) + ',' + str(atshow) + '\n')

        runtime += FRAMEMS
        steps += 1
        # Update physics
        if not (atresp or atshow):
            r = table.step(FRAMEMS / 1000.)
            if runtime >= SHOWTIME:
                atresp = True
        elif atshow:
            r = table.step(FRAMEMS / 1000. * SHOWSPEEDUP)
            if r:
                running = False
                if r == REDGOAL:
                    rawgoal = "R"
                elif r == GREENGOAL:
                    rawgoal = "G"
        else:
            if runtime >= (SHOWTIME + TIME_MAX):
                rawresp = "NA"
                atshow = True
                if motionType == 'None':
                    table.balls.setvel(origvel)

        # Get input
        keypress = pg.event.get(KEYDOWN)
        if DUMMYMODE:
            keypress += initpress
        for e in keypress:
            print e.key
            if quitevent():
                print "Force quit!"
                sys.exit(0)
            elif e.key == K_z and atresp and not atshow:
                atshow = True
                rt = runtime - SHOWTIME
                if motionType == 'None':
                    table.balls.setvel(origvel)
                if redOnRight:
                    rawresp = "G"
                else:
                    rawresp = "R"
            elif e.key == K_m and atresp and not atshow:
                atshow = True
                rt = runtime - SHOWTIME
                if motionType == 'None':
                    table.balls.setvel(origvel)
                if redOnRight:
                    rawresp = "R"
                else:
                    rawresp = "G"


        # Redraw
        pgscreen.blit(drawTable(table, redOnRight, score, atresp, True), (0, 0))
        display.show()

        # And wait
        clk.tick(FPS)

    # Do the final tracker sample
    ex, ey = tracker.sample()
    pup = tracker.pupil_size()
    ttime = libtime.get_time()
    trackfl.write(track_hdr + str(runtime) + ',' + str(ttime) + ',' + str(steps) + ',' + str(ex) + ',' + \
                  str(ey) + ',' + str(pup) + ',' + str(atresp) + ',' + str(atshow) + '\n')
    tracker.stop_recording()

    # Resolve the trial
    if switch:
        if rawresp == "R":
            resp = "G"
        elif rawresp == 'G':
            resp = "R"
        else:
            resp = "NA"
        if rawgoal == "R":
            goal = "G"
        else:
            goal = "R"
    else:
        resp = rawresp
        goal = rawgoal

    newscore = calcScore(rt, resp, goal)

    ofl.write(sum_hdr + str(rt) + ',' + rawresp + ',' + rawgoal + ',' + str(newscore) + ',' + resp + ',' + goal + '\n')
    displayInstructions(str(newscore)+" points", pgscreen, True, False)
    return newscore




'''
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
'''
