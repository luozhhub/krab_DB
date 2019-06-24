#!/usr/bin/python

import sys, os
import pandas as pd
import ZFWebDatabase as DB

db = DB.AccurityWebDB("luozh", "luozh123", "ZNFdb", hostname="localhost")
db.Connect()


db.dropAll()
db.CreateAllTable()


class import_data():
    def __init__(self):
        # 236 files
        self.ZNF_GSE78099 = "/home/luozhihui/PycharmProjects/ZNFdatabase/data/GSE78099_diff/diff"
        # 161 files
        self.ZNF_GSE76496 = "/home/luozhihui/PycharmProjects/ZNFdatabase/data/GSE76496_diff/diff"
        #img file path
        self.GSE78099_img_path = "/home/luozhihui/PycharmProjects/ZNFdatabase/data/GSE78099_out"

    def parse_GSE78099(self, input_file=None):
        df_1 = pd.read_table(input_file, header=None, sep="\t",
                             names=["chr", "start", "end", "peak_name", "enrichment", "strand", \
                                    "repeat_chr", "repeat_start", "repeat_end", "repeat_strand", "repeat_name", \
                                    "sub_family", "main_family",  "overlap_len", "type"])
        return(df_1)

    def basic_data_import(self):
        for one_file in os.listdir(self.ZNF_GSE78099):
            znf_name = one_file.split("_")[1]
            # for table 1
            # znf_item = DB.Znf(entrez_id=None, gene_symbol=znf_name)
            znf_item = db.getZnf(gene_symbol=znf_name)
            print(znf_item)
            session.add_all([znf_item])

            # for table 2
            data_name = one_file.split("_")[0]
            data_source = "GSE78099"
            chip_data_item = db.getChip_data(data_name=data_name, data_source=data_source)
            chip_data_item.znf = znf_item
            session.add_all([chip_data_item])

            # for table 7
            motif_img_path = os.path.join(self.GSE78099_img_path, "_".join([data_source, znf_name]))
            znf_all_motif_img_path = os.path.join(motif_img_path, "raw", "logo1.png")
            znf_all_motif_matrix_path = os.path.join(motif_img_path, "raw", "matrix")
            znf_full_motif_img_path = os.path.join(motif_img_path, "full", "logo1.png")
            znf_full_motif_matrix_path = os.path.join(motif_img_path, "full", "matrix")
            znf_part_motif_img_path = os.path.join(motif_img_path, "part", "logo1.png")
            znf_part_motif_matrix_path = os.path.join(motif_img_path, "part", "matrix")
            znf_None_motif_img_path = os.path.join(motif_img_path, "None", "logo1.png")
            znf_None_motif_matrix_path = os.path.join(motif_img_path, "None", "matrix")
            motif_item = DB.Motif(znf_all_motif_img_path=znf_all_motif_img_path,
                                  znf_all_motif_matrix_path=znf_all_motif_matrix_path, \
                                  znf_full_motif_img_path=znf_full_motif_img_path,
                                  znf_full_motif_matrix_path=znf_full_motif_matrix_path, \
                                  znf_part_motif_img_path=znf_part_motif_img_path,
                                  znf_part_motif_matrix_path=znf_None_motif_matrix_path, \
                                  znf_None_motif_img_path=znf_None_motif_img_path,
                                  znf_None_motif_matrix_path=znf_None_motif_matrix_path)
            motif_item.chip_data = chip_data_item
            session.add_all([motif_item])
            session.flush()
            session.commit()

            print("%s success!!" % znf_item.gene_symbol)
            # for table 3
            # for table 5
            file_path = os.path.join(importData.ZNF_GSE78099, one_file)
            df_bed = importData.parse_GSE78099(input_file=file_path)
            all_peaks = []
            all_repeats = []

            for index, row in df_bed.iterrows():
                if row["repeat_start"] == -1 and row["repeat_end"] == -1:
                    continue

                # table 5
                peak_chr = row["chr"]
                peak_start = row["start"]
                peak_end = row["end"]
                peak_strand = row["strand"]
                peak_enrichment = row["enrichment"]
                peaks_item = DB.Peaks(chr=peak_chr, start=int(peak_start), end=int(peak_end), strand=peak_strand,
                                      enrichment=float(peak_enrichment), peakName=data_name + row["peak_name"])
                if peaks_item is not None:
                    # the chip-data can't be replicate
                    peaks_item.chip_data.append(chip_data_item)
                    session.add(peaks_item)
                    session.flush()
                # table 3
                repeat_name = row["repeat_name"]
                repeat_item = db.getRepeat(repeat_name=repeat_name)
                if repeat_item is not None:
                    repeat_item.znf.append(znf_item)
                    session.add(repeat_item)
                    session.flush()
                # table 4
                sub_family = row["sub_family"]
                main_family = row["main_family"]
                repeat_family_item = db.getRepeat_family(repeat_name=repeat_name, sub_family=sub_family,
                                                         main_family=main_family)
                if repeat_family_item is not None:
                    if repeat_item is None:
                        repeat_item = db.getRepeat(repeat_name=repeat_name, no_duplicate=False)
                        exit("wrong")
                    repeat_family_item.repeat = repeat_item
                    session.add(repeat_family_item)
                    session.flush()

                print("repeat success!!! in %s" % (znf_item.gene_symbol))
                # table 6
                repeat_chr = row["repeat_chr"]
                repeat_start = row["repeat_start"]
                repeat_end = row["repeat_end"]
                repeat_strand = row["repeat_strand"]
                repeat_region_item = DB.Repeat_region(chr=repeat_chr, start=repeat_start, end=repeat_end,
                                                      strand=repeat_strand)
                if repeat_region_item is not None:
                    if repeat_item is None:
                        repeat_item = db.getRepeat(repeat_name=repeat_name, no_duplicate=False)
                    repeat_region_item.repeat.append(repeat_item)

                    repeat_region_item.znf.append(znf_item)
                    # print(repeat_region_item)
                    # print(repeat_item)
                    session.add(repeat_region_item)
                    session.flush()
                session.commit()
                print("%s %s %s file sucess!!!" % (repeat_chr, repeat_start, repeat_end))


