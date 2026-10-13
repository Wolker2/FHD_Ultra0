from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import io, struct, zlib

SEED_KEY = bytes([0x89,0xC6,0xE8,0xB1])

@dataclass
class Entry:
    name: str
    value: str | 'Block'

@dataclass
class Block:
    sorted: bool = True
    entries: list[Entry] = field(default_factory=list)
    def add_param(self,name,value): self.entries.append(Entry(name,str(value)))
    def add_block(self,name, block=None):
        b = block or Block(True)
        self.entries.append(Entry(name,b)); return b
    def ordered_entries(self):
        if not self.sorted: return list(self.entries)
        # Stable sort, case-sensitive matches the reference RedBlackTree comparator.
        return sorted(self.entries, key=lambda e:e.name)

class Reader:
    def __init__(self,b): self.b=io.BytesIO(b)
    def u8(self): return struct.unpack('<B',self.b.read(1))[0]
    def u32(self): return struct.unpack('<I',self.b.read(4))[0]
    def wstr(self):
        chunks=[]
        while True:
            c=self.b.read(2)
            if len(c)<2: raise EOFError('unterminated widestr')
            if c==b'\0\0': break
            chunks.append(c)
        return b''.join(chunks).decode('utf-16le')
    def read_block(self,new_format=True):
        sort=bool(self.u8()); count=self.u32(); blk=Block(sort)
        for _ in range(count):
            if new_format and sort: self.b.read(8)
            kind=self.u8(); name=self.wstr()
            if kind==1: val=self.wstr()
            elif kind==2: val=self.read_block(new_format)
            else: raise ValueError(f'bad kind {kind}')
            blk.entries.append(Entry(name,val))
        return blk

def rand31pm(seed):
    while True:
        hi,lo=divmod(seed,0x1f31d)
        seed=lo*0x41a7-hi*0xb14
        if seed<1: seed+=0x7fffffff
        yield seed-1

def crypt(data: bytes, seed:int)->bytes:
    out=bytearray(data); g=rand31pm(seed)
    for i in range(len(out)): out[i]^=(next(g)&255)
    return bytes(out)

def decode_dat(path):
    b=Path(path).read_bytes()
    h=struct.unpack('<I',b[:4])[0]
    seed_raw=bytes(x^y for x,y in zip(b[4:8],SEED_KEY))
    seed=struct.unpack('<i',seed_raw)[0]
    plain=crypt(b[8:],seed)
    if zlib.crc32(plain)&0xffffffff != h:
        raise ValueError('crc mismatch')
    if plain[:4]!=b'ZL01': raise ValueError(plain[:4])
    usize=struct.unpack('<I',plain[4:8])[0]
    raw=zlib.decompress(plain[8:])
    if len(raw)!=usize: raise ValueError((len(raw),usize))
    return Reader(raw).read_block(True), seed

def encode_block(block:Block)->bytes:
    out=io.BytesIO()
    def w_u8(v): out.write(struct.pack('<B',v))
    def w_u32(v): out.write(struct.pack('<I',v))
    def w_s(s): out.write(s.encode('utf-16le')+b'\0\0')
    def rec(blk:Block):
        w_u8(1 if blk.sorted else 0)
        ordered=blk.ordered_entries(); w_u32(len(ordered))
        # duplicate run metadata is encoded per sorted entry
        run_counts={}
        if blk.sorted:
            for e in ordered: run_counts[e.name]=run_counts.get(e.name,0)+1
        run_index={}
        for e in ordered:
            if blk.sorted:
                idx=run_index.get(e.name,0)
                w_u32(idx); w_u32(run_counts[e.name] if idx==0 else 0)
                run_index[e.name]=idx+1
            if isinstance(e.value,Block):
                w_u8(2); w_s(e.name); rec(e.value)
            else:
                w_u8(1); w_s(e.name); w_s(e.value)
    rec(block); return out.getvalue()

def encode_dat(block:Block,path,seed=123456789):
    raw=encode_block(block)
    plain=b'ZL01'+struct.pack('<I',len(raw))+zlib.compress(raw,9)
    h=zlib.crc32(plain)&0xffffffff
    seed_bytes=struct.pack('<i',seed)
    stored_seed=bytes(x^y for x,y in zip(seed_bytes,SEED_KEY))
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_bytes(struct.pack('<I',h)+stored_seed+crypt(plain,seed))

def flatten(block:Block,prefix=''):
    out=[]
    for e in block.ordered_entries() if block.sorted else block.entries:
        p=f'{prefix}/{e.name}' if prefix else e.name
        if isinstance(e.value,Block): out.extend(flatten(e.value,p))
        else: out.append((p,e.value))
    return out

def from_flat(items, sorted=True):
    root=Block(sorted)
    # map tuple path -> Block; preserve append order but canonical sorted serialization
    blocks={():root}
    for path,value in items:
        parts=path.split('/')
        cur=root; key=()
        for part in parts[:-1]:
            key2=key+(part,)
            if key2 not in blocks:
                nb=Block(sorted); cur.entries.append(Entry(part,nb)); blocks[key2]=nb
            cur=blocks[key2]; key=key2
        cur.entries.append(Entry(parts[-1],str(value)))
    return root

if __name__=='__main__':
    import sys
    b,seed=decode_dat(sys.argv[1]); print('seed',seed,'entries',len(flatten(b)))
    for p,v in flatten(b)[:20]: print(p+'='+v)
