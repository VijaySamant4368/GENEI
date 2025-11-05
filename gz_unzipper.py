import gzip
import shutil

FILENAME = "GSE24080_series_matrix.txt"

with gzip.open(FILENAME + ".gz", 'rb') as f_in:
    with open(FILENAME, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

print("File unzipped successfully.")
