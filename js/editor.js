/* ============================================================
 * editor.js — 模板设计器（布局/字体/边距/表头 + 内容编辑 + 字段管理）
 * 全局对象：Editor
 * 依赖：Fields
 * ========================================================== */
(function (global) {
  'use strict';

  var FONT_OPTIONS = [
    { v: "'Microsoft YaHei', 'PingFang SC', sans-serif", t: '微软雅黑' },
    { v: "'SimSun', '宋体', serif", t: '宋体' },
    { v: "'SimHei', '黑体', sans-serif", t: '黑体' },
    { v: "'KaiTi', '楷体', serif", t: '楷体' },
    { v: "'NSimSun', '新宋体', serif", t: '新宋体' },
    { v: "Arial, Helvetica, sans-serif", t: 'Arial' },
    { v: "'Times New Roman', serif", t: 'Times New Roman' }
  ];

  var DEFAULT_SETTINGS = {
    pageSize: 'A4',
    orientation: 'portrait',
    marginTop: 15, marginRight: 15, marginBottom: 15, marginLeft: 15,
    fontFamily: FONT_OPTIONS[0].v,
    fontSize: 14,
    lineHeight: 1.6,
    headerText: '',
    headerAlign: 'center',
    footerText: '',
    footerAlign: 'center',
    tableBorder: true
  };

  var root = null;
  var editorEl = null;
  var tpl = null;
  var savedRange = null;
  var onDirty = null;

  /* ---------- 选区保存/恢复（用于插入字段） ---------- */
  function captureSelection() {
    var sel = window.getSelection();
    if (sel && sel.rangeCount && editorEl.contains(sel.anchorNode)) {
      savedRange = sel.getRangeAt(0).cloneRange();
    }
  }
  function restoreAndInsert(text) {
    editorEl.focus();
    if (savedRange) {
      var sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(savedRange);
    }
    document.execCommand('insertText', false, text);
    captureSelection();
    markDirty();
  }

  function caretToEnd() {
    editorEl.focus();
    var r = document.createRange();
    r.selectNodeContents(editorEl);
    r.collapse(false);
    var s = window.getSelection();
    s.removeAllRanges();
    s.addRange(r);
  }

  /** 按指定行列插入表格（可含表头行），单元格可见边框、可直接编辑 */
  function insertTableAtSaved(rows, cols, header) {
    var border = 'border:1px solid #888;padding:5px 8px;vertical-align:top;';
    function cell(isHead) {
      return isHead
        ? '<th style="' + border + 'background:#f3f3f3;font-weight:600">&nbsp;</th>'
        : '<td style="' + border + '">&nbsp;</td>';
    }
    var html = '<table style="width:100%;border-collapse:collapse;margin:8px 0">';
    if (header) {
      html += '<thead><tr>';
      for (var c = 0; c < cols; c++) html += cell(true);
      html += '</tr></thead><tbody>';
      for (var r = 1; r < rows; r++) {
        html += '<tr>';
        for (var c2 = 0; c2 < cols; c2++) html += cell(false);
        html += '</tr>';
      }
      html += '</tbody>';
    } else {
      html += '<tbody>';
      for (var r2 = 0; r2 < rows; r2++) {
        html += '<tr>';
        for (var c3 = 0; c3 < cols; c3++) html += cell(false);
        html += '</tr>';
      }
      html += '</tbody>';
    }
    html += '</table>';

    editorEl.focus();
    if (savedRange) {
      var s = window.getSelection();
      s.removeAllRanges();
      s.addRange(savedRange);
    } else {
      caretToEnd();
    }
    document.execCommand('insertHTML', false, html);
    captureSelection();
    markDirty();
  }

  /** 把命令作用到当前选区（先恢复上次保存的选区，适合字体/颜色等） */
  function applyToSelection(cmd, val) {
    editorEl.focus();
    if (savedRange) {
      var s = window.getSelection();
      s.removeAllRanges();
      s.addRange(savedRange);
    }
    document.execCommand(cmd, false, val);
    captureSelection();
    markDirty();
  }

  /** 清理从 Word/网页粘贴来的 HTML：去掉内联样式(表格外)/class/id/事件，保留结构 */
  function sanitizeHtml(html) {
    var doc = new DOMParser().parseFromString(html, 'text/html');
    var all = doc.body.querySelectorAll('*');
    for (var i = all.length - 1; i >= 0; i--) {
      var el = all[i];
      var tag = (el.tagName || '').toLowerCase();
      if (tag === 'script' || tag === 'style' || tag === 'meta' || tag === 'link' || tag === 'title') {
        if (el.parentNode) el.parentNode.removeChild(el);
        continue;
      }
      var keepStyle = (tag === 'table' || tag === 'td' || tag === 'th' || tag === 'tr' || tag === 'img');
      var attrs = el.attributes;
      for (var j = attrs.length - 1; j >= 0; j--) {
        var n = attrs[j].name.toLowerCase();
        if (n === 'style') { if (!keepStyle) el.removeAttribute('style'); }
        else if (n === 'class' || n === 'id' || n === 'lang' || n === 'dir') { el.removeAttribute(n); }
        else if (n.indexOf('on') === 0) { el.removeAttribute(n); }
      }
    }
    return doc.body.innerHTML;
  }

  /** 字数统计（中文字符 + 非空白词） */
  function updateStatus() {
    var el = root.querySelector('#editorStatus');
    if (!el || !editorEl) return;
    var text = (editorEl.innerText || '').replace(/\s/g, '');
    el.textContent = '字数：' + text.length;
  }

  /** 让编辑区像一页 Word 纸：按纸张尺寸设置页面宽度 */
  var SHEET_WIDTH = { A4: 794, A5: 559, A3: 1123, Letter: 816 };
  function applySheetSize() {
    if (!editorEl || !tpl) return;
    var w = SHEET_WIDTH[tpl.settings.pageSize] || 794;
    editorEl.style.maxWidth = w + 'px';
  }

  /** 找到选区所在的块级元素（用于段落缩进） */
  function currentBlock() {
    var sel = window.getSelection();
    if (!sel || !sel.rangeCount) return null;
    var node = sel.anchorNode;
    if (!node) return null;
    if (node.nodeType === 3) node = node.parentNode;
    var BLOCKS = ['P', 'DIV', 'LI', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'TD', 'TH', 'BLOCKQUOTE', 'PRE'];
    while (node && node !== editorEl) {
      if (node.nodeType === 1 && BLOCKS.indexOf(node.tagName.toUpperCase()) >= 0) return node;
      node = node.parentNode;
    }
    return null;
  }

  /** Word 式段落缩进：以固定步长增减当前段落的左外边距 */
  /** Word 式首行缩进（中文文档标准：2 字符 ≈ 2em 为一步）。只缩进段落首行 */
  function indentBlock(dir) {
    var block = currentBlock();
    if (!block) return;
    editorEl.focus();
    if (savedRange) {
      var s = window.getSelection();
      s.removeAllRanges();
      s.addRange(savedRange);
    }
    var cs = window.getComputedStyle(block);
    var fs = parseFloat(cs.fontSize) || 14;
    var curEm = (parseFloat(cs.textIndent) || 0) / fs;
    var step = 2; // 一次 2 字符
    var nextEm = curEm + dir * step;
    if (nextEm <= 0) {
      // 清掉内联后若仍因继承保留首行缩进（默认 2em），显式置 0
      if (block.style.textIndent) block.style.textIndent = '';
      var cs2 = window.getComputedStyle(block);
      if ((parseFloat(cs2.textIndent) || 0) > 0) block.style.textIndent = '0em';
    } else {
      block.style.textIndent = nextEm + 'em';
    }
    captureSelection();
    markDirty();
  }

  /* ---------- 工具栏命令 ---------- */
  function exec(cmd, val) {
    editorEl.focus();
    captureSelection();
    document.execCommand(cmd, false, val || null);
    markDirty();
  }

  /* ---------- 构建静态骨架（只执行一次） ---------- */
  function buildSkeleton() {
    root.innerHTML = `
      <div class="design-grid">
        <div class="design-left">
          <div class="card">
            <div class="card-title">基本信息</div>
            <label class="lbl">模板名称</label>
            <input id="tplName" class="inp" placeholder="如：发货单模板" />
            <label class="lbl">说明</label>
            <textarea id="tplDesc" class="inp" rows="2" placeholder="可选，便于区分模板"></textarea>
          </div>

          <div class="card">
            <div class="card-title">页面与样式</div>
            <div class="row2">
              <div>
                <label class="lbl">纸张</label>
                <select id="setPageSize" class="inp">
                  <option value="A4">A4 (210×297mm)</option>
                  <option value="A5">A5 (148×210mm)</option>
                  <option value="A3">A3 (297×420mm)</option>
                  <option value="Letter">Letter (216×279mm)</option>
                </select>
              </div>
              <div>
                <label class="lbl">方向</label>
                <select id="setOrientation" class="inp">
                  <option value="portrait">纵向</option>
                  <option value="landscape">横向</option>
                </select>
              </div>
            </div>
            <div class="row4">
              <div><label class="lbl">上边距(mm)</label><input id="mTop" class="inp" type="number" min="0" step="1"></div>
              <div><label class="lbl">下边距</label><input id="mBottom" class="inp" type="number" min="0" step="1"></div>
              <div><label class="lbl">左边距</label><input id="mLeft" class="inp" type="number" min="0" step="1"></div>
              <div><label class="lbl">右边距</label><input id="mRight" class="inp" type="number" min="0" step="1"></div>
            </div>
            <div class="row2">
              <div>
                <label class="lbl">正文字体</label>
                <select id="setFont" class="inp"></select>
              </div>
              <div>
                <label class="lbl">正文字号(px)</label>
                <input id="setFontSize" class="inp" type="number" min="8" step="1">
              </div>
            </div>
            <div class="row2">
              <div>
                <label class="lbl">表头文字</label>
                <input id="setHeaderText" class="inp" placeholder="每页顶部显示的标题，可留空">
              </div>
              <div>
                <label class="lbl">表头对齐</label>
                <select id="setHeaderAlign" class="inp">
                  <option value="left">左</option><option value="center">居中</option><option value="right">右</option>
                </select>
              </div>
            </div>
            <div class="row2">
              <div>
                <label class="lbl">页脚文字</label>
                <input id="setFooterText" class="inp" placeholder="如：第 1 页 / 共 1 页（留空则不显示）">
              </div>
              <div>
                <label class="lbl">页脚对齐</label>
                <select id="setFooterAlign" class="inp">
                  <option value="left">左</option><option value="center">居中</option><option value="right">右</option>
                </select>
              </div>
            </div>
            <label class="chk"><input type="checkbox" id="setTableBorder"> 表格显示边框</label>
          </div>

          <div class="card">
            <div class="card-title">可变字段管理
              <button id="syncFields" class="mini-btn" title="从正文中扫描 {{字段}} 自动补全">从正文同步</button>
            </div>
            <div id="fieldRows" class="field-rows"></div>
            <div class="field-add">
              <input id="newFieldLabel" class="inp" placeholder="字段标签，如：客户名称">
              <select id="newFieldType" class="inp">
                ${Object.keys(Fields.TYPES).map(function (k) {
                  return '<option value="' + k + '">' + Fields.TYPES[k].label + '</option>';
                }).join('')}
              </select>
              <button id="addField" class="btn primary sm">+ 添加字段</button>
            </div>
            <p class="hint">字段类型：文本 / 数值 / 日期 / 表格(Excel数据源) / 下拉。正文中用 <code>{{key}}</code> 引用。</p>
          </div>
        </div>

        <div class="design-right">
          <div class="editor-toolbar">
            <div class="tb-group">
              <button class="tb" data-cmd="undo" title="撤销">↶</button>
              <button class="tb" data-cmd="redo" title="重做">↷</button>
            </div>
            <span class="sep"></span>
            <div class="tb-group">
              <select id="tbFont" class="inp xs" title="字体"></select>
              <select id="tbSize" class="inp xs" title="字号">
                <option value="1">8pt</option><option value="2">10pt</option><option value="3">12pt</option>
                <option value="4">14pt</option><option value="5">18pt</option><option value="6">24pt</option><option value="7">36pt</option>
              </select>
            </div>
            <span class="sep"></span>
            <div class="tb-group">
              <button class="tb" data-cmd="bold" title="加粗"><b>B</b></button>
              <button class="tb" data-cmd="italic" title="斜体"><i>I</i></button>
              <button class="tb" data-cmd="underline" title="下划线"><u>U</u></button>
              <button class="tb" data-cmd="strikeThrough" title="删除线"><s>S</s></button>
            </div>
            <span class="sep"></span>
            <div class="tb-group">
              <input type="color" id="tbColor" class="tb-color" title="文字颜色" value="#222222">
              <input type="color" id="tbBg" class="tb-color" title="高亮颜色" value="#ffff00">
            </div>
            <span class="sep"></span>
            <div class="tb-group">
              <button class="tb" data-cmd="formatBlock" data-val="H1" title="标题1">H1</button>
              <button class="tb" data-cmd="formatBlock" data-val="H2" title="标题2">H2</button>
              <button class="tb" data-cmd="formatBlock" data-val="H3" title="标题3">H3</button>
              <button class="tb" data-cmd="formatBlock" data-val="P" title="正文">¶</button>
            </div>
            <span class="sep"></span>
            <div class="tb-group">
              <button class="tb" data-cmd="justifyLeft" title="左对齐">⬅</button>
              <button class="tb" data-cmd="justifyCenter" title="居中">↔</button>
              <button class="tb" data-cmd="justifyRight" title="右对齐">➡</button>
              <button class="tb" data-cmd="justifyFull" title="两端对齐">☰</button>
            </div>
            <span class="sep"></span>
            <div class="tb-group">
              <button class="tb" data-cmd="insertUnorderedList" title="项目符号">•</button>
              <button class="tb" data-cmd="insertOrderedList" title="编号">1.</button>
              <button class="tb" data-cmd="outdent" title="减少缩进">⇤</button>
              <button class="tb" data-cmd="indent" title="增加缩进">⇥</button>
            </div>
            <span class="sep"></span>
            <div class="tb-group">
              <div class="tb-wrap">
                <button class="tb" id="insertTableBtn" title="插入表格">▦ 表格</button>
                <div id="tablePopover" class="popover" style="display:none">
                  <div class="pop-row"><label>行数</label><input id="tblRows" type="number" min="1" max="50" value="3" class="inp sm"></div>
                  <div class="pop-row"><label>列数</label><input id="tblCols" type="number" min="1" max="20" value="3" class="inp sm"></div>
                  <div class="pop-row"><label class="chk sm"><input type="checkbox" id="tblHeader" checked>首行为表头</label></div>
                  <button class="btn primary sm" id="tblInsert" style="width:100%">插入表格</button>
                </div>
              </div>
              <button class="tb" id="insertImageBtn" title="插入图片">🖼</button>
              <button class="tb" id="insertHrBtn" title="插入分隔线">―</button>
              <button class="tb" data-cmd="removeFormat" title="清除格式">⌫</button>
            </div>
            <span class="sep"></span>
            <div class="tb-group">
              <label class="ins-field-label">插入字段：</label>
              <select id="fieldSelect" class="inp sm"></select>
              <button class="btn primary sm" id="insertFieldBtn">插入</button>
            </div>
          </div>
          <div id="editorContent" class="editor-content" contenteditable="true" spellcheck="false"></div>
          <div class="editor-status" id="editorStatus">字数：0</div>
          <p class="hint center">像 Word 一样编辑：选中文字后设置字体/字号/颜色，或用工具栏排版；把光标放到要替换的位置，用右侧“插入字段”生成 <code>{{字段key}}</code> 占位符。支持从 Word/网页直接粘贴（自动清理格式）。</p>
          <input type="file" id="imageInput" accept="image/*" style="display:none">
        </div>
      </div>
    `;

    // 字体选项
    var fontSel = root.querySelector('#setFont');
    FONT_OPTIONS.forEach(function (f) {
      var o = document.createElement('option');
      o.value = f.v; o.textContent = f.t; fontSel.appendChild(o);
    });
    var tbFont = root.querySelector('#tbFont');
    FONT_OPTIONS.forEach(function (f) {
      var o = document.createElement('option');
      o.value = f.v; o.textContent = f.t; tbFont.appendChild(o);
    });

    editorEl = root.querySelector('#editorContent');

    // 中文 Word 风格：使用 CSS 样式 + Enter 创建 <p>（而非 <div>）
    try { document.execCommand('styleWithCSS', false, true); } catch (e) {}
    try { document.execCommand('defaultParagraphSeparator', false, 'p'); } catch (e) {}

    // 工具栏
    root.querySelectorAll('.tb[data-cmd]').forEach(function (b) {
      b.addEventListener('mousedown', function (e) { e.preventDefault(); });
      b.addEventListener('click', function () {
        var cmd = b.getAttribute('data-cmd');
        var val = b.getAttribute('data-val');
        if (cmd === 'indent') { indentBlock(1); return; }
        if (cmd === 'outdent') { indentBlock(-1); return; }
        exec(cmd, val);
      });
    });
    root.querySelector('#insertTableBtn').addEventListener('mousedown', function (e) { e.preventDefault(); });
    root.querySelector('#insertTableBtn').addEventListener('click', function (e) {
      e.stopPropagation();
      var pop = root.querySelector('#tablePopover');
      pop.style.display = (pop.style.display === 'none') ? 'block' : 'none';
    });
    root.querySelector('#tblInsert').addEventListener('click', function () {
      var rows = Math.max(1, Math.min(50, parseInt(root.querySelector('#tblRows').value, 10) || 3));
      var cols = Math.max(1, Math.min(20, parseInt(root.querySelector('#tblCols').value, 10) || 3));
      var header = root.querySelector('#tblHeader').checked;
      insertTableAtSaved(rows, cols, header);
      root.querySelector('#tablePopover').style.display = 'none';
    });
    // 点击其他区域关闭表格弹层
    document.addEventListener('click', function (e) {
      var pop = root.querySelector('#tablePopover');
      if (!pop || pop.style.display === 'none') return;
      if (pop.contains(e.target) || e.target === root.querySelector('#insertTableBtn')) return;
      pop.style.display = 'none';
    });

    // 字体 / 字号 / 颜色 / 高亮（作用于选区）
    root.querySelector('#tbFont').addEventListener('change', function () {
      if (this.value) applyToSelection('fontName', this.value);
    });
    root.querySelector('#tbSize').addEventListener('change', function () {
      applyToSelection('fontSize', this.value);
    });
    root.querySelector('#tbColor').addEventListener('change', function () {
      applyToSelection('foreColor', this.value);
    });
    root.querySelector('#tbBg').addEventListener('change', function () {
      try { document.execCommand('styleWithCSS', false, true); } catch (e) {}
      applyToSelection('hiliteColor', this.value);
      try { document.execCommand('styleWithCSS', false, false); } catch (e) {}
    });

    // 插入图片（转 base64 内联）
    root.querySelector('#insertImageBtn').addEventListener('click', function () {
      root.querySelector('#imageInput').click();
    });
    root.querySelector('#imageInput').addEventListener('change', function () {
      var file = this.files[0];
      if (!file) return;
      var reader = new FileReader();
      reader.onload = function () {
        applyToSelection('insertImage', reader.result);
      };
      reader.readAsDataURL(file);
      this.value = '';
    });

    // 插入分隔线
    root.querySelector('#insertHrBtn').addEventListener('click', function () {
      applyToSelection('insertHorizontalRule', null);
    });

    // 智能粘贴：从 Word/网页粘贴时清理冗余样式
    editorEl.addEventListener('paste', function (e) {
      e.preventDefault();
      var cd = (e.originalEvent || e).clipboardData || window.clipboardData;
      if (!cd) return;
      var html = cd.getData('text/html');
      var text = cd.getData('text/plain');
      if (html) {
        document.execCommand('insertHTML', false, sanitizeHtml(html));
      } else if (text) {
        document.execCommand('insertText', false, text);
      }
      captureSelection();
      markDirty();
    });

    // 纸张尺寸变化 → 同步编辑区“纸张”宽度
    root.querySelector('#setPageSize').addEventListener('change', function () {
      tpl.settings.pageSize = this.value;
      applySheetSize();
      markDirty();
    });

    // 插入字段
    root.querySelector('#insertFieldBtn').addEventListener('click', function () {
      var key = root.querySelector('#fieldSelect').value;
      if (!key) { alert('请先在左侧添加字段'); return; }
      restoreAndInsert('{{' + key + '}}');
    });

    // 添加字段
    root.querySelector('#addField').addEventListener('click', addFieldFromInput);

    // 从正文同步字段
    root.querySelector('#syncFields').addEventListener('click', syncFieldsFromContent);

    // 编辑器选区跟踪
    ['keyup', 'mouseup', 'focus', 'input'].forEach(function (ev) {
      editorEl.addEventListener(ev, function () { captureSelection(); });
    });
    editorEl.addEventListener('input', markDirty);

    // 设置项双向绑定
    bindSetting('#tplName', 'name');
    bindSetting('#tplDesc', 'description');
    bindSetting('#setPageSize', 'pageSize', 'settings');
    bindSetting('#setOrientation', 'orientation', 'settings');
    bindSetting('#mTop', 'marginTop', 'settings', true);
    bindSetting('#mBottom', 'marginBottom', 'settings', true);
    bindSetting('#mLeft', 'marginLeft', 'settings', true);
    bindSetting('#mRight', 'marginRight', 'settings', true);
    bindSetting('#setFont', 'fontFamily', 'settings');
    bindSetting('#setFontSize', 'fontSize', 'settings', true);
    bindSetting('#setHeaderText', 'headerText', 'settings');
    bindSetting('#setHeaderAlign', 'headerAlign', 'settings');
    bindSetting('#setFooterText', 'footerText', 'settings');
    bindSetting('#setFooterAlign', 'footerAlign', 'settings');
    root.querySelector('#setTableBorder').addEventListener('change', function () {
      tpl.settings.tableBorder = this.checked; markDirty();
    });
  }

  function bindSetting(sel, prop, group, isNum) {
    var el = root.querySelector(sel);
    el.addEventListener('input', function () {
      var val = isNum ? (parseFloat(this.value) || 0) : this.value;
      if (group) { if (!tpl[group]) tpl[group] = {}; tpl[group][prop] = val; }
      else tpl[prop] = val;
      markDirty();
    });
    el.addEventListener('change', function () {
      var val = isNum ? (parseFloat(this.value) || 0) : this.value;
      if (group) { if (!tpl[group]) tpl[group] = {}; tpl[group][prop] = val; }
      else tpl[prop] = val;
      markDirty();
    });
  }

  /* ---------- 字段管理 ---------- */
  function addFieldFromInput() {
    var labelEl = root.querySelector('#newFieldLabel');
    var typeEl = root.querySelector('#newFieldType');
    var label = labelEl.value.trim();
    if (!label) { alert('请填写字段标签'); return; }
    var key = Fields.normalizeKey(label);
    // 避免重复 key
    var exist = tpl.fields.some(function (f) { return f.key === key; });
    if (exist) {
      var i = 2;
      while (tpl.fields.some(function (f) { return f.key === key + '_' + i; })) i++;
      key = key + '_' + i;
    }
    tpl.fields.push({
      key: key, label: label, type: typeEl.value,
      default: '', required: false, validation: {},
      options: typeEl.value === 'select' ? [] : undefined
    });
    labelEl.value = '';
    renderFieldRows();
    refreshFieldSelect();
    markDirty();
  }

  function renderFieldRows() {
    var wrap = root.querySelector('#fieldRows');
    wrap.innerHTML = '';
    if (!tpl.fields.length) {
      wrap.innerHTML = '<p class="hint">暂无字段。添加后可在正文中插入占位符。</p>';
      return;
    }
    tpl.fields.forEach(function (f, idx) {
      var row = document.createElement('div');
      row.className = 'field-row';
      row.innerHTML = `
        <div class="fr-main">
          <input class="inp fr-label" value="${Fields.esc(f.label)}" placeholder="标签">
          <span class="fr-key" title="正文占位符 key">key: <code>${Fields.esc(f.key)}</code></span>
          <select class="inp fr-type">
            ${Object.keys(Fields.TYPES).map(function (k) {
              return '<option value="' + k + '"' + (k === f.type ? ' selected' : '') + '>' + Fields.TYPES[k].label + '</option>';
            }).join('')}
          </select>
          <input class="inp fr-default" value="${Fields.esc(f.default || '')}" placeholder="默认值">
          <label class="chk sm"><input type="checkbox" class="fr-req" ${f.required ? 'checked' : ''}>必填</label>
        </div>
        <div class="fr-extra"></div>
        <button class="fr-val-toggle mini-btn" type="button">校验规则 ▾</button>
        <div class="fr-validation" style="display:none"></div>
        <button class="icon-del" title="删除字段">✕</button>
      `;
      // 绑定
      row.querySelector('.fr-label').addEventListener('input', function () {
        f.label = this.value; markDirty();
      });
      row.querySelector('.fr-type').addEventListener('change', function () {
        f.type = this.value;
        f.options = f.type === 'select' ? (f.options || []) : undefined;
        renderFieldRows(); markDirty();
      });
      row.querySelector('.fr-default').addEventListener('input', function () { f.default = this.value; markDirty(); });
      row.querySelector('.fr-req').addEventListener('change', function () { f.required = this.checked; markDirty(); });
      row.querySelector('.icon-del').addEventListener('click', function () {
        tpl.fields.splice(idx, 1); renderFieldRows(); refreshFieldSelect(); markDirty();
      });
      // 下拉选项编辑
      if (f.type === 'select') {
        var extra = row.querySelector('.fr-extra');
        extra.innerHTML = '<input class="inp fr-opts" value="' +
          Fields.esc((f.options || []).join(',')) + '" placeholder="选项用逗号分隔，如：男,女">';
        extra.querySelector('.fr-opts').addEventListener('input', function () {
          f.options = this.value.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
          markDirty();
        });
      }
      // 校验规则面板
      var valWrap = row.querySelector('.fr-validation');
      buildValidationPanel(valWrap, f);
      row.querySelector('.fr-val-toggle').addEventListener('click', function () {
        var open = valWrap.style.display !== 'none';
        valWrap.style.display = open ? 'none' : 'block';
        this.textContent = open ? '校验规则 ▾' : '校验规则 ▴';
      });
      wrap.appendChild(row);
    });
  }

  /* ---------- 校验规则面板（图形化） ---------- */
  function escNum(n) {
    return (n === undefined || n === null || n === '') ? '' : n;
  }

  /** 根据字段类型渲染对应的校验规则控件，并双向绑定到 f.validation */
  function buildValidationPanel(wrap, f) {
    if (!f.validation) f.validation = {};
    var v = f.validation;
    var html = '';
    if (f.type === 'text') {
      html +=
        '<div class="val-grid">' +
          '<label>最小长度<input class="inp sm v-minlen" type="number" min="0" value="' + escNum(v.minLen) + '"></label>' +
          '<label>最大长度<input class="inp sm v-maxlen" type="number" min="0" value="' + escNum(v.maxLen) + '"></label>' +
        '</div>' +
        '<div class="val-grid">' +
          '<label>正则<input class="inp sm v-pattern" value="' + Fields.esc(v.pattern || '') + '" placeholder="如：^1[3-9]\\d{9}$"></label>' +
          '<label>错误提示<input class="inp sm v-patternmsg" value="' + Fields.esc(v.patternMsg || '') + '" placeholder="如：手机号格式不正确"></label>' +
        '</div>';
    } else if (f.type === 'number') {
      html +=
        '<div class="val-grid">' +
          '<label>最小值<input class="inp sm v-min" type="number" value="' + escNum(v.min) + '"></label>' +
          '<label>最大值<input class="inp sm v-max" type="number" value="' + escNum(v.max) + '"></label>' +
        '</div>' +
        '<label class="chk sm"><input type="checkbox" class="v-integer" ' + (v.integer ? 'checked' : '') + '>必须为整数</label>';
    } else if (f.type === 'date') {
      html +=
        '<div class="val-grid">' +
          '<label>最早日期<input class="inp sm v-min" type="date" value="' + Fields.esc(v.min || '') + '"></label>' +
          '<label>最晚日期<input class="inp sm v-max" type="date" value="' + Fields.esc(v.max || '') + '"></label>' +
        '</div>';
    } else if (f.type === 'select') {
      html += '<p class="hint">下拉字段仅需设置上方「必填」。</p>';
    } else if (f.type === 'table') {
      html += '<p class="hint">表格字段仅需设置上方「必填」（至少 1 行数据）。</p>';
    }

    wrap.innerHTML = html;

    function bind(sel, prop) {
      var el = wrap.querySelector(sel);
      if (!el) return;
      el.addEventListener('input', function () {
        if (this.value === '') delete f.validation[prop];
        else f.validation[prop] = this.value;
        markDirty();
      });
    }
    bind('.v-minlen', 'minLen');
    bind('.v-maxlen', 'maxLen');
    bind('.v-pattern', 'pattern');
    bind('.v-patternmsg', 'patternMsg');
    bind('.v-min', 'min');
    bind('.v-max', 'max');
    var integ = wrap.querySelector('.v-integer');
    if (integ) integ.addEventListener('change', function () { f.validation.integer = this.checked; markDirty(); });
  }

  function refreshFieldSelect() {
    var sel = root.querySelector('#fieldSelect');
    var cur = sel.value;
    sel.innerHTML = '<option value="">— 选择字段 —</option>';
    tpl.fields.forEach(function (f) {
      var o = document.createElement('option');
      o.value = f.key; o.textContent = f.label + ' (' + f.key + ')';
      sel.appendChild(o);
    });
    if (cur) sel.value = cur;
  }

  function syncFieldsFromContent() {
    var tokens = Fields.extractTokens(editorEl.innerHTML);
    var added = 0;
    tokens.forEach(function (k) {
      if (!tpl.fields.some(function (f) { return f.key === k; })) {
        tpl.fields.push({ key: k, label: k, type: 'text', default: '', required: false });
        added++;
      }
    });
    if (added) {
      renderFieldRows(); refreshFieldSelect();
      alert('已从正文同步新增 ' + added + ' 个字段（请补充标签与类型）。');
    } else {
      alert('正文中的占位符已全部存在对应字段。');
    }
    markDirty();
  }

  function markDirty() { if (onDirty) onDirty(); updateStatus(); }

  /* ---------- 对外接口 ---------- */
  function init(rootEl, dirtyCb) {
    root = rootEl;
    onDirty = dirtyCb || null;
    buildSkeleton();
  }

  function load(t) {
    tpl = JSON.parse(JSON.stringify(t || {}));
    if (!tpl.name) tpl.name = '';
    if (!tpl.description) tpl.description = '';
    if (!tpl.settings) tpl.settings = JSON.parse(JSON.stringify(DEFAULT_SETTINGS));
    // 补全默认字段
    Object.keys(DEFAULT_SETTINGS).forEach(function (k) {
      if (tpl.settings[k] === undefined) tpl.settings[k] = DEFAULT_SETTINGS[k];
    });
    if (!Array.isArray(tpl.fields)) tpl.fields = [];
    tpl.fields.forEach(function (f) { if (!f.validation) f.validation = {}; });
    if (tpl.content === undefined) tpl.content = '';

    root.querySelector('#tplName').value = tpl.name;
    root.querySelector('#tplDesc').value = tpl.description;
    root.querySelector('#setPageSize').value = tpl.settings.pageSize;
    root.querySelector('#setOrientation').value = tpl.settings.orientation;
    root.querySelector('#mTop').value = tpl.settings.marginTop;
    root.querySelector('#mBottom').value = tpl.settings.marginBottom;
    root.querySelector('#mLeft').value = tpl.settings.marginLeft;
    root.querySelector('#mRight').value = tpl.settings.marginRight;
    root.querySelector('#setFont').value = tpl.settings.fontFamily;
    root.querySelector('#setFontSize').value = tpl.settings.fontSize;
    root.querySelector('#setHeaderText').value = tpl.settings.headerText;
    root.querySelector('#setHeaderAlign').value = tpl.settings.headerAlign;
    root.querySelector('#setFooterText').value = tpl.settings.footerText;
    root.querySelector('#setFooterAlign').value = tpl.settings.footerAlign;
    root.querySelector('#setTableBorder').checked = !!tpl.settings.tableBorder;
    editorEl.innerHTML = tpl.content || '';

    applySheetSize();
    updateStatus();

    renderFieldRows();
    refreshFieldSelect();
    savedRange = null;
  }

  function collect() {
    tpl.name = root.querySelector('#tplName').value.trim();
    tpl.description = root.querySelector('#tplDesc').value.trim();
    tpl.content = editorEl.innerHTML;
    return tpl;
  }

  function blank() {
    load({
      name: '', description: '', settings: JSON.parse(JSON.stringify(DEFAULT_SETTINGS)),
      fields: [], content: '<p>在此处设计固定内容与样式，例如标题、说明文字、表格框架等。</p><p>把光标放到需要替换的位置，用左侧“插入字段”生成占位符，如 <code>{{客户名称}}</code>。</p>'
    });
  }

  global.Editor = {
    init: init,
    load: load,
    collect: collect,
    blank: blank,
    getPdfSize: function () { return tpl.settings.pageSize; }
  };
})(window);
