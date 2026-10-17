"""Lint narrative dependencies and branch returns, not visible teaching quality."""
import argparse
import json
from pathlib import Path

def inspect(document):
    errors=[]
    def need(condition,where,message):
        if not condition:errors.append({'state':where,'message':message})
    objects=document.get('objects',{});results=document.get('results',{})
    universe=set(objects)|set(results);known=set(document.get('initialKnown',[]))
    need(known<=universe,'lesson','Initial knowledge contains undefined objects/results')
    states=document.get('states',[]);branches=document.get('branches',[])
    need(bool(states),'lesson','No chronological states')
    ids=[s.get('id') for s in states]
    need(all(isinstance(x,str) and x for x in ids) and len(ids)==len(set(ids)),'lesson','State IDs must be unique nonempty strings')
    branchids=[b.get('id') for b in branches]
    need(all(isinstance(x,str) and x for x in branchids) and len(branchids)==len(set(branchids)),'lesson','Branch IDs must be unique nonempty strings')
    lookup={b['id']:b for b in branches if b.get('id')}
    for rid,result in results.items():
        need(bool(result.get('statement')),rid,'Result needs a statement')
        need(isinstance(result.get('conditions'),list),rid,'Result needs explicit conditions (empty list is allowed)')
        need(result.get('scope') in ['general','example'],rid,'Distinguish general result from example')
    seen={};stack=[];returned={};closed={};entered=set();used=[]
    for position,state in enumerate(states):
        sid=state.get('id');kind=state.get('kind');bid=state.get('branch')
        for field in ['purpose','why','activeObject','scene','context']:
            need(bool(state.get(field)),sid,'Missing '+field)
        need(kind in ['overview','main','focus','derive','return'],sid,'Unknown state kind')
        need(state.get('activeObject') in objects,sid,'Active object is undefined')
        requirements=set(state.get('requires',[]));outputs=set(state.get('produces',[]));carries=set(state.get('carries',[]))
        need(requirements<=known,sid,'Uses not-yet-established knowledge: '+', '.join(sorted(requirements-known)))
        required_visible={rid for rid in requirements if rid in results and results[rid].get('keepVisibleDuringUse',False)}
        need(required_visible<=carries,sid,'A key rule marked keepVisibleDuringUse is absent from this operation: '+', '.join(sorted(required_visible-carries)))
        need(outputs<=universe,sid,'Produces undefined objects/results')
        need(not(outputs&known),sid,'Redefines established knowledge; use requires for a proof of a supplied result')
        visible=set(state.get('objects',[]))
        need(visible<=set(objects),sid,'Visible object IDs are undefined')
        if 'objects' in state:need(state.get('activeObject') in visible,sid,'Active object is absent from the declared visible objects')
        if kind=='focus':
            branch=lookup.get(bid)
            need(branch is not None,sid,'Focus has no declared branch')
            if branch:
                origin=seen.get(branch.get('originState'))
                need(origin is not None,sid,'Branch origin has not been shown')
                need(bid not in entered,sid,'Branch opened more than once')
                if origin:
                    need(branch.get('focusObject') in origin.get('objects',[]),sid,'Focus object was absent from the originating process')
                    need(origin.get('scene')==state.get('scene') and origin.get('context')==state.get('context'),sid,'Focus is not a view of the same originating scene/context')
                need(state.get('activeObject')==branch.get('focusObject'),sid,'Focus active object differs from the declared originating object')
                need(branch.get('result') in results,sid,'Branch result is undefined')
                need(branch.get('returnState') in ids,sid,'Branch has no declared return state')
                stack.append(bid);entered.add(bid)
        elif kind=='return':
            need(bool(stack) and stack[-1]==bid,sid,'Return does not close the active branch')
            branch=lookup.get(bid,{})
            origin=seen.get(branch.get('originState'),{})
            need(sid==branch.get('returnState'),sid,'Not the declared return state')
            need(origin.get('scene')==state.get('scene') and origin.get('context')==state.get('context'),sid,'Return changes the originating scene/context')
            result=branch.get('result')
            need(result in known and result in carries,sid,'Returned overview does not retain the established branch result')
            need(set(origin.get('objects',[]))<=visible,sid,'Return loses originating process objects')
            if stack and stack[-1]==bid:stack.pop()
            if bid in closed:need(False,sid,'Branch returned more than once')
            closed[bid]=position
        elif bid:
            need(bool(stack) and stack[-1]==bid,sid,'Detail is outside its active branch')
        elif stack:
            need(False,sid,'Mainline advanced before returning from the active branch')
        known.update(outputs)
        need(carries<=known and carries<=set(results),sid,'Carries an unestablished or undefined result')
        if kind in ['overview','return']:
            context=(state.get('context'),stack[-1] if stack else None)
            need(returned.get(context,set())<=carries,sid,'Previously returned conclusions disappear from this context')
            returned[context]=returned.get(context,set())|carries
        used.extend((value,position) for value in requirements)
        seen[sid]=state
    need(not stack,'lesson','Unclosed branches: '+', '.join(stack))
    for bid,branch in lookup.items():
        need(bid in entered and bid in closed,bid,'Branch is orphaned or never returned')
        result=branch.get('result');end=closed.get(bid,len(states))
        need(any(value==result and position>end for value,position in used),bid,'Returned result is never used by a subsequent operation')
    return {'passed':not errors,'states':len(states),'branches':len(branches),'findings':errors,
            'claimBoundary':'Planning graph only. Does not certify visible continuity, mathematics, animation or native playback.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('map',type=Path);parser.add_argument('--report',type=Path)
    args=parser.parse_args();report=inspect(json.loads(args.map.read_text(encoding='utf-8')))
    if args.report:
        with args.report.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2)
    print(json.dumps(report,indent=2));return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
