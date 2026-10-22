import test from 'node:test';
import assert from 'node:assert/strict';
import {matches,scoreChange,maxWager,validWager,roundOrder} from '../static/logic.mjs';
test('answer normalization accepts standard phrasing and punctuation without substring matching',()=>{
 assert.equal(matches('What is the Eiffel Tower?', 'Eiffel Tower'),true);
 assert.equal(matches('cafe', 'Café'),true);
 assert.equal(matches('', ''),false);
 assert.equal(matches('York','New York'),false);
});
test('correct, incorrect, and pass scoring also works for wagers',()=>{
 assert.equal(scoreChange(true,false,400),400);
 assert.equal(scoreChange(false,false,400),-400);
 assert.equal(scoreChange(false,true,400),0);
 assert.equal(scoreChange(false,false,1500),-1500);
});
test('daily double limits support negative scores and larger balances',()=>{
 const qs=[{point_value:200},{point_value:1000}];
 assert.equal(maxWager(-400,qs),1000);
 assert.equal(maxWager(3200,qs),3200);
 assert.equal(validWager('1000',1000),true);
 for(const value of ['', '0', '-1','1001','1.5','abc'])assert.equal(validWager(value,1000),false);
 assert.equal(maxWager(-200,qs,true),0);
 assert.equal(validWager('0',0,true),true);
});
test('rounds follow game order',()=>{
 assert.equal(roundOrder('Jeopardy!'),1);
 assert.equal(roundOrder('Double Jeopardy!'),2);
 assert.equal(roundOrder('Final Jeopardy!'),3);
});
