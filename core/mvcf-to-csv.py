import sys
import csv
from cyvcf2 import VCF

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <vcf_file>", file=sys.stderr)
    sys.exit(1)

vcf_file = sys.argv[1]

# Open VCF
vcf = VCF(vcf_file)

# Get sample names
samples = vcf.samples

# Create CSV writer to stdout
writer = csv.writer(sys.stdout)

# Write header
header = ["CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER"] + samples
writer.writerow(header)

# Iterate through VCF records
for record in vcf:
    row = [
        record.CHROM,
        record.POS,
        record.ID,
        record.REF,
        ",".join(record.ALT),  # join multiple ALT alleles
        record.QUAL,
        ";".join(record.FILTER) if record.FILTER else "PASS",
    ]

    # Add genotypes for each sample
    for gt in record.genotypes:  # [allele1, allele2, phased, ...]
        genotype = "/".join(
            ["." if allele is None else str(allele) for allele in gt[:2]]
        )
        row.append(genotype)

    writer.writerow(row)
