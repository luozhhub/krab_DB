from flask import Flask, render_template, redirect, json, url_for, jsonify, request
import pandas as pd
from random import choice
from app import app
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from sqlalchemy import func

import sys,os

sys.path.insert(0, "/home/luozhihui/PycharmProjects/ZNFdatabase")
import ZFWebDatabase as DB
import pandas as pd

db = DB.AccurityWebDB("luozh", "luozh123", "ZNFdb", hostname="localhost")
db.Connect()
session = db.SessionUp()


@app.route('/')
@app.route('/index/')
def index():
    return render_template("index.html")


@app.route('/Help/')
def help():
    return render_template("help.html")


@app.route('/About/')
def about():
    return render_template("about.html")


@app.route('/Expression/')
def expression():
    return render_template("expression.html")

@app.route('/Download/')
def download():
    return render_template("Download.html")


@app.route('/KZFP/')
def kzfp():
    form = searchZnfForm()
    return render_template("KZFP.html", form=form)


class searchZnfForm(FlaskForm):
    znfSymbol = StringField("znfSymbol", validators=[DataRequired()])
    submit = SubmitField('Search')


class searchRepeatForm(FlaskForm):
    repeatSymbol = StringField("repeatSymbol", validators=[DataRequired()])
    submit = SubmitField('Search')


@app.route('/Repeat/')
def repeat_page():
    form = searchRepeatForm()
    return render_template("Repeat.html", form=form)


@app.route('/searchZnf', methods=['GET', 'POST'])
def searchZnf():
    form = searchZnfForm()
    if form.validate_on_submit():
        # print(request.form.get('znfSymbol'))
        zz = request.form.get('znfSymbol')
        znf_item = session.query(DB.Znf).filter_by(gene_symbol=zz).first()
        if znf_item is None:
            return render_template("No_result.html")
        else:
            id = znf_item.id
            # return redirect(url_for('/KZFP/zinc_fingure/%s' % id))
            return kzfp_one(id)


@app.route('/searchRepeat', methods=['GET', 'POST'])
def searchRepeat():
    form = searchRepeatForm()
    if form.validate_on_submit():
        # print(request.form.get('znfSymbol'))
        zz = request.form.get('repeatSymbol')
        znf_item = session.query(DB.Repeat).filter_by(gene_symbol=zz).first()
        if znf_item is None:
            return render_template("No_result.html")
        else:
            id = znf_item.id
            # return redirect(url_for('/KZFP/zinc_fingure/%s' % id))
            return repeat_one(id)


