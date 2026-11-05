/* Puddle's Bread Exchange v0.1.0. No network or model calls. */
(function(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.BreadEngine = api;
})(typeof window !== 'undefined' ? window : this, function() {
  'use strict';
  const topologies = {
    choir:[10], loud_minority:[8,1,1], two_sources:[5,5],
    mixed:[4,3,2,1], five_pairs:[2,2,2,2,2], ten_roots:Array(10).fill(1)
  };
  const rules = ['headcount','receipts','shared_cause'];
  function independentPosterior(successes, count, error) {
    if (!Number.isInteger(successes) || !Number.isInteger(count) || count<1 || successes<0 || successes>count || !(error>0 && error<.5)) throw new RangeError('Invalid independent sensor parameters');
    const l1 = (1-error)**successes * error**(count-successes);
    const l0 = error**successes * (1-error)**(count-successes);
    return l1/(l1+l0);
  }
  function localError(marginal, shared) {
    if (!(shared>=0 && shared<marginal && marginal<.5)) throw new RangeError('Require 0 <= shared < marginal < .5');
    return (marginal-shared)/(1-2*shared);
  }
  function predict(bits, copies, marginal, shared) {
    if (!Array.isArray(bits) || !bits.length || bits.some(b=>b!==0 && b!==1) || bits.length!==copies.length || copies.some(w=>!Number.isInteger(w) || w<=0)) throw new RangeError('Invalid observations or multiplicities');
    const e=localError(marginal,shared), n=bits.length, s=bits.reduce((a,b)=>a+b,0);
    const total=copies.reduce((a,b)=>a+b,0), positive=bits.reduce((a,b,i)=>a+b*copies[i],0);
    return {
      headcount:independentPosterior(positive,total,marginal),
      receipts:independentPosterior(s,n,marginal),
      shared_cause:shared+(1-2*shared)*independentPosterior(s,n,e)
    };
  }
  function decide(p) {
    if (!Number.isFinite(p) || p<0 || p>1) throw new RangeError('Probability outside [0,1]');
    // 1e-12 tolerance implements exact 90%/10% boundaries in floating point.
    return p>=.9-1e-12 ? 'buy' : p<=.1+1e-12 ? 'reject' : 'hold';
  }
  function expectedPayoff(action,p) {
    if(action==='hold') return 0;
    if(action==='buy') return 10*p-9;
    if(action==='reject') return 1-10*p;
    throw new RangeError('Unknown action');
  }
  function payoff(action,truth) {
    if(!['buy','reject','hold'].includes(action) || ![0,1].includes(truth)) throw new RangeError('Invalid action or truth');
    return action==='hold' ? 0 : ((action==='buy')===Boolean(truth) ? 1 : -9);
  }
  function fraction(text) { const [n,d]=String(text).split('/').map(Number); return d===undefined?n:n/d; }
  return Object.freeze({topologies,rules,independentPosterior,localError,predict,decide,payoff,expectedPayoff,fraction});
});
