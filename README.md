# GENEI

Tries to classify patients in GSE24080 into three classes using the important genes : "EPAS1", "ERC2", "PRC1", "CSGALNACT1", "CCND1"; as discussed in the paper https://pubmed.ncbi.nlm.nih.gov/34917133/, using similar mythology as was done in MRS classification https://www.sciencedirect.com/science/article/pii/S1936523321001492?via%3Dihub

## Download:

GSE24080_MM_UAMS565_ClinInfo_27Jun2008_LS_clean.xls: /geo/download/?acc=GSE24080&amp;format=file&amp;file=GSE24080%5FMM%5FUAMS565%5FClinInfo%5F27Jun2008%5FLS%5Fclean%2Exls%2Egz

GSE24080_series_matrix.txt.gz: https://ftp.ncbi.nlm.nih.gov/geo/series/GSE24nnn/GSE24080/matrix/GSE24080_series_matrix.txt.gz

GPL570-55999.txt: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GPL570 then Download Full Table

## Execution Order:
gz_unzipper.py:
- unzips .gz file
- requires GSE24080_series_matrix.txt.gz
- outputs GSE24080_series_matrix.txt

txt_to_csv.py:
- Breaks GSE24080_series_matrix.txt into Expression Matrix and Metadata
- requires: GSE24080_series_matrix.txt
- outputs: expression_matrix.csv, sample_metadata.csv

five_genes.ipynb:
- Extracts the value of the five genes for all patients
- requires: expression_matrix.csv, GPL570-55999.txt
- outputs: five_gene_matrix.csv

Merger.ipynb:
- Merges the 5 genes values, the ISS Staging(With B2M and Albumin), and the OS and PFS ecents
- requires: five_gene_matrix.csv, sample_metadata.csv, GSE24080_MM_UAMS565_ClinInfo_27Jun2008_LS_clean.xls
- outputs: final_columns.csv

FullTrain.ipynb:
- Trains a KNN on the full dataset, using the 5 genes values (Steps similar to MRS: https://www.sciencedirect.com/science/article/pii/S1936523321001492?via%3Dihub )
- requires: final_columns.csv
- outputs: full_GENEI.csv

comparion.ipynb:
- Compares the ISS staging and GENEI on both OS and EFS
- requires: full_GENEI.csv
- outputs: displays the output on the notebook