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

Experiment = function(triallist, table, textbox, leftctr, rightctr, score, trcounter, ptobj) {

    this.pt = ptobj;

    // Load in the trial object
    this.rol = Math.random() < 0.5;
    this.trial = new Trial(table,textbox,leftctr,rightctr,score,trcounter,this.rol);
    this.trial.showinstruct("Please wait for all of the data to load.", 'black','white', function() {return;}, true);

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

    this.trial.trcounter.setnumtrials(this.trlist.length);

    this.pt.recordUnstructuredData('RedOnLeft',this.rol);    
};

Experiment.prototype.startTrials = function(me) {
    //this.trial.loadTrial('trials/'+this.trlist[0]+'.json');
    this.trial.loadFromTList(this.loaded.tnms[0],this.loaded);
};

Experiment.prototype.run = function(me) {
    console.log(me.loaded.tconds[me.tridx])
    console.log(me.loaded.tnms[me.tridx])

    me.badtrial = false;
    me.trial.runtrial(DT,DISPLAY_TIME,RESPONSE_TIME,MAX_TIME,function () {
	me.recordTrial(me);
    }, me.loaded.tconds[me.tridx][0], me.loaded.tconds[me.tridx][1]);
};

Experiment.prototype.nextTrial = function(me) {
    me.badtrial = false; // Reset badness
    me.tridx++;
    if (me.tridx >= me.trlist.length) {
        me.endExp();
        return;
    }
    me.trial.trcounter.incr();

    //me.trial.loadTrial('trials/'+me.trlist[me.tridx]+'.json');
    me.trial.loadFromTList(me.loaded.tnms[me.tridx],me.loaded);
    me.run(me);
};

