from __future__ import annotations
import json, os, sqlite3, threading, uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

TELEMETRY_DB=os.getenv("TELEMETRY_DB_PATH","/telemetry/hhl-simulation.db")
ASSESSMENT_DB=os.getenv("ASSESSMENT_DB_PATH","/data/hhl-assessment.db")
PORT=int(os.getenv("PORT","8093")); HOST="0.0.0.0"; CAMPAIGN_ID="HHL02-A"; LOCK=threading.Lock()
WEIGHTS={"CRITICAL":10,"HIGH":8,"MEDIUM":5,"LOW":2,"INFO":0}
TEMPLATES={
 "HHL-F001":{"title":"Repeated synthetic-user interaction","severity":"MEDIUM","source_rule":"HHL-D001","cause":"One synthetic user generated more than three click events in a campaign run.","impact":"Training-only signal requiring investigation.","remediation":"Review synthetic awareness controls, detection thresholds and response workflow."},
 "HHL-F002":{"title":"Campaign-wide synthetic click burst","severity":"MEDIUM","source_rule":"HHL-D002","cause":"At least five distinct synthetic users generated click events in one campaign run.","impact":"Training-only signal requiring investigation.","remediation":"Review synthetic awareness controls, detection coverage and response workflow."},
}
def now(): return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z")
def telem():
 c=sqlite3.connect(f"file:{TELEMETRY_DB}?mode=ro",uri=True); c.row_factory=sqlite3.Row; return c
def init():
 c=sqlite3.connect(ASSESSMENT_DB,check_same_thread=False); c.execute("PRAGMA journal_mode=WAL")
 c.execute("CREATE TABLE IF NOT EXISTS findings(finding_id TEXT PRIMARY KEY,assessment_id TEXT,template_id TEXT,campaign_id TEXT,correlation_id TEXT,severity TEXT,status TEXT,evidence_json TEXT,created_at TEXT)")
 c.execute("CREATE TABLE IF NOT EXISTS actions(action_id TEXT PRIMARY KEY,finding_id TEXT,action_type TEXT,description TEXT,status TEXT,evidence_json TEXT,created_at TEXT)")
 c.commit(); return c
def events(campaign):
 c=telem()
 try:
  rows=c.execute("SELECT id,campaign_id,user_id,event_type,timestamp,correlation_id FROM events WHERE campaign_id=? ORDER BY timestamp,id",(campaign,)).fetchall()
  return rows
 finally: c.close()
def derive(campaign=CAMPAIGN_ID):
 clicks={}; users={}
 for e in events(campaign):
  if e["event_type"]!="clicked": continue
  k=(e["campaign_id"],e["correlation_id"]); clicks.setdefault((k,e["user_id"]),[]).append(e); users.setdefault(k,set()).add(e["user_id"])
 out=[]
 for (k,u),rows in sorted(clicks.items()):
  if len(rows)>3:
   out.append({"template_id":"HHL-F001","campaign_id":k[0],"correlation_id":k[1],"severity":"MEDIUM","evidence":{"rule_id":"HHL-D001","user_id":u,"event_ids":[r["id"] for r in rows],"event_count":len(rows)}})
 for k,us in sorted(users.items()):
  if len(us)>=5:
   out.append({"template_id":"HHL-F002","campaign_id":k[0],"correlation_id":k[1],"severity":"MEDIUM","evidence":{"rule_id":"HHL-D002","users":sorted(us),"user_count":len(us)}})
 return out
def materialize(aid,campaign,db):
 created=[]
 for x in derive(campaign):
  with LOCK: exists=db.execute("SELECT finding_id FROM findings WHERE assessment_id=? AND template_id=? AND correlation_id=?",(aid,x["template_id"],x["correlation_id"])).fetchone()
  if exists: continue
  fid=f'{x["template_id"]}-{uuid.uuid4().hex[:8]}'
  with LOCK:
   db.execute("INSERT INTO findings VALUES(?,?,?,?,?,?,?,?,?)",(fid,aid,x["template_id"],x["campaign_id"],x["correlation_id"],x["severity"],"OPEN",json.dumps(x["evidence"],sort_keys=True),now())); db.commit()
  created.append(fid)
 return created
