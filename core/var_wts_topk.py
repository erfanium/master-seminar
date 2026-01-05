import pandas as pd
import json


def extract_topk(var_file, k=100):
    df = pd.read_csv(var_file, sep=r"\s+")

    pca_columns = [col for col in df.columns if col.startswith("PC")]
    output = {}

    for pc in pca_columns:
        abs_col = f"ABS_{pc}"
        df[abs_col] = df[pc].abs()

        top_snps = df.sort_values(abs_col, ascending=False).head(k)

        output[pc] = []
        for _, row in top_snps.iterrows():
            var = row["VAR"]
            try:
                chrom, pos, ref, alt = var.split("-")
                pos = int(pos)
            except ValueError:
                chrom, pos, ref, alt = None, None, None, None

            output[pc].append(
                {
                    "chrom": chrom,
                    "pos": pos,
                    "ref": ref,
                    "alt": alt,
                    "score": row[pc],
                }
            )

    return output


def write_topk_json(var_file, out_file, k=100):
    result = extract_topk(var_file, k=k)
    with open(out_file, "w") as f:
        json.dump(result, f, indent=2)
