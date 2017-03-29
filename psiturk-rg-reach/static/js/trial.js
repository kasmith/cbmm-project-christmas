/* 
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/* global cp*, Table, Ball, Wall, Occluder, Goal */

// Variables for timing
var TIMEPERSTEP = .025;
var TIMEPERPOLL = .1;


var assert = function(value, message)
{
	if (!value) {
		throw new Error('Assertion failed: ' + message);
	}
};

Button = function(color, elemname, txt, font) {
    this.color = color;
    this.ele = document.getElementById(elemname);
    this.ctx = this.ele.getContext('2d');
    this.txt = txt;
    
    // Setup the drawing
    var wid = this.ele.width;
    var hgt = this.ele.height;
    $('#'+elemname).css({'border-color':this.color});
    
    var boxleft = 0;
        
    this.ctx.fillStyle = color;
    this.ctx.strokeStyle = 'black';
    this.ctx.fillRect(boxleft,0,wid,hgt);
    //this.ctx.strokeRect(boxleft,0,this.boxwid,hgt);
    

    console.log(font);
    console.log(txt)
    if (font === undefined)
        font = '30px Times New Roman bold';
    console.log(font)
    this.ctx.font = font;
    this.ctx.fillStyle = 'black';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText(this.txt, boxleft + wid/2, hgt/2);
    
    this.draw();
};

Button.prototype.draw = function(clear) {
    if (typeof(clear)==='undefined') clear = false;
    if (clear) this.ctx.clearRect(0,0,this.ele.width,this.ele.height);
    else {
        //this.ctx.fillStyle = this.color;
        //this.ctx.fillRect(0,0,this.ele.width,this.ele.height);
        this.ctx.fillStyle = 'black';
        this.ctx.fillText(this.txt, this.ele.width/2, this.ele.height/2);
    }
};

ScoreDisp = function(elemname) {
    this.ele = document.getElementById(elemname);
    this.ctx = this.ele.getContext('2d');
    this.score = 0;
};

ScoreDisp.prototype.add = function(sc) {
    this.score += sc;
};
ScoreDisp.prototype.draw = function() {
    var ewid = this.ele.width;
    var ehgt = this.ele.height;
    
    this.ctx.clearRect(0,0,this.ele.width,this.ele.height);
    
    this.ctx.font = '20px Times New Roman bold';
    this.ctx.fillStyle = 'black';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'top';
    this.ctx.fillText('Score:',ewid/2,0);
    
    this.ctx.textBaseline = 'bottom';
    this.ctx.fillText(this.score, ewid/2,ehgt);
    
};
ScoreDisp.prototype.reset = function() {
    this.score = 0;
};


TrialCounter = function(elemname) {
    this.ele = document.getElementById(elemname);
    this.ctx = this.ele.getContext('2d');
    this.count = 1;
    this.numtrials = 1;
    this.display = false;
};

TrialCounter.prototype.incr = function() {
    this.count += 1;
};
TrialCounter.prototype.setnumtrials = function(numtrials) {
    this.numtrials = numtrials;
}
TrialCounter.prototype.draw = function() {
    if (!this.display) return;

    var ewid = this.ele.width;
    var ehgt = this.ele.height;
    
    this.ctx.clearRect(0,0,this.ele.width,this.ele.height);
    
    this.ctx.font = '20px Times New Roman bold';
    this.ctx.fillStyle = 'black';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'top';
    this.ctx.fillText('Trial:',ewid-40,0);
    
    this.ctx.textBaseline = 'bottom';
    this.ctx.fillText(this.count+'/'+this.numtrials,ewid-40,ehgt);
    this.ctx.fillStyle = 'white';
    
};
TrialCounter.prototype.reset = function() {
    this.count = 1;
};

