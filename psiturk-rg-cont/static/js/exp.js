/* 
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */



/**
 * Function to check the window size, and determine whether it is
 * large enough to fit the given experiment. If the window size is not
 * large enough, it hides the experiment display and instead displays
 * the error in the #window-error DOM element. If the window size is
 * large enough, then this centers the experiment horizontally and
 * vertically.
 *
 * From Jessica Hamrick - thanks Jess!
 *
 * @param {Experiment} exp - The experiment object
 */

windowsizer = function(minx, miny,exp) {
    this.x = minx;
    this.y = miny;
    this.tbshown = false;
    this.replaced = false;
    this.exp = exp;
    
    this.checkSize = function(wsme) {
        var maxWidth = $(window).width(),
            maxHeight = $(window).height();
    
        $("#textfield").width(Math.min(1000,maxWidth));
        
        if ((minx > maxWidth) || (miny > maxHeight)) {
            wsme.exp.badtrial = true;
            if ($("#table").is(":visible")) {
                $("#table").hide(0);
                wsme.tbshown = true;
            }
            
            if (!wsme.replaced) {
                wsme.exp.trial.replaceText('Your window is too small for this experiment. Please make it larger.');
                wsme.replaced = true;
            }
            
            $("#textfield").show(0);
            return;
        }
        
        if (wsme.replaced) {
            wsme.exp.trial.restoreText();
            wsme.replaced = false;
        }
        if (wsme.tbshown) {
            $("#table").show(0);
            $("#textfield").hide(0);
        }
        
        wsme.tbshown = false;
        
      
    };
};

// From http://stackoverflow.com/questions/2450954/how-to-randomize-shuffle-a-javascript-array
function shuffle(array) {
  var currentIndex = array.length, temporaryValue, randomIndex ;

  // While there remain elements to shuffle...
  while (0 !== currentIndex) {

    // Pick a remaining element...
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex -= 1;

    // And swap it with the current element.
    temporaryValue = array[currentIndex];
    array[currentIndex] = array[randomIndex];
    array[randomIndex] = temporaryValue;
  }

  return array;
}

DT = 0.025;
DISPLAY_TIME = 0.5;
RESPONSE_TIME = 2.5;
MAX_TIME = 20;

Experiment = function(triallist, table, leftctr, rightctr, score, trcounter, ptobj) {
    
    this.pt = ptobj;
    
    // Load in the list of trials to use & shuffle them
    var that = this;
    var lst = new ajaxStruct();
    $.ajax({
        dataType: "json",
        url: triallist,
        async: false,
        success: function(data) {
            that.trlist = data[that.pt.taskdata.get('condition')];
        },
        error: function(req) {
            throw new Error('Failure to load trial list file');
        }
    });
    this.trlist = shuffle(this.trlist);
    this.tridx = 0;
    
    this.loaded = new TrialList(this.trlist, 'trials');
    
    this.badtrial = false; // Holder for if window is too small or minimzied
    
    // Load in the trial object
    this.rol = Math.random() < 0.5;
    this.trial = new Trial(table,leftctr,rightctr,score,trcounter,this.rol);
    this.trial.trcounter.setnumtrials(this.trlist.length);
    
    this.pt.recordUnstructuredData('RedOnLeft',this.rol);
    
};

Experiment.prototype.startTrials = function(me) {
    //this.trial.loadTrial('trials/'+this.trlist[0]+'.json');
    this.trial.loadFromTList(this.trlist[0][0],this.loaded);
};

Experiment.prototype.run = function(me) {
    me.badtrial = false;
    me.trial.runtrial(DT,DISPLAY_TIME,RESPONSE_TIME,MAX_TIME,function () {
	me.recordTrial(me);
    });
};

Experiment.prototype.nextTrial = function(me) {
    me.badtrial = false; // Reset badness
    me.tridx++;
    if (me.tridx >= me.trlist.length) {
        me.endExp();
        return;
    }
    me.trial.trcounter.incr();
    console.info(me.trlist.length);
    console.info(me.tridx);
    // XXX Will always load same trial (switch back after debugging)
    me.trial.loadTrial('trials/RTr_Bl1_0.json');
    //me.trial.loadTrial('trials/'+me.trlist[me.tridx]+'.json');
    //me.trial.loadFromTList(me.trlist[me.tridx][0],me.loaded);
    me.run(me);
};

Experiment.prototype.recordTrial = function(me) {
    var trname = me.trial.tb.name;
    var motioncond = me.trial.motioncond
    var goalsw = me.trial.isswitched();
    var resp = me.trial.response;
    var resptime = me.trial.resptime;
    
    assert(me.trial.done, 'Cannot record trial that is not finished');

    var sc = me.trial.lastscore;
    var realgoal = me.trial.realgoal;

    // Insert psiturk recording code here
    //console.log(resp);
    //console.log(realgoal);
    me.pt.recordTrialData([trname,me.tridx,motioncond,goalsw,resp,sc,realgoal,me.badtrial]);
    
    var bi;
    if (me.badtrial) {
        bi = 'Please keep the window open, on top of the screen, and large enough to see everything';
        me.trial.showinstruct(bi,'black','white',function() {me.nextTrial(me);});
        return;
    }
    
    me.pt.saveData({
        error: function() {console.log('Error recording data');}
    });
    me.nextTrial(me);
};

Experiment.prototype.endExp = function() {
    var me = this;
    this.trial.showinstruct('Congrats! You are now done!<br><br>Press the spacebar to return to Mechanical Turk','black','white',
        me.pt.completeHIT);
};

