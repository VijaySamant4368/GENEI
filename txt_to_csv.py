import pandas as pd

series_file = "GSE24080_series_matrix.txt"

with open(series_file, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

sample_meta = {}
for line in lines:
    if line.startswith("!Sample_"):
        key, *vals = line.strip().split("\t")
        key = key.replace("!Sample_", "")
        vals = [v.strip().strip('"') for v in vals]
        sample_meta[key] = vals

gsm_ids = sample_meta.get("geo_accession") or sample_meta.get("title")
if gsm_ids is None:
    raise ValueError("Couldn't find sample identifiers in !Sample_geo_accession or !Sample_title")

# all lists should be the same length; if not, pandas will fill missing cells with NaN
meta_df = pd.DataFrame(sample_meta, index=gsm_ids)
meta_df.index.name = "GSM_ID"
meta_df.to_csv("sample_metadata.csv")
print(f"Saved sample metadata: {meta_df.shape}")

expr_df = pd.read_csv(series_file, sep="\t", comment="!", dtype=str)

# first column is usually ID_REF (probe/gene id)
expr_df = expr_df.set_index(expr_df.columns[0])
expr_df.to_csv("expression_matrix.csv")
print(f"Saved expression matrix: {expr_df.shape}")

print("All done! Files written:\n - sample_metadata.csv\n - expression_matrix.csv")