def risk(aid,db):
 with LOCK: rows=db.execute("SELECT finding_id,severity,status FROM findings WHERE assessment_id=?",(aid,)).fetchall()
 initial=sum(WEIGHTS.get(r[1],0) for r in rows)
 residual=0
 verified=set()
 with LOCK:
  rs=db.execute("SELECT DISTINCT finding_id FROM actions WHERE action_type='REMEDIATION' AND status='VERIFIED' AND finding_id IN (SELECT finding_id FROM findings WHERE assessment_id=?)",(aid,)).fetchall()
 verified={r[0] for r in rs}
 for fid,sev,status in rows:
  if fid not in verified and status!="CLOSED": residual+=WEIGHTS.get(sev,0)
 counts={}
 for _,sev,_ in rows: counts[sev]=counts.get(sev,0)+1
 return {"assessment_id":aid,"finding_counts":counts,"risk_points_initial":initial,"risk_points_residual":residual,"verified_remediations":len(verified),"method":"contextual training weight; not CVSS or a production security score"}
class Handler(BaseHTTPRequestHandler):
 def __init__(self,*a,db=None,**kw): self.db=db; super().__init__(*a,**kw)
 def out(self,s,p):
  b=json.dumps(p,separators=(",",":")).encode(); self.send_response(s); self.send_header("Content-Type","application/json"); self.send_header("Cache-Control","no-store"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
 def do_GET(self):
  p=urlparse(self.path); q=parse_qs(p.query)
  if p.path=="/health": return self.out(200,{"status":"ok","service":"hhl-assessment"})
  if p.path=="/templates": return self.out(200,TEMPLATES)
  if p.path in ("/assessments","/risk"):
   aid=q.get("id",[None])[0]
   if not aid: return self.out(400,{"error":"missing_id"})
   materialize(aid,CAMPAIGN_ID,self.db)
   if p.path=="/risk": return self.out(200,risk(aid,self.db))
   with LOCK: rows=self.db.execute("SELECT finding_id,template_id,campaign_id,correlation_id,severity,status,evidence_json,created_at FROM findings WHERE assessment_id=? ORDER BY created_at,finding_id",(aid,)).fetchall()
   fs=[{"finding_id":r[0],"template_id":r[1],"campaign_id":r[2],"correlation_id":r[3],"severity":r[4],"status":r[5],"evidence":json.loads(r[6]),"created_at":r[7]} for r in rows]
   return self.out(200,{"assessment_id":aid,"findings":fs,"risk":risk(aid,self.db)})
  return self.out(404,{"error":"not_found"})
 def do_POST(self):
  if self.path!="/actions": return self.out(404,{"error":"not_found"})
  try:
   n=min(int(self.headers.get("Content-Length","0")),16384); p=json.loads(self.rfile.read(n) or b"{}")
   fid=p["finding_id"]; typ=p["action_type"]; desc=p["description"]; status=p.get("status","PLANNED"); evidence=p.get("evidence",{})
   if typ not in {"REMEDIATION","RETEST"}: return self.out(400,{"error":"invalid_action_type"})
   if status not in {"PLANNED","IN_PROGRESS","VERIFIED","FAILED"}: return self.out(400,{"error":"invalid_status"})
   with LOCK:
    if not self.db.execute("SELECT 1 FROM findings WHERE finding_id=?",(fid,)).fetchone(): return self.out(404,{"error":"finding_not_found"})
    self.db.execute("INSERT INTO actions VALUES(?,?,?,?,?,?,?)",(f"ACT-{uuid.uuid4().hex[:10]}",fid,typ,desc,status,json.dumps(evidence,sort_keys=True),now()))
    if typ=="REMEDIATION" and status=="VERIFIED": self.db.execute("UPDATE findings SET status='REMEDIATED' WHERE finding_id=?",(fid,))
    self.db.commit()
   return self.out(201,{"status":"recorded","finding_id":fid})
  except (KeyError,ValueError,json.JSONDecodeError): return self.out(400,{"error":"invalid_payload"})
  except sqlite3.Error: return self.out(503,{"error":"assessment_storage_unavailable"})
 def log_message(self,*a): return
if __name__=="__main__":
 db=init()
 ThreadingHTTPServer((HOST,PORT),lambda *a,**kw:Handler(*a,db=db,**kw)).serve_forever()
