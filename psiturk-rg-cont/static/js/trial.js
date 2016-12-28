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

Button = function(onleft, color, elemname) {
    this.color = color;
    this.ele = document.getElementById(elemname);
    this.ctx = this.ele.getContext('2d');
    this.onleft = onleft;
    
    // Setup the drawing
    var wid = this.ele.width;
    var hgt = this.ele.height;
    $('#'+elemname).css({'border-color':this.color});
    
    var boxleft = 0;
        
    this.ctx.fillStyle = color;
    this.ctx.strokeStyle = 'black';
    this.ctx.fillRect(boxleft,0,wid,hgt);
    //this.ctx.strokeRect(boxleft,0,this.boxwid,hgt);
    
    this.ctx.font = '30px Times New Roman bold';
    this.ctx.fillStyle = 'black';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText(this.onleft ? 'z' : 'm', boxleft + wid/2, hgt/2);
    
    this.draw();
};

Button.prototype.draw = function(clear) {
    if (typeof(clear)==='undefined') clear = false;
    if (clear) this.ctx.clearRect(0,0,this.ele.width,this.ele.height);
    else {
	this.ctx.fillStyle = this.color;
        this.ctx.fillRect(0,0,this.ele.width,this.ele.height);
        this.ctx.fillStyle = 'black';
        this.ctx.fillText(this.onleft ? 'z' : 'm', this.ele.width/2, this.ele.height/2);
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
};

TrialCounter.prototype.incr = function() {
    this.count += 1;
};
TrialCounter.prototype.setnumtrials = function(numtrials) {
    this.numtrials = numtrials;
}
TrialCounter.prototype.draw = function() {
    var ewid = this.ele.width;
    var ehgt = this.ele.height;
    
    this.ctx.clearRect(0,0,this.ele.width,this.ele.height);
    
    this.ctx.font = '20px Times New Roman bold';
    this.ctx.fillStyle = 'black';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'top';
    this.ctx.fillText('Trial:',ewid-25,0);
    
    this.ctx.textBaseline = 'bottom';
    this.ctx.fillText(this.count+'/'+this.numtrials,ewid-25,ehgt);
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

Trial = function(table, leftbtn, rightbtn, score, trcounter, redonleft) {
    this.rol = redonleft;
    this.tbele = tbele = document.getElementById(table);
    if (redonleft) {lbcol = RED; rbcol = GREEN;}
    else {lbcol = GREEN; rbcol = RED;}
    this.lbtn = new Button(true,lbcol,leftbtn);
    this.rbtn = new Button(false,rbcol,rightbtn);
    this.score = new ScoreDisp(score);
    this.trcounter = new TrialCounter(trcounter);
    this.response = NORESPONSE; 
    this.resptime = -1;
    this.goalswitched = false;
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
    this.realgoal = this.gettrialgoal(TIMEPERSTEP);
    this.response = NORESPONSE;
    this.resptime = -1;
};
Trial.prototype.loadFromTList = function(trname, trlist) {
    this.tb = trlist.loadTrial(trname, this.tbele);
    this.done = false;
    this.realgoal = this.gettrialgoal(TIMEPERSTEP);
    this.response = NORESPONSE;
    this.resptime = -1;
};
Trial.prototype.draw = function() {
    this.tb.draw();
    this.lbtn.draw();
    this.rbtn.draw();
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

	    //TODO Move this all into trial draw() with parameter for buttons
            that.tb.draw();
            that.score.draw();
            that.trcounter.draw();
            that.lbtn.draw(true);
            that.rbtn.draw(true);

            if (pev !== 0) {
                assert(pev !== TIMEUP, "Oddly, your trial ran too long");
                clearInterval(interid);

                // Update score
                if (that.response === NORESPONSE) {
                    score = 0;
                }
                else if (that.realgoal !== that.response) {
                    score = -10;
                }
                else {
                    score = 100 * (1 - (that.resptime-TIME_BEGIN)/(TIME_END-TIME_BEGIN)); 
                    score = Math.round(Math.max(Math.min(score,100),0));
                }
                that.score.add(score);
                that.draw();
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
        that.lbtn.draw(false);
        that.rbtn.draw(false);

        var timeoutid;
        var start = new Date();
        that.keyhandler.setpress(function(k) {
            // TODO Verify double press? Or just record first key pressed?
            if (k===77) { 
                that.keyhandler.setpress(function(k) {});
                clearTimeout(timeoutid);
                that.resptime = (new Date() - start) / 1000;
                if (that.rol) that.response = GREENGOAL;
                else that.response = REDGOAL;
                finishtrial();
            }
            else if (k===90) {
                that.keyhandler.setpress(function(k) {});
                clearTimeout(timeoutid);
                that.resptime = (new Date() - start) / 1000;
                if (that.rol) that.response = REDGOAL;
                else that.response = GREENGOAL;
                finishtrial();
            }
        });
        // TODO Fix race condition, multiple calls to finishtrial
        timeoutid = setTimeout(finishtrial, responsetime*1000);
    };

    // set ball vel by motion condition
    this.tb.ball.setvel(vel['x']*this.motioncond, vel['y']*this.motioncond);
    // display trial 
    var pev = 0;
    interid = setInterval(function () {
        pev = that.tb.step(dt,displaytime);

	//TODO Move this all into trial draw() with parameter for buttons
        that.tb.draw();
        that.score.draw();
        that.trcounter.draw();
        that.lbtn.draw(true);
        that.rbtn.draw(true);

        if (pev !== 0) {
            assert(pev === TIMEUP, "Oddly, your trial ended too soon");
            clearInterval(interid);
            waitresponse();
        }
    }, dt*1000);
};

Trial.prototype.switchgoal = function() {
    var g;
    for (i=0;i<this.tb.goals.length;i++) {
        g = this.tb.goals[i];
        if (g.onret === GREENGOAL) {
            g.onret = REDGOAL;
            g.color = RED;
        }
        else {
            g.onret = GREENGOAL;
            g.color = GREEN;
        }
    }
    
    if (this.realgoal === GREENGOAL) {
        this.realgoal = REDGOAL;
    }
    else {
	this.realgoal = GREENGOAL;
    }
    //this.goalswitched = true;
};

Trial.prototype.isswitched = function() {
    return this.goalswitched;
};

Trial.prototype.runtrial = function(dt,displaytime,responsetime,maxtime,callback,randomizegoal,showscore,motioncond) {
    if (typeof(randomizegoal) === 'undefined') randomizegoal = true;
    if (randomizegoal) {
        if (Math.random() < 0.5) 
        {
            this.switchgoal();
            this.goalswitched = true;
        }
        else {
            this.goalswitched = false;
        }
    }
    else this.goalswitched = false;
    // generate random motion condition if undefined, one of {-1,0,1}
    if (typeof(motioncond) === 'undefined') 
        motioncond = Math.floor(Math.random()*3)-1; 
    this.motioncond = motioncond;

    var that = this;
    var runfn = function() {that.showtrial(dt,displaytime,responsetime,maxtime,callback,showscore);};
    this.showinstruct('Press the spacebar to begin','black','lightgrey',runfn);
};
