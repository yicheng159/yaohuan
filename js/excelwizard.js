/* ============================================================
 * excelwizard.js — Excel 数据导入向导（图形化、零代码）
 * 全局对象：ExcelWizard
 * 流程：上传 Excel → 自动映射列到模板标量字段（可手动改）
 *      → 数据预览 + 逐行校验 + 错误提示 → 仅生成无误的行
 * 依赖：Importer, Validation, Printer, Fields
 * ========================================================== */
(function (global) {
  'use strict';

  var modal, body, closeBtn;
  var state = { tpl: null, data: null, map: [] };

  function $(s) { return body.querySelector(s); }

  function open(tpl) {
    if (!tpl) return;
    state = { tpl: tpl, data: null, map: [] };
    if (!modal) { modal = document.getElementById('excelModal'); body = document.getElementById('excelBody'); closeBtn = document.getElementById('excelClose'); }
    modal.style.display = 'flex';
    renderUpload();
  }
  function close() {
    if (modal) modal.style.display = 'none';
    state = { tpl: null, data: null, map: [] };
  }

  /* ---------- 步骤 1：上传 ---------- */
  function renderUpload() {
    body.innerHTML =
      '<div class="wz-step">第 1 步 / 共 3 步 · 选择 Excel 文件</div>' +
      '<div class="wz-upload">' +
        '<input type="file" id="wzFile" accept=".xlsx,.xls,.csv" class="inp">' +
        '<div class="ff-tip">支持 .xlsx / .xls / .csv。第一行需为<b>表头</b>（列名），后续每一行将生成一份文档。表头会尽量自动匹配模板字段。</div>' +
        '<div class="wz-status" id="wzStatus"></div>' +
      '</div>';
    var inp = $('#wzFile');
    inp.addEventListener('change', function () {
      var file = inp.files[0];
      if (!file) return;
      var st = $('#wzStatus');
      if (st) st.textContent = '正在解析「' + file.name + '」…';
      global.Importer.importExcel(file).then(function (data) {
        state.data = data;
        if (!data.headers.length) { alert('未识别到表头，请确认第一行是列名。'); if (st) st.textContent = ''; return; }
        autoMatch();
        renderMapping();
      }).catch(function (e) { alert('Excel 读取失败：' + e.message); if (st) st.textContent = ''; });
    });
  }

  /* ---------- 自动映射：表头 → 标量字段 ---------- */
  function autoMatch() {
    var scalar = (state.tpl.fields || []).filter(function (f) { return f.type !== 'table'; });
    state.map = state.data.headers.map(function (h) {
      var hl = String(h || '').trim().toLowerCase();
      if (!hl) return null;
      var hit = scalar.find(function (f) {
        return (f.label && f.label.trim().toLowerCase() === hl) || (f.key && f.key.toLowerCase() === hl);
      });
      if (hit) return hit.key;
      hit = scalar.find(function (f) {
        return (f.label && f.label.trim().toLowerCase().indexOf(hl) >= 0) ||
               (f.key && f.key.toLowerCase().indexOf(hl) >= 0);
      });
      if (hit) return hit.key;
      return null;
    });
  }

  /* ---------- 步骤 2：映射 ---------- */
  function renderMapping() {
    var scalar = (state.tpl.fields || []).filter(function (f) { return f.type !== 'table'; });
    var mappedCount = state.map.filter(Boolean).length;
    var fieldOpts = '<option value="">— 忽略此列 —</option>' +
      scalar.map(function (f) {
        return '<option value="' + Fields.esc(f.key) + '">' + Fields.esc(f.label) + ' (' + Fields.esc(f.key) + ')</option>';
      }).join('');

    var rows = state.data.headers.map(function (h, i) {
      var sel = '<select class="inp sm map-sel" data-col="' + i + '">' +
        fieldOpts.replace('value="' + (state.map[i] || '') + '"', 'value="' + (state.map[i] || '') + '" selected') +
        '</select>';
      return '<div class="map-row"><span class="map-col">列 <b>' + (i + 1) + '</b>：' + Fields.esc(h || '(空)') + '</span>' + sel + '</div>';
    }).join('');

    body.innerHTML =
      '<div class="wz-step">第 2 步 / 共 3 步 · 确认列与字段的对应关系（已自动匹配）</div>' +
      '<div class="wz-tip">已自动匹配 <b>' + mappedCount + '</b> / ' + scalar.length + ' 个字段，可下拉手动调整；不需要的列选「忽略」。未映射的字段将使用默认值。</div>' +
      '<div class="map-list">' + rows + '</div>' +
      (scalar.length === 0 ? '<div class="wz-warn">该模板没有可映射的标量字段（可能只有表格字段）。请改用填写页的「表格上传」来导入名单。</div>' : '') +
      '<div class="wz-actions">' +
        '<button class="btn" id="wzBack1">← 重新选择文件</button>' +
        '<button class="btn primary" id="wzNext">预览并校验 →</button>' +
      '</div>';

    $all('.map-sel').forEach(function (el) {
      el.addEventListener('change', function () {
        state.map[parseInt(el.getAttribute('data-col'), 10)] = el.value || null;
      });
    });
    $('#wzBack1').addEventListener('click', renderUpload);
    $('#wzNext').addEventListener('click', renderPreview);
  }

  function $all(s) { return Array.prototype.slice.call(body.querySelectorAll(s)); }

  /* ---------- 构建每条记录的值 ---------- */
  function buildValues() {
    var fields = (state.tpl.fields || []).filter(function (f) { return f.type !== 'table'; });
    return state.data.rows.map(function (r) {
      var vals = {};
      state.map.forEach(function (fk, ci) {
        if (fk) vals[fk] = r[ci] != null ? String(r[ci]) : '';
      });
      fields.forEach(function (f) {
        if (vals[f.key] === undefined && f.default) vals[f.key] = f.default;
      });
      return vals;
    });
  }

  /* ---------- 步骤 3：预览 + 校验 ---------- */
  function renderPreview() {
    var fields = (state.tpl.fields || []);
    var scalar = fields.filter(function (f) { return f.type !== 'table'; });
    var list = buildValues();
    var results = global.Validation.validateBatchStructured(fields, list);

    // 仅取已映射的字段用于展示
    var shownFields = scalar.filter(function (f) {
      return state.map.indexOf(f.key) >= 0;
    });

    // 错误定位：row → {key:true}
    var errByRow = {};
    var totalErr = 0;
    results.forEach(function (res) {
      if (res.errors.length) {
        errByRow[res.row] = {};
        res.errors.forEach(function (e) { errByRow[res.row][e.key] = e.message; totalErr++; });
      }
    });

    var cleanCount = results.filter(function (r) { return !r.errors.length; }).length;

    // 表头
    var thead = '<tr><th>#</th>' + shownFields.map(function (f) {
      return '<th>' + Fields.esc(f.label) + (f.required ? ' <span class="req">*</span>' : '') + '</th>';
    }).join('') + '</tr>';

    var tbody = list.map(function (vals, i) {
      var rowNum = i + 1;
      var cells = shownFields.map(function (f) {
        var msg = errByRow[rowNum] && errByRow[rowNum][f.key];
        var val = vals[f.key] != null ? vals[f.key] : '';
        return '<td class="' + (msg ? 'cell-err' : '') + '" title="' + (msg ? Fields.esc(msg) : '') + '">' + Fields.esc(val) + '</td>';
      }).join('');
      return '<tr class="' + (errByRow[rowNum] ? 'row-err' : '') + '"><td class="rownum">' + rowNum + '</td>' + cells + '</tr>';
    }).join('');

    var errBox = '';
    if (totalErr > 0) {
      var items = [];
      results.forEach(function (res) {
        res.errors.forEach(function (e) { items.push('<li>第 ' + res.row + ' 行 · ' + Fields.esc(e.message) + '</li>'); });
      });
      errBox = '<div class="wz-errbox"><div class="wz-errtitle">⚠ 共 ' + totalErr + ' 处校验错误（红色单元格已定位）：</div>' +
        '<ul class="wz-errlist">' + items.join('') + '</ul></div>';
    }

    body.innerHTML =
      '<div class="wz-step">第 3 步 / 共 3 步 · 数据预览与校验</div>' +
      errBox +
      '<div class="wz-tip">共 ' + list.length + ' 行数据，校验通过 ' + cleanCount + ' 行' +
        (totalErr ? '，错误 ' + totalErr + ' 处（生成时将跳过）' : '。') + '</div>' +
      '<div class="wz-gridwrap"><table class="wz-grid"><thead>' + thead + '</thead><tbody>' + tbody + '</tbody></table></div>' +
      '<div class="wz-actions">' +
        '<button class="btn" id="wzBack2">← 返回映射</button>' +
        '<button class="btn primary" id="wzGen" ' + (cleanCount === 0 ? 'disabled style="opacity:.5;cursor:not-allowed"' : '') +
          '>生成无误的 ' + cleanCount + ' 份</button>' +
      '</div>';

    $('#wzBack2').addEventListener('click', renderMapping);
    $('#wzGen').addEventListener('click', function () {
      if (cleanCount === 0) return;
      var cleanVals = list.filter(function (v, i) { return !results[i].errors.length; });
      try { global.Printer.printMulti(state.tpl, cleanVals); } catch (e) { alert('生成失败：' + e.message); return; }
      close();
    });
  }

  // 暴露外部关闭按钮
  document.addEventListener('DOMContentLoaded', function () {
    modal = document.getElementById('excelModal');
    closeBtn = document.getElementById('excelClose');
    if (closeBtn) closeBtn.addEventListener('click', close);
    if (modal) modal.addEventListener('click', function (e) { if (e.target === modal) close(); });
  });

  global.ExcelWizard = {
    open: open, close: close,
    // 测试钩子（不影响正常使用）：直接喂入解析后的 Excel 数据，跑真实映射与校验
    _test: function (tpl, headers, rows, map) {
      state = { tpl: tpl, data: { headers: headers, rows: rows }, map: map ? map.slice() : [] };
      if (!map) autoMatch();
      var values = buildValues();
      return {
        autoMap: state.map.slice(),
        values: values,
        errors: global.Validation.validateBatchStructured(tpl.fields, values)
      };
    }
  };
})(window);
