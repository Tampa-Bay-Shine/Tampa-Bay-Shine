const REPO = "Tampa-Bay-Shine/Tampa-Bay-Shine";
const BRANCH = "seo-dashboard";
const WORKFLOW_PATH = "cloudflare-site/seo-dashboard/data/opportunity-workflow.json";
const INTELLIGENCE_PATH = "cloudflare-site/seo-dashboard/data/opportunity-intelligence.json";
const EVENTS_PATH = "cloudflare-site/seo-dashboard/data/events.json";
const ALLOWED_ORIGIN = "https://seo.tampabayshine.com";
const STATUSES = ["new","investigating","implemented","measuring","closed"];
const NEXT = {new:"investigating",investigating:"implemented",implemented:"measuring",measuring:"closed"};
const CATEGORIES = ["Technical","Content","On-page","Internal linking","Migration","Local SEO","AEO"];

function json(body,status=200){
  return new Response(JSON.stringify(body),{status,headers:{"Content-Type":"application/json","Cache-Control":"no-store"}});
}
async function gh(env,path,options={}){
  const r=await fetch("https://api.github.com"+path,{
    ...options,
    headers:{
      "Accept":"application/vnd.github+json",
      "Authorization":`Bearer ${env.GITHUB_TOKEN}`,
      "X-GitHub-Api-Version":"2022-11-28",
      "User-Agent":"TampaBayShine-SEO-Workflow-Worker/1.0",
      ...(options.headers||{})
    }
  });
  if(!r.ok) throw new Error(`GitHub ${r.status}: ${await r.text()}`);
  return r.status===204?null:r.json();
}
function decode64(s){
  const bin=atob(String(s).replace(/\n/g,"")); const bytes=new Uint8Array(bin.length);
  for(let i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);
  return new TextDecoder().decode(bytes);
}
async function readRepoJson(env,path){
  const x=await gh(env,`/repos/${REPO}/contents/${path}?ref=${encodeURIComponent(BRANCH)}`);
  return JSON.parse(decode64(x.content));
}
async function atomicCommit(env,files,message){
  const ref=await gh(env,`/repos/${REPO}/git/ref/heads/${BRANCH}`);
  const parent=ref.object.sha;
  const commit=await gh(env,`/repos/${REPO}/git/commits/${parent}`);
  const tree=[];
  for(const [path,content] of Object.entries(files)){
    const blob=await gh(env,`/repos/${REPO}/git/blobs`,{method:"POST",body:JSON.stringify({content,encoding:"utf-8"}),headers:{"Content-Type":"application/json"}});
    tree.push({path,mode:"100644",type:"blob",sha:blob.sha});
  }
  const nt=await gh(env,`/repos/${REPO}/git/trees`,{method:"POST",body:JSON.stringify({base_tree:commit.tree.sha,tree}),headers:{"Content-Type":"application/json"}});
  const nc=await gh(env,`/repos/${REPO}/git/commits`,{method:"POST",body:JSON.stringify({message,tree:nt.sha,parents:[parent]}),headers:{"Content-Type":"application/json"}});
  await gh(env,`/repos/${REPO}/git/refs/heads/${BRANCH}`,{method:"PATCH",body:JSON.stringify({sha:nc.sha,force:false}),headers:{"Content-Type":"application/json"}});
  return nc.sha;
}
function iso(){return new Date().toISOString()}
function today(){return new Date().toISOString().slice(0,10)}
function findAction(intel,id){
  const a=(intel.actions||[]).find(x=>x.id===id);
  if(!a) throw new Error("Opportunity is not present in current Opportunity Intelligence.");
  return a;
}
function ensureRecord(workflow,action){
  workflow.items ||= {};
  const now=iso();
  const old=workflow.items[action.id]||{};
  return {
    id:action.id,status:old.status||"new",subject:action.subject||null,query:action.query||null,
    page:action.page||null,type:action.type||null,created_at:old.created_at||now,
    updated_at:old.updated_at||now,implemented_at:old.implemented_at||null,
    implementation_summary:old.implementation_summary||"",notes:old.notes||"",seo_event:old.seo_event||null
  };
}
export default {
  async fetch(request,env){
    // Cloudflare Access must protect this Worker custom domain. This header is
    // supplied by Access after successful authentication.
    const email=request.headers.get("Cf-Access-Authenticated-User-Email")||"";
    if(!email) return json({error:"Cloudflare Access authentication required."},401);
    if(env.ALLOWED_EMAIL && email.toLowerCase()!==env.ALLOWED_EMAIL.toLowerCase())
      return json({error:"Authenticated user is not authorized."},403);
    if(request.method==="GET"){
      try{
        const workflow=await readRepoJson(env,WORKFLOW_PATH);
        return json(workflow,200);
      }catch(e){
        return json({error:String(e?.message||e)},500);
      }
    }
    if(request.method!=="POST") return json({error:"Method not allowed."},405);

    try{
      const body=await request.json();
      const id=String(body.id||"");
      const target=String(body.status||"").toLowerCase();
      if(!id || !STATUSES.includes(target)) return json({error:"Invalid opportunity ID or status."},400);

      const [workflow,intel]=await Promise.all([readRepoJson(env,WORKFLOW_PATH),readRepoJson(env,INTELLIGENCE_PATH)]);
      const action=findAction(intel,id);
      const record=ensureRecord(workflow,action);
      const current=String(record.status||"new").toLowerCase();
      if(NEXT[current]!==target) return json({error:`Illegal transition: ${current} → ${target}.`},409);

      const now=iso(); const files={};
      if(target==="implemented"){
        const category=String(body.category||"");
        const summary=String(body.summary||"").trim();
        if(!CATEGORIES.includes(category)) return json({error:"Choose a valid SEO Event category."},400);
        if(summary.length<5) return json({error:"Describe what was implemented."},400);
        const events=await readRepoJson(env,EVENTS_PATH);
        if(events.schema_version!==1 || !Array.isArray(events.events)) throw new Error("Invalid events dataset.");
        const eventDate=today();
        const title=`Opportunity implemented: ${action.subject||id}`;
        if(events.events.some(e=>e.date===eventDate && String(e.title||"").toLowerCase()===title.toLowerCase()))
          return json({error:"A matching SEO Event already exists for today."},409);
        const event={date:eventDate,category,title,description:summary,urls:action.page?[action.page]:[],
          notes:`Opportunity Intelligence ID: ${id}. Event timing provides measurement context and does not prove causation.`};
        events.events.push(event);
        events.events.sort((a,b)=>`${a.date||""}|${String(a.title||"").toLowerCase()}`.localeCompare(`${b.date||""}|${String(b.title||"").toLowerCase()}`));
        record.implemented_at=record.implemented_at||now;
        record.implementation_summary=summary;
        record.seo_event={date:eventDate,category,title};
        files[EVENTS_PATH]=JSON.stringify(events,null,2)+"\n";
      }
      if(target==="closed"){
        const notes=String(body.notes||"").trim();
        if(notes.length<5) return json({error:"Add a short measurement outcome before closing."},400);
        record.notes=notes;
      }
      record.status=target; record.updated_at=now;
      workflow.items[id]=record; workflow.updated_at=now;
      files[WORKFLOW_PATH]=JSON.stringify(workflow,null,2)+"\n";
      const sha=await atomicCommit(env,files,`Move SEO opportunity to ${target}: ${action.subject||id}`);
      return json({ok:true,id,status:target,commit:sha,record},200);
    }catch(e){
      return json({error:String(e?.message||e)},500);
    }
  }
};