if __name__ == "__main__":
    importData = import_data()
    session = db.SessionUp()


    #step 1: import basic data
    for one_file in os.listdir(importData.ZNF_GSE78099):
        znf_name = one_file.split("_")[1]
        # for table 1
        # znf_item = DB.Znf(entrez_id=None, gene_symbol=znf_name)
        znf_item = db.getZnf(gene_symbol=znf_name)
        print(znf_item)
        session.add_all([znf_item])

        # for table 2
        data_name = one_file.split("_")[0]
        data_source = "GSE78099"
        chip_data_item = db.getChip_data(data_name=data_name, data_source=data_source)
        chip_data_item.znf = znf_item
        session.add_all([chip_data_item])

        #for table 7
        motif_img_path = os.path.join(importData.GSE78099_img_path, "_".join([data_source, znf_name]))
        znf_all_motif_img_path = os.path.join(motif_img_path, "raw", "logo1.png")
        znf_all_motif_matrix_path = os.path.join(motif_img_path, "raw", "matrix")
        znf_full_motif_img_path = os.path.join(motif_img_path, "full", "logo1.png")
        znf_full_motif_matrix_path = os.path.join(motif_img_path, "full", "matrix")
        znf_part_motif_img_path = os.path.join(motif_img_path, "part", "logo1.png")
        znf_part_motif_matrix_path = os.path.join(motif_img_path, "part", "matrix")
        znf_None_motif_img_path = os.path.join(motif_img_path, "None", "logo1.png")
        znf_None_motif_matrix_path = os.path.join(motif_img_path, "None", "matrix")
        motif_item = DB.Motif(znf_all_motif_img_path=znf_all_motif_img_path, znf_all_motif_matrix_path=znf_all_motif_matrix_path,\
                              znf_full_motif_img_path=znf_full_motif_img_path, znf_full_motif_matrix_path=znf_full_motif_matrix_path,\
                              znf_part_motif_img_path=znf_part_motif_img_path, znf_part_motif_matrix_path=znf_None_motif_matrix_path,\
                              znf_None_motif_img_path=znf_None_motif_img_path, znf_None_motif_matrix_path=znf_None_motif_matrix_path)
        motif_item.chip_data = chip_data_item
        session.add_all([motif_item])
        session.flush()

        session.commit()


        print("%s success!!" % znf_item.gene_symbol)
        # for table 3
        # for table 5

        file_path = os.path.join(importData.ZNF_GSE78099, one_file)
        df_bed = importData.parse_GSE78099(input_file=file_path)
        all_peaks = []
        all_repeats = []

        for index, row in df_bed.iterrows():
            if row["repeat_start"] == -1 and row["repeat_end"] == -1:
                continue

            #table 5
            peak_chr = row["chr"]
            peak_start = row["start"]
            peak_end = row["end"]
            peak_strand = row["strand"]
            peak_enrichment = row["enrichment"]
            peaks_item = DB.Peaks(chr=peak_chr, start=int(peak_start), end=int(peak_end), strand=peak_strand,
                                     enrichment=float(peak_enrichment), peakName=data_name + row["peak_name"])
            if peaks_item is not None:
                #the chip-data can't be replicate
                peaks_item.chip_data.append(chip_data_item)
                session.add(peaks_item)
                session.flush()
            #table 3
            repeat_name = row["repeat_name"]
            repeat_item = db.getRepeat(repeat_name=repeat_name)
            if repeat_item is not None:
                repeat_item.znf.append(znf_item)
                session.add(repeat_item)
                session.flush()
            #table 4
            sub_family = row["sub_family"]
            main_family = row["main_family"]
            repeat_family_item = db.getRepeat_family(repeat_name=repeat_name, sub_family=sub_family, main_family=main_family)
            if repeat_family_item is not None:
                if repeat_item is None:
                    repeat_item = db.getRepeat(repeat_name=repeat_name, no_duplicate=False)
                    exit("wrong")
                repeat_family_item.repeat = repeat_item
                session.add(repeat_family_item)
                session.flush()

            print("repeat success!!! in %s" % (znf_item.gene_symbol))
            #table 6
            repeat_chr = row["repeat_chr"]
            repeat_start = row["repeat_start"]
            repeat_end = row["repeat_end"]
            repeat_strand = row["repeat_strand"]
            repeat_region_item = DB.Repeat_region(chr=repeat_chr, start=repeat_start, end=repeat_end,
                                                     strand=repeat_strand)
            if repeat_region_item is not None:
                if repeat_item is None:
                    repeat_item = db.getRepeat(repeat_name=repeat_name, no_duplicate=False)
                repeat_region_item.repeat.append(repeat_item)

                repeat_region_item.znf.append(znf_item)
                #print(repeat_region_item)
                #print(repeat_item)
                session.add(repeat_region_item)
                session.flush()
            session.commit()
            print("%s %s %s file sucess!!!" % (repeat_chr, repeat_start, repeat_end))

        #session.commit()



