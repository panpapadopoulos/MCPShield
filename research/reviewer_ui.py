"""Self-contained offline review form; no network requests or automatic attestations."""
import argparse
from pathlib import Path
import json
from .cli import read
from .data import digest, validate
from .reviews import export_review
from .expand_cli import write_text_new


def render(form):
    if form["proposal_visible"] or form["human_attestation"] or form["independent_attestation"]:
        raise ValueError("Generate only blank blind human-review pages")
    payload = json.dumps(form, ensure_ascii=True).replace("<", "\\u003c")
    return """<!doctype html><html lang="en"><meta charset="utf-8"><title>MCPShield independent review</title>
<style>body{font:17px system-ui;max-width:950px;margin:30px auto;padding:16px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eee;padding:14px}textarea{width:100%;height:90px}button,input,select{font:inherit;padding:8px;margin:8px}label{display:block}#status{color:#843b00}</style>
<h1>Independent interaction review</h1><p>Work offline. Do not execute tool content. Review only what is visible at the current boundary. Read INSTRUCTIONS.md before starting. No proposed answers are shown.</p>
<label>Your stable reviewer identifier <input id="reviewer"></label><label>Resume a saved draft before submission <input type="file" id="resume" accept="application/json"></label><p id="count"></p>
<h2>Authorized task and scope</h2><pre id="scope"></pre><h2>Available interaction at this boundary</h2><pre id="events"></pre>
<label>Decision <select id="decision"><option value="">Choose independently</option><option>ALLOWED</option><option>WARNING</option><option>BLOCKED</option><option>REJECT</option></select></label>
<label>Category (see guidelines) <input id="category" list="categories"></label><datalist id="categories"><option>none</option><option>scope_ambiguity</option><option>ambiguous_instruction</option><option>prompt_injection</option><option>tool_poisoning</option><option>command_injection</option><option>unauthorized_file_access</option><option>unauthorized_resource_access</option><option>excessive_permissions</option><option>malicious_response</option><option>unauthorized_data_transfer</option></datalist>
<label>Reason / justification <textarea id="reason"></textarea></label><button id="previous">Previous</button><button id="next">Save and next</button>
<p id="status"></p><label><input type="checkbox" id="human">I personally reviewed the submitted items.</label><label><input type="checkbox" id="independent">I did not author their labels and reviewed independently.</label>
<button id="draft">Save draft without attestations</button><button id="download">Download completed responses</button><p>Save a draft before closing. Resume it here later. Final submissions include completed items only. Keep the original blank package.</p>
<script>
const form=PAYLOAD; let index=0; const $=id=>document.getElementById(id); $('reviewer').value=form.reviewer;
function show(){let x=form.items[index];$('count').textContent=`Item ${index+1} of ${form.items.length} · boundary ${x.event_index}`;$('scope').textContent=JSON.stringify(x.authorized,null,2);$('events').textContent=JSON.stringify(x.events.slice(0,x.event_index+1),null,2);$('decision').value=x.action==='reject'?'REJECT':x.reviewed_label?.decision||'';$('category').value=x.reviewed_label?.attack_category||'';$('reason').value=x.justification||'';}
function save(){let d=$('decision').value,reason=$('reason').value.trim(),cat=$('category').value.trim(),x=form.items[index];if(!d){x.action=null;x.reviewed_label=null;x.justification='';return true;}if(!reason||(d!=='REJECT'&&!cat)){ $('status').textContent='Please supply a category and a reason, or choose REJECT with a reason.';return false;}x.action=d==='REJECT'?'reject':'modify';x.justification=reason;x.reviewed_label=d==='REJECT'?null:{event_index:x.event_index,decision:d,attack_category:cat,rationale:reason};$('status').textContent='Saved in this page. Download to keep your work.';return true;}
$('previous').onclick=()=>{if(save()){index=Math.max(0,index-1);show();}};$('next').onclick=()=>{if(save()){index=Math.min(form.items.length-1,index+1);show();}};
function download(output,name){let url=URL.createObjectURL(new Blob([JSON.stringify(output,null,2)],{type:'application/json'}));let a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('draft').onclick=()=>{if(save())download({...form,reviewer:$('reviewer').value.trim(),human_attestation:false,independent_attestation:false},'review-draft.json');};
$('resume').onchange=async event=>{try{let saved=JSON.parse(await event.target.files[0].text());if(saved.dataset_sha256!==form.dataset_sha256||saved.proposal_visible)throw Error('Wrong dataset or non-blind form');let updates=[];for(let item of saved.items){let original=form.items.find(x=>x.episode_id===item.episode_id&&x.event_index===item.event_index);if(!original||original.episode_sha256!==item.episode_sha256||JSON.stringify(original.events)!==JSON.stringify(item.events)||JSON.stringify(original.authorized)!==JSON.stringify(item.authorized))throw Error('Changed or unknown interaction');updates.push([original,item]);}for(let [original,item] of updates){original.action=item.action;original.reviewed_label=item.reviewed_label;original.justification=item.justification;}$('reviewer').value=saved.reviewer;$('human').checked=false;$('independent').checked=false;show();$('status').textContent='Draft resumed. Attestations remain unchecked.';}catch(error){$('status').textContent='Cannot resume: '+error.message;}};
$('download').onclick=()=>{if(!save())return;let reviewer=$('reviewer').value.trim();if(!reviewer||!$('human').checked||!$('independent').checked){$('status').textContent='Enter your identifier and attest only if the statements are true.';return;}let submitted=form.items.filter(x=>x.action);if(!submitted.length){$('status').textContent='No completed items to submit.';return;}let output={...form,reviewer,human_attestation:true,independent_attestation:true,items:submitted};let url=URL.createObjectURL(new Blob([JSON.stringify(output,null,2)],{type:'application/json'}));let a=document.createElement('a');a.href=url;a.download='review-responses.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};show();
</script></html>""".replace("PAYLOAD", payload)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="data/generated/research-expansion-v3.json")
    parser.add_argument("--output", default=".local/research-phase2/review-ready-v2")
    args = parser.parse_args(argv)
    dataset = read(args.dataset)
    validate(dataset)
    root = Path(__file__).resolve().parents[1]
    instructions = (root / "docs/REVIEW_GUIDELINES.md").read_text(encoding="utf-8")
    for person in ("reviewer-A", "reviewer-B"):
        form = export_review(dataset, person, opaque_ids=True)
        if len(form["items"]) != sum(len(e["events"]) for e in dataset["episodes"]):
            raise ValueError("Incomplete reviewer package")
        destination = Path(args.output) / person
        write_text_new(destination / "REVIEW.html", render(form))
        write_text_new(destination / "INSTRUCTIONS.md", instructions)
    print(f"Two blank offline reviewer pages prepared for dataset {digest(dataset)}")


if __name__ == "__main__":
    main()
