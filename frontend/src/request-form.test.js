import {test} from 'node:test';
import assert from 'node:assert/strict';
import {HIERARCHY,COURSE,financeError,sectionError,stepsFor,submissionData,validRut} from './request-form.js';
const activity={category:COURSE,request_date:'2026-03-01',start:'2026-03-01',end:'2026-12-31',supervisor_identifier:'12.345.678-5',weekly_hours:'2.5',total_hours:'10.5',lective_hours:'8',non_lective_hours:'2.5'};
test('hierarchy skips financing while course keeps it',()=>{
 assert.equal(stepsFor(HIERARCHY).includes('Financiamiento'),false);
 assert.equal(stepsFor(COURSE).includes('Financiamiento'),true);
 assert.equal(stepsFor(COURSE,true).includes('Datos bancarios'),false);
});
test('calendar allows more than six months but rejects crossing years or retroactive start',()=>{
 assert.equal(sectionError('Actividad',activity),'');
 assert.ok(sectionError('Actividad',{...activity,end:'2027-01-01'}));
 assert.ok(sectionError('Actividad',{...activity,start:'2026-02-28'}));
});
test('teaching checks decimal hour totals and supervisor identity',()=>{
 assert.equal(validRut('12.345.678-5'),true);
 assert.ok(sectionError('Actividad',{...activity,non_lective_hours:'2'}));
 assert.ok(sectionError('Actividad',{...activity,supervisor_identifier:'12.345.678-0'}));
});
test('monthly payments allow gaps, require whole pesos, distinct values and exact total',()=>{
 const data={...activity,amount:'100000',installments:[{month:'2026-03',amount:'50500'},{month:'2026-11',amount:'49500'}]};
 assert.equal(financeError(data),'');
 for(const installments of [[],[{month:'2026-03',amount:'50000'},{month:'2026-11',amount:'50000'}],[{month:'2026-03',amount:'100000.5'}],[{month:'2027-01',amount:'100000'}]])assert.ok(financeError({...data,installments}));
 assert.ok(financeError({...data,amount:'1'}));
});
test('hierarchy never submits stale amounts or installments after switching activity',()=>{
 const data=submissionData({...activity,category:HIERARCHY,public_employee:'no',cost_center:'old',amount:100000,installments:[{month:'2026-03',amount:100000}]});
 assert.equal(data.amount,null);assert.deepEqual(data.installments,[]);assert.equal(data.cost_center,'');assert.equal(data.public_employee,false);assert.equal(data.non_lective_hours,2.5);
 const correction=submissionData({...activity,category:HIERARCHY,installments:[]},{data:{category:HIERARCHY,cost_center:'CC-123'},version:4});
 assert.equal(correction.cost_center,'CC-123');assert.equal(correction.version,4);
});
