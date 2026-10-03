from __future__ import annotations
import hashlib
import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ASSESSMENT_DB=os.getenv("ASSESSMENT_DB_PATH","/assessment/hhl-assessment.db")
REPORT_DB=os.getenv("REPORT_DB_PATH","/data/hhl-reporting.db")
REPORT_DIR=Path(os.getenv("REPORT_DIR","/reports"))
PORT=int(os.getenv("PORT","8094")); HOST="0.0.0.0"; LOCK=threading.Lock()
WEIGHTS={"CRITICAL":10,"HIGH":8,"MEDIUM":5,"LOW":2,"INFO":0}
TEMPLATES={
 "HHL-F001":{"title":"Repeated synthetic-user interaction","source_rule":"HHL-D001","cause":"One synthetic user generated more than three click events in a campaign run.","impact":"Training-only signal requiring investigation.","remediation":"Review synthetic awareness controls, detection thresholds and response workflow."},
 "HHL-F002":{"title":"Campaign-wide synthetic click burst","source_rule":"HHL-D002","cause":"At least five distinct synthetic users generated click events in one campaign run.","impact":"Training-only signal requiring investigation.","remediation":"Review synthetic awareness controls, detection coverage and response workflow."},
}

def now():
 return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z")

def ro(path):
 c=sqlite3.connect(f"file:{path}?mode=ro",uri=True); c.row_factory=sqlite3.Row; return c

def init():
 REPORT_DIR.mkdir(parents=True,exist_ok=True)
 c=sqlite3.connect(REPORT_DB,check_same_thread=False)
 c.execute("PRAGMA journal_mode=WAL")
 c.execute("CREATE TABLE IF NOT EXISTS reports(report_id TEXT PRIMARY KEY,assessment_id TEXT,created_at TEXT,report_json TEXT,markdown_path TEXT,json_path TEXT)")
 c.execute("CREATE TABLE IF NOT EXISTS audit(audit_id INTEGER PRIMARY KEY AUTOINCREMENT,report_id TEXT,event_type TEXT,details_json TEXT,created_at TEXT)")
 c.execute("CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'audit_append_only'); END")
 c.execute("CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'audit_append_only'); END")
 c.commit(); return c

def snapshot(aid):
 c=ro(ASSESSMENT_DB)
 try:
  fs=c.execute("SELECT finding_id,assessment_id,template_id,campaign_id,correlation_id,severity,status,evidence_json,created_at FROM findings WHERE assessment_id=? ORDER BY created_at,finding_id",(aid,)).fetchall()
  ids=[r["finding_id"] for r in fs]; actions=[]
  if ids:
   q=",".join("?" for _ in ids)
   actions=c.execute(f"SELECT action_id,finding_id,action_type,description,status,evidence_json,created_at FROM actions WHERE finding_id IN ({q}) ORDER BY created_at,action_id",ids).fetchall()
  findings=[{"finding_id":r["finding_id"],"assessment_id":r["assessment_id"],"template_id":r["template_id"],"campaign_id":r["campaign_id"],"correlation_id":r["correlation_id"],"severity":r["severity"],"status":r["status"],"evidence":json.loads(r["evidence_json"]),"created_at":r["created_at"]} for r in fs]
  acts=[{"action_id":r["action_id"],"finding_id":r["finding_id"],"action_type":r["action_type"],"description":r["description"],"status":r["status"],"evidence":json.loads(r["evidence_json"]),"created_at":r["created_at"]} for r in actions]
  verified={a["finding_id"] for a in acts if a["action_type"]=="REMEDIATION" and a["status"]=="VERIFIED"}
  initial=sum(WEIGHTS.get(f["severity"],0) for f in findings)
  residual=sum(WEIGHTS.get(f["severity"],0) for f in findings if f["finding_id"] not in verified and f["status"]!="CLOSED")
  return {"assessment_id":aid,"findings":findings,"actions":acts,"risk":{"risk_points_initial":initial,"risk_points_residual":residual,"verified_remediations":len(verified),"method":"contextual training weight; not CVSS or a production security score"}}
 finally: c.close()

def evidence_index(s):
 out=[]
 for f in s["findings"]:
  e=f["evidence"]; t=TEMPLATES.get(f["template_id"],{})
  users=e.get("users",[]) or ([e["user_id"]] if e.get("user_id") else [])
  acts=[a for a in s["actions"] if a["finding_id"]==f["finding_id"]]
  out.append({"finding_id":f["finding_id"],"source_rule":t.get("source_rule"),"campaign_id":f["campaign_id"],"correlation_id":f["correlation_id"],"event_ids":e.get("event_ids",[]),"users":users,"action_ids":[a["action_id"] for a in acts]})
 return out

def build(aid):
 s=snapshot(aid); ev=evidence_index(s)
 counts={}
 for f in s["findings"]: counts[f["severity"]]=counts.get(f["severity"],0)+1
 register=[]
 for f in s["findings"]:
  verified=any(a["finding_id"]==f["finding_id"] and a["action_type"]=="REMEDIATION" and a["status"]=="VERIFIED" for a in s["actions"])
  register.append({"finding_id":f["finding_id"],"severity":f["severity"],"status":f["status"],"residual_weight":0 if verified or f["status"]=="CLOSED" else WEIGHTS.get(f["severity"],0)})
 rid="RPT-"+hashlib.sha256(json.dumps({"assessment":s,"evidence":ev},sort_keys=True,separators=(",",":")).encode()).hexdigest()[:16]
 findings=[]
 for f in s["findings"]:
  t=TEMPLATES.get(f["template_id"],{})
  findings.append({**f,"title":t.get("title","Unknown template"),"source_rule":t.get("source_rule"),"cause":t.get("cause"),"impact":t.get("impact"),"remediation":t.get("remediation")})
 return {"report_id":rid,"assessment_id":aid,"generated_at":now(),"scope":"Local synthetic Human Hacking Lab only; no real credentials, personal data, third-party targets or external messaging.","executive_summary":{"finding_count":len(findings),"severity_counts":counts,"risk":s["risk"],"statement":"This report describes observed and derived evidence within the executed lab scope. It does not declare the lab or any external system secure."},"findings":findings,"evidence_index":ev,"remediation_tracking":s["actions"],"residual_risk_register":register,"limitations":["Evidence is limited to synthetic telemetry and assessment records available to the lab.","Retest records are tracked independently; current Phase 06 residual-risk logic reduces residual weight after VERIFIED remediation.","No external systems, identities, credentials or messaging infrastructure were assessed."]}

