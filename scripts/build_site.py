"""Build static NIL Scoreboard site into dist/ from data/schools.json. No dependencies."""
import json, os, shutil, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, "data", "schools.json")))
OUT = os.path.join(ROOT, "dist")
SUB = "https://nilscoreboard.substack.com"; BSKY = "https://bsky.app/profile/nilscoreboard.bsky.social"
CONFS = ["ACC", "Big Ten", "Big 12", "SEC"]
e = html.escape

def money(v):
    if v is None: return '<span class="na">n/a</span>'
    return f"${v/1e6:,.1f}M"

def page(title, body, depth=0):
    p = "../" * depth
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} | NIL Scoreboard</title><link rel="stylesheet" href="{p}style.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script></head><body>
<header><a class="brand" href="{p}index.html">NIL Scoreboard</a><nav><a href="{p}index.html">Leaderboards</a><a href="{p}methodology/index.html">Methodology &amp; sources</a>
<a href="{SUB}">Newsletter</a><a href="{BSKY}">Bluesky</a></nav></header><main>{body}</main>
<footer>Data: U.S. Dept. of Education EADA (public domain). Every number links to its source. <a href="{p}methodology/index.html">How we count</a> ·
<a href="{SUB}">Subscribe on Substack</a> · <a href="{BSKY}">@nilscoreboard.bsky.social</a> · <a href="{p}data/schools.csv">Download CSV</a></footer></body></html>"""

def V(s, k): return s["metrics"][k]["value"]

def badge(m):
    c = m["confidence"]
    return f'<span class="badge">{e(c)}</span>' if c else '<span class="badge none">Unknown</span>'

def home():
    parts = ["<h1>Who spends what in college sports</h1><p class='lede'>FY2025 athletics revenue and expenses for every Power 4 school plus Notre Dame, from federal EADA filings. NIL and revenue-sharing figures per school are added only when a public record backs them.</p>"]
    for conf in CONFS + ["Independent"]:
        rows = [s for s in D["schools"] if s["conference"].startswith(conf)]
        rows.sort(key=lambda s: -(V(s, "eada_total_revenue") or 0))
        cid = conf.replace(" ", "")
        tr = "".join(f"<tr><td>{i+1}</td><td><a href='schools/{s['slug']}/index.html'>{e(s['name'])}</a></td><td>{s['control']}</td><td>{money(V(s,'eada_total_revenue'))}</td><td>{money(V(s,'eada_total_expenses'))}</td><td>{money(V(s,'eada_football_revenue'))}</td><td>{money(V(s,'eada_mbb_revenue'))}</td></tr>" for i, s in enumerate(rows))
        chart = "" if len(rows) < 2 else f"""<canvas id="c{cid}" height="110"></canvas><script>new Chart(document.getElementById('c{cid}'),{{type:'bar',data:{{labels:{json.dumps([s['name'] for s in rows])},datasets:[{{label:'Revenue ($M)',data:{json.dumps([round((V(s,'eada_total_revenue') or 0)/1e6,1) for s in rows])},backgroundColor:'#1f6feb'}},{{label:'Expenses ($M)',data:{json.dumps([round((V(s,'eada_total_expenses') or 0)/1e6,1) for s in rows])},backgroundColor:'#f0883e'}}]}},options:{{plugins:{{legend:{{position:'bottom'}}}}}}}});</script>"""
        parts.append(f"<section><h2>{e(conf)}</h2>{chart}<table><thead><tr><th>#</th><th>School</th><th>Type</th><th>Total revenue</th><th>Total expenses</th><th>Football rev.</th><th>Men's hoops rev.</th></tr></thead><tbody>{tr}</tbody></table><p class='src'>Source: EADA 2025 collection (FY2025, Jul 2024 to Jun 2025). Confidence: Official filing.</p></section>")
    return page("Power 4 money leaderboards", "".join(parts))

LABELS = [("eada_total_revenue","Total athletics revenue (EADA)"),("eada_total_expenses","Total athletics expenses (EADA)"),
          ("eada_football_revenue","Football revenue (EADA)"),("eada_football_expenses","Football expenses (EADA)"),
          ("eada_mbb_revenue","Men's basketball revenue (EADA)"),("eada_mbb_expenses","Men's basketball expenses (EADA)"),
          ("kn_total_revenue","Total revenue (Knight-Newhouse / NCAA MFRS)"),("kn_total_expenses","Total expenses (Knight-Newhouse / NCAA MFRS)"),
          ("kn_contributions","Donor contributions (Knight-Newhouse / NCAA MFRS)"),("mfrs_contributions","Donor contributions (MFRS via records request)"),
          ("revenue_share_budget_fy26","Athlete revenue-sharing budget, FY2026")]

def school(s):
    rows = ""
    for k, lab in LABELS:
        m = s["metrics"][k]
        src = f"<a href='{e(m['source_url'])}'>{e(m['source'] or 'source')}</a>" if m.get("source_url") else "Pending records request"
        rows += f"<tr><td>{lab}</td><td>{money(m['value'])}</td><td>{e(m['fiscal_year'] or '')}</td><td>{badge(m)}</td><td>{src}</td><td>{e(m['as_of'] or '')}</td></tr>"
    net = None
    if V(s,'eada_total_revenue') is not None and V(s,'eada_total_expenses') is not None:
        net = V(s,'eada_total_revenue') - V(s,'eada_total_expenses')
    note = "" if s["control"] == "Public" else "<p class='note'>Private school: not subject to state open-records laws, so only federal EADA totals are available.</p>"
    body = f"""<p><a href="../../index.html">&larr; Leaderboards</a></p><h1>{e(s['name'])}</h1><p class="lede">{e(s['conference'])} · {s['control']} · {e(s['state'])} · EADA ID {s['unitid']} ({e(s['eada_institution_name'] or '')})</p>{note}