@app.route('/KZFP/zinc_fingure/<data_name>', methods=['GET'])
def kzfp_one(data_name):
    #data_name = "GSM2466491"
    chip_data = session.query(DB.Chip_data).filter_by(data_name=data_name).first()
    znf = session.query(DB.Znf).filter_by(id=chip_data.znf_id).first()
    znf_data = {}
    ensembl = znf.ensembl

    znf_data["ensembl"] = znf.ensembl
    znf_data["entrez_id"] = znf.entrez_id
    znf_data["species"] = znf.species
    znf_data["gene_symbol"] = znf.gene_symbol
    znf_data["family"] = znf.family
    znf_data["proteins"] = znf.proteins
    znf_data["gene_synonym"] = znf.gene_synonym
    znf_data["unipro_feature"] = json.loads(znf.unipro_feature)

    znf_data["data_name"] = chip_data.data_name
    znf_data["data_source"] = chip_data.data_source
    znf_data["peak_number"] = chip_data.peak_number
    znf_data["repeat_number"] = chip_data.repeat_number


    znf_data["img_base_path"] = "/static/img/%s_out/%s_%s/" % (
        znf_data["data_source"], znf_data["data_name"], znf_data["gene_symbol"])
    znf_data["score"] = {}
    for one_type in ["raw", "part", "none", "full"]:
        score_file_path = "./app/static/img/%s_out/%s_%s/%s/score" % (
        znf_data["data_source"], znf_data["data_name"], znf_data["gene_symbol"], one_type)
        print(score_file_path)
        if os.path.exists(score_file_path):
            handle = open(score_file_path,"r")
            array = handle.readline().strip("\n").split("\t")
            znf_data["score"][one_type] = array
            handle.close()
        else:
            znf_data["score"][one_type] = ["", "", ""]



    all_repeats = session.query(func.count(DB.Peaks.repeat_repeat_name) , DB.Peaks.repeat_repeat_name).filter_by(chip_data_data_name=data_name).group_by(DB.Peaks.repeat_repeat_name).all()
    hightchart_list = []
    overlapped_peaks = 0
    for repea in all_repeats:
        overlapped_peaks = overlapped_peaks + repea[0]
        hightchart_list.append([repea[1], repea[0]])
    znf_data["overlapped_peaks"] = overlapped_peaks

    #expression
    expression_item = session.query(DB.Expression).filter_by(ensembl=ensembl, project="E-MTAB-4748").first()
    cell_line_item = session.query(DB.Cell_line).filter_by(project="E-MTAB-4748").first()
    if expression_item is None:
        expres = None
    else:
        expres = expression_item.expression


    # gene structure
    structures_item = session.query(DB.Gene_structure).filter_by(ensembl=ensembl).first()
    structures = json.loads(structures_item.structure)
    gene_start = structures["Transcripts"][0]["start_position"]
    gene_end = structures["Transcripts"][0]["end_position"]
    gene_length = gene_end - gene_start
    transcription = []
    for transcript in structures["Transcripts"]:
        transcription.append(
            {"exon": transcript["exons"], "ensembl_transcript_id": transcript["ensembl_transcript_id"]})
    gap = gene_length / 10
    svgs = ''
    scale = '<svg width="980" height="30" xmlns="http://www.w3.org/2000/svg">\n'
    scale = scale + '<line x1="0" y1="50%" x2="800" y2="50%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="0" y1="60%" x2="0" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="80" y1="60%" x2="80" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="160" y1="60%" x2="160" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="240" y1="60%" x2="240" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="320" y1="60%" x2="320" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="400" y1="60%" x2="400" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="480" y1="60%" x2="480" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="560" y1="60%" x2="560" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="640" y1="60%" x2="640" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="720" y1="60%" x2="720" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="800" y1="60%" x2="800" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<text x="0" y="8" font-family="Verdana" font-size="10">' + str(
        round(gene_start / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="80" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 1) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="160" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 2) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="240" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 3) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="320" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 4) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="400" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 5) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="480" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 6) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="560" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 7) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="640" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 8) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="720" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 9) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="800" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 10) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '</svg>\n'
    svgs = svgs + scale
    for i in transcription:
        svg = '<svg width="980" height="10" xmlns="http://www.w3.org/2000/svg">\n'
        polylines = '<line x1="0" y1="50%" x2="800" y2="50%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
        rects = '<g fill="#CDCD00">\n'
        for m in i['exon']:
            width = (m["exon_chrom_end"] - m["exon_chrom_start"]) / float(gene_length) * 800
            x = (m["exon_chrom_start"] - gene_start) / float(gene_length) * 800
            rect = '<rect x="' + str(x) + '" y="0" width="' + str(width) + '" height="10"></rect>\n'
            rects = rects + rect
        rects = rects + "</g>\n"
        text = '<text x="810" y="50%" dy=".3em" fill="black" font-size="12">' + i["ensembl_transcript_id"] + '</text>\n'
        svg = svg + polylines + rects + text + '</svg>\n'
        svgs = svgs + svg
    # gene_structures = {"transcript": structures["Transcripts"], "gene_model": svgs}
    gene_structures = svgs

    """
    znf_data["znf_symbol"] = znf.gene_symbol
    znf_data["data_no"] = znf.chip_data[0].data_name
    znf_data["data_source"] = znf.chip_data[0].data_source
    znf_data["peaks"] = znf.chip_data[0].peaks
    znf_data["peaks_num"] = len(znf.chip_data[0].peaks)
    znf_data["repeats"] = znf.repeat
    znf_data["repeats_num"] = len(znf.repeat)

    znf_data["motif_all_img_path"] = znf.chip_data[0].motif.znf_all_motif_img_path
    znf_data["motif_part_img_path"] = znf.chip_data[0].motif.znf_part_motif_img_path
    znf_data["motif_none_img_path"] = znf.chip_data[0].motif.znf_None_motif_img_path
    znf_data["motif_full_img_path"] = znf.chip_data[0].motif.znf_full_motif_img_path

    znf_data["motif_all_matrix_path"] = znf.chip_data[0].motif.znf_all_motif_matrix_path
    znf_data["motif_part_matrix_path"] = znf.chip_data[0].motif.znf_part_motif_matrix_path
    znf_data["motif_none_matrix_path"] = znf.chip_data[0].motif.znf_None_motif_matrix_path
    znf_data["motif_full_matrix_path"] = znf.chip_data[0].motif.znf_full_motif_matrix_path
    # print(znf_data["repeats"])
    # print (znf.repeat[0].repeat_region)
    # img_base_path = "/static/img/%s_out/%s_%s/" % (znf_data["data_source"], znf_data["data_no"], znf_data["znf_symbol"])
    znf_data["img_base_path"] = "/static/img/%s_out/%s_%s/" % (
    znf_data["data_source"], znf_data["data_no"], znf_data["znf_symbol"])

    hightchart_list = []
    print (len(znf.repeat_region))
    if len(znf.repeat_region) == 0:
        return render_template("one_znf.html", znf_data=znf_data)
    for i in range(len(znf.repeat)):
        one_repeat = znf.repeat[i]
        number = len(one_repeat.repeat_region)
        hightchart_list.append([one_repeat.repeat_name, number])
    


    #expression
    expression_item = session.query(DB.Expression).filter_by(ensembl=ensembl, project="E-MTAB-4748").first()
    cell_line_item = session.query(DB.Cell_line).filter_by(project="E-MTAB-4748").first()

    #gene structure
    structures_item = session.query(DB.Gene_structure).filter_by(ensembl=ensembl).first()
    structures = json.loads(structures_item.structure)
    gene_start = structures["Transcripts"][0]["start_position"]
    gene_end = structures["Transcripts"][0]["end_position"]
    gene_length = gene_end - gene_start
    transcription = []
    for transcript in structures["Transcripts"]:
        transcription.append(
            {"exon": transcript["exons"], "ensembl_transcript_id": transcript["ensembl_transcript_id"]})
    gap = gene_length / 10
    svgs = ''
    scale = '<svg width="980" height="30" xmlns="http://www.w3.org/2000/svg">\n'
    scale = scale + '<line x1="0" y1="50%" x2="800" y2="50%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="0" y1="60%" x2="0" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="80" y1="60%" x2="80" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="160" y1="60%" x2="160" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="240" y1="60%" x2="240" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="320" y1="60%" x2="320" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="400" y1="60%" x2="400" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="480" y1="60%" x2="480" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="560" y1="60%" x2="560" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="640" y1="60%" x2="640" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="720" y1="60%" x2="720" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<line x1="800" y1="60%" x2="800" y2="40%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
    scale = scale + '<text x="0" y="8" font-family="Verdana" font-size="10">' + str(
        round(gene_start / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="80" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 1) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="160" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 2) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="240" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 3) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="320" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 4) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="400" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 5) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="480" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 6) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="560" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 7) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="640" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 8) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="720" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 9) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '<text x="800" y="8" font-family="Verdana" font-size="10" text-anchor="middle">' + str(
        round((gene_start + gap * 10) / 1000000.0, 2)) + 'Mb' + '</text>\n'
    scale = scale + '</svg>\n'
    svgs = svgs + scale
    for i in transcription:
        svg = '<svg width="980" height="10" xmlns="http://www.w3.org/2000/svg">\n'
        polylines = '<line x1="0" y1="50%" x2="800" y2="50%" style="stroke:rgb(255,0,0);stroke-width:2" />\n'
        rects = '<g fill="#CDCD00">\n'
        for m in i['exon']:
            width = (m["exon_chrom_end"] - m["exon_chrom_start"]) / float(gene_length) * 800
            x = (m["exon_chrom_start"] - gene_start) / float(gene_length) * 800
            rect = '<rect x="' + str(x) + '" y="0" width="' + str(width) + '" height="10"></rect>\n'
            rects = rects + rect
        rects = rects + "</g>\n"
        text = '<text x="810" y="50%" dy=".3em" fill="black" font-size="12">' + i["ensembl_transcript_id"] + '</text>\n'
        svg = svg + polylines + rects + text + '</svg>\n'
        svgs = svgs + svg
    #gene_structures = {"transcript": structures["Transcripts"], "gene_model": svgs}
    gene_structures = svgs

    """


    #return render_template("one_znf.html", znf_data=znf_data, hi_data=hightchart_list, expre=expression_item.expression,\
    #                       cell_line=cell_line_item.cell, svg_code=gene_structures)
    return render_template("oneZnf.html", znf_data=znf_data, hi_data=hightchart_list, expre=expres,\
                            cell_line=cell_line_item.cell, svg_code=gene_structures)


