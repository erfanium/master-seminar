import pandas as pd
import sys
import json

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <.eigenvec.var file>", file=sys.stderr)
    sys.exit(1)

var_file = sys.argv[1]

# Read the var file
df = pd.read_csv(var_file, sep=r"\s+")

pca_columns = [col for col in df.columns if col.startswith("PC")]

output = {}

for pc in pca_columns:
    abs_col = f"ABS_{pc}"
    df[abs_col] = df[pc].abs()

    top_snps = df.sort_values(abs_col, ascending=False).head(100)

    output[pc] = []
    for _, row in top_snps.iterrows():
        var = row["VAR"]
        # Expect format: chr-pos-ref-alt
        try:
            chrom, pos, ref, alt = var.split("-")
        except ValueError:
            chrom, pos, ref, alt = (None, None, None, None)

        output[pc].append(
            {
                "chrom": chrom,
                "pos": int(pos) if pos is not None else None,
                "ref": ref,
                "alt": alt,
                "score": row[pc],
            }
        )

# Print JSON
print(json.dumps(output, indent=2))
