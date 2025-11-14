import pandas as pd
import sys

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <.eigenvec.var file>", file=sys.stderr)
    sys.exit(1)

var_file = sys.argv[1]


# Read the var file
df = pd.read_csv(var_file, sep="\\s+")

pca_columns = [col for col in df.columns if col.startswith("PC")]


for pc in pca_columns:
    abs_col = f"ABS_{pc}"
    df[abs_col] = df[pc].abs()

    top_snps = df.sort_values(abs_col, ascending=False).head(100)
    print(f"\nTop 100 SNPs for {pc}:")
    for _, row in top_snps.iterrows():
        # print(row)
        print(f"{row['VAR']} (Loading: {row[pc]})")
