/* ============================================================
 * app.js — 主控制器：导航 / 模板库 / 设计 / 填写打印 / 导入导出
 * 依赖：Store, Fields, Importer, Editor, Printer
 * ========================================================== */
(function () {
  'use strict';

  var state = { view: 'home', current: null, tplList: [], dirty: false, fillTable: {}, batchExcel: null };

  /* ---------- 工具 ---------- */
  function $(s, r) { return (r || document).querySelector(s); }
  function $all(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function toast(msg, type) {
    var t = $('#toast');
    t.textContent = msg;
    t.className = 'toast show ' + (type || '');
    clearTimeout(t._tm);
    t._tm = setTimeout(function () { t.className = 'toast'; }, 2200);
  }
  function fmtDate(ts) {
    if (!ts) return '';
    var d = new Date(ts);
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }

  /* ---------- 视图切换 ---------- */
  function show(view) {
    state.view = view;
    $all('.nav-tab').forEach(function (b) { b.classList.toggle('active', b.getAttribute('data-view') === view); });
    $('#homeView').style.display = view === 'home' ? 'block' : 'none';
    $('#designView').style.display = view === 'design' ? 'block' : 'none';
    $('#fillView').style.display = view === 'fill' ? 'block' : 'none';
    if (view === 'home') renderHome();
  }

  /* ---------- 侧边栏模板列表 ---------- */
  function renderSidebar() {
    state.tplList = Store.all();
    var list = $('#tplList');
    list.innerHTML = '';
    if (!state.tplList.length) {
      list.innerHTML = '<li class="empty">尚无模板。点击右上角「📄 导入 Word 建模板」，上传即可使用。</li>';
      return;
    }
    state.tplList.forEach(function (t) {
      var li = document.createElement('li');
      li.className = 'tpl-item';
      li.innerHTML =
        '<div class="ti-main"><div class="ti-name">' + Fields.esc(t.name || '未命名') + '</div>' +
        '<div class="ti-meta">' + (t.fields ? t.fields.length : 0) + ' 字段 · ' + fmtDate(t.updatedAt) + '</div></div>' +
        '<div class="ti-actions">' +
          '<button class="mini-btn" data-act="design" title="编辑设计">设计</button>' +
          '<button class="mini-btn" data-act="fill" title="填写并打印">打印</button>' +
        '</div>';
      li.querySelector('[data-act="design"]').addEventListener('click', function (e) {
        e.stopPropagation(); openDesign(t.id);
      });
      li.querySelector('[data-act="fill"]').addEventListener('click', function (e) {
        e.stopPropagation(); openFill(t.id);
      });
      li.addEventListener('click', function () { openFill(t.id); });
      list.appendChild(li);
    });
  }

  /* ---------- 首页（模板库） ---------- */
  function renderHome() {
    renderSidebar();
    var grid = $('#homeGrid');
    grid.innerHTML = '';
    if (!state.tplList.length) {
      grid.innerHTML = '<div class="empty-state">还没有模板。<br>点右上角「📄 导入 Word 建模板」→ 上传 .docx 文件（含 {{字段名}} 占位符）→ <b>自动保存并进入填写页</b>，无需任何配置即可使用。</div>';
      return;
    }
    state.tplList.forEach(function (t) {
      var card = document.createElement('div');
      card.className = 'tpl-card';
      card.innerHTML =
        '<div class="tc-head"><span class="tc-name">' + Fields.esc(t.name || '未命名') + '</span></div>' +
        '<div class="tc-desc">' + Fields.esc(t.description || '（无说明）') + '</div>' +
        '<div class="tc-tags"><span class="tag">' + (t.settings ? t.settings.pageSize : 'A4') + '</span>' +
          '<span class="tag">' + (t.fields ? t.fields.length : 0) + ' 字段</span></div>' +
        '<div class="tc-foot">' +
          '<button class="btn primary sm" data-act="fill">填写打印</button>' +
          '<button class="btn sm" data-act="design">设计</button>' +
          '<button class="btn sm danger" data-act="del">删除</button>' +
        '</div>';
      card.querySelector('[data-act="fill"]').addEventListener('click', function (e) { e.stopPropagation(); openFill(t.id); });
      card.querySelector('[data-act="design"]').addEventListener('click', function (e) { e.stopPropagation(); openDesign(t.id); });
      card.querySelector('[data-act="del"]').addEventListener('click', function (e) {
        e.stopPropagation();
        if (confirm('确认删除模板「' + (t.name || '未命名') + '」？')) {
          Store.remove(t.id); renderHome(); toast('已删除');
        }
      });
      grid.appendChild(card);
    });
  }

  /* ---------- 设计视图 ---------- */
  function openDesign(id) {
    var tpl = id ? Store.get(id) : null;
    show('design');
    if (tpl) Editor.load(tpl); else Editor.blank();
    state.current = tpl;
    state.dirty = false;
  }
  function saveDesign() {
    var tpl = Editor.collect();
    if (!tpl.name) { toast('请填写模板名称', 'err'); $('#designView').querySelector('#tplName').focus(); return; }
    // 校验必填字段值？设计阶段不校验填值
    Store.upsert(tpl);
    state.current = tpl;
    state.dirty = false;
    renderSidebar();
    toast('模板已保存');
  }

  /* ---------- 填写 / 打印视图 ---------- */
  function openFill(id) {
    var tpl = Store.get(id);
    if (!tpl) { toast('模板不存在', 'err'); return; }
    state.current = tpl;
    state.fillTable = {};
    show('fill');
    buildFillView(tpl);
  }

  function buildFillView(tpl) {
    var wrap = $('#fillMain');
    var fields = tpl.fields || [];
    var formHtml = '<div class="fill-form"><div class="card"><div class="card-title">填写可变字段</div>';
    if (!fields.length) {
      formHtml += '<p class="hint">该模板没有定义可变字段，将直接打印固定内容。</p>';
    }
    fields.forEach(function (f) {
      formHtml += '<div class="ff-row">';
      formHtml += '<label class="ff-label">' + Fields.esc(f.label) + (f.required ? ' <span class="req">*</span>' : '') +
        ' <span class="ff-key">{' + Fields.esc(f.key) + '}</span></label>';
      if (f.type === 'table') {
        formHtml +=
          '<div class="ff-tip"><b>方式一：</b>上传 Excel/CSV（首行为表头）</div>' +
          '<input type="file" class="ff-file" data-key="' + f.key + '" accept=".xlsx,.xls,.csv">' +
          '<div class="ff-tip" style="margin-top:6px"><b>方式二（更快）：</b>在 Excel/WPS 里选中数据区复制（Ctrl+C），然后<b>点击下方框</b>按 Ctrl+V 粘贴；需为 <b>Tab 分隔</b>（Excel 默认复制格式），首行为表头。</div>' +
          '<textarea class="inp ff-paste" data-key="' + f.key + '" rows="4" placeholder="点击此处按 Ctrl+V 粘贴…"></textarea>' +
          '<div class="ff-table-preview" data-prev="' + f.key + '"></div>';
      } else if (f.type === 'select') {
        var opts = (f.options || []).map(function (o) {
          return '<option value="' + Fields.esc(o) + '">' + Fields.esc(o) + '</option>';
        }).join('');
        formHtml += '<select class="inp ff-input" data-key="' + f.key + '"><option value="">— 请选择 —</option>' + opts + '</select>';
      } else if (f.type === 'date') {
        formHtml += '<input type="date" class="inp ff-input" data-key="' + f.key + '" value="' + Fields.esc(f.default || '') + '">';
      } else if (f.type === 'number') {
        formHtml += '<input type="number" class="inp ff-input" data-key="' + f.key + '" value="' + Fields.esc(f.default || '') + '" placeholder="数值">';
      } else {
        formHtml += '<input type="text" class="inp ff-input" data-key="' + f.key + '" value="' + Fields.esc(f.default || '') + '" placeholder="文本">';
      }
      formHtml += '</div>';
    });

    // 批量生成
    var hasScalar = fields.some(function (f) { return f.type !== 'table'; });
    formHtml += '</div>';
    if (hasScalar) {
      formHtml += '<div class="card"><div class="card-title">批量生成（可选）</div>' +
        '<label class="chk"><input type="checkbox" id="batchChk"> 使用 Excel 批量生成（每行 = 一份文档）</label>' +
        '<div id="batchBox" style="display:none;margin-top:8px">' +
          '<input type="file" id="batchFile" accept=".xlsx,.xls,.csv">' +
          '<div class="ff-tip">Excel 首行为表头，需与字段标签/key 对应；每一行生成一份打印页。</div>' +
        '</div></div>';
    }
    formHtml += '</div>';

    wrap.innerHTML = formHtml;

    // 绑定标量输入 → 实时预览
    $all('.ff-input', wrap).forEach(function (el) {
      el.addEventListener('input', schedulePreview);
      el.addEventListener('change', schedulePreview);
    });
    // 表格上传
    $all('.ff-file', wrap).forEach(function (el) {
      el.addEventListener('change', function () {
        var key = el.getAttribute('data-key');
        var file = el.files[0];
        if (!file) return;
        Importer.importExcel(file).then(function (data) {
          state.fillTable[key] = { headers: data.headers, rows: data.rows };
          var prev = wrap.querySelector('[data-prev="' + key + '"]');
          if (prev) prev.innerHTML = '<div class="mini-table">已载入 ' + data.rows.length + ' 行 × ' +
            data.headers.length + ' 列：' + Fields.esc(data.headers.join(' / ')) + '</div>';
          schedulePreview();
          toast('表格数据已载入');
        }).catch(function (e) { alert('Excel 读取失败：' + e.message); });
      });
    });
    // 表格粘贴（从 Excel/WPS 直接复制）
    $all('.ff-paste', wrap).forEach(function (el) {
      el.addEventListener('input', function () {
        var key = el.getAttribute('data-key');
        var text = el.value;
        if (!text || !text.trim()) return;
        var parsed = parsePastedTable(text);
        var prev = wrap.querySelector('[data-prev="' + key + '"]');
        if (!parsed || !parsed.headers.length) {
          if (prev) prev.innerHTML = '<div class="mini-table" style="color:#c00">未识别到有效数据，请确认首行为表头、单元格用 Tab 分隔（Excel 默认）。</div>';
          return;
        }
        state.fillTable[key] = parsed;
        if (prev) prev.innerHTML = '<div class="mini-table">已从剪贴板载入 ' + parsed.rows.length + ' 行 × ' +
          parsed.headers.length + ' 列：' + Fields.esc(parsed.headers.join(' / ')) + '</div>';
        el.value = '';
        schedulePreview();
        toast('已从粘贴内容载入 ' + parsed.rows.length + ' 行');
      });
    });
    // 批量
    var batchChk = $('#batchChk');
    if (batchChk) {
      batchChk.addEventListener('change', function () {
        $('#batchBox').style.display = this.checked ? 'block' : 'none';
      });
      $('#batchFile').addEventListener('change', function () {
        var file = this.files[0];
        if (!file) return;
        Importer.importExcel(file).then(function (data) {
          state.batchExcel = data;
          toast('批量数据源已载入（' + data.rows.length + ' 行）');
        }).catch(function (e) { alert('Excel 读取失败：' + e.message); });
      });
    }

    schedulePreview();
  }

  /** 解析从 Excel/WPS 粘贴的 Tab 分隔文本为表头+数据行 */
  function parsePastedTable(text) {
    var lines = String(text || '').replace(/\r/g, '').split('\n');
    if (!lines.length) return null;
    // 过滤完全空白的行（首尾空行）
    var rowsRaw = lines.map(function (l) { return l.split('\t'); });
    var firstNonEmpty = -1;
    for (var i = 0; i < rowsRaw.length; i++) {
      if (rowsRaw[i].some(function (c) { return (c || '').trim() !== ''; })) { firstNonEmpty = i; break; }
    }
    if (firstNonEmpty < 0) return null;
    // 用第一个非空行作为表头
    var headers = rowsRaw[firstNonEmpty].map(function (h) { return (h == null ? '' : String(h)).trim(); });
    var dataRows = [];
    for (var j = firstNonEmpty + 1; j < rowsRaw.length; j++) {
      var r = rowsRaw[j];
      if (!r.some(function(c) { return (c || '').trim() !== ''; })) continue;
      // 与表头等长
      var out = [];
      for (var k = 0; k < headers.length; k++) out.push(r[k] != null ? String(r[k]) : '');
      dataRows.push(out);
    }
    return { headers: headers, rows: dataRows };
  }

  function gatherValues() {
    var tpl = state.current;
    var vals = {};
    $all('.ff-input', $('#fillMain')).forEach(function (el) {
      vals[el.getAttribute('data-key')] = el.value;
    });
    // 表格数据
    Object.keys(state.fillTable).forEach(function (k) { vals[k] = state.fillTable[k]; });
    return vals;
  }

  var previewTimer = null;
  function schedulePreview() {
    clearTimeout(previewTimer);
    previewTimer = setTimeout(function () {
      if (!state.current) return;
      var vals = gatherValues();
      Printer.showPreview($('#previewFrame'), state.current, vals);
    }, 200);
  }

  function doPrint() {
    var tpl = state.current;
    if (!tpl) return;
    if ($('#batchChk') && $('#batchChk').checked && state.batchExcel) {
      var list = buildBatchValues(tpl);
      if (!list.length) { toast('批量数据为空', 'err'); return; }
      // 逐行校验：仅生成无误行，错误行跳过并提示
      var results = Validation.validateBatchStructured(tpl.fields, list);
      var clean = list.filter(function (v, i) { return !results[i].errors.length; });
      var errCount = results.reduce(function (a, r) { return a + r.errors.length; }, 0);
      if (!clean.length) { toast('全部 ' + errCount + ' 处校验未通过，未生成', 'err'); return; }
      if (errCount) toast('已跳过 ' + (list.length - clean.length) + ' 行（共 ' + errCount + ' 处错误）');
      Printer.printMulti(tpl, clean);
      toast('已发送 ' + clean.length + ' 份到打印');
    } else {
      var vals = gatherValues();
      // 字段校验（必填 + 数据类型 + 校验规则）
      var errs = Validation.validateRecord(tpl.fields, vals);
      if (errs.length) { toast('校验未通过：' + errs.join('；'), 'err'); return; }
      Printer.printOne(tpl, vals);
      toast('已发送到打印');
    }
  }

  function buildBatchValues(tpl) {
    var data = state.batchExcel;
    var headers = data.headers;
    var out = [];
    // 字段→列索引映射（先按 label，再按 key）
    var map = {};
    (tpl.fields || []).forEach(function (f) {
      if (f.type === 'table') return;
      var idx = headers.indexOf(f.label);
      if (idx < 0) idx = headers.indexOf(f.key);
      if (idx >= 0) map[f.key] = idx;
    });
    data.rows.forEach(function (r) {
      var vals = {};
      Object.keys(map).forEach(function (k) { vals[k] = r[map[k]] != null ? String(r[map[k]]) : ''; });
      // 表格字段（如有）统一应用
      Object.keys(state.fillTable).forEach(function (k) { vals[k] = state.fillTable[k]; });
      // 未映射字段用默认值
      (tpl.fields || []).forEach(function (f) {
        if (f.type === 'table') return;
        if (vals[f.key] === undefined && f.default) vals[f.key] = f.default;
      });
      out.push(vals);
    });
    return out;
  }

  /* ---------- Word 导入（上传即用，无需手动改动） ---------- */
  /** 根据占位符名称智能推断字段类型 */
  function guessFieldType(k) {
    if (/名单|明细|清单|列表|表$|表数据|数据|记录|花名册|list|detail|item|table|data|rows/i.test(k)) return 'table';
    if (/日期|时间|date|time/i.test(k)) return 'date';
    if (/数量|金额|编号|年龄|数量|num|qty|amount|age/i.test(k)) return 'number';
    return 'text';
  }
  /** 智能推断是否必填（姓名/日期/编号/班级等关键字段默认必填） */
  function guessFieldRequired(k) {
    return /姓名|名字|日期|时间|学号|编号|班级|name|date|time|no|id/i.test(k);
  }
  function importWord() {
    var inp = document.createElement('input');
    inp.type = 'file'; inp.accept = '.docx';
    inp.addEventListener('change', function () {
      var file = inp.files[0];
      if (!file) return;
      toast('正在解析 Word…');
      Importer.importWord(file).then(function (res) {
        if (!res.tokens.length) {
          toast('未识别到 {{字段}} 占位符，请在 Word 里用 {{字段名}} 标记需要替换的内容', 'err');
          return;
        }
        var fields = res.tokens.map(function (k) {
          return {
            key: k,
            label: k,
            type: guessFieldType(k),
            default: '',
            required: guessFieldRequired(k),
            validation: {}
          };
        });
        var tpl = {
          name: file.name.replace(/\.docx$/i, ''),
          description: '由 Word 上传自动创建，共 ' + fields.length + ' 个字段。',
          settings: { pageSize: 'A4', orientation: 'portrait', marginTop: 15, marginRight: 15, marginBottom: 15, marginLeft: 15,
            fontFamily: "'Microsoft YaHei', 'PingFang SC', sans-serif", fontSize: 14, lineHeight: 1.6,
            headerText: '', headerAlign: 'center', footerText: '', footerAlign: 'center', tableBorder: true },
          fields: fields,
          content: res.html
        };
        Store.upsert(tpl);
        renderSidebar();
        renderHome();
        toast('模板已保存：' + tpl.name + '（' + fields.length + ' 字段），可直接填写');
        // 直接进入填写 / 打印页 —— 无需经过设计器
        openFill(tpl.id);
      }).catch(function (e) { alert('Word 导入失败：' + e.message); });
    });
    inp.click();
  }

  /* ---------- 示例模板（首次使用时注入） ---------- */
  function seedSampleIfEmpty() {
    if (Store.all().length) return;
    var sample = {
      name: '发货单（示例）',
      description: '演示模板：含文本、日期、表格等字段，可修改或另存。',
      settings: { pageSize: 'A4', orientation: 'portrait', marginTop: 18, marginRight: 16, marginBottom: 18, marginLeft: 16,
        fontFamily: "'Microsoft YaHei', 'PingFang SC', sans-serif", fontSize: 14, lineHeight: 1.6,
        headerText: '示例贸易有限公司', headerAlign: 'center', footerText: '', footerAlign: 'center', tableBorder: true },
      fields: [
        { key: 'customer', label: '客户名称', type: 'text', default: '', required: true },
        { key: 'date', label: '日期', type: 'date', default: '', required: true },
        { key: 'order_no', label: '单号', type: 'text', default: '' },
        { key: 'phone', label: '联系电话', type: 'text', default: '' },
        { key: 'address', label: '收货地址', type: 'text', default: '' },
        { key: 'items', label: '商品明细', type: 'table', default: '' },
        { key: 'remark', label: '备注', type: 'text', default: '' },
        { key: 'operator', label: '制单人', type: 'text', default: '' }
      ],
      content:
        '<h2 style="text-align:center;margin:4px 0">发 货 单</h2>' +
        '<table style="width:100%;border-collapse:collapse;margin:8px 0;font-size:13px">' +
          '<tr><td style="padding:4px 6px">客户名称：{{customer}}</td><td style="padding:4px 6px">日期：{{date}}</td></tr>' +
          '<tr><td style="padding:4px 6px">单号：{{order_no}}</td><td style="padding:4px 6px">联系电话：{{phone}}</td></tr>' +
        '</table>' +
        '<p style="margin:4px 0">收货地址：{{address}}</p>' +
        '<h3 style="margin:8px 0 4px">商品明细</h3>' +
        '{{items}}' +
        '<p style="margin:8px 0 4px">备注：{{remark}}</p>' +
        '<p style="text-align:right;margin:10px 0">制单人：{{operator}}</p>'
    };
    Store.upsert(sample);
  }

  /* ---------- 同步状态条 ---------- */
  function setSyncStatus() {
    var el = $('#syncStatus');
    if (!el) return;
    var st = (window.Cloud && window.Cloud.status) || 'local';
    var map = {
      local:     { t: '● 本地',      c: 'ss-local' },
      connecting:{ t: '● 连接中…',   c: 'ss-busy' },
      online:    { t: '● 已云同步',  c: 'ss-online' },
      offline:   { t: '● 离线(本地)', c: 'ss-offline' }
    };
    var m = map[st] || map.local;
    el.textContent = m.t;
    el.className = 'sync-status ' + m.c;
  }

  /* ---------- 初始化 ---------- */
  function init() {
    seedSampleIfEmpty();
    setSyncStatus();

    $('#navHome').addEventListener('click', function () { show('home'); });
    $('#navDesign').addEventListener('click', function () { openDesign(null); });
    $('#navFill').addEventListener('click', function () {
      if (!state.current) { toast('请先在模板库选择模板', 'err'); show('home'); return; }
      openFill(state.current.id);
    });
    $('#btnNew').addEventListener('click', function () { openDesign(null); });
    $('#btnImportWord').addEventListener('click', importWord);
    $('#btnSaveDesign').addEventListener('click', saveDesign);
    $('#btnPrint').addEventListener('click', doPrint);
    $('#btnExcelWizard').addEventListener('click', function () {
      if (!state.current) { toast('请先选择模板', 'err'); show('home'); return; }
      ExcelWizard.open(state.current);
    });
    $('#btnBackHome').addEventListener('click', function () { show('home'); });
    $('#btnFillBack').addEventListener('click', function () { show('home'); });

    Editor.init($('#designEditor'), function () { state.dirty = true; });

    // 云端同步：初始化 → 拉取云端覆盖本地 → 订阅实时变更
    Cloud.init().then(function (ok) {
      setSyncStatus();
      if (!ok) return; // 未配置/失败 → 保持本地
      Store.syncFromCloud().then(function (did) {
        if (did) { renderSidebar(); renderHome(); }
        Cloud.subscribe(function () {
          Store.syncFromCloud().then(function () { renderSidebar(); renderHome(); });
        });
        setSyncStatus();
      });
    }).catch(function () { setSyncStatus(); });

    show('home');
  }

  document.addEventListener('DOMContentLoaded', init);
})();
