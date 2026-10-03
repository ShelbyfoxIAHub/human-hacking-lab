from __future__ import annotations
import hashlib,json,os,sqlite3,threading
from datetime import datetime,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import parse_qs,urlparse

ASSESSMENT_DB=os.getenv("ASSESSMENT_DB_PATH","/assessment/hhl-assessment.db")
REPORT_DB=os.getenv("REPORT_DB_PATH","/reporting/hhl-reporting.db")
VERIFY_DB=os.getenv("VERIFY_DB_PATH","/data/hhl-verification.db")
PORT=int(os.getenv("PORT","8095")); HOST="0.0.0.0"; LOCK=threading.Lock()
CHECKS={
 "HHL-V001":{"name":"Assessment evidence integrity","description":"Assessment findings must contain a source rule, campaign, correlation and non-empty evidence.","severity":"HIGH"},
 "HHL-V002":{"name":"Remediation/retest linkage","description":"Every remediation or retest action must reference an existing finding and carry evidence.","severity":"MEDIUM"},
 "HHL-V003":{"name":"Reporting audit integrity","description":"Reporting audit records must be append-only and tied to a generated report.","severity":"HIGH"},
 "HHL-V004":{"name":"Regression gate","description":"A verification run must have zero failed control checks.","severity":"HIGH"},
}
def now(): return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z")
def ro(path):
 c=sqlite3.connect(f"file:{path}?mode=ro",uri=True); c.row_factory=sqlite3.Row; return c
def init():
 c=sqlite3.connect(VERIFY_DB,check_same_thread=False)
 c.execute("PRAGMA journal_mode=WAL")
 c.execute("CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY,assessment_id TEXT,created_at TEXT,content_hash TEXT,status TEXT)")
 c.execute("CREATE TABLE IF NOT EXISTS checks(check_id INTEGER PRIMARY KEY AUTOINCREMENT,run_id TEXT,control_id TEXT,status TEXT,evidence_json TEXT,created_at TEXT)")
 c.execute("CREATE TABLE IF NOT EXISTS evidence(evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,run_id TEXT,source TEXT,content_hash TEXT,created_at TEXT)")
 c.commit(); return c
def verify(aid):
 results=[]
 ac=ro(ASSESSMENT_DB)
 try:
  fs=ac.execute("SELECT finding_id,template_id,campaign_id,correlation_id,severity,status,evidence_json FROM findings WHERE assessment_id=?",(aid,)).fetchall()
  ids={r["finding_id"] for r in fs}
  acts=ac.execute("SELECT action_id,finding_id,action_type,status,evidence_json FROM actions WHERE finding_id IN (SELECT finding_id FROM findings WHERE assessment_id=?)",(aid,)).fetchall()
 finally: ac.close()
 bad=[r["finding_id"] for r in fs if not r["template_id"] or not r["campaign_id"] or not r["correlation_id"] or not json.loads(r["evidence_json"])]
 results.append({"control_id":"HHL-V001","status":"PASS" if not bad else "FAIL","evidence":{"finding_ids":bad,"finding_count":len(fs)}})
 bad_actions=[r["action_id"] for r in acts if r["finding_id"] not in ids or not json.loads(r["evidence_json"])]
 results.append({"control_id":"HHL-V002","status":"PASS" if not bad_actions else "FAIL","evidence":{"action_ids":bad_actions,"action_count":len(acts)}})
 try:
  rc=ro(REPORT_DB)
  rows=rc.execute("SELECT report_id,assessment_id,report_json FROM reports WHERE assessment_id=?",(aid,)).fetchall()
  audit=rc.execute("SELECT audit_id,report_id,event_type FROM audit WHERE report_id IN (SELECT report_id FROM reports WHERE assessment_id=?)",(aid,)).fetchall()
  missing=[r["report_id"] for r in rows if not any(a["report_id"]==r["report_id"] and a["event_type"]=="REPORT_GENERATED" for a in audit)]
  results.append({"control_id":"HHL-V003","status":"PASS" if not missing else "FAIL","evidence":{"report_ids":[r["report_id"] for r in rows],"missing_audit_report_ids":missing,"audit_count":len(audit)}})
  for r in rows:
   payload=r["report_json"].encode(); results.append({"control_id":"HHL-V003","status":"PASS","evidence":{"report_id":r["report_id"],"report_hash":hashlib.sha256(payload).hexdigest()}})
  rc.close()
 except (sqlite3.Error,FileNotFoundError) as e:
  results.append({"control_id":"HHL-V003","status":"FAIL","evidence":{"error":str(e)}})
 failed=[x for x in results if x["status"]=="FAIL"]
 results.append({"control_id":"HHL-V004","status":"PASS" if not failed else "FAIL","evidence":{"failed_control_ids":[x["control_id"] for x in failed]}})
 status="PASS" if not failed else "FAIL"
 return status,results
class Handler(BaseHTTPRequestHandler):
 def __init__(self,*a,db=None,**kw): self.db=db; super().__init__(*a,**kw)
 def out(self,s,p):
  b=json.dumps(p,separators=(",",":")).encode(); self.send_response(s); self.send_header("Content-Type","application/json"); self.send_header("Cache-Control","no-store"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
 def do_GET(self):
  p=urlparse(self.path); q=parse_qs(p.query); aid=q.get("id",[None])[0]
  if p.path=="/health": return self.out(200,{"status":"ok","service":"hhl-verification"})
  if p.path=="/controls": return self.out(200,CHECKS)
  if p.path=="/verify":
   if not aid:return self.out(400,{"error":"missing_id"})
   status,checks=verify(aid)
   canonical=json.dumps({"assessment_id":aid,"status":status,"checks":checks},sort_keys=True,separators=(",",":"))
   rid="VRF-"+hashlib.sha256(canonical.encode()).hexdigest()[:16]
   with LOCK:
    self.db.execute("INSERT OR REPLACE INTO runs VALUES(?,?,?,?,?)",(rid,aid,now(),hashlib.sha256(canonical.encode()).hexdigest(),status))
    self.db.executemany("INSERT INTO checks(run_id,control_id,status,evidence_json,created_at) VALUES(?,?,?,?,?)",[(rid,x["control_id"],x["status"],json.dumps(x["evidence"],sort_keys=True),now()) for x in checks]); self.db.commit()
   return self.out(200,{"run_id":rid,"assessment_id":aid,"status":status,"checks":checks})
  if p.path.startswith("/runs/"):
   rid=p.path.rsplit("/",1)[-1]
   with LOCK:
    row=self.db.execute("SELECT run_id,assessment_id,created_at,content_hash,status FROM runs WHERE run_id=?",(rid,)).fetchone()
    rows=self.db.execute("SELECT control_id,status,evidence_json,created_at FROM checks WHERE run_id=? ORDER BY check_id",(rid,)).fetchall()
   if not row:return self.out(404,{"error":"run_not_found"})
   return self.out(200,{"run_id":row[0],"assessment_id":row[1],"created_at":row[2],"content_hash":row[3],"status":row[4],"checks":[{"control_id":x[0],"status":x[1],"evidence":json.loads(x[2]),"created_at":x[3]} for x in rows]})
  return self.out(404,{"error":"not_found"})
 def log_message(self,*a):return
if __name__=="__main__":
 db=init(); ThreadingHTTPServer((HOST,PORT),lambda *a,**kw:Handler(*a,db=db,**kw)).serve_forever()