@app.route('/Repeat/repeat_one/<repeat_id>', methods=['GET'])
def repeat_one(repeat_id):
    repeat = session.query(DB.Repeat).filter_by(id=repeat_id).first()
    repeat_data = {}
    repeat_data["repeat_name"] = repeat.repeat_name
    repeat_data["repeat_sub_family"] = repeat.repeat_family.sub_family
    repeat_data["repeat_main_family"] = repeat.repeat_family.main_family
    repeat_data["repeat_znfs"] = len(repeat.znf)
    repeat_data["repeat_regions"] = len(repeat.repeat_region)
    repeat_data["repeat_id"] = repeat_id

    if len(repeat.znf) == 0:
        return render_template("one_repeat.html")

    highcharts_list = []

    for i in range(len(repeat.znf)):
        repeat_regions = repeat.znf[i].repeat_region
        number = len(repeat_regions)
        highcharts_list.append([repeat.znf[i].gene_symbol, number])
    return render_template("one_repeat.html", repeat_data=repeat_data, hi_data=highcharts_list)


@app.route('/repeatDataJson/', methods=['GET', 'POST'])
def repeatData():



    all_repeat = session.query(DB.Repeat_family).all()
    data = []
    for one_repeat in all_repeat:
        d = {"repeat_id": one_repeat.repeat_id, "repeat_name": one_repeat.repeat_name, \
             "sub_family": one_repeat.sub_family, "mian_family": one_repeat.main_family, \
             "repeat_region_num": len(one_repeat.repeat.repeat_region), "znf_number": len(one_repeat.repeat.znf)}
        data.append(d)
    if request.method == 'POST':
        print('post')
    if request.method == 'GET':
        info = request.values
        limit = info.get('limit', 10)  # 每页显示的条数
        offset = info.get('offset', 0)  # 分片数，(页码-1)*limit，它表示一段数据的起点
    return jsonify({'total': len(data), 'rows': data[int(offset):(int(offset) + int(limit))]})


