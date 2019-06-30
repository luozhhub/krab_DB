#!/usr/bin/python

import sys, os
import pandas as pd
import ZFWebDatabase as DB
import json
import numpy

db = DB.AccurityWebDB("luozh", "luozh123", "ZNFdb", hostname="localhost")
db.Connect()




class import_data():
    def __init__(self):
        # 236 files
        self.ZNF_GSE78099 = "/home/luozhihui/PycharmProjects/ZNFdatabase/data/GSE78099_diff/diff"
        # 161 files
        self.ZNF_GSE76496 = "/home/luozhihui/PycharmProjects/ZNFdatabase/data/GSE76496_diff/diff"
        # img file path
        self.GSE78099_img_path = "/home/luozhihui/PycharmProjects/ZNFdatabase/data/GSE78099_out"
        # ensemble_list
        self.ensemble_list = []
        self.basic_information = {}
        self.repeat_family_cache = {}

    def parse_GSE78099(self, input_file=None):
        df_1 = pd.read_table(input_file, header=None, sep="\t",
                             names=["chr", "start", "end", "peak_name", "enrichment", "strand", \
                                    "repeat_chr", "repeat_start", "repeat_end", "repeat_strand", "repeat_name", \
                                    "sub_family", "main_family", "overlap_len", "type"])
        return (df_1)

    def parseUniprot(self):
        human_input_file = "/home/luozhihui/Project/ZF_database/data_process/C2H2_list/uniprot-c2h2-human.txt"
        df_1 = pd.read_table(human_input_file, header=0, sep="\t")
        unipro_list = {}
        for index, row in df_1.iterrows():
            unipro = {}
            unipro["uniproID"] = row[0]
            unipro["Gene names"] = row[4]
            unipro["length"] = row[6]
            unipro["protein_names"] = row[3]
            #unipro["zinc_finger"] = {}
            unipro["zinc_finger"] = 0

            if pd.isnull(row["Zinc finger"]):
                unipro_list[unipro["uniproID"]] = unipro
                continue


            fingers = row["Zinc finger"].split(";")
            fing_num = 0
            for finger in fingers:
                array = finger.strip(" ").split(" ")
                if array[0] != "ZN_FING":
                    continue
                fing_num = fing_num + 1
                if len(array) > 4:
                    finger_id = array[3] + " " + array[4]
                else:
                    finger_id = array[3]
                finger_id = finger_id.strip(".")
                #unipro["zinc_finger"][finger_id] = (array[1], array[2])
            unipro["zinc_finger"] = fing_num
            unipro_list[unipro["uniproID"]] = unipro
        return unipro_list


    def C2H2_information(self):
        # mapping uniprot to ensembl
        unipro_dict = self.parseUniprot()
        #uniprot id and ensembl id
        mapping_human_df = pd.read_table(
            "/home/luozhihui/Project/ZF_database/data_process/C2H2_list/Homo_sapiens_mapping_list.txt", header=0,
            sep="\t")
        unipro_dict_ensembl = {}

        #k is UniproID, v is information,make, make emsembl as key
        for (uniproID, values) in unipro_dict.items():
            df_s = mapping_human_df[mapping_human_df["uniprot_gn"] == uniproID]
            if df_s.empty:
                continue
            # UniproID : EnsemblID
            Ensem = df_s.iloc[0, 0]
            if Ensem not in unipro_dict_ensembl:
                unipro_dict_ensembl[Ensem] = [values]
            else:
                unipro_dict_ensembl[Ensem].append(values)

        # main table
        human_input_file = "/home/luozhihui/Project/ZF_database/data_process/C2H2_list/Homo_sapiens_TF"
        mouse_input_file = "/home/luozhihui/Project/ZF_database/data_process/C2H2_list/Mus_musculus_TF"
        df_1 = pd.read_table(human_input_file, header=0, sep="\t")
        df_2 = pd.read_table(mouse_input_file, header=0, sep="\t")
        df_c2h2_human = df_1[df_1["Family"] == "zf-C2H2"]
        df_c2h2_mouse = df_2[df_2["Family"] == "zf-C2H2"]

        df = pd.concat([df_c2h2_human, df_c2h2_mouse], ignore_index=True)
        # print(df[1:5])

        #for human data
        for index, row in df_c2h2_human.iterrows():
            ensemblID = row["Ensembl"]
            if ensemblID in unipro_dict_ensembl:
                data_dict_list = unipro_dict_ensembl[ensemblID]
                protein_n = len(data_dict_list)
                row["protein_n"] = protein_n
                row["gene_synonym"] = data_dict_list[0]["Gene names"]
                row["unipro_feature"] = []
                for i in range(protein_n):
                    unipro_one = {}
                    unipro_one["uniproID"] = data_dict_list[i]["uniproID"]
                    unipro_one["length"] = data_dict_list[i]["length"]
                    #unipro_one["protein_names"] = data_dict_list[i]["protein_names"]
                    #unipro_one["zinc_finger"] = json.dumps(data_dict_list[i]["zinc_finger"])
                    unipro_one["zinc_finger"] = data_dict_list[i]["zinc_finger"]
                    row["unipro_feature"].append(unipro_one)
                self.ensemble_list.append(ensemblID)
                self.basic_information[ensemblID] = row
        return None
                #print("%s\t%s\t%s"% (row["Ensembl"], row["Symbol"], len(new_unipro_list[row["Ensembl"]]["zinc_finger"].keys())))

    #table 1, Znf table
    def import_basic_information(self):
        print("begin to import table 1: Znf")
        if len(self.ensemble_list) == 0:
            print("no basic information!")
            exit(1)
        for ensembl in self.ensemble_list:
            info = self.basic_information[ensembl]
            znf_item = db.getZnf(ensembl=ensembl, entrez_id=info["Entrez ID"], gene_symbol=info["Symbol"],
                                 species=info["Species"], family=info["Family"], proteins=info["Protein"],
                                 gene_synonym=info["gene_synonym"], unipro_feature=json.dumps(info["unipro_feature"]))
            session.add_all([znf_item])
            session.flush()
        session.commit()
        print("finish to import table 1")
        return None

    #for table 2 chip_data and table 3 repeat
    def import_repeat(self, species="Homo_sapiens", project_dir=None):
        print("begin table 3: repeat.")
        for one_file in os.listdir(self.ZNF_GSE78099):
            #print(one_file)
            znf_name = one_file.split("_")[1]
            znf_symbol = znf_name.split("-")[0]
            znf_item = session.query(DB.Znf).filter_by(gene_symbol=znf_symbol, species=species).first()
            if znf_item is None:
                print("we has no data:%s " %znf_symbol)
                continue


            file_path = os.path.join(importData.ZNF_GSE78099, one_file)
            df_bed = importData.parse_GSE78099(input_file=file_path)
            repeat_series = df_bed["repeat_name"].drop_duplicates()
            repeat_list = list(repeat_series.values)
            repeat_list.remove(".")
            number = len(repeat_list)
            for one in repeat_list:
                repeat_item = db.getRepeat(repeat_name=one)
                repeat_item.znf.append(znf_item)
                session.add_all([repeat_item])
                session.flush()

            peak_name_series = df_bed["peak_name"].drop_duplicates()
            peak_number = len(peak_name_series)

            data_sample_name = one_file.split("_")[0]
            data_project_name = "GSE78099"
            chip_data_item = db.getChip_data(data_name=data_sample_name, data_source=data_project_name, \
                                             repeat_number=number, peak_number=peak_number)
            chip_data_item.znf = znf_item
            session.add_all([chip_data_item])
            session.flush()
        session.commit()
        print("finish table 2 and table 3: repeat.")


    def import_peaks(self, species="Homo_sapiens", project_dir=None):
    #for table 5, peaks
        i = 0
        for one_file in os.listdir(self.ZNF_GSE78099):
            print(one_file)
            znf_name = one_file.split("_")[1]
            znf_symbol = znf_name.split("-")[0]
            znf_item = session.query(DB.Znf).filter_by(gene_symbol=znf_symbol, species=species).first()
            if znf_item is None:
                print("we has no data:%s " %znf_symbol)
                continue
            data_sample_name = one_file.split("_")[0]

            file_path = os.path.join(importData.ZNF_GSE78099, one_file)
            df_bed = importData.parse_GSE78099(input_file=file_path)

            for index, row in df_bed.iterrows():
                if row["repeat_start"] == -1 and row["repeat_end"] == -1:
                    continue

                # table peaks
                repeat_name = row["repeat_name"]
                repeat_item = db.getRepeat(repeat_name=repeat_name)
                chip_data_item = db.getChip_data(data_name=data_sample_name)

                if repeat_name not in self.repeat_family_cache:
                    sub_family = row["sub_family"]
                    main_family = row["main_family"]
                    repeat_item.sub_family = sub_family
                    repeat_item.main_family = main_family
                    session.add(repeat_item)
                    session.flush()
                    self.repeat_family_cache[repeat_name] = 1

                # add peak region
                peak_chr = row["chr"]
                peak_start = row["start"]
                peak_end = row["end"]
                peak_strand = row["strand"]
                peak_enrichment = row["enrichment"]
                peak_ensembl = znf_item.ensembl
                peaks_item = DB.Peaks(chr=peak_chr, start=int(peak_start), end=int(peak_end), strand=peak_strand,
                                      enrichment=float(peak_enrichment), ensembl=peak_ensembl)
                peaks_item.chip_data = chip_data_item
                peaks_item.repeat = repeat_item
                peaks_item.znf = znf_item
                session.add(peaks_item)
                session.flush()

                #add repeat region
                repeat_chr = row["repeat_chr"]
                repeat_start = row["repeat_start"]
                repeat_end = row["repeat_end"]
                repeat_strand = row["repeat_strand"]
                repeat_region_item = DB.Repeat_region(chr=repeat_chr, start=repeat_start, end=repeat_end,
                                                      strand=repeat_strand)
                repeat_region_item.repeat = repeat_item
                repeat_region_item.znf.append(znf_item)
                repeat_region_item.chip_data.append(chip_data_item)
                session.add(repeat_region_item)
                session.flush()
            session.commit()
            i = i + 1
            print("finish %s file" % (i))
        print("finish peaks")
        return None


    def basic_data_import(self):
        df = self.C2H2_information()
        for one_file in os.listdir(self.ZNF_GSE78099):
            znf_name = one_file.split("_")[1]
            # for table 1
            # znf_item = DB.Znf(entrez_id=None, gene_symbol=znf_name)
            znf_source_name = znf_name.split("-")[0]
            # print(df["Species"] == "Human" & df["Symbol"] == znf_source_name)
            df_1 = df[(df["Species"] == "Homo_sapiens") & (df["Symbol"] == znf_source_name)]
            if len(df_1) == 1:
                # print(df_1["Ensembl"].iloc[0])
                znf_item = db.getZnf(ensembl=df_1["Ensembl"].iloc[0], entrez_id=df_1["Entrez ID"].iloc[0],
                                     gene_symbol=znf_name, species="Homo_sapiens", symbol=df_1["Symbol"].iloc[0])
            else:
                znf_item = db.getZnf(gene_symbol=znf_name, symbol=znf_source_name, species="Homo_sapiens")
            # print(znf_item)
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

                # table 3
                repeat_name = row["repeat_name"]
                repeat_item = db.getRepeat(repeat_name=repeat_name)
                if repeat_item is not None:
                    repeat_item.znf.append(znf_item)
                    session.add(repeat_item)
                    session.flush()


                # table 5
                peak_chr = row["chr"]
                peak_start = row["start"]
                peak_end = row["end"]
                peak_strand = row["strand"]
                peak_enrichment = row["enrichment"]
                peak_znf_ensembl = "?????"

                peaks_item = DB.Peaks(chr=peak_chr, start=int(peak_start), end=int(peak_end), strand=peak_strand,
                                      enrichment=float(peak_enrichment), peakName=data_name + row["peak_name"])
                if peaks_item is not None:
                    # the chip-data can't be replicate
                    peaks_item.chip_data.append(chip_data_item)
                    session.add(peaks_item)
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









    def import_expression(self):
        cellLine_base_path = "/home/luozhihui/Project/ZF_database/data_process/expression/cell_line"
        experiment = ["E-MTAB-4729", "E-MTAB-2706", "E-MTAB-2770", "E-MTAB-3983", "E-MTAB-4101", "E-MTAB-4748",
                      "E-MTAB-6867"]
        files = ["E-MTAB-4729-query-results.tpms.tsv", "E-MTAB-2706-query-results.tpms.tsv", \
                 "E-MTAB-2770-query-results.tpms.tsv", "E-MTAB-3983-query-results.tpms.tsv", \
                 "E-MTAB-4101-query-results.tpms.tsv", "E-MTAB-4748-query-results.tpms.tsv", \
                 "E-MTAB-6867-query-results.tpms.tsv"]
        print("ensemble length: %s" % len(self.ensemble_list))
        for i in range(7):
            print("begine table %s" % files[i])
            f_path = os.path.join(cellLine_base_path, files[i])
            project = experiment[i]
            df = pd.read_table(f_path, sep="\t", header=0, comment="#")
            cell_line = json.dumps(list(df.columns[2:]))
            cell_line_item = DB.Cell_line(cell=cell_line, project=project)
            session.add_all([cell_line_item])
            session.flush()
            # df["Gene ID"].astype('str')
            # print(type(df["Gene ID"].iloc[0]))
            # print(df["Gene ID"] == self.ensemble_list[1])
            # select_S = df.loc[df["Gene ID"] == self.ensemble_list[1], df.columns[2:]]

            for ensembl in self.ensemble_list:
                select_S = df.loc[df["Gene ID"] == ensembl, df.columns[2:]]
                if select_S.empty:
                    continue
                Expre = json.dumps(list(select_S.iloc[0]))
                expre_item = DB.Expression(ensembl=ensembl, project=project, expression=Expre)
                session.add_all([expre_item])
                session.flush()
            session.commit()
            print("finish table %s" % files[i])
        return None

    def get_exon(self, df):
        exons = []
        for j in df.index:
            exon = dict(df.ix[j])
            for k, v in exon.items():
                if isinstance(v, numpy.int64):
                    exon[k] = int(exon[k])
            del exon['ensembl_transcript_id']
            exons.append(exon)
        return exons

    def import_gene_structure(self):
        print("begin table gene structure")
        Transcripts = pd.read_csv(
            "/home/luozhihui/Project/ZF_database/data_process/gene_structure/humangene_structures.csv").fillna("")
        exons = pd.read_csv(
            "/home/luozhihui/Project/ZF_database/data_process/gene_structure/humanTranscript_exon.csv").fillna("")
        # for ensembl_gene_id in Transcripts['ensembl_gene_id'].drop_duplicates():
        for ensembl_gene_id in self.ensemble_list:
            structures = Transcripts.loc[Transcripts['ensembl_gene_id'] == ensembl_gene_id]
            records = []
            for Transcript in structures.index:
                record = dict(structures.ix[Transcript])
                for k, v in record.items():
                    if isinstance(v, numpy.int64):
                        record[k] = int(record[k])
                del record['ensembl_gene_id']
                record['exons'] = self.get_exon(
                    exons.loc[exons['ensembl_transcript_id'] == record["ensembl_transcript_id"]])
                records.append(record)
            result = {"ensembl_gene_id": ensembl_gene_id, "Transcripts": records}
            # print(result)
            structure = json.dumps(result)
            structure_item = DB.Gene_structure(ensembl=ensembl_gene_id, structure=structure)
            session.add_all([structure_item])
            session.flush()
            print("one gene")
        session.commit()
        print("finish table gene structure")
        return None

    def import_orthologs(self):
        print("begin table orthologs")
        Transcripts = pd.read_csv(
            "/home/luozhihui/Project/ZF_database/data_process/orthologs/9606gene_homolog.csv").fillna("")
        for ensembl_gene_id in self.ensemble_list:
            orthologs = Transcripts.loc[Transcripts['ensembl_gene_id'] == ensembl_gene_id]
            for index, row in orthologs.iterrows():
                orthologs_item = DB.Orthologs(ensembl=row["ensembl_gene_id"], Scientific_name=row["Scientific_name"], \
                                              ortholog_external_gene_name=row["ortholog_external_gene_name"], \
                                              ortholog=row["ortholog"], homolog_perc_id=row["homolog_perc_id"], \
                                              homolog_perc_id_r1=row["homolog_perc_id_r1"],
                                              homolog_wga_coverage=row["homolog_wga_coverage"], \
                                              homolog_orthology_confidence=row["homolog_orthology_confidence"])
                session.add_all([orthologs_item])
                session.flush()
            #print("one gene")
        session.commit()
        print("finish table orthologs")
        return None


if __name__ == "__main__":
    db.dropAll()
    #DB.Znf.__table__.drop(db.engine)
    db.CreateAllTable()

    importData = import_data()
    session = db.SessionUp()

    importData.C2H2_information()
    importData.import_basic_information()
    importData.import_repeat()
    importData.import_peaks()
    importData.import_expression()
    importData.import_gene_structure()
    importData.import_orthologs()

