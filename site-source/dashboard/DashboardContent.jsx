import React,{useMemo} from 'react';
import {EvidenceChart,DataComponent,DataTable,Filters,SectionHeader,SortableRegion,SortableItem,MetricCard, useDataApp,useDashboardTabs} from '../../data-app-public.jsx';
import {parseProducts,buildModel,number,percent,money} from './price-model.js';
import './dashboard.css';
const ids=['category','period','cohort'];
const tabs=[{id:'dashboard',label:'Discount patterns',filterIds:ids},{id:'products',label:'Product explorer',filterIds:ids,focusFields:['upc']},{id:'coverage',label:'Catalog coverage',filterIds:['category','period']}];
const line=(y,fields=[y])=>({type:'line',x:'date',y,fields,showXAxisLabel:false,showYAxisLabel:false,showLegend:fields.length>1,stackable:false,valueDecimals:2});
const cols=[{field:'name',label:'Product',presentation:'identity',secondaryField:'upc'},{field:'category',label:'Category'},{field:'observations',label:'Weeks seen'},{field:'discountRate',label:'Weeks discounted',renderCell:percent},{field:'discountDepth',label:'Mean discount',renderCell:percent},{field:'reversals',label:'Reversals'},{field:'low',label:'Lowest',renderCell:money},{field:'latest',label:'Endpoint price',renderCell:money}];
export function DashboardContent(){
 const shell=useDataApp(),{snapshot,queries,filters,setFilter}=shell;
 const {activeTabId}=useDashboardTabs(tabs);const tab=tabs.some(t=>t.id===activeTabId)?activeTabId:'dashboard';
 const parsed=useMemo(()=>parseProducts(queries.products.rows),[queries.products.rows]);
 const effective=useMemo(()=>tab==='coverage'?{...filters,cohort:'all'}:filters,[filters,tab]);
 const m=useMemo(()=>buildModel(parsed,queries.calendar.rows,effective),[parsed,queries.calendar.rows,effective]);
 const choose=p=>shell.exploreDashboard('products',{filters,focus:{upc:p.upc}});
 const cards=[];
 const add=(id,row,span,node,kind='chart')=>cards.push({id,row,span,node,kind});
 const chart=(id,row,span,title,description,spec,rows,sourceRows=m.sources,extra={})=>add(id,row,span,<EvidenceChart id={id} queryId="products" variant="card" title={title} description={description} spec={spec} rows={rows} sourceRows={sourceRows} height={290} {...extra}/>);
 const table=(id,row,title,description,rows,columns,sourceRows=m.sources,extra={})=>add(id,row,12,<DataComponent id={id} queryId="products" variant="card" kind="table" title={title} description={description} sourceRows={sourceRows} displayRows={rows}><DataTable rows={rows} columns={columns} rowKey={rows[0]?.upc?'upc':columns[0].field} label={title} {...extra}/></DataComponent>,'table');
 if(tab==='dashboard'){
  const metricRows=[{products:m.upcs,changes:m.total.changed??0,sameRegularShare:m.total.changed?m.total.sameRegular/m.total.changed:null,matched:m.total.matched??0,reversals:m.reversals}];
  for(const [id,title,value,desc] of [
   ['scope-products','Products observed',number(m.upcs),'Distinct UPCs seen at least once in the selected period and population.'],
   ['scope-changes','Weekly price changes',number(m.total.changed??0),'Matched consecutive observations with different current prices; both dates fall inside the selected period.'],
   ['scope-discounts','Regular price unchanged',percent(m.total.changed?m.total.sameRegular/m.total.changed:null),'Share of current-price changes where listed regular price did not change. This is consistent with discount changes, not proof of promotion causality.']])add(id,'metrics',4,<MetricCard id={id} queryId="products" title={title} value={value} description={desc} sourceRows={m.sources} displayRows={metricRows}/>,'metric');
  const movement=m.history.slice(1).flatMap(h=>[{date:h.date,type:'Regular price unchanged',changes:h.sameRegular},{date:h.date,type:'Regular price changed',changes:h.newRegular}]);
  chart('weekly-movement','movement',7,'Weekly price changes','Counts of changed current prices, split by whether listed regular price also changed.',{type:'stackedBar',x:'date',y:'changes',series:'type',showLegend:true,valueDecimals:0,colors:{'Regular price unchanged':'var(--chart-1)','Regular price changed':'var(--chart-2)'}},movement);
  chart('discount-frequency','movement',5,'Share of products discounted','Discounted UPCs divided by observed UPCs in each snapshot. Missing products are excluded from the denominator.',line('discountRate'),m.history);
  const ranked=m.cats.filter(c=>c.matched>=100).sort((a,b)=>b.changeRate-a.changeRate||b.matched-a.matched).slice(0,12);
  chart('category-frequency','categories',6,'Price-change frequency by category','Top 12 categories by changes / matched weekly comparisons; at least 100 comparisons. Categories are fixed to each UPC’s final observed category.',{type:'horizontalBar',x:'category',y:'changeRate',showValues:true,stackable:false,valueDecimals:1},ranked,m.sources,{height:380,chartOptions:{getMarkActions:({row})=>[{label:'Explore category',onSelect:()=>setFilter('category',row.category)}]}});
  const depth=m.cats.filter(c=>c.discounted>=30).sort((a,b)=>b.discountDepth-a.discountDepth).slice(0,12);
  chart('category-depth','categories',6,'Average discount depth by category','Mean percentage below listed regular price, among discounted observations only. Top 12 categories with at least 30 discounted observations.',{type:'horizontalBar',x:'category',y:'discountDepthRate',showValues:true,stackable:false,valueDecimals:1},depth.map(c=>({...c,discountDepthRate:c.discountDepth})),m.sources,{height:380,chartOptions:{getMarkActions:({row})=>[{label:'Explore category',onSelect:()=>setFilter('category',row.category)}]}});
  table('category-detail','category-details','Category comparison','Rates use pooled numerators and denominators; discount depth excludes observations without a discount.',m.cats.sort((a,b)=>b.changed-a.changed),[{field:'category',label:'Category'},{field:'products',label:'Products'},{field:'matched',label:'Matched comparisons'},{field:'changed',label:'Changes'},{field:'changeRate',label:'Change frequency',renderCell:percent},{field:'sameRegularShare',label:'Regular unchanged',renderCell:percent},{field:'discountRate',label:'Discount frequency',renderCell:percent},{field:'discountDepth',label:'Discount depth',renderCell:percent},{field:'reversals',label:'Reversals'}],m.sources,{onRowSelect:r=>setFilter('category',r.category),rowActionLabel:r=>`Explore ${r.category}`});
  const repeated=m.stats.filter(p=>p.reversals>0).sort((a,b)=>b.reversals-a.reversals||a.upc.localeCompare(b.upc)); const repeatedIds=new Set(repeated.map(p=>p.upc));
  table('repeat-discounts','reversals','Products with observed discount reversals','A reversal is a drop followed by a return to the earlier price over three consecutive weekly observations, with regular price constant. These are observed patterns, not a forecast.',repeated,cols,m.sources.filter(p=>repeatedIds.has(p.upc)),{onRowSelect:choose,rowActionLabel:r=>`View price history for ${r.name}`});
 }
 if(tab==='products'){
  const selected=m.stats.find(p=>p.upc===shell.viewFocus?.upc);
  if(selected){
   const p=m.pool.find(p=>p.upc===selected.upc),source=m.sources.filter(p=>p.upc===selected.upc);
   const hist=m.weeks.map(w=>({date:w.date,current:p.obs.get(w.index)?.current??null,regular:p.obs.get(w.index)?.regular??null,observed:p.obs.has(w.index)?'Observed':'Not observed'}));
   chart('product-history','detail',12,selected.name,`UPC ${selected.upc} · ${selected.category}. Gaps are unobserved weeks; values are not interpolated.`,{...line('current',['current','regular']),currency:'USD',connectNulls:false,legend:{labels:{current:'Current price',regular:'Listed regular price'}}},hist,source,{height:320});
   table('product-observations','observations','Weekly observations',`${selected.observations} of ${m.weeks.length} selected weeks observed.`,hist,[{field:'date',label:'Snapshot'},{field:'current',label:'Current price',renderCell:money},{field:'regular',label:'Listed regular price',renderCell:money},{field:'observed',label:'Observation'}],source,{searchable:false});
  }
  table('all-products','registry',selected?'Explore another product':'Products and price history','Search a product name or UPC, then select a row to inspect its full weekly history. Lowest price and discount statistics apply to the selected period.',m.stats.sort((a,b)=>b.reversals-a.reversals||a.name.localeCompare(b.name)),cols,m.sources,{onRowSelect:r=>{shell.setDashboardFocus({upc:r.upc});window.scrollTo({top:0,behavior:'smooth'});},rowActionLabel:r=>`View price history for ${r.name}`});
 }
 if(tab==='coverage'){
  chart('catalog-size','size',7,'Products observed each week','Distinct UPCs in each weekly snapshot for the selected category. Counts measure catalog capture, not physical stock.',line('products'),m.history);
  chart('matched-coverage','size',5,'Prior snapshot matched','UPCs present in both snapshots / UPCs in the prior snapshot. Missing first-period comparison is not zero.',line('coverageRate'),m.history);
  chart('catalog-movement','gaps',12,'Missing and newly observed products','Missing means present the prior week and absent this week. Newly observed includes first appearances and returning items.',{type:'bar',x:'date',y:'missing',fields:['missing','entered'],showLegend:true,legend:{labels:{missing:'Missing versus prior week',entered:'Newly observed versus prior week'}},valueDecimals:0},m.history.slice(1));
  table('coverage-details','coverage-detail','Snapshot coverage','These counts are for the selected category. Cause of any gap remains unresolved.',m.history,[{field:'date',label:'Snapshot'},{field:'products',label:'Observed UPCs'},{field:'matched',label:'Matched prior',renderCell:(v,r)=>r.date===m.weeks[0]?.date?'—':number(v)},{field:'coverageRate',label:'Prior coverage',renderCell:percent},{field:'missing',label:'Missing',renderCell:(v,r)=>r.date===m.weeks[0]?.date?'—':number(v)},{field:'entered',label:'Newly observed',renderCell:(v,r)=>r.date===m.weeks[0]?.date?'—':number(v)},{field:'returned',label:'Previously seen returns',renderCell:(v,r)=>r.date===m.weeks[0]?.date?'—':number(v)}],m.sources,{searchable:false});
 }
 const layout=[...new Set(cards.map(c=>c.row))].map(row=>({id:`kk:${tab}:${row}`,kind:row==='metrics'?'metrics':undefined,items:cards.filter(c=>c.row===row).map(c=>c.id)}));
 return <div className="kk-exploration">
 <header className="kk-retirement" aria-label="Project retirement notice">
 <strong>Project retired — September 6, 2026.</strong> Maintenance, support, and automated updates have ended. This site remains available for reference. Its data is no longer refreshed and may be out of date.
 </header>
 <Filters filters={snapshot.filters.filter(f=>tabs.find(t=>t.id===tab).filterIds.includes(f.id))} queries={queries} values={filters} onChange={setFilter} clearLabel="Reset view"/>
 <div className="kk-context"><span>Historical catalog · 17 weekly snapshots · collection ended September 6, 2026</span><span>{number(m.total.matched??0)} matched comparisons in this view</span></div>
 <p className="kk-note" data-editable-id={`kk-note-${tab}`} data-editable-narrative>{tab==='coverage'?'Missing from a snapshot does not establish a stockout or discontinuation. Large August gaps affect catalog-wide averages.':'Discount = current price below listed regular price. The crawler can substitute current price for unavailable regular prices. “Every week, stable name” restricts the view to a fixed cohort; it may not represent the full catalog.'}</p>
 {shell.canReturnFromExploration&&<button type="button" className="button kk-back" onClick={shell.returnFromExploration}>Back to previous view</button>}
 {m.weeks.length<2&&<p className="kk-note">Choose at least two weekly snapshots to compare prices; three are needed to observe a reversal.</p>}
 {m.upcs===0?<p role="status">No products were observed for this selection. Reset the filters or widen the period.</p>:<SortableRegion id={`kk:${tab}`} variant="canvas" spacing="standard" rows={layout} authoredRevision={1} label="Price exploration blocks">{cards.map(c=><SortableItem key={c.id} id={c.id} kind={c.kind} span={c.span} label={c.id}>{c.node}</SortableItem>)}</SortableRegion>}
 <footer className="kk-final-footer" aria-label="Site footer"><span>King Kullen Research · Final public interface</span><nav aria-label="Footer"><a href="./old-site/">Old Site</a><a href="https://github.com/frankstop/KingKullenResearch">GitHub</a></nav></footer>
 </div>;
}