@app.route('/oneRepeatDataJson/<repeat_id>', methods=['GET', 'POST'])
def oneRepeatDataJson(repeat_id):
    repeat = session.query(DB.Repeat).filter_by(id=repeat_id).first()
    data = []
    n = 0
    for i in range(len(repeat.repeat_region)):
        n = n + 1
        region = repeat.repeat_region[i]
        d = {"id": str(n), "chr": region.chr, "start": region.start, "end": region.end,
             "znf_name": region.znf[0].gene_symbol}
        data.append(d)
    if request.method == 'POST':
        print('post')
    if request.method == 'GET':
        info = request.values
        print(info)
        limit = info.get('limit', 10)  # 每页显示的条数
        offset = info.get('offset', 0)  # 分片数，(页码-1)*limit，它表示一段数据的起点
        print('get', limit)
        print('get  offset', offset)
        return jsonify({'total': len(data), 'rows': data[int(offset):(int(offset) + int(limit))]})


@app.route('/kzpfdatajson/', methods=['GET', 'POST'])
def kzfpData():
    data = []
    chip_data = session.query(DB.Chip_data).all()

    i = 0
    for chip in chip_data:
        i = i + 1
        d = {"znf_id": str(i), "znf_name": chip.znf.gene_symbol, "data_no": chip.data_name, "data_source": chip.data_source,
        "peak_number": chip.peak_number, "repeat_number": chip.repeat_number, "motif_all_img_path": "aaa"}
        data.append(d)

    if request.method == 'POST':
        print('post')
    if request.method == 'GET':
        info = request.values
        print(info)
        limit = info.get('limit', 10)  # 每页显示的条数
        offset = info.get('offset', 0)  # 分片数，(页码-1)*limit，它表示一段数据的起点
        print('get', limit)
        print('get  offset', offset)

        return jsonify({'total': len(data), 'rows': data[int(offset):(int(offset) + int(limit))]})
        # 注意total与rows是必须的两个参数，名字不能写错，total是数据的总长度，rows是每页要显示的数据,它是一个列表
        # 前端根本不需要指定total和rows这俩参数，他们已经封装在了bootstrap table里了