Experiment.prototype.recordTrial = function(me) {
    var trname = me.trial.tb.name;
    var motioncond = me.trial.motioncond
    var goalin = me.trial.isgoalin();
    var resp = me.trial.response;
    var resptime = me.trial.resptime;
    var expcondition = this.pt.taskdata.get('condition');

    assert(me.trial.done, 'Cannot record trial that is not finished');

    var sc = me.trial.lastscore;

    // Insert psiturk recording code here
    //console.log(resp);
    // TODO Why 199? What about NORESPONSE?
    var respdict = {199: "NA"};
    respdict[true] = true;
    respdict[false] = false;
    var modict = {1: "Fwd", 0: "None"};
    modict[-1] = "Rev";
    var recdat = {Condition: expcondition,
                  Trial: trname,
                  TrialOrder: me.tridx,
                  RT: resptime,
                  RawResponse: respdict[resp],
                  MotionDirection: modict[motioncond],
                  GoalReachable: goalin,
                  Score: sc,
                  WasBad: me.badtrial
              };
    console.log(recdat);
    me.pt.recordTrialData(recdat);

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
        lcol = 'YES';
        rcol = 'NO';
        rkey = 'z';
        gkey = 'm';
    } else {
        rcol = 'NO';
        lcol = 'YES';
        gkey = 'z';
        rkey = 'm';
    }

    var isizing = 'Please keep the window open and large enough for the experiment';

    var i1 = "In this experiment, you will see a ball bouncing around the screen for a short amount of time and then stop. You will also see a red rectangle. <br><br>";
    i1 += "After the ball stops you will need to answer: <br> Can the ball reach the red rectangle? <br><br>";
    i1 += "You should press the 'z' button for " + lcol + " - that is, if you believe the ball CAN reach the red rectangle. You should press the 'm' button for " + rcol + " - that is, if you believe the ball CANNOT reach the red rectangle.<br><br>";
    i1 += "Press the spacebar to continue.";

    i1a += "However you cannot give your response at any time - you will need to press the key corresponding to your response only after the options flash on at the bottom of the screen. <br> <br>";
    i1a += "Once you have made your prediction, you will see the correct answer.<br><br>Press the spacebar to see an example.";

    var i2 = "The longer you take to push the button and make your prediction, the fewer points you get. <br> <br> Press the spacebar to continue, then press the '" + rkey + "' key after it flashes at the bottom of the screen to earn some points.";

    var irepeat = "You didn't press the '"+rkey+"' key fast enough. <br> <br> Press the spacebar to try again";
    var irepeat2 = "You didn't press the '"+gkey+"' key. <br> <br> Press the spacebar to try again";

    var i3 = "Watch out though - if you press the key for the wrong answer, you will lose points. <br> <br> Press the spacebar to continue, then press the '"+gkey+"' key to see how you can lose points.";

    var i4 = "One extra detail: in some cases you won't see the ball move at all!<br><br>";
    i4 += "In these cases you will still have to try to answer the question without knowing the direction that the ball will start moving in. <br><br>";
    i4 += "Let's look at one example. <br> <br> Press the spacebar to continue.";

    var i5 = "Now let's try a few more examples before we start the experiment. <br> <br> Press the spacebar to continue.";
    var i6 = "A couple more for practice... <br> <br> Press the spacebar to continue.";
    var i7 = "As you just saw, remember that sometimes you won't see the ball move. Still, make your best guess to try to answer the question. <br> <br> Just one more practice round. <br> <br> Press the spacebar to continue.";
    var i8 = "You are now done with the instructions. <br> <br> Press the spacebar to start earning points!";
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
        },'forward','in',true);
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
            else if (that2.trial.lastscore < 10) {
                that2.trial.showinstruct(irepeat,'black','white',runS2,true);
                return;
            }
            else {
                that2.trial.score.reset();
                that2.trial.showinstruct(i3,'black','white',runS3,true);
                return;
            }
        },'forward','in');
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
            else if (that2.trial.lastscore !== -10) {
                that2.trial.showinstruct(irepeat2,'black','white',runS3,true);
                return;
            }
            else {
                that2.trial.score.reset();
                that2.trial.showinstruct(i4,'black','white',runS4,true);
                return;
            }
        },'forward','in');
    };

    runS4 = function() {
        that2.trial.loadTrial('trials/InstTr1.json');
        that2.badtrial = false;
        that2.trial.runtrial(DT,DISPLAY_TIME,RESPONSE_TIME,MAX_TIME,function () {
            if (that2.badtrial) {
                that2.trial.showinstruct(isizing,'black','white',runS4,true);
                that2.badtrial = false;
                return;
            }
            else {
                that2.trial.score.reset();
                that2.trial.showinstruct(i5,'black','white',runS5,true);
                return;
            };

        },'static','in');
    };

    runS5 = function() {
        that2.trial.loadTrial('trials/InstTr2.json');
        that2.badtrial = false;
        that2.trial.runtrial(DT,DISPLAY_TIME,RESPONSE_TIME,MAX_TIME,function () {
            if (that2.badtrial) {
                that2.trial.showinstruct(isizing,'black','white',runS5,true);
                that2.badtrial = false;
                return;
            }
            else {
                that2.trial.score.reset();
                that2.trial.showinstruct(i6,'black','white',runS6,true);
                return;
            };

        },'forward','in');
    };

    runS6 = function() {
        that2.trial.loadTrial('trials/InstTr3.json');
        that2.badtrial = false;
        that2.trial.runtrial(DT,DISPLAY_TIME,RESPONSE_TIME,MAX_TIME,function () {
            if (that2.badtrial) {
                that2.trial.showinstruct(isizing,'black','white',runS6,true);
                that2.badtrial = false;
                return;
            }
            else {
                that2.trial.score.reset();
                that2.trial.showinstruct(i7,'black','white',runS7,true);
                return;
            };

        },'forward','out');
    };

    runS7 = function() {
        that2.trial.loadTrial('trials/InstTr2.json');
        that2.badtrial = false;
        that2.trial.runtrial(DT,DISPLAY_TIME,RESPONSE_TIME,MAX_TIME,function () {
            if (that2.badtrial) {
                that2.trial.showinstruct(isizing,'black','white',runS7,true);
                that2.badtrial = false;
                return;
            }
            else {
                that2.trial.score.reset();
                that2.pt.finishInstructions(); // Set participant code to done with instructions
                that2.trial.loadTrial('trials/'+that2.loaded.tnms[0]);
		that2.trial.trcounter.display = true;
                that2.run(that2);
                return;
            };

        },'forward','out');
    };


    that2.trial.showinstruct(i1,'black','white', function() {
        that2.trial.showinstruct(i1a, 'black','white', runS1, true);
    }, true );

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