/**
 * 
 * @param {array} keys - array of keys to keep track of (using jquery numbering)
 * @param {function} onkeypress - a function that takes in the key pressed and gets called when
 *                           one of the tracked keys is pressed
 * @param {function} onkeyrelease - like onkeypress, but for when a key is released
 * @returns {KeyHandler}
 */
KeyHandler = function(keys, onkeypress, onkeyrelease) {
    this.keys = keys;
    this.state = {};
    for (i=0;i<keys.length;i++) {
        this.state[keys[i]] = false;
    }
    
    this.onkp = onkeypress;
    this.onkr = onkeyrelease;
    
    // Set handlers
    var that = this;
    var k;
    $(document).keydown(function(event) {
        k = event.which;
        if (that.keys.indexOf(k+"") > -1) {
            if (that.state[k] === false) {
                that.state[k] = true;
                that.onkp(k);
            }
        }
    });
    $(document).keyup(function(event) {
        k = event.which;
        if (that.keys.indexOf(k+"") > -1) {
            that.state[k] = false;
            that.onkr(k);
        }
    });
};
KeyHandler.prototype.getstate = function() {return this.state;};
KeyHandler.prototype.setpress = function(fn) {this.onkp = fn;};
KeyHandler.prototype.setrelease = function(fn) {this.onkr = fn;};

TIME_BEGIN = 0.3;
TIME_END = 2.0;

Trial = function(table, textbox, leftbtn, rightbtn, score, trcounter, redonleft) {
    this.rol = redonleft;
    this.tbele = tbele = document.getElementById(table);
    if (redonleft) {lbtxt = 'Yes: Z'; rbtxt = 'No: M';}
    else {lbtxt = 'No: Z'; rbtxt = 'Yes: M';}
    this.txtele = document.getElementById(textbox);
    this.txtbox = new Button(WHITE,textbox,'Can the ball reach the goal?','26px Times New Roman bold');
    this.lbtn = new Button(BLACK,leftbtn,lbtxt);
    this.rbtn = new Button(BLACK,rightbtn,rbtxt);
    this.score = new ScoreDisp(score);
    this.trcounter = new TrialCounter(trcounter);
    this.response = NORESPONSE; 
    this.resptime = -1;
    this.goalin = false;
    this.motioncond = 1;
    this.done = false;
    this.paused = false;

    assert(tbele.getContext,'No support for canvases!');
    
    this.tb = new Table('tmp',tbele.width,tbele.height,tbele);
    
    this.keymap = {
        32: 'space',
        77: 'm',
        90: 'z'
    };
    // Initialize handler with no functions
    this.keyhandler = new KeyHandler(
        Object.keys(this.keymap),
        function(k) {},
        function(k) {});
    
};
Trial.prototype.loadTrial = function(trfile) {
    this.tb = loadTrial(trfile,this.tbele);
    this.done = false;
    this.response = NORESPONSE;
    this.resptime = -1;
};
Trial.prototype.loadFromTList = function(trname, trlist) {
    this.tb = trlist.loadTrial(trname, this.tbele);
    this.done = false;
    this.response = NORESPONSE;
    this.resptime = -1;
};
Trial.prototype.draw = function(flash) {
    if (flash === 'undefined')
        flash = true;

    this.tb.draw();
    this.txtbox.draw(true);
    this.txtbox.draw();
    this.lbtn.draw(flash);
    this.rbtn.draw(flash);
    this.score.draw();
    this.trcounter.draw();
};
Trial.prototype.step = function(dt) {
    var e = this.tb.step(dt);
    // Do event handling here
    this.draw();
    return e;
};
Trial.prototype.gettrialsteps = function(dt) {
    var tableclone = this.tb.clone();
    
    var nsteps = 0;
    var e = 0;
    while (e === 0) { e = tableclone.step(dt); nsteps++; }
    return nsteps;
};
Trial.prototype.gettrialgoal = function(dt) {
    var tableclone = this.tb.clone();
    
    var e = 0;
    while (e === 0) 
        e = tableclone.step(dt);
    return e;
};

