/* 
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

var WHITE = 'rgb(255,255,255)';
var BLUE = 'rgb(0,0,255)';
var RED = 'rgb(255,0,0)';
var BLACK = 'rgb(0,0,0)';

var s = new cp.Space();
var cbody = new cp.Body(1.0, cp.momentForCircle(1.,0,20,cp.vzero));
var circ = new cp.CircleShape(cbody, 20, cp.vzero);
var floor = s.addShape(new cp.SegmentShape(s.staticBody, cp.v(0,500),cp.v(600,500),1));

var cb2 = new cp.Body(1.0,cp.momentForCircle(1.,0,20,cp.vzero));
var c2 = new cp.CircleShape(cb2,20,cp.vzero);

floor.setElasticity(1);
floor.setFriction(1);

circ.setElasticity(1);
//circ.setFriction(0);

c2.setElasticity(1);
//c2.setFriction(0);

s.addBody(cbody);
s.addBody(cb2);
s.addShape(circ);
s.addShape(c2);

cbody.setPos(cp.v(300,100));
cbody.setVel(cp.v(0,100));

cb2.setPos(cp.v(300,400));


function draw(ctx) {
    
    ctx.fillStyle = WHITE;
    
    ctx.clearRect(0,0,1000,900);

    
    ctx.fillStyle = BLUE;
    ctx.strokeStyle = BLUE;
    ctx.beginPath();
    pos = cbody.getPos();
    //console.log(pos.x+','+pos.y);
    ctx.moveTo(pos.x,pos.y);
    ctx.arc(pos.x,pos.y,20,0,2*Math.PI,true);
    ctx.fill();
    
    ctx.fillStyle = BLACK;
    ctx.strokeStyle = BLACK;
    ctx.beginPath();
    ctx.moveTo(0,500);
    ctx.lineTo(600,500);
    ctx.stroke();
    
    
    ctx.fillStyle=RED;
    ctx.strokeStyle=RED;
    p2 = cb2.getPos();
    //console.log(p2.x+','+p2.y);
    ctx.beginPath();
    ctx.moveTo(p2.x,p2.y);
    ctx.arc(p2.x,p2.y,20,0,2*Math.PI,true);
    ctx.fill();
    
};

function stepndraw(ctx) {
    for (i=0;i<100;i++) {s.step(1/1000.);}
    draw(ctx);
};

function main() {
    console.log(~(1<<31));
    var canvas = document.getElementById('table');
    var ctx = canvas.getContext('2d');
    window.setInterval(function() {stepndraw(ctx);},100);
    /*
    for(i = 0; i<200; i++) {
        s.step(.1);
        draw(ctx);}
        */
};