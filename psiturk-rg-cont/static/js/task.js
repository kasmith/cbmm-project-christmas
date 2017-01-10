/*
 * Requires:
 *     psiturk.js
 *     utils.js
 */

// Initalize psiturk object
var psiTurk = new PsiTurk(uniqueId, adServerLoc, mode);

psiTurk.preloadPages(["stage.html"]);


/*******************
 * Run Task
 ******************/
$(window).load( function(){
    psiTurk.showPage("stage.html");
    $('.field').hide(0);
    exp = new Experiment('trials/ConditionList.json','table','lbutton','rbutton','score','trialcounter',psiTurk);
    ws = new windowsizer(1010,755,exp);
    ws.checkSize(ws);
    $(window).resize(function() {ws.checkSize(ws);});
    $(window).blur(function() {exp.badtrial = true;});
    
    exp.instructions();
});