Trial.prototype.displaytext = function(text, textcol, bkcol,hideall) {
    if (typeof(bkcol)==='undefined') bkcol = "white";
    if (typeof(textcol)==='undefined') textcol = "black";
    if (text.substring(0,6) === "<span>") htmtext = text;
    else htmtext = "<span>"+text+"</span>";
    var wid = this.tbele.width;
    var hgt = this.tbele.height;
    $("#"+this.tbele.id).hide(0);
    if (typeof(hideall)!== "undefined" & hideall) {
        $("#"+this.txtbox.ele.id).hide(0);
        $("#"+this.lbtn.ele.id).hide(0);
        $("#"+this.score.ele.id).hide(0);
        $("#"+this.rbtn.ele.id).hide(0);
        $("#"+this.trcounter.ele.id).hide(0);
    }
    
    
    tf = $('#textfield');
    tf.html(htmtext);
    tf.css({'background-color':bkcol,'color':textcol});
    tf.show(0); 
    
};
Trial.prototype.hidetext = function() {
    $("#"+this.tbele.id).show(0);
    
    $("#"+this.txtbox.ele.id).show(0);
    $("#"+this.lbtn.ele.id).show(0);
    $("#"+this.score.ele.id).show(0);
    $("#"+this.rbtn.ele.id).show(0);
    $("#"+this.trcounter.ele.id).show(0);
    $('#textfield').hide(0);
};
Trial.prototype.showinstruct = function(text,textcol,bkcol, callback, hideall) {
    this.displaytext(text,textcol,bkcol,hideall);
    // Wait until a click
    var that = this;
    this.keyhandler.setpress(function(k) {
        if (k===32) {
            that.hidetext();
            that.keyhandler.setpress(function(k) {});
            callback();
        }
    });
};

Trial.prototype.replaceText = function(newtext,textcol,bkcol) {
    this.oldtext = $('#textfield').html();
    this.displaytext(newtext,textcol,bkcol);
};

Trial.prototype.restoreText = function(textcol,bkcol) {
    this.displaytext(this.oldtext,textcol,bkcol);
    this.oldtext = '';
};

