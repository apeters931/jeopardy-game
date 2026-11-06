import test from 'node:test';
import assert from 'node:assert/strict';
import {matches,scoreChange,maxWager,validWager,roundOrder,countAsCorrect} from '../static/logic.mjs';
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
test('minor spelling mistakes and adjacent transpositions are accepted',()=>{
 for(const [answer, expected] of [
  ['Pariss', 'Paris'], ['Shakespear', 'Shakespeare'],
  ['Shakespaere', 'Shakespeare'], ['Tchaikovski', 'Tchaikovsky'],
  ['  Who is William Shakespear?  ', 'William Shakespeare'],
  ['icecream', 'ice cream'], ['Wal Mart', 'Wal-Mart'],
  ['U.S.A.', 'USA'], ['rock and roll', 'rock & roll']
 ]) assert.equal(matches(answer,expected),true,`${answer} / ${expected}`);
});
test('leniency does not allow missing words, short-word changes, or different numbers',()=>{
 for(const [answer, expected] of [
  ['Mars', 'Wars'], ['cat', 'car'], ['Iran', 'Iraq'],
  ['1968', '1969'], ['Apollo 12', 'Apollo 13'], ['1 23', '123'],
  ['Shakespeare', 'William Shakespeare'], ['York', 'New York'],
  ['London or Paris', 'Paris'], ['I do not know', 'Paris'],
  ['George Bush', 'George Washington'], ['  ', 'Paris'],
  ['x'.repeat(501), 'y'.repeat(501)]
 ]) assert.equal(matches(answer,expected),false,`${answer} / ${expected}`);
});

test('self-grading replaces penalties, including wagers, and cannot count twice',()=>{
 for(const amount of [200, 1500, 0]) {
  const incorrect = {response:'an equivalent answer', passed:false, correct:false, amount, delta:-amount};
  const corrected = countAsCorrect(incorrect);
  assert.equal(corrected.correct,true);
  assert.equal(corrected.delta,amount);
  assert.equal(corrected.selfGraded,true);
  assert.equal(incorrect.correct,false);
  assert.deepEqual(countAsCorrect(corrected),corrected);
  assert.deepEqual(JSON.parse(JSON.stringify(corrected)),corrected);
 }
});
test('skips and blank responses cannot be self-graded',()=>{
 for(const [passed,response] of [[true,''],[false,''],[false,'  ']]) {
  const answer = {passed,response,correct:false,amount:200,delta:passed?0:-200};
  assert.equal(countAsCorrect(answer),answer);
 }
});