<p>FY2025 EADA revenue minus expenses: <b>{money(net)}</b>. <small>(EADA reports must balance revenue and expenses for many schools, so this gap is not a profit measure.)</small></p>
<canvas id="c" height="90"></canvas><script>new Chart(document.getElementById('c'),{{type:'bar',data:{{labels:['Football','Men\\'s basketball','All athletics'],datasets:[{{label:'Revenue ($M)',data:{json.dumps([round((V(s,k) or 0)/1e6,1) for k in ('eada_football_revenue','eada_mbb_revenue','eada_total_revenue')])},backgroundColor:'#1f6feb'}},{{label:'Expenses ($M)',data:{json.dumps([round((V(s,k) or 0)/1e6,1) for k in ('eada_football_expenses','eada_mbb_expenses','eada_total_expenses')])},backgroundColor:'#f0883e'}}]}}}});</script>
<table><thead><tr><th>Metric</th><th>Value</th><th>FY</th><th>Confidence</th><th>Source</th><th>As of</th></tr></thead><tbody>{rows}</tbody></table>
<p class="src">Spot a missing or wrong number? Tell us via the <a href="{SUB}">newsletter</a>.</p>"""
    return page(s["name"], body, 2)

def methodology():
    body = f"""<h1>Methodology &amp; sources</h1>
<h2>Confidence labels</h2><ul><li><b>Audited</b>: from an NCAA financial report (MFRS) with an independent agreed-upon-procedures review, obtained from the school or a public record.</li>
<li><b>Official filing</b>: a school's own filing with a government agency, e.g. the federal EADA survey. Not audited by us.</li>
<li><b>Reported</b>: published by credible news outlets or school statements, with a link.</li><li><b>Estimate</b>: our calculation, always labeled, with the method shown.</li>
<li><b>Unknown</b>: no public number yet. We never fill gaps with guesses.</li></ul>
<h2>Sources</h2><ul><li><a href="https://ope.ed.gov/athletics/">Equity in Athletics Data Analysis (EADA)</a>, U.S. Department of Education. 2025 collection = academic year 2024-25 (FY2025). Public domain. Used for total athletics revenue/expenses (grand totals) and football and men's basketball revenue/expenses.</li>
<li><a href="https://www.knightnewhousedata.org/">Knight-Newhouse College Athletics Database</a>: standardized NCAA financial reports for public schools. Its data is copyright-protected and free for non-commercial use only, so we link to it rather than republish its numbers.</li>
<li>NCAA financial reports (MFRS) and revenue-sharing budgets obtained via state public-records requests (in progress for FY2025 and FY2026).</li>
<li><a href="https://www.collegesportscommission.org/">College Sports Commission</a>: national NIL Go and revenue-sharing totals only; no school-level figures.</li></ul>
<h2>Caveats</h2><ul><li>EADA and NCAA reports use different definitions; numbers will not match exactly.</li><li>EADA revenue often equals expenses by design when institutional support covers deficits.</li>
<li>Private schools (Boston College, Duke, Miami, SMU, Stanford, Syracuse, Wake Forest, Baylor, BYU, TCU, Northwestern, USC, Vanderbilt, Notre Dame) are not subject to state records laws.</li>
<li>Conference membership is for 2026-27 (unchanged from 2025-26 per <a href="https://www.espn.com/college-football/story/_/id/49498819/college-football-conference-changes-realignment-fbs">ESPN</a> and <a href="https://apnews.com/article/conference-realignment-f43c885f6532a7b929ef1146f6de962f">AP</a>). Notre Dame is a football independent.</li></ul>
<p>Data last generated {D['generated']}. <a href="../data/schools.csv">CSV</a> · <a href="../data/schools.json">JSON</a></p>"""
    return page("Methodology", body, 1)

CSS = """body{font-family:system-ui,sans-serif;margin:0;color:#1b1f24;background:#fafbfc}header{display:flex;gap:2rem;align-items:center;padding:1rem 2rem;background:#0d1117;color:#fff;flex-wrap:wrap}
header a{color:#fff;text-decoration:none;margin-right:1rem}.brand{font-weight:800;font-size:1.3rem}main{max-width:1100px;margin:auto;padding:1rem 2rem}
table{border-collapse:collapse;width:100%;margin:1rem 0;background:#fff}th,td{padding:.4rem .6rem;border-bottom:1px solid #e1e4e8;text-align:left;font-size:.92rem}th{background:#f3f4f6}
.lede{font-size:1.1rem;color:#444}.src,.note{font-size:.85rem;color:#57606a}.na{color:#999}.badge{background:#ddf4ff;color:#0969da;padding:.1rem .4rem;border-radius:4px;font-size:.8rem}.badge.none{background:#eee;color:#666}
section{margin:2rem 0}footer{padding:2rem;font-size:.85rem;color:#57606a;text-align:center}"""

def main():
    shutil.rmtree(OUT, ignore_errors=True); os.makedirs(os.path.join(OUT, "data"))
    open(os.path.join(OUT, "style.css"), "w").write(CSS)
    open(os.path.join(OUT, "index.html"), "w").write(home())
    open(os.path.join(OUT, ".nojekyll"), "w").write("")
    os.makedirs(os.path.join(OUT, "methodology")); open(os.path.join(OUT, "methodology", "index.html"), "w").write(methodology())
    for s in D["schools"]:
        p = os.path.join(OUT, "schools", s["slug"]); os.makedirs(p); open(os.path.join(p, "index.html"), "w").write(school(s))
    for f in ("schools.csv", "schools.json", "values_long.csv"): shutil.copy(os.path.join(ROOT, "data", f), os.path.join(OUT, "data", f))
    print("built", len(D["schools"]), "school pages")
if __name__ == "__main__": main()