Experiment.prototype.instructions = function() {
    
    var itr1 = 'trials/InstTr1.json';
    var itr2 = 'trials/InstTr2.json';
    
    var lcol, rcol, rkey, gkey;
    
    if (this.rol) {
        lcol = 'red';
        rcol = 'green';
        rkey = 'z';
        gkey = 'm';
    } else {
        rcol = 'red';
        lcol = 'green';
        gkey = 'z';
        rkey = 'm';
    }
    
    var i1 = "In this experiment, you will see a ball bouncing around the screen and will need to predict whether it will go into the red or the green goal. <br> <br> Press the spacebar to see an example of what a table might look like.";
    var i2 = "But you won't just watch the ball - you will need to predict where it will go. <br> <br> You may have noticed the " + lcol + " 'z' button and the " + rcol + " 'm' button - you should hold down the 'z' key if you think the ball will go in the " + lcol + " goal, ";
    i2 = i2 + "or the 'm' key if you think the ball will go in the "+rcol+" goal. <br> <br> The longer you hold it down for the correct goal, the more points you will get. <br> <br> Press the spacebar to continue, then hold down the '" + rkey + "' key to see the red counter rise.";
    var irepeat = "You didn't hold down the '"+rkey+"' key for long enough. <br> <br> Press the spacebar to try again";
    var irepeat2 = "You didn't hold down the '"+gkey+"' key for long enough. <br> <br> Press the spacebar to try again";
    var isizing = 'Please keep the window open and large enough for the experiment';
    var i3 = "Watch out though - if you hold down the key for the wrong goal, you will lose points. <br> <br> Press the spacebar to continue, then hold down the '"+gkey+"' key to see the green counter rise and demonstrate how you can lose points.";
    var i4 = "You aren't stuck with one prediction though: you can change your mind during each table by switching from 'z' to 'm' or vice versa. What matters is how long you hold down the key - if you hold it down longer for the correct goal, you ";
    i4 = i4 + "will gain points, but if you hold it down longer for the other goal, you will lose points. <br> <br> Thus you must strike a balance: you should make a prediction early to earn more points, but if you make it too early and get it wrong, you ";
    i4 = i4 + "might lose points. <br> <br> Press the spacebar to continue.";
    var i5 = "Now let's try one last sample table before we start the experiment. <br> <br> Press the spacebar to continue.";
    var i6 = "You are now done with the instructions. <br> <br> Press the spacebar to start the tables where you will earn points.";
    // Intermediate functions to do recursive stuff in instructions
    
    var that2 = this;
    runS1 = function() {
        that2.trial.loadTrial('trials/InstTr1.json');
        that2.badtrial = false;
        that2.trial.runtrial(DT,DISPLAY_TIME,RESPONSE_TIME,MAX_TIME,function () {
            if (that2.badtrial) {
                that2.trial.showinstruct(isizing,'black','white',runS1,true);
                that2.badtrial = false;
                return;
            }
            else {
                that2.trial.score.reset();
                that2.trial.showinstruct(i2,'black','white',runS2,true);
                return;
            }
        },false,true);
    };
    
    runS2 = function() {
        that2.trial.loadTrial('trials/InstTr1.json');
        that2.badtrial = false;
        that2.trial.runtrial(DT,DISPLAY_TIME,RESPONSE_TIME,MAX_TIME,function () {
            if (that2.badtrial) {
                that2.trial.showinstruct(isizing,'black','white',runS2,true);
                that2.badtrial = false;
                return;
            }
            else if (that2.trial.lastscore < 40) {
                that2.trial.showinstruct(irepeat,'black','white',runS2,true);
                return;
            }
            else {
                that2.trial.score.reset();
                that2.trial.showinstruct(i3,'black','white',runS3,true);
                return;
            }
        },false);
    };
    
    runS3 = function() {
        that2.trial.loadTrial('trials/InstTr1.json');
        that2.badtrial = false;
        that2.trial.runtrial(DT,DISPLAY_TIME,RESPONSE_TIME,MAX_TIME,function () {
            if (that2.badtrial) {
                that2.trial.showinstruct(isizing,'black','white',runS3,true);
                that2.badtrial = false;
                return;
            }
            else if (that2.trial.lastscore > 0) {
                that2.trial.showinstruct(irepeat2,'black','white',runS3,true);
                return;
            }
            else {
                that2.trial.score.reset();
                that2.trial.showinstruct(i4,'black','white',function() {
                    that2.trial.showinstruct(i5,'black','white',runS4,true);
                }, true);
                return;
            }
        },false);
    };
    
    runS4 = function() {
        that2.trial.loadTrial('trials/InstTr2.json');
        that2.badtrial = false;
        that2.trial.runtrial(DT,DISPLAY_TIME,RESPONSE_TIME,MAX_TIME,function () {
            if (that2.badtrial) {
                that2.trial.showinstruct(isizing,'black','white',runS4,true);
                that2.badtrial = false;
                return;
            }
            else {
                that2.trial.score.reset();
                that2.pt.finishInstructions(); // Set participant code to done with instructions
                that2.trial.loadTrial('trials/'+that2.trlist[0][0]+'.json');
		that2.trial.trcounter.display = true;
                that2.run(that2);
                return;
            };
            
        },false);
    };

    that2.trial.showinstruct(i1,'black','white', runS1, true );

};
/*
function main() {
    
    exp = new Experiment('trials/TrList.json','table','lcounter','rcounter','score');
    ws = new windowsizer(1010,870,exp);
    $(window).resize(function() {ws.checkSize(ws);});
    $(window).blur(function() {exp.badtrial = true;});
    
    exp.instructions();
    
};
*/
