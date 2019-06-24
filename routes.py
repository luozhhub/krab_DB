from flask import Flask, render_template, redirect, json, url_for, jsonify, request
import pandas as pd
from random import choice
from app import app
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

import sys

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


@app.route('/KZFP/zinc_fingure/<znf_id>', methods=['GET'])
def kzfp_one(znf_id):
    znf = session.query(DB.Znf).filter_by(id=znf_id).first()
    znf_data = {}
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

    return render_template("one_znf.html", znf_data=znf_data, hi_data=hightchart_list)


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
    handle = open("./app/static/znf_summary.table", "r")
    handle.readline()
    data = []
    i = 0
    for line in handle:
        i = i + 1
        array = line.strip("\n").split("\t")
        d = {"znf_id": str(i), "znf_name": array[0], "data_no": array[1], "data_source": array[2],
             "peak_number": array[3], \
             "repeat_number": array[4], "motif_all_img_path": array[5]}
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