@app.route('/znf_summary_json', methods=['GET', 'POST'])
def query():
    """
    print url_for('hello_world')   #可以获取hello_world函数的路由
    row=[{'字段一':'value1','字段二':'value2'},{'字段一':'value3','字段二':'value4'}]
    result = json.dumps(row)
    return result
    """

    db = DB.AccurityWebDB("luozh", "luozh123", "ZNFdb", hostname="localhost")
    db.Connect()
    session = db.SessionUp()
    all_znf = session.query(DB.Znf).all()
    df = pd.DataFrame(
        columns=["znf_name", "data_no", "data_source", "peak_number", "repeat_number", "motif_all_img_path"])
    print(df)
    data_json = []
    for item in all_znf:
        znf_name = item.gene_symbol
        data_no = item.chip_data[0].data_name
        data_source = item.chip_data[0].data_source
        peak_number = len((item.chip_data[0].peaks))
        repeat_number = len(item.repeat)
        motif_all_img_path = item.chip_data[0].motif.znf_all_motif_img_path

    ser = pd.Series([znf_name, data_no, data_source, peak_number, repeat_number, motif_all_img_path], \
                    index=["znf_name", "data_no", "data_source", "peak_number", "repeat_number",
                           "motif_all_img_path"])
    # print(ser)
    # df = df.append(ser, ignore_index=True)
    dd = dict(znf_name=znf_name, data_no=data_no, data_source=data_source, peak_number=peak_number, \
              repeat_number=repeat_number, motif_all_img_path=motif_all_img_path)
    data_json.append(dd)
    return json.dumps(
        [{"znf_name": znf_name, "data_no": data_no, "data_source": data_source, "peak_number": peak_number, \
          "repeat_number": repeat_number, "motif_all_img_path": motif_all_img_path}, \
         {"znf_name": znf_name, "data_no": data_no, "data_source": data_source, "peak_number": peak_number, \
          "repeat_number": repeat_number, "motif_all_img_path": motif_all_img_path}])


@app.route('/searchorthologs', methods=['GET', 'POST'])
def api_searchorthologs():
    ensembl = request.values["ensembl"]
    orthologs_items = session.query(DB.Orthologs).filter_by(ensembl=ensembl)
    msgs = []
    for item in orthologs_items:
        msgs.append(item.returnDict())
        # msgs.append(item.json)
    # jData = json.dumps(msgs)
    jData = {"total": len(msgs), "rows": msgs}
    return json.dumps(jData)