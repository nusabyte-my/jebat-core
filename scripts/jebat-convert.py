#!/usr/bin/env python3
import sys
import os
import argparse
from pathlib import Path

# Add llama.cpp gguf-py to path
sys.path.insert(0, str(Path(os.getcwd()) / "llama.cpp" / "gguf-py"))

from gguf import GGUFReader, GGUFWriter, GGUFValueType

def main():
    parser = argparse.ArgumentParser(description="🗡️ JEBAT-CONVERT: Inject JEBAT metadata into GGUF models")
    parser.add_argument("input", help="Input GGUF file")
    parser.add_argument("output", help="Output GGUF file")
    parser.add_argument("--role", default="panglima", help="JEBAT Agent Role (panglima, tukang, etc.)")
    parser.add_argument("--layer", default="M3_CONCEPTUAL", help="JEBAT Memory Layer compatibility")
    parser.add_argument("--version", default="2.0.0-refactored", help="JEBAT Core Version")
    
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found.")
        sys.exit(1)

    print(f"🗡️  Reading {args.input}...")
    reader = GGUFReader(args.input)
    
    # Initialize writer
    writer = GGUFWriter(args.output, arch=reader.fields['general.architecture'].parts[0].tobytes().decode('utf-8').strip('\x00'))

    print("🐝 Copying metadata and injecting JEBAT standards...")
    
    # Copy existing metadata
    for field in reader.fields.values():
        if field.name in ['general.architecture']:
            continue
        
        # Avoid duplicate keys if we're overwriting them
        if field.name in ['jebat.version', 'jebat.agent_role', 'jebat.memory_layer']:
            continue
            
        # Use add_key_value for generic copy
        val = field.contents()
        # Some fields return list for arrays, some return single values
        vtype = field.types[0]
        
        if vtype == GGUFValueType.ARRAY:
            sub_type = field.types[-1]
            writer.add_key_value(field.name, val, vtype, sub_type=sub_type)
        else:
            writer.add_key_value(field.name, val, vtype)

    # Inject JEBAT metadata
    writer.add_string("jebat.version", args.version)
    writer.add_string("jebat.agent_role", args.role)
    writer.add_string("jebat.memory_layer", args.layer)
    writer.add_string("jebat.author", "NusaByte")

    print(f"📦 Copying {len(reader.tensors)} tensors...")
    for tensor in reader.tensors:
        writer.add_tensor(tensor.name, tensor.data, raw_shape=tensor.shape, raw_dtype=tensor.tensor_type)

    print(f"💾 Saving to {args.output}...")
    writer.write_header_to_file()
    writer.write_kv_data_to_file()
    writer.write_tensors_to_file()
    writer.close()

    print("\n✅ JEBAT Metadata Injection Complete!")
    print(f"   Role:  {args.role}")
    print(f"   Layer: {args.layer}")

if __name__ == "__main__":
    main()
