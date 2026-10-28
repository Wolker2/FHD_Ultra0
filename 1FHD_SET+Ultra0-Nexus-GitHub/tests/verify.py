#!/usr/bin/env python3
"""Verify isolated rebuild, serialization, references and preserved release facts."""
from pathlib import Path
import copy,json,platform,re,shutil,subprocess,sys,tempfile,zlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from build import build,hashes,load
from dat_codec import decode as dat_decode,encode as dat_encode
from gi_codec import decode as gi_decode,encode as gi_encode

def walk(block,prefix=''):
    for entry in block['entries']:
        name=prefix+entry['name'];yield name,entry
        if entry['kind']=='block':yield from walk(entry['value'],name+'.')

def verify():
    checks=[]
    def check(condition,label):
        assert condition,label;checks.append(label)
    with tempfile.TemporaryDirectory() as tmp:
        clean=Path(tmp)
        for name in ['source','scripts']:shutil.copytree(ROOT/name,clean/name,ignore=shutil.ignore_patterns('__pycache__'))
        files=build(clean)
    expected=load(ROOT/'original-file-sha256.json')
    check(hashes(files)==expected,'Isolated source-only build reproduces all original runtime SHA-256 hashes')
    check(len(files)==8,'Exactly eight runtime files')
    check(sum(n.endswith('.dat') for n in files)==5,'Five DATs rebuilt')
    check(not any(n.endswith(('.dll','.scr')) for n in files),'No DLL or SCR in the supplied runtime set')
    indices={};texts=[];all_paths=set();configs={}
    for name,data in sorted(files.items()):
        if not name.endswith('.dat'):continue
        fmt='cachedata' if name.endswith('CacheData.dat') else 'blockpar'
        tree=dat_decode(data,fmt);configs[name]=tree
        check(dat_encode(tree)==data,'DAT decode/encode: '+name)
        entries=list(walk(tree['root']));index=dict(entries);indices[name]=index;all_paths.update(index)
        texts.extend((name,path,e['value']) for path,e in entries if e['kind']=='parameter')
    static_refs=set();dynamic_calls=0
    for name,path,text in texts:
        static_refs.update(re.findall(r"(?:CT|GenerateCodeStringFromBlock)\('([^']*)'\)",text))
        dynamic_calls+=len(re.findall(r"(?:CT|GenerateCodeStringFromBlock)\('([^']*)'\s*\+",text))
    missing=sorted(static_refs-all_paths)
    check(not missing,'All '+str(len(static_refs))+' complete literal CT/code-block references resolve in supplied configs')
    cache=[]
    for name,path,text in texts:
        if text.startswith('Mods\\FHD_MODS\\'):
            target=text.replace('\\','/').removeprefix('Mods/FHD_MODS/')
            # CacheData also records the module directory, rather than a file.
            present=target in files or any(n.startswith(target.rstrip('/')+'/') for n in files)
            check(present,'Local runtime path resolves: '+target);cache.append({'field':path,'target':target,'directory':target not in files})
    resource='FHD_SET/DATA/ItemsUseless/FHDSET_SearchTool.gi';graphic=gi_decode(files[resource])
    check(gi_encode(graphic)==files[resource],'GI type-2 full roundtrip')
    check(graphic['type']==2 and graphic['bounds']==[0,0,31,31] and len(graphic['layers'])==3,'31x31 GI with all three planes retained')
    changed=copy.deepcopy(graphic)
    plane=next(l for l in changed['layers'] if l['pixel_format']=='rgb565' and any('pixels' in c for c in l['commands']))
    packet=next(c for c in plane['commands'] if 'pixels' in c);packet['pixels'][0]^=31
    edited=gi_encode(changed)
    check(edited!=files[resource] and gi_decode(edited)==changed,'Editable GI pixel source changes the encoded resource losslessly')
    lang=configs['FHD_Ultra0/CFG/Rus/Lang.dat'];edited_tree=copy.deepcopy(lang)
    ammo=dict(walk(edited_tree['root']))['Script.FHDULTRA.ApplyAmmo.003'];old=ammo['value']
    check('(base*55)/100' in old,'Uploaded Ultra ammo code uses 55% capacity (45% reduction)')
    ammo['value']=old.replace('(base*55)/100','(base*54)/100')
    modified=dat_encode(edited_tree)
    check(modified!=files['FHD_Ultra0/CFG/Rus/Lang.dat'] and dat_decode(modified,'blockpar')==edited_tree,'DAT script edits compile and decode without altering other source fields')
    for module,priority in [('FHD_SET',1),('FHD_Ultra0',2)]:
        text=files[module+'/ModuleInfo.txt'].decode('cp1251')
        check('Name='+module+'\r\n' in text and 'Priority='+str(priority)+'\r\n' in text,'CP1251 metadata and module priority retained: '+module)
        check('Languages=Eng' in text and not any(n.startswith(module+'/CFG/Eng/') for n in files),'Original English metadata/absent English DAT retained: '+module)
    # These are observed original inconsistencies, not fixes or gameplay claims.
    observations=[
        {'id':'version-label','fact':'CacheData FHDSETV1.Version is 2.3.0-v25-canonical; supplied Ultra notes require FHD_SET v2.4.14+. Exact FHD_SET release cannot be established from these labels alone.'},
        {'id':'ammo-description','fact':'Ultra ModuleInfo says -40% ammo. Runtime ApplyAmmo uses (base*55)/100 and ExText/notes say -45%. Original runtime and metadata are unchanged.'},
        {'id':'undeclared-ultra-dependency','fact':'Ultra notes require FHD_SET, and Ultra scripts call FHD_SET blocks. ModuleInfo has no Dependence key; both supplied modules are built together.'},
        {'id':'language-files','fact':'Both ModuleInfo files advertise Eng, but the upload contains CFG/Rus/Lang.dat only. No English DAT was invented.'}]
    return {'status':'passed','checks_passed':len(checks),'checks':checks,'runtime_sha256':hashes(files),
        'literal_reference_count':len(static_refs),'missing_literal_references':missing,'dynamic_reference_calls_not_resolved':dynamic_calls,
        'local_paths':cache,'observations':observations,'live_game_executed':False,
        'test_scope':'Source-only reconstruction, byte identity, DAT/GI edit roundtrips and static configuration reference checks; no game interpreter, loader or gameplay execution',
        'environment':{'python':platform.python_version(),'zlib':zlib.ZLIB_RUNTIME_VERSION}}

if __name__=='__main__':
    report=verify()
    if len(sys.argv)>1:
        target=Path(sys.argv[1]);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','checks_passed','literal_reference_count','missing_literal_references']},indent=2))
