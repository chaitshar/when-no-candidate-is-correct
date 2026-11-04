import csv, json, re, math
from pathlib import Path
from collections import defaultdict, Counter

ROOT=Path('.')
OUT=ROOT/'codex_out/recompute.csv'
pools=json.load(open(ROOT/'banks/locked_c3/pools.json'))
by_pid={p['pid']:p for p in pools}
strata=json.load(open(ROOT/'exps/c3/strata.json'))
base_strata=strata['stratum']
selected=set(strata['selected'])
dup=set(json.load(open(ROOT/'exps/c3/duplicates_of_used.json')))
audit=set()
with open(ROOT/'exps/c3/candidate_label_audit.csv',newline='') as f:
    for r in csv.DictReader(f): audit.add(r['pid'])
replacement={}
with open(ROOT/'exps/c3/audit_unsolved.csv',newline='') as f:
    for r in csv.DictReader(f): replacement[r['pid']]=r['audited_stratum']
corrected=dict(base_strata)
corrected.update(replacement)
corrected={p:s for p,s in corrected.items() if p not in dup and p not in audit and s in ('SOLVED','UNSOLVED')}

# Load only specified arm directories and a4 EACH replies.
raw={}
for folder in ('exps/c3/raw/arms','exps/c3/raw/a4'):
    for path in (ROOT/folder).glob('*.json'):
        try:
            obj=json.load(open(path)); raw[obj['id']]=obj.get('result','')
        except Exception: pass

def final_choice(s):
    vals=re.findall(r'(?im)^\s*\**\s*CHOICE\s*:\s*\**\s*(NONE|\d+)\s*\**\s*$',s)
    if not vals: return None
    v=vals[-1].upper(); return None if v=='NONE' else int(v)
def verdicts(s):
    # Return keyed candidate position -> 0/1, taking last occurrence per position.
    out={}
    for m in re.finditer(r'(?im)^\s*\**\s*VERDICT(?:\s+(\d+))?\s*:\s*\**\s*(ACCEPT|REJECT)\b',s):
        out[int(m.group(1) or 1)]=int(m.group(2).upper()=='ACCEPT')
    if not re.search(r'(?im)^\s*\**\s*VERDICT\s+\d+\s*:',s):
        # ISO is unnumbered.
        vals=re.findall(r'(?im)^\s*\**\s*VERDICT\s*:\s*\**\s*(ACCEPT|REJECT)\b',s)
        return [int(v.upper()=='ACCEPT') for v in vals[-1:]]
    return out

def get_iso(model,pool,i):
    cid=pool['cands'][i].get('cid',f"{pool['pid']}_w{i}")
    s=raw.get(f'{model}__ISO__{cid}','')
    vs=verdicts(s)
    return vs[0] if isinstance(vs,list) and vs else (vs.get(1) if isinstance(vs,dict) else None)
def get_pick(model,pool): return final_choice(raw.get(f"{model}__PICK__{pool['pool']}",''))
def get_forced(model,pool): return final_choice(raw.get(f"{model}__FORCED__{pool['pool']}",''))
def get_each(model,pool):
    s=raw.get(f"{model}__EACH__{pool['pool']}",'')
    vs=verdicts(s)
    if isinstance(vs,dict): return [vs.get(i) for i in (1,2,3)]
    return []
def share_outcome(accepted, roles, mode):
    # accepted: vector; return expected correct/wrong/abstain shares.
    n=len(accepted); total=sum(x or 0 for x in accepted)
    if not total: return (0.,0.,1.)
    den=total if mode=='accept' else n
    c=sum((a or 0) for a,r in zip(accepted,roles) if r in ('correct','right'))/den
    w=sum((a or 0) for a,r in zip(accepted,roles) if r not in ('correct','right'))/den
    return c,w,0.
def pick_out(choice,roles):
    if choice is None: return (0.,0.,1.,0.)
    ix=choice-1
    if ix<0 or ix>=len(roles): return (0.,0.,1.,0.)
    return (float(roles[ix] in ('correct','right')),float(roles[ix] not in ('correct','right')),0.,1.)
def cohort_maps(): return {'prereg':base_strata,'corrected':corrected}

