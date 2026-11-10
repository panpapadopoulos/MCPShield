import React, {useEffect, useState} from 'react';

const names={no_defense:'No defense (authorization only)',rules:'Rule-based baseline',pretrained_qwen:'Pretrained Qwen',setfit:'Trained SetFit/MiniLM',ppo:'Trained PPO'};
const value=v=>v==null?'Not scored':v;
export default function ResearchComparison({api}){
 const [report,setReport]=useState(null),[error,setError]=useState('');
 async function refresh(){try{setReport(await api('research-evaluation'));setError('')}catch(e){setReport(null);setError(e.message)}}
 useEffect(()=>{let active=true;api('research-evaluation').then(r=>{if(active)setReport(r)}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[]);
 return <section className="panel"><div className="panel-heading"><div><h2>Five-method research comparison</h2><p>Read-only published results. Historical four-method experiments remain below.</p></div><button onClick={refresh}>Refresh results</button></div>
 <div className="notice">{report?.evidence_kind==='DEVELOPMENT_ONLY'?'DEVELOPMENT ONLY — synthetic simulation; not independently validated.':'PENDING — no compatible published experiment.'} Model recommendations and mandatory authorization overrides are separate. Recovery-assisted completion does not establish attack recognition.</div>
 {error&&<p role="alert">{error}</p>}
 <div className="table-scroll"><table><thead><tr><th>Method</th><th>Status</th><th>Task goals</th><th>Uninterrupted</th><th>Unsafe outcomes</th><th>Initial blocks</th><th>Authorization overrides</th></tr></thead><tbody>{Object.entries(names).map(([key,label])=>{const row=report?.methods?.[key],run=row?.status==='RUN',m=row?.security_utility;return <tr key={key}><td>{label}<small>{row?.reason}</small></td><td>{row?.status||'NOT RUN'}</td><td>{run?value(row.summary?.task_goal_completions):'—'}</td><td>{run?value(m?.uninterrupted_completion):'—'}</td><td>{run?value(m?.unsafe_outcomes):'—'}</td><td>{run&&m?.initial_action_block_rate!=null?(100*m.initial_action_block_rate).toFixed(1)+'%':'—'}</td><td>{run?value(m?.authorization_overrides):'—'}</td></tr>})}</tbody></table></div>
 {report?.comparison_sha256&&<details><summary>Evidence and model decisions</summary><pre>{JSON.stringify({comparison_sha256:report.comparison_sha256,allocation_sha256:report.allocation_sha256,provenance:report.provenance,methods:report.methods},null,2)}</pre></details>}
 </section>
}