def md(r):
 lines=[f"# Human Hacking Lab Assessment Report — {r['report_id']}","","## Scope",r["scope"],"","## Executive Summary",r["executive_summary"]["statement"],f"- Findings: {r['executive_summary']['finding_count']}",f"- Severity counts: {json.dumps(r['executive_summary']['severity_counts'],sort_keys=True)}",f"- Initial risk points: {r['executive_summary']['risk']['risk_points_initial']}",f"- Residual risk points: {r['executive_summary']['risk']['risk_points_residual']}","","## Findings"]
 for f in r["findings"]:
  lines += [f"### {f['finding_id']} — {f['title']}",f"- Severity: {f['severity']}",f"- Status: {f['status']}",f"- Source rule: {f['source_rule']}",f"- Campaign: {f['campaign_id']}",f"- Correlation: {f['correlation_id']}",f"- Evidence: {json.dumps(f['evidence'],sort_keys=True)}",f"- Cause: {f['cause']}",f"- Impact: {f['impact']}",f"- Remediation: {f['remediation']}",""]
 lines += ["## Evidence Index"]+[f"- {x['finding_id']} -> rule {x['source_rule']}, correlation {x['correlation_id']}, events {','.join(map(str,x['event_ids']))}, actions {','.join(x['action_ids'])}" for x in r["evidence_index"]]
 lines += ["","## Remediation Tracking"]+[f"- {a['action_id']} {a['action_type']} {a['status']} for {a['finding_id']} — {a['description']}" for a in r["remediation_tracking"]]
 lines += ["","## Residual Risk Register"]+[f"- {x['finding_id']} severity {x['severity']} status {x['status']} residual weight {x['residual_weight']}" for x in r["residual_risk_register"]]
 lines += ["","## Limitations"]+[f"- {x}" for x in r["limitations"]]
 return "\n".join(lines)+"\n"

def persist(r,db):
 mdp=REPORT_DIR/f"{r['report_id']}.md"; jsp=REPORT_DIR/f"{r['report_id']}.json"
 mdp.write_text(md(r),encoding="utf-8"); jsp.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 with LOCK:
  db.execute("INSERT OR REPLACE INTO reports VALUES(?,?,?,?,?,?)",(r["report_id"],r["assessment_id"],r["generated_at"],json.dumps(r,sort_keys=True),str(mdp),str(jsp)))
  db.execute("INSERT INTO audit(report_id,event_type,details_json,created_at) VALUES(?,?,?,?)",(r["report_id"],"REPORT_GENERATED",json.dumps({"assessment_id":r["assessment_id"],"finding_count":len(r["findings"])},sort_keys=True),r["generated_at"]))
  db.commit()

class Handler(BaseHTTPRequestHandler):
 def __init__(self,*a,db=None,**kw): self.db=db; super().__init__(*a,**kw)
 def out(self,status,p):
  b=json.dumps(p,separators=(",",":")).encode(); self.send_response(status); self.send_header("Content-Type","application/json"); self.send_header("Cache-Control","no-store"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
 def do_GET(self):
  p=urlparse(self.path); q=parse_qs(p.query); aid=q.get("id",[None])[0]
  if p.path=="/health": return self.out(200,{"status":"ok","service":"hhl-reporting"})
  if p.path in ("/reports","/evidence","/residual-risk") and not aid: return self.out(400,{"error":"missing_id"})
  if p.path=="/reports":
   r=build(aid); persist(r,self.db); return self.out(200,r)
  if p.path=="/evidence": return self.out(200,{"assessment_id":aid,"evidence_index":evidence_index(snapshot(aid))})
  if p.path=="/residual-risk":
   r=build(aid); return self.out(200,{"assessment_id":aid,"register":r["residual_risk_register"],"summary":r["executive_summary"]["risk"]})
  if p.path=="/audit":
   with LOCK:
    rows=self.db.execute("SELECT audit_id,report_id,event_type,details_json,created_at FROM audit"+(" WHERE report_id IN (SELECT report_id FROM reports WHERE assessment_id=?)" if aid else "")+" ORDER BY audit_id",(aid,) if aid else ()).fetchall()
   return self.out(200,{"audit":[{"audit_id":x[0],"report_id":x[1],"event_type":x[2],"details":json.loads(x[3]),"created_at":x[4]} for x in rows]})
  if p.path.startswith("/reports/"):
   rid=p.path.rsplit("/",1)[-1]
   with LOCK: row=self.db.execute("SELECT report_json FROM reports WHERE report_id=?",(rid,)).fetchone()
   if not row: return self.out(404,{"error":"report_not_found"})
   return self.out(200,json.loads(row[0]))
  return self.out(404,{"error":"not_found"})
 def log_message(self,*a): return

if __name__=="__main__":
 db=init()
 ThreadingHTTPServer((HOST,PORT),lambda *a,**kw:Handler(*a,db=db,**kw)).serve_forever()