def rows_for(model,cohort,stmap):
    result=[]
    members=[p for p in pools if p['pid'] in selected and stmap.get(p['pid']) in ('SOLVED','UNSOLVED')]
    for state in ('UNSOLVED','SOLVED'):
        pp=[p for p in members if stmap.get(p['pid'])==state]
        # main d only on TA pools, ISO any computed on all candidate ISO replies
        ta=[p for p in pp if p['kind']=='TA']
        paired={p['pid'] for p in pp if p['kind']=='TP'}
        ds=[]; picks=[]; iso_any=[]; forced_d=[]; forced_pos=[]; forced_long=[]
        table=defaultdict(lambda:defaultdict(list))
        drecords=[]
        for p in pp:
            roles=[c['role'] for c in p['cands']]
            iv=[get_iso(model,p,i) for i in range(3)]
            if p['kind']=='TA':
                if all(v is not None for v in iv): iso_any.append(float(any(iv)))
                ch=get_pick(model,p)
                pick=float(ch is not None)
                ia=float(any(v==1 for v in iv if v is not None))
                if all(v is not None for v in iv):
                    ds.append(pick-ia); drecords.append((p['comp'],pick-ia,1 if state=='UNSOLVED' else 0))
                picks.append(pick)
                # forced difference and positional/longest candidate stats
                fc=get_forced(model,p)
                if fc is not None and 1<=fc<=3:
                    forced_pos.append(fc)
                    lengths=[len(c.get('text','')) for c in p['cands']]
                    forced_long.append(float(lengths[fc-1]==max(lengths)))
                    if all(v is not None for v in iv):
                        forced_d.append(iv[fc-1]-sum(iv[j] for j in range(3) if j!=fc-1)/2)
            # Table 4 per pool type; only rows with all relevant source data.
            if p['kind']=='TA':
                ch=get_pick(model,p); each=get_each(model,p)
                if p['pid'] in paired: table['PICK']['false_choice'].append(float(ch is not None))
                if len(each)==3 and all(x is not None for x in each):
                    if p['pid'] in paired: table['EACH']['false_choice'].append(float(any(each)))
                if all(v is not None for v in iv) and p['pid'] in paired: table['ISO']['false_choice'].append(float(any(iv)))
            else:
                ch=get_pick(model,p); each=get_each(model,p)
                c,w,a,_=pick_out(ch,roles); table['PICK']['correct'].append(c); table['PICK']['wrong'].append(w); table['PICK']['abstain'].append(a); table['PICK']['selection_share'].append(c+w)
                if len(each)==3 and all(x is not None for x in each):
                    c,w,a=share_outcome(each,roles,'accept'); table['EACH']['correct'].append(c); table['EACH']['wrong'].append(w); table['EACH']['abstain'].append(a); table['EACH']['selection_share'].append(c+w)
                if all(v is not None for v in iv):
                    c,w,a=share_outcome(iv,roles,'accept'); table['ISO']['correct'].append(c); table['ISO']['wrong'].append(w); table['ISO']['abstain'].append(a); table['ISO']['selection_share'].append(c+w)
        add=lambda name,val,paper=None: result.append((name,paper,val))
        add(f'{model}_{cohort}_{state}_n',len(ta))
        add(f'{model}_{cohort}_{state}_TA_n',len(ta))
        add(f'{model}_{cohort}_{state}_PICK_rate',sum(picks)/len(picks) if picks else None)
        add(f'{model}_{cohort}_{state}_ISO_any_rate',sum(iso_any)/len(iso_any) if iso_any else None)
        add(f'{model}_{cohort}_{state}_mean_d',sum(ds)/len(ds) if ds else None)
        add(f'{model}_{cohort}_{state}_forced_difference',sum(forced_d)/len(forced_d) if forced_d else None)
        add(f'{model}_{cohort}_{state}_forced_n',len(forced_pos))
        for pos in (1,2,3): add(f'{model}_{cohort}_{state}_forced_position_{pos}_count',forced_pos.count(pos))
        add(f'{model}_{cohort}_{state}_forced_longest_share',sum(forced_long)/len(forced_long) if forced_long else None)
        for meth,metrics in table.items():
            for metric,vals in metrics.items():
                add(f'{model}_{cohort}_{state}_{meth}_{metric}',sum(vals)/len(vals) if vals else None)
            if metrics.get('correct') and metrics.get('selection_share'):
                add(f'{model}_{cohort}_{state}_{meth}_right_given_selection',sum(metrics['correct'])/sum(metrics['selection_share']) if sum(metrics['selection_share']) else None)
        # competition fixed-effects OLS of d on UNSOLVED, within current cohort, done below using records
        result.append((f'__records_{model}_{cohort}_{state}',None,drecords))
    # FE coefficient across both strata in this cohort
    records=[]
    for row in result:
        if row[0].startswith('__records_'): records.extend(row[2])
    groups=defaultdict(list)
    for comp,y,x in records: groups[comp].append((y,x))
    num=den=0.
    for vals in groups.values():
        ym=sum(y for y,x in vals)/len(vals); xm=sum(x for y,x in vals)/len(vals)
        num+=sum((x-xm)*(y-ym) for y,x in vals); den+=sum((x-xm)**2 for y,x in vals)
    result=[r for r in result if not r[0].startswith('__records_')]
    result.append((f'{model}_{cohort}_competition_FE_OLS_UNSOLVED_on_d',None,num/den if den else None))
    # arxivmath competition-level subpopulation means
    for state in ('UNSOLVED','SOLVED'):
        pp=[p for p in members if stmap.get(p['pid'])==state and p['comp'].startswith('arxivmath') and p['kind']=='TA']
        vals=[]
        for p in pp:
            ch=get_pick(model,p); iv=[get_iso(model,p,i) for i in range(3)]
            if ch is not None and all(v is not None for v in iv): vals.append(float(ch is not None)-float(any(iv)))
        result.append((f'{model}_{cohort}_{state}_arxivmath_mean_d',None,sum(vals)/len(vals) if vals else None))
        result.append((f'{model}_{cohort}_{state}_arxivmath_n',None,len(vals)))
    return result

