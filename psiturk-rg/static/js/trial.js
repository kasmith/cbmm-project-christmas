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

Counter = function(maxval, onleft, color, elemname, boxwid) {
    this.maxval = maxval;
    this.color = color;
    this.curval = 0;
    this.ele = document.getElementById(elemname);
    this.ctx = this.ele.getContext('2d');
    this.onleft = onleft;
    if (typeof(boxwid)==='undefined') boxwid = 50;
    this.boxwid = boxwid;
    
    // Setup the drawing
    var wid = this.ele.width;
    var hgt = this.ele.height;
    assert(boxwid < wid, 'Width of counter element must be greater than boxwidth');
    $('#'+elemname).css({'border-color':this.color});
    
    var char;
    var boxleft;
    
    if (this.onleft) {
        char = 'z';
        boxleft = wid - this.boxwid;
    }
    else {
        char = 'm';
        boxleft = 0;
    }
    
    this.ctx.fillStyle = color;
    this.ctx.strokeStyle = 'black';
    this.ctx.fillRect(boxleft,0,this.boxwid,hgt);
    //this.ctx.strokeRect(boxleft,0,this.boxwid,hgt);
    
    this.ctx.font = '30px Times New Roman bold';
    this.ctx.fillStyle = 'black';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText(char, boxleft + this.boxwid/2, hgt/2);
    
    this.draw();
};

Counter.prototype.increment = function() {
    this.curval++;
};
Counter.prototype.getpct = function() {
    return this.curval / this.maxval; 
};
Counter.prototype.setmax = function(newmax) {
    this.maxval = newmax;
    this.curval = 0;
    this.draw(true);
};
Counter.prototype.draw = function(clear) {
    if (typeof(clear)==='undefined') clear = false;
    var clearwid = this.ele.width - this.boxwid;
    var drawwid = clearwid * this.curval / 100; // Keep all bars to a constant length so people can't see the time
    var drawst;
    if (this.onleft) {
        drawst = clearwid - drawwid;
        if (clear) this.ctx.clearRect(0,0,this.ele.width-this.boxwid,this.ele.height);
    
    }
    else {
        drawst = this.boxwid;
        if (clear) this.ctx.clearRect(this.boxwid,0,this.ele.width,this.ele.height);
    }
    this.ctx.fillStyle = this.color;
    this.ctx.fillRect(drawst,0,drawwid,this.ele.height);
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

Trial = function(table, leftctr, rightctr, score, redonleft) {
    this.rol = redonleft;
    this.tbele = tbele = document.getElementById(table);
    if (redonleft) {lccol = RED; rccol = GREEN;}
    else {lccol = GREEN; rccol = RED;}
    this.lctr = new Counter(10,true,lccol,leftctr);
    this.rctr = new Counter(10,false,rccol,rightctr);
    this.score = new ScoreDisp(score);
    this.record = [];
    this.goalswitched = false;
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
    var steps = this.gettrialsteps(TIMEPERPOLL);
    this.lctr.setmax(steps);
    this.rctr.setmax(steps);
    this.done = false;
    this.record = [];
};
Trial.prototype.loadFromTList = function(trname, trlist) {
    this.tb = trlist.loadTrial(trname, this.tbele);
    var steps = this.gettrialsteps(TIMEPERPOLL);
    this.lctr.setmax(steps);
    this.rctr.setmax(steps);
    this.done = false;
    this.record = [];
};
Trial.prototype.draw = function() {
    this.tb.draw();
    this.lctr.draw();
    this.rctr.draw();
    this.score.draw();
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
Trial.prototype.displaytext = function(text, textcol, bkcol,hideall) {
    if (typeof(bkcol)==='undefined') bkcol = "white";
    if (typeof(textcol)==='undefined') textcol = "black";
    if (text.substring(0,6) === "<span>") htmtext = text;
    else htmtext = "<span>"+text+"</span>";
    var wid = this.tbele.width;
    var hgt = this.tbele.height;
    $("#table").hide(0);
    if (typeof(hideall)!== "undefined" & hideall) {
        $("#lcounter").hide(0);
        $("#score").hide(0);
        $("#rcounter").hide(0);
    }
    
    
    tf = $('#textfield');
    tf.html(htmtext);
    tf.css({'background-color':bkcol,'color':textcol});
    tf.show(0); 
    
};
Trial.prototype.hidetext = function() {
    $("#table").show(0);
    
    $("#lcounter").show(0);
    $("#score").show(0);
    $("#rcounter").show(0);
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
Trial.prototype.showtrial = function(dt,maxtime,callback,showscore) {
    
    
    this.nsteps = 0;
    var stepsperpoll = TIMEPERPOLL / dt;
    if (stepsperpoll % 1 !== 0) alert('Steps per poll not divisible by timesteps');
    var pev = 0;
    var that = this;
    
    
    
    interid = setInterval(function () {
        pev = that.tb.step(dt,maxtime);
        that.nsteps++;
        inpoll = that.nsteps % stepsperpoll === 0;
        if ((inpoll) || (pev !== 0)) {
            kpress = that.keyhandler.getstate();
            if (kpress[77] && !kpress[90]) {
                that.rctr.increment();
                if (that.rol) that.record[that.record.length] = GREENGOAL;
                else that.record[that.record.length] = REDGOAL;
            }
            else if (kpress[90] && !kpress[77]) {
                that.lctr.increment();
                if (that.rol) that.record[that.record.length] = REDGOAL;
                else that.record[that.record.length] = GREENGOAL;
            }
            else that.record[that.record.length] = UNCERTAIN;
            
        }
        that.draw();
        // Ending code
        if (pev !== 0) {
            clearInterval(interid);
            
            lctsc = that.lctr.getpct();
            rctsc = that.rctr.getpct();
            
            assert(pev !== TIMEUP, "Oddly, your trial ran too long");
            
            if ( (pev===GREENGOAL && that.rol) || (pev===REDGOAL && !that.rol)) {
                scpct = rctsc - lctsc;
            }
            else {
                scpct = lctsc - rctsc;
            }
            score = Math.round(20 + 80*scpct);
            that.score.add(score);
            that.draw();
            that.writenewscore(score,showscore);
            that.done = true;
            that.lastscore = score;
            that.realgoal = pev;
            
            that.keyhandler.setpress(function(k) {
                if (k===32) { 
                    that.hidetext();
                    that.keyhandler.setpress(function(k) {});
                    callback();
                }
            });
        }
    },dt*1000);
    
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
    //this.goalswitched = true;
};

Trial.prototype.isswitched = function() {
    return this.goalswitched;
};

Trial.prototype.runtrial = function(dt,maxtime,callback,randomizegoal,showscore) {
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
    var that = this;
    var runfn = function() {that.showtrial(dt,maxtime,callback,showscore);};
    this.showinstruct('Press the spacebar to begin','black','lightgrey',runfn);
};