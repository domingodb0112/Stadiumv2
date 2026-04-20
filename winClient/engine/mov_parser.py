"""
mov_parser.py
Traducción del C++ video_engine.cpp a Python.
Parsea archivos .mov y retorna la lista de frames (offset, tamaño) y el FPS.
"""
import struct
from pathlib import Path


def _read_atom(f):
    """Lee el encabezado de un átomo MOV: (size, name, offset_después_del_header)."""
    data = f.read(8)
    if len(data) < 8:
        return None, None, None
    size = struct.unpack('>I', data[:4])[0]
    name = data[4:8].decode('latin-1')
    if size < 8:
        return None, None, None
    return size, name, f.tell()


def _find_atom(buf: bytes, name: str):
    """Busca un átomo por nombre dentro de un buffer. Retorna (offset_datos, tamaño_datos)."""
    i = 0
    while i + 8 <= len(buf):
        size = struct.unpack('>I', buf[i:i+4])[0]
        atom = buf[i+4:i+8].decode('latin-1')
        if size < 8 or i + size > len(buf):
            break
        if atom == name:
            return i + 8, size - 8
        i += size
    return None, None


def _nav(buf: bytes, name: str) -> bytes:
    """Extrae el contenido del primer átomo con ese nombre."""
    o, s = _find_atom(buf, name)
    if o is None:
        return b''
    return buf[o:o+s]


def parse_mov(path: str):
    """
    Parsea un archivo .mov y retorna:
        frames : list of (file_offset: int, byte_size: int)
        fps    : float
    """
    import os
    path = str(path)
    if not os.path.exists(path):
        print(f"[!] MOV file not found: {path}")
        return [], 30.0

    try:
        moov_buf = None
        with open(path, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
            f.seek(0)

            # Buscar átomo 'moov'
            while f.tell() < file_size:
                size, name, offset = _read_atom(f)
                if size is None:
                    break
                if name == 'moov':
                    f.seek(offset)
                    moov_buf = f.read(size - 8)
                    break
                f.seek(offset + size - 8)

        if not moov_buf:
            return [], 30.0

        trak = _nav(moov_buf, 'trak')
        mdia = _nav(trak, 'mdia')

        # Timescale desde mdhd
        ts = 30
        mdhd_o, _ = _find_atom(mdia, 'mdhd')
        if mdhd_o is not None and len(mdia) >= mdhd_o + 16:
            ts = struct.unpack('>I', mdia[mdhd_o+12:mdhd_o+16])[0]

        minf = _nav(mdia, 'minf')
        stbl = _nav(minf, 'stbl')

        # Sample duration (stts)
        sd = max(ts // 30, 1)
        stts_o, stts_s = _find_atom(stbl, 'stts')
        if stts_o is not None and (stts_s or 0) >= 12:
            sd = struct.unpack('>I', stbl[stts_o+12:stts_o+16])[0]
        fps = ts / sd if sd > 0 else 30.0

        # Sample sizes (stsz)
        stsz_o, _ = _find_atom(stbl, 'stsz')
        if stsz_o is None:
            return [], fps
        fixed_sz    = struct.unpack('>I', stbl[stsz_o+4:stsz_o+8])[0]
        sample_cnt  = struct.unpack('>I', stbl[stsz_o+8:stsz_o+12])[0]
        if fixed_sz:
            sizes = [fixed_sz] * sample_cnt
        else:
            sizes = [struct.unpack('>I', stbl[stsz_o+12+i*4:stsz_o+16+i*4])[0]
                     for i in range(sample_cnt)]

        # Chunk offsets (stco o co64)
        chunks = []
        stco_o, _ = _find_atom(stbl, 'stco')
        if stco_o is not None:
            chunk_cnt = struct.unpack('>I', stbl[stco_o+4:stco_o+8])[0]
            chunks = [struct.unpack('>I', stbl[stco_o+8+i*4:stco_o+12+i*4])[0]
                      for i in range(chunk_cnt)]
        else:
            co64_o, _ = _find_atom(stbl, 'co64')
            if co64_o is not None:
                chunk_cnt = struct.unpack('>I', stbl[co64_o+4:co64_o+8])[0]
                chunks = [struct.unpack('>Q', stbl[co64_o+8+i*8:co64_o+16+i*8])[0]
                          for i in range(chunk_cnt)]

        if not chunks:
            return [], fps

        # Sample-to-chunk (stsc)
        stsc_o, _ = _find_atom(stbl, 'stsc')
        entry_cnt = struct.unpack('>I', stbl[stsc_o+4:stsc_o+8])[0]
        stsc_entries = [(struct.unpack('>I', stbl[stsc_o+8+i*12:stsc_o+12+i*12])[0],
                         struct.unpack('>I', stbl[stsc_o+12+i*12:stsc_o+16+i*12])[0])
                        for i in range(entry_cnt)]  # (first_chunk, samples_per_chunk)

        frames = []
        sample_idx = 0
        for ci, chunk_offset in enumerate(chunks):
            if sample_idx >= sample_cnt:
                break
            spc = 1
            for fc, s in reversed(stsc_entries):
                if ci + 1 >= fc:
                    spc = s
                    break
            off = chunk_offset
            for _ in range(spc):
                if sample_idx >= sample_cnt:
                    break
                frames.append((off, sizes[sample_idx]))
                off += sizes[sample_idx]
                sample_idx += 1

        return frames, fps
    except Exception as e:
        print(f"[!] Error parsing MOV: {e}")
        return [], 30.0