Trial.prototype.writenewscore = function(newscore,showscore) {
    var tx1 = "You earned " + newscore + " points on this trial";
    var tx2 = "Press spacebar to continue";
    
    var ctx = this.tbele.getContext('2d');
    ctx.font = "30px Times New Roman";
    ctx.fillStyle = 'black';
    ctx.strokeStyle = 'black';
    ctx.textAlign = 'center';
    
    var newwid = 10 + Math.max(ctx.measureText(tx1).width,ctx.measureText(tx2).width);
    
    var centx = this.tbele.width/2;
    var centy = this.tbele.height/2;
    
    ctx.clearRect(centx - newwid/2, centy - 37.5, newwid, 75);
    ctx.strokeRect(centx - newwid/2, centy - 37.5, newwid, 75);
    
    if (typeof(showscore) === 'undefined' || !showscore) {
        ctx.textBaseline = 'top';
        ctx.fillText(tx1,centx,centy - 32.5);
        ctx.textBaseline = 'bottom';
        ctx.fillText(tx2,centx,centy + 32.5);
    }
    else {
        ctx.textBaseline = 'middle';
        ctx.fillText(tx2,centx,centy);
    }
};
Trial.prototype.showtrial = function(dt,displaytime,responsetime,maxtime,callback,showscore) {
    var that = this;
    // store trial ball vel
    var vel = this.tb.ball.getvel();

    // function to be called after subject response
    var finishtrial = function() {
        that.keyhandler.setpress(function(k) {});

        // set ball vel back to original, if it was set to 0
        if (that.motioncond == 0) {
            that.tb.ball.setvel(vel['x'], vel['y']);
	}
        // display trial ending for feedback at triple speed
        var pev = 0;
        interid = setInterval(function () {
            pev = that.tb.step(dt,maxtime);

            that.draw(true);

            if (pev !== 0) {
                //assert(pev !== TIMEUP, "Oddly, your trial ran too long");
                if (pev === TIMEUP)
                    console.log('Debug: Trial timeup')
                clearInterval(interid);

                // Update score
                if (that.response === NORESPONSE) {
                    score = 0;
                }
                else if (that.goalin !== that.response) {
                    score = -10;
                }
                else {
                    score = 100 * (1 - (that.resptime-TIME_BEGIN)/(TIME_END-TIME_BEGIN)); 
                    score = Math.round(Math.max(Math.min(score,100),0));
                }
                that.score.add(score);
                that.draw(true);
                that.writenewscore(score,showscore);
                that.done = true;
                that.lastscore = score;
                
                that.keyhandler.setpress(function(k) {
                    if (k===32) { 
                        that.hidetext();
                        that.keyhandler.setpress(function(k) {});
                        callback();
                    }
                });

            }
        }, dt*1000 / 3); 
    };

    // function to be called after trial display, to wait for response
    var waitresponse = function() {
        // Flash something to sinalize beginning of response period
        that.draw(false);

        var timeoutid;
        var start = new Date();
        that.keyhandler.setpress(function(k) {
            if (k===77) { 
                that.keyhandler.setpress(function(k) {});
                clearTimeout(timeoutid);
                that.resptime = (new Date() - start) / 1000;
                if (that.rol) that.response = false;
                else that.response = true;
                finishtrial();
            }
            else if (k===90) {
                that.keyhandler.setpress(function(k) {});
                clearTimeout(timeoutid);
                that.resptime = (new Date() - start) / 1000;
                if (that.rol) that.response = true;
                else that.response = false;
                finishtrial();
            }
        });
        // Possible race condition, multiple calls to finishtrial
        timeoutid = setTimeout(finishtrial, responsetime*1000);
    };

    // set ball vel by motion condition
    this.tb.ball.setvel(vel['x']*this.motioncond, vel['y']*this.motioncond);
    // display trial 
    var pev = 0;
    interid = setInterval(function () {
        pev = that.tb.step(dt,displaytime);

        that.draw(true);

        if (pev !== 0) {
            assert(pev === TIMEUP, "Oddly, your trial ended too soon");
            clearInterval(interid);
            waitresponse();
        }
    }, dt*1000);
};

// Keep only the correct goal, either in (goal in is true),
// or out (goalin is false)
Trial.prototype.goalinout = function(goalin) {
    if (goalin) 
        if (this.tb.goals[0].onret === GREENGOAL) 
            this.tb.goals.splice(1, 1);
        else
            this.tb.goals.splice(0, 1);
    else 
        if (this.tb.goals[0].onret === GREENGOAL) 
            this.tb.goals.splice(0, 1);
        else
            this.tb.goals.splice(1, 1);

    this.tb.goals[0].color = RED;
};

Trial.prototype.isgoalin= function() {
    return this.goalin;
};

Trial.prototype.runtrial = function(dt,displaytime,responsetime,maxtime,callback,motioncond,goalcond,showscore) {
    if (typeof(goalcond) === 'undefined') 
        goalcond = (Math.random() < 0.5);
    this.goalin = (goalcond != 'out');
    console.log(this.goalin)
    this.goalinout(this.goalin);

    // assign motion condition value
    if (motioncond === 'static')
        this.motioncond = 0;
    else if (motioncond === 'forward')
        this.motioncond = 1;
    else if (motioncond === 'reverse')
        this.motioncond = -1;
    else // generate random motion condition if undefined, one of {-1,0,1}
        this.motioncond = Math.floor(Math.random()*3)-1; 

    var that = this;
    var runfn = function() {that.showtrial(dt,displaytime,responsetime,maxtime,callback,showscore);};
    this.showinstruct('Press the spacebar to begin','black','lightgrey',runfn, true);
};

