export const number = value => value == null ? '—' : new Intl.NumberFormat('en-US').format(value);
export const percent = value => value == null ? '—' : `${(100 * value).toFixed(1)}%`;
export const money = value => value == null ? '—' : new Intl.NumberFormat('en-US', {style:'currency',currency:'USD'}).format(value);
export function parseProducts(rows) {
  return rows.map(p => ({...p, obs:new Map(JSON.parse(p.observations).map(([i,c,r]) => [i,{current:c,regular:r}]))}));
}
export function buildModel(products, calendar, filters) {
  const [start,end] = String(filters.period ?? '2026-05-17..2026-09-06').split('..');
  const weeks=calendar.filter(d=>d.index>0 && (start==='all'||(d.date>=start && d.date<=(end??start))));
  const pool=products.filter(p=>(!filters.category||filters.category==='all'||p.category===filters.category)&&(!filters.cohort||filters.cohort==='all'||p.cohort===filters.cohort));
  const history=weeks.map(w=>({...w,products:0,discounted:0,depthSum:0,matched:0,changed:0,sameRegular:0,newRegular:0,increases:0,decreases:0,missing:0,returned:0,entered:0,currentSum:0,regularSum:0}));
  const stats=[]; const categories=new Map(); const sources=[];
  for(const p of pool){
    let observations=0,discounted=0,depthSum=0,matched=0,changed=0,sameRegular=0,reversals=0,low=Infinity,high=0,first=null,last=null;
    const selected=[];
    for(let j=0;j<weeks.length;j++){
      const w=weeks[j],v=p.obs.get(w.index),a=j?p.obs.get(weeks[j-1].index):null;
      const h=history[j];
      if(!v){if(a)h.missing++;continue;}
      selected.push([w.index,v.current,v.regular]);observations++;h.products++;h.currentSum+=v.current;h.regularSum+=v.regular;
      first??=v.current;last=v.current;low=Math.min(low,v.current);high=Math.max(high,v.current);
      if(v.current<v.regular){discounted++;h.discounted++;const depth=(v.regular-v.current)/v.regular;depthSum+=depth;h.depthSum+=depth;}
      if(j && !a){h.entered++;if([...p.obs.keys()].some(i=>i<weeks[j-1].index))h.returned++;}
      if(a && w.index===weeks[j-1].index+1){
        matched++;h.matched++;
        if(v.current!==a.current){changed++;h.changed++;if(v.regular===a.regular){sameRegular++;h.sameRegular++;}else h.newRegular++;if(v.current>a.current)h.increases++;else h.decreases++;}
      }
      if(j>=2){const b=p.obs.get(weeks[j-2].index);if(b&&a&&b.current===v.current&&a.current<v.current&&b.regular===a.regular&&a.regular===v.regular)reversals++;}
    }
    if(!observations)continue;
    const row={upc:p.upc,name:p.name,category:p.category,observations,discounted,discountRate:discounted/observations,discountDepth:discounted?depthSum/discounted:null,matched,changed,sameRegular,reversals,low,high,latest:p.obs.get(weeks.at(-1)?.index)?.current??null,status:p.obs.has(weeks.at(-1)?.index)?'Observed at endpoint':'Missing at endpoint',changeRate:matched?changed/matched:null};
    stats.push(row);sources.push({...p,obs:undefined,observations:JSON.stringify(selected)});
    const c=categories.get(p.category)??{category:p.category,products:0,observations:0,discounted:0,depthSum:0,matched:0,changed:0,sameRegular:0,reversals:0};
    c.products++;for(const k of ['observations','discounted','depthSum','matched','changed','sameRegular','reversals'])c[k]+=({observations,discounted,depthSum,matched,changed,sameRegular,reversals})[k];categories.set(p.category,c);
  }
  history.forEach((h,j)=>{h.discountRate=h.products?h.discounted/h.products:null;h.discountDepth=h.discounted?h.depthSum/h.discounted:null;h.changeRate=h.matched?h.changed/h.matched:null;h.sameRegularShare=h.changed?h.sameRegular/h.changed:null;h.coverageRate=j&&history[j-1].products?h.matched/history[j-1].products:null;h.averageCurrent=h.products?h.currentSum/h.products:null;});
  const cats=[...categories.values()].map(c=>({...c,discountRate:c.discounted/c.observations,discountDepth:c.discounted?c.depthSum/c.discounted:null,changeRate:c.matched?c.changed/c.matched:null,sameRegularShare:c.changed?c.sameRegular/c.changed:null}));
  const total=history.reduce((a,h)=>{for(const k of ['matched','changed','sameRegular','discounted','products'])a[k]=(a[k]??0)+h[k];return a;},{});
  return {weeks,pool,history,stats,cats,sources,total,upcs:stats.length,reversals:stats.reduce((s,p)=>s+p.reversals,0)};
}