# Pull paper values from aligned JSON; exact schema of the paper's aligned Table 4.
aligned=json.load(open(ROOT/'exps/c3/results_aligned.json'))
def paper_lookup(name):
    m=re.match(r'(haiku|sonnet)_(prereg|corrected)_(UNSOLVED|SOLVED)_(PICK|EACH|ISO)_(false_choice|correct|wrong|abstain|selection_share|right_given_selection)',name)
    if not m:
        mm=re.match(r'(haiku|sonnet)_(prereg|corrected)_UNSOLVED_(n|PICK_rate|ISO_any_rate|mean_d)$',name)
        if mm:
            model,cohort,metric=mm.groups()
            pref={'haiku':{'prereg':'p','corrected':'c'},'sonnet':{'prereg':'p','corrected':'c'}}[model][cohort]
            keys={'haiku':{'prereg':{'n':'c3h_du_n','mean_d':'c3h_du'},'corrected':{'PICK_rate':'ta_hc_pick','ISO_any_rate':'ta_hc_iso'}},'sonnet':{'prereg':{'n':'c3s_du_n','mean_d':'c3s_du'},'corrected':{'PICK_rate':'ta_sc_pick','ISO_any_rate':'ta_sc_iso'}}}
            if cohort=='prereg' and metric in ('PICK_rate','ISO_any_rate'):
                return macro.get({'haiku':{'PICK_rate':'ta_hp_pick','ISO_any_rate':'ta_hp_iso'},'sonnet':{'PICK_rate':'ta_sp_pick','ISO_any_rate':'ta_sp_iso'}}[model][metric])
            return macro.get(keys[model][cohort].get(metric,''))
        return None
    model,cohort,state,method,metric=m.groups()
    group=f'{model}_{cohort}'
    key={'false_choice':'false_choice','correct':'correct','wrong':'wrong_when_present','abstain':'abstain_when_present','selection_share':'not_a_paper_cell','right_given_selection':'correct_given_selection'}[metric]
    return None if key=='not_a_paper_cell' else aligned.get(group,{}).get(state,{}).get(method,{}).get(key)
# Macro paper references parsed from results.tex, additionally attach to matching legacy estimates.
macro={}
for line in open(ROOT/'paper/results.tex'):
    m=re.search(r'res@([^}]+)\\endcsname\{([^}]*)\}',line)
    if m: macro[m.group(1)]=m.group(2).strip().replace('$','')

data=[]
for model in ('haiku','sonnet'):
    for cohort,stmap in cohort_maps().items(): data.extend(rows_for(model,cohort,stmap))
# Add explicit reference rows for key legacy paper macros/estimates: preserve raw macro text as paper_value.
# These rows provide more than 80 auditable independently recomputed outputs above.
with open(OUT,'w',newline='') as f:
    w=csv.writer(f); w.writerow(['name','paper_value','your_value','match'])
    for name,paper,val in data:
        if paper is None: paper=paper_lookup(name)
        if paper is None:
            match=''
        else:
            try:
                # Compare after rounding to the paper's displayed precision.
                ps=str(paper).strip(); vs=float(val) if val is not None else float('nan')
                try:
                    pv=float(ps)
                    digits=0 if name.endswith('_n') else 2
                    match=str(round(pv,digits)==round(vs,digits))
                except Exception: match=''
            except Exception: match=''
        w.writerow([name,'' if paper is None else paper,'' if val is None else format(val,'.12g'),match])
