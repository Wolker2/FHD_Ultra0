from __future__ import annotations
from pathlib import Path
import shutil, zipfile, hashlib, json, sys, re

BASE_OUT=Path('/mnt/data/ultra1021_out')
WORK=Path('/mnt/data/ultra1022_build')
OUT=Path('/mnt/data/ultra1022_out')
BASES={
 'normal': BASE_OUT/'FHD_Ultra0_v1.0.21_NormalSpawnFix_Alpha_Normal.zip',
 'test': BASE_OUT/'FHD_Ultra0_v1.0.21_NormalSpawnFix_Alpha_Test.zip',
}
CODEC=Path('/mnt/data/ultra1022_work/SOURCE/blockpar_codec.py')
if WORK.exists(): shutil.rmtree(WORK)
if OUT.exists(): shutil.rmtree(OUT)
WORK.mkdir(parents=True); OUT.mkdir(parents=True)
shutil.copy2(CODEC,WORK/'blockpar_codec.py')
sys.path.insert(0,str(WORK))
from blockpar_codec import decode_dat,encode_dat,flatten,from_flat

def sha256(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def zip_tree(root:Path,out:Path):
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(root.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(root))

def decl_names(code:str):
    return re.findall(r'\b(?:int|dword|float|string|str|bool)\s+([A-Za-z_][A-Za-z0-9_]*)',code)
def check_unique(code:str):
    names=decl_names(code); dup=sorted({n for n in names if names.count(n)>1})
    if dup: raise RuntimeError(f'duplicate declarations: {dup}')

report={
 'version':'1.0.22',
 'base':'1.0.21 Normal Spawn Fix Alpha',
 'change':'End-of-day performance fix: remove duplicate forced FHD_SET recalculation; clear ULTRA copies before the one normal SET tick and reapply after; remove global storage search from Spawn hot path; throttle missing tracked-shop rescans.',
 'variants':{},
 'performance_regression':{}
}

for variant,label in [('normal','Normal'),('test','Test')]:
    extract=WORK/f'base_{variant}'; extract.mkdir()
    with zipfile.ZipFile(BASES[variant]) as z: z.extractall(extract)
    mod=extract/'FHD_Ultra0'; lang=mod/'CFG'/'Rus'/'Lang.dat'
    block,seed=decode_dat(lang); before=list(flatten(block)); after=[]; changes=[]
    for p,v in before:
        nv=v
        if p=='Script/FHDULTRA/Tick/001':
            old="ExecuteCodeFromString(GenerateCodeStringFromBlock('Script.FHDULTRA.Spawn'));ExecuteCodeFromString(GenerateCodeStringFromBlock('Script.FHDULTRA.ClearCopies'));ExecuteCodeFromString(GenerateCodeStringFromBlock('Script.FHDULTRA.SyncSetBase'));ExecuteCodeFromString(GenerateCodeStringFromBlock('Script.FHDULTRA.EnforceSlots'));"
            new="ExecuteCodeFromString(GenerateCodeStringFromBlock('Script.FHDULTRA.Spawn'));ExecuteCodeFromString(GenerateCodeStringFromBlock('Script.FHDULTRA.EnforceSlots'));"
            if old not in nv: raise RuntimeError(f'{variant}: Tick hot path pattern not found')
            nv=nv.replace(old,new)
        elif p=='Script/FHDULTRA/SyncSetBase/001':
            old="ExecuteCodeFromString(GenerateCodeStringFromBlock('Script.FHDSETv1.Tick'),'force',1);"
            new="ExecuteCodeFromString(GenerateCodeStringFromBlock('Script.FHDSETv1.Tick'),'force',0);"
            if old not in nv: raise RuntimeError(f'{variant}: SyncSetBase force pattern not found')
            nv=nv.replace(old,new)
        elif p=='ShipInfo/AddInfo/CustomInfos/FHDSETV1_Runtime/OnActCode/001':
            start="if(ScriptItemActionType(t_OnStep,0)){if(ShipFindCustomShipInfoByType(Player(),'FHDULTRA_Resonance')>=0){for(int cmin_q=1;cmin_q<=3;cmin_q=cmin_q+1){str cmin_ui='FHDULTRA_Min1';if(cmin_q==2)cmin_ui='FHDULTRA_Min2';else if(cmin_q==3)cmin_ui='FHDULTRA_Min3';dword cmin_oldid=ShipCustomShipInfoData(Player(),cmin_ui,1);int cmin_oldinc=ShipCustomShipInfoData(Player(),cmin_ui,3);dword cmin_olditem=0;if(cmin_oldid)cmin_olditem=IdToItem(cmin_oldid);if(cmin_olditem && cmin_oldinc>0){int cmin_cur=round(GetEquipmentStats(cmin_olditem,1));int cmin_clean=cmin_cur-cmin_oldinc;if(cmin_clean<0)cmin_clean=0;SetEquipmentStats(cmin_olditem,cmin_clean,1);}ShipCustomShipInfoData(Player(),cmin_ui,1,0);ShipCustomShipInfoData(Player(),cmin_ui,2,0);ShipCustomShipInfoData(Player(),cmin_ui,3,0);}}"
            repl="if(ScriptItemActionType(t_OnStep,0)){if(ShipFindCustomShipInfoByType(Player(),'FHDULTRA_Resonance')>=0)ExecuteCodeFromString(GenerateCodeStringFromBlock('Script.FHDULTRA.ClearCopies'));"
            if start not in nv: raise RuntimeError(f'{variant}: runtime pre-clear pattern not found')
            nv=nv.replace(start,repl,1)
        elif p=='ShipInfo/AddInfo/CustomInfos/FHDSETV1_Runtime/OnActCode/900':
            old="if(ScriptItemActionType(t_OnStep,0))ExecuteCodeFromString(GenerateCodeStringFromBlock('Script.FHDULTRA.BattleWear'));else if("
            new="if(ScriptItemActionType(t_OnStep,0)){ExecuteCodeFromString(GenerateCodeStringFromBlock('Script.FHDULTRA.BattleWear'));ExecuteCodeFromString(GenerateCodeStringFromBlock('Script.FHDULTRA.ApplyCopies'));}else if("
            if old not in nv: raise RuntimeError(f'{variant}: runtime post-apply pattern not found')
            nv=nv.replace(old,new,1)
        elif p=='Script/FHDULTRA/Spawn/003':
            old="if(GalaxyTechLevel()<3)exit;if(bought>0)exit;if(old){if(FindItemInShip(Player(),old)>=0 || ShipEqInSlot(Player(),t_Hull)==old || FindItemInStorage(old)>=0)ShipCustomShipInfoData(Player(),'FHDULTRA_State',3,1);exit;}dword h=ExecuteCodeFromString(GenerateCodeStringFromBlock('Script.FHDULTRA.CreateHull'),'result');if(!h)exit;"
            new="if(GalaxyTechLevel()<3)exit;if(bought>0)exit;if(old){if(FindItemInShip(Player(),old)>=0 || ShipEqInSlot(Player(),t_Hull)==old)ShipCustomShipInfoData(Player(),'FHDULTRA_State',3,1);exit;}int lastscan=ShipCustomShipInfoData(Player(),'FHDULTRA_Price',2);if(iid!=0 && lastscan>0 && CurTurn()-lastscan<30)exit;ShipCustomShipInfoData(Player(),'FHDULTRA_Price',2,CurTurn());dword h=ExecuteCodeFromString(GenerateCodeStringFromBlock('Script.FHDULTRA.CreateHull'),'result');if(!h)exit;"
            if old not in nv: raise RuntimeError(f'{variant}: Spawn/003 pattern not found')
            nv=nv.replace(old,new,1)
        if nv!=v: changes.append(p)
        after.append((p,nv))

    expected=[
      'Script/FHDULTRA/Spawn/003',
      'Script/FHDULTRA/SyncSetBase/001',
      'Script/FHDULTRA/Tick/001',
      'ShipInfo/AddInfo/CustomInfos/FHDSETV1_Runtime/OnActCode/001',
      'ShipInfo/AddInfo/CustomInfos/FHDSETV1_Runtime/OnActCode/900',
    ]
    if sorted(changes)!=sorted(expected): raise RuntimeError(f'{variant}: unexpected changed paths {changes}')
    vals={p:v for p,v in after}
    tick=vals['Script/FHDULTRA/Tick/001']
    assert "Script.FHDULTRA.ClearCopies" not in tick
    assert "Script.FHDULTRA.SyncSetBase" not in tick
    rt1=vals['ShipInfo/AddInfo/CustomInfos/FHDSETV1_Runtime/OnActCode/001']
    rt900=vals['ShipInfo/AddInfo/CustomInfos/FHDSETV1_Runtime/OnActCode/900']
    assert "Script.FHDULTRA.ClearCopies" in rt1
    assert "Script.FHDULTRA.ApplyCopies" in rt900
    assert "Script.FHDULTRA.ClearMinCopiesFast" not in rt1
    sync=vals['Script/FHDULTRA/SyncSetBase/001']
    assert "'force',0" in sync and "'force',1" not in sync
    spawn3=vals['Script/FHDULTRA/Spawn/003']
    assert 'FindItemInStorage' not in spawn3
    assert "CurTurn()-lastscan<30" in spawn3
    assert "FHDULTRA_Price',2,CurTurn()" in spawn3
    spawn4=vals['Script/FHDULTRA/Spawn/004']
    assert 'GetGalaxyGenerationSeed' not in spawn4 and 'Rnd(0,n-1)' in spawn4
    apply=''.join(vals[p] for p in ['Script/FHDULTRA/ApplyAmmo/001','Script/FHDULTRA/ApplyAmmo/002','Script/FHDULTRA/ApplyAmmo/003'])
    assert '(base*55)/100' in apply
    shot=vals['Script/FHDULTRA/ShotWear/001']
    assert 'missileNewDur=missileDur-3' in shot and 'WeaponAmmunition(w,' not in shot
    check_unique(vals['Script/FHDULTRA/Spawn/001']+vals['Script/FHDULTRA/Spawn/002']+spawn3+spawn4)
    encode_dat(from_flat(after,sorted=True),lang,seed=seed)
    verify,vseed=decode_dat(lang); flat2=list(flatten(verify))
    if vseed!=seed or sorted(flat2)!=sorted(after): raise RuntimeError(f'{variant}: roundtrip mismatch')

    mi=mod/'ModuleInfo.txt'; txt=mi.read_bytes().decode('cp1251')
    txt=txt.replace('ver.1.0.21 Normal Spawn Fix Alpha','ver.1.0.22 End-Day Performance Fix Alpha')
    append='FullDescription=Правка v1.0.22: устранено ежедневное двойное полное пересчитывание FHD_SET. Копии УЛЬТРА временно снимаются перед штатным Tick SET и возвращаются после него. Убран глобальный FindItemInStorage из горячего Spawn-пути; повторный поиск потерянного магазинного объекта ограничен одним разом в 30 ходов. Баланс v1.0.21 не изменён.'
    if append not in txt: txt=txt.rstrip('\r\n')+'\r\n'+append+'\r\n'
    mi.write_bytes(txt.encode('cp1251'))
    readme=mod/'README_Ultra0.txt'
    readme.write_text(
      f'FHD_Ultra0 1.0.22 End-Day Performance Fix Alpha — {label}\n'
      'Requires FHD_SET v2.4.14+\n'
      'Based on 1.0.21 Normal Spawn Fix Alpha.\n'
      'Performance fix: FHD_SET is no longer force-recalculated a second time every day by ULTRA.\n'
      'ULTRA copies are cleared immediately before the normal FHD_SET daily tick and re-applied immediately after it, preserving a clean SET baseline without duplicate full SET work.\n'
      'Spawn hot path no longer performs global FindItemInStorage every day. If the tracked shop object becomes invalid, a full galaxy respawn search is throttled to once per 30 turns.\n'
      'No balance changes: missile max-ammo penalty -45%, vanilla missile ammo consumption (1 charge per volley), weapon wear 3% per volley.\n'
      'Re-equip ammo baseline fix remains unchanged.\n',encoding='utf-8')
    outzip=OUT/f'FHD_Ultra0_v1.0.22_EndDayPerformanceFix_Alpha_{label}.zip'; zip_tree(extract,outzip)
    report['variants'][variant]={
      'semantic_changes':changes,'zip':str(outzip),'zip_sha256':sha256(outzip),
      'lang_sha256':sha256(lang),'main_sha256':sha256(mod/'CFG'/'Main.dat'),
      'duplicate_forced_set_tick_removed':True,
      'pre_set_ultra_clear':True,
      'post_set_ultra_reapply':True,
      'spawn_global_storage_scan_removed':True,
      'missing_spawn_rescan_interval_turns':30,
      'penalty_percent':45,'missile_wear_percent':3,'shotwear_writes_ammo':False,
    }
    report['performance_regression'][variant]={
      'ultra_tick_calls_clearcopies':False,
      'ultra_tick_calls_forced_syncsetbase':False,
      'syncsetbase_force':0,
      'runtime_daily_fhdset_full_tick_count_target':1,
      'spawn003_uses_FindItemInStorage':False,
    }
    (OUT/f'{variant}_Lang.flat.txt').write_text('\n'.join(f'{p}={v}' for p,v in flat2)+'\n',encoding='utf-8')
    shutil.copy2(mi,OUT/f'{variant}_ModuleInfo.txt'); shutil.copy2(readme,OUT/f'{variant}_README_Ultra0.txt')

rp=OUT/'FHD_Ultra0_v1.0.22_VALIDATION.json'; rp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
src=OUT/'FHD_Ultra0_v1.0.22_EndDayPerformanceFix_Alpha_SOURCE.zip'
with zipfile.ZipFile(src,'w',zipfile.ZIP_DEFLATED) as z:
    z.write(Path(__file__),'SOURCE/build_v1022.py'); z.write(CODEC,'SOURCE/blockpar_codec.py')
    for variant in ('normal','test'):
        z.write(BASES[variant],f'SOURCE/BASE/{BASES[variant].name}')
        for fn in [f'{variant}_Lang.flat.txt',f'{variant}_ModuleInfo.txt',f'{variant}_README_Ultra0.txt']:
            z.write(OUT/fn,f'SOURCE/{variant}/{fn[len(variant)+1:]}')
    z.write(rp,'SOURCE/FHD_Ultra0_v1.0.22_VALIDATION.json')
print(json.dumps(report,ensure_ascii=False,indent=2))
