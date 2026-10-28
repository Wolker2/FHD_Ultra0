#!/usr/bin/env python3
"""Build FHD_SET and FHD_Ultra0 using editable sources only (Python stdlib)."""
from pathlib import Path
import argparse,hashlib,json,zipfile
from dat_codec import encode as dat_encode
from gi_codec import encode as gi_encode
ROOT=Path(__file__).resolve().parents[1]
def load(path):return json.loads(Path(path).read_text('utf-8'))
def hashes(files):return {name:hashlib.sha256(data).hexdigest() for name,data in sorted(files.items())}
def build(root=ROOT):
    source=Path(root)/'source';files={}
    for module in load(source/'modules.json'):
        name=module['name'];folder=source/'modules'/name
        assert module['metadata_encoding']=='cp1251'
        for path in sorted((folder/'CFG').rglob('*.json')):
            files[name+'/'+path.relative_to(folder).with_suffix('.dat').as_posix()]=dat_encode(load(path))
        files[name+'/ModuleInfo.txt']=(folder/'ModuleInfo.txt').read_bytes().decode('utf-8').encode('cp1251')
    files['FHD_SET/DATA/ItemsUseless/FHDSET_SearchTool.gi']=gi_encode(load(source/'graphics/FHDSET_SearchTool.json'))
    return files
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-original',action='store_true')
    parser.add_argument('--output',type=Path,default=ROOT/'dist/FHD_SET-with-Ultra0-install.zip')
    args=parser.parse_args();files=build()
    if args.verify_original:
        expected=load(ROOT/'original-file-sha256.json');actual=hashes(files)
        changed=sorted(n for n in actual.keys()|expected.keys() if actual.get(n)!=expected.get(n))
        if changed:raise SystemExit('Original-byte verification failed: '+', '.join(changed))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo('Mods/FHD_MODS/'+name,(2026,1,1,0,0,0));info.external_attr=0o644<<16
            z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    print(json.dumps({'runtime_files':len(files),'original_bytes_verified':args.verify_original,'output':str(args.output)},indent=2))
if __name__=='__main__':main()
