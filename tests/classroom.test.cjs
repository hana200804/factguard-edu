'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const C = require('../web/classroom-core.js');
const catalog = require('../web/catalog.json');
const response = (e, extra={}) => ({exercise_id:e.id,label:e.label,evidence_ids:[...e.evidence],confidence:75,reason:'Tôi đối chiếu chi tiết trong dữ kiện được cung cấp.',...extra});
function attempt(extra={}) {
  const assignment=C.defaultAssignment();
  return {schema:'factguard-attempt-v1',bank_version:C.VERSION,attempt_id:'software-fixture-001',assignment,started_at:'2026-10-25T07:00:00Z',completed_at:'2026-10-25T07:10:00Z',responses:assignment.exercise_ids.map(id=>response(C.BANK.find(e=>e.id===id))),...extra};
}
test('all fifteen source-backed exercises have valid references and balanced labels',()=>{
  assert.equal(C.validateBank(catalog),true);assert.equal(C.BANK.length,15);
  for(const label of C.LABELS)assert.equal(C.BANK.filter(e=>e.label===label).length,5);
  assert.equal(new Set(C.BANK.map(e=>e.id)).size,15);
  assert.throws(()=>C.validateBank({facts:[]}));
});
test('every ideal answer earns all points; explanations are preserved for human review',()=>{
  for(const e of C.BANK){const r=C.grade(response(e));assert.equal(r.points,3);assert.equal(r.explanation,e.explanation);}
});
test('a correct guess and a valid but irrelevant source have independent scores',()=>{
  const e=C.BANK[0];const r=C.grade(response(e,{evidence_ids:['F007']}));assert.equal(r.label_correct,true);assert.equal(r.evidence_correct,false);assert.equal(r.points,2);
  const wrong=C.grade(response(e,{label:'contradicted'}));assert.equal(wrong.points,1);
});
test('multi-clause support requires all necessary evidence and rejects select-all shortcuts',()=>{
  const e=C.BANK.find(e=>e.id==='LT13');
  assert.equal(C.grade(response(e,{evidence_ids:['F015']})).evidence_correct,false);
  assert.equal(C.grade(response(e,{evidence_ids:['F016','F015']})).evidence_correct,true);
  assert.equal(C.grade(response(e,{evidence_ids:[...e.choices]})).evidence_correct,false);
});
test('counterexample suffices for mixed false claim; unknown detail remains insufficient',()=>{
  assert.deepEqual(C.BANK.find(e=>e.id==='LT14').evidence,['F030']);
  for(const id of ['LT06','LT15'])assert.equal(C.BANK.find(e=>e.id===id).label,'insufficient');
});
test('assignment rejects duplicate, missing, oversized and unknown exercise lists',()=>{
  const a=C.defaultAssignment();for(const ids of [[],['LT99'],['LT01','LT01'],new Array(16).fill('LT01')])assert.throws(()=>C.assignment({...a,exercise_ids:ids}));
  assert.throws(()=>C.assignment({...a,id:'../../file'}));assert.throws(()=>C.assignment({...a,bank_version:'future'}));assert.throws(()=>C.assignment({...a,title:'x'}));
});
test('answers reject empty source, foreign source, invalid confidence and empty reasoning',()=>{
  const e=C.BANK[0];for(const patch of [{label:'yes'},{evidence_ids:[]},{evidence_ids:['F033']},{evidence_ids:['F001','F001']},{confidence:'75'},{confidence:80},{reason:'short'},{reason:'x'.repeat(601)}])assert.throws(()=>C.grade(response(e,patch)));
});
test('import recalculates scores and ignores forged score fields',()=>{
  const a=attempt();a.responses[0]={...a.responses[0],label:'contradicted',points:999,label_correct:true};a.points=999;
  const s=C.summarize(a);assert.equal(s.points,16);assert.equal(s.label_correct,5);assert.equal(s.confident_errors,1);assert.equal(s.max_points,18);assert.equal('points' in s.report,false);
});
test('unfinished, reordered and repeated responses cannot become completed reports',()=>{
  const a=attempt();assert.throws(()=>C.report({...a,responses:a.responses.slice(1)}));
  assert.throws(()=>C.report({...a,responses:[...a.responses].reverse()}));assert.throws(()=>C.report({...a,responses:a.responses.map(()=>a.responses[0])}));
});
test('malformed date and time reversal rejected',()=>{
  for(const patch of [{started_at:'invalid'},{completed_at:'2026-10-25T06:59:59Z'},{attempt_id:'<script>'},{bank_version:'old'}])assert.throws(()=>C.report(attempt(patch)));
});
test('aggregation deduplicates identical imports and computes actual denominators',()=>{
  const a=attempt(), b=attempt({attempt_id:'software-fixture-002'});b.responses[0].label='contradicted';
  const s=C.aggregate([a,a,b]);assert.equal(s.attempts,2);assert.equal(s.duplicates,1);assert.equal(s.count,12);assert.equal(s.label_correct,11);assert.equal(s.evidence_correct,12);assert.equal(s.confident_errors,1);assert.equal(s.matrix[0][1],1);assert.equal(s.by_exercise[0].label_correct,1);
});
test('conflicting duplicate fails before any partial result',()=>{
  const a=attempt(),b=attempt();b.responses[0].label='contradicted';assert.throws(()=>C.aggregate([a,b]),/nội dung khác nhau/);
});
test('different lesson ids, titles and order cannot be mixed',()=>{
  for(const patch of [{id:'other-lesson'},{title:'Bộ bài khác'}]){const a=attempt(),b=attempt({attempt_id:'software-fixture-002'});Object.assign(b.assignment,patch);assert.throws(()=>C.aggregate([a,b]),/khác nhau/);}
  assert.throws(()=>C.aggregate([]));assert.throws(()=>C.aggregate(new Array(201).fill(attempt())));
});
test('CSV neutralizes spreadsheet formulas and quotes multiline text',()=>{
  const csv=C.csv([['=HYPERLINK("x")',' +1','@sum(A1)','-2','\tformula','a,"b"\nline']]);
  assert.ok(csv.startsWith('\ufeff'));for(const prefix of ["'=HYPERLINK","' +1","'@sum","'-2","'\tformula"])assert.ok(csv.includes(prefix));assert.ok(csv.includes('"a,""b""\nline"'));
});
