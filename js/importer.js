/* ============================================================
 * importer.js — Word / Excel 导入
 * 全局对象：Importer
 *   importWord(file, cb)  ->  { html, tokens:[key...] }
 *   importExcel(file, cb) ->  { headers:[...], rows:[[...]], objects:[{col:val}] }
 * 依赖：lib/mammoth.browser.min.js, lib/xlsx.full.min.js
 * ========================================================== */
(function (global) {
  'use strict';

  function readAsArrayBuffer(file) {
    return new Promise(function (resolve, reject) {
      var r = new FileReader();
      r.onload = function (e) { resolve(e.target.result); };
      r.onerror = function (e) { reject(e); };
      r.readAsArrayBuffer(file);
    });
  }

  /** 导入 Word (.docx)：转 HTML + 自动识别 {{占位符}} 字段 */
  function importWord(file) {
    return readAsArrayBuffer(file).then(function (ab) {
      if (typeof mammoth === 'undefined') {
        throw new Error('mammoth 库未加载，请检查 lib/mammoth.browser.min.js');
      }
      return mammoth.convertToHtml({ arrayBuffer: ab });
    }).then(function (result) {
      var html = result.value || '';
      var messages = result.messages || [];
      if (messages.length) console.info('Word 导入提示:', messages);
      var tokens = global.Fields.extractTokens(html);
      return { html: html, tokens: tokens };
    });
  }

  /** 导入 Excel (.xlsx/.xls)：返回表头与数据 */
  function importExcel(file) {
    return readAsArrayBuffer(file).then(function (ab) {
      if (typeof XLSX === 'undefined') {
        throw new Error('SheetJS 库未加载，请检查 lib/xlsx.full.min.js');
      }
      var wb = XLSX.read(ab, { type: 'array' });
      var firstSheet = wb.SheetNames[0];
      var ws = wb.Sheets[firstSheet];
      // 含表头的二维数组
      var matrix = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '', raw: false });
      // 去除完全空的尾部行
      while (matrix.length && matrix[matrix.length - 1].every(function (c) { return c === '' || c == null; })) {
        matrix.pop();
      }
      var headers = matrix.length ? matrix[0].map(function (h) { return (h == null ? '' : String(h)).trim(); }) : [];
      var rows = matrix.slice(1).map(function (r) {
        // 与表头等长
        var out = [];
        for (var i = 0; i < headers.length; i++) out.push(r[i] == null ? '' : String(r[i]));
        return out;
      });
      var objects = rows.map(function (r) {
        var o = {};
        headers.forEach(function (h, i) { o[h] = r[i]; });
        return o;
      });
      return { sheetName: firstSheet, headers: headers, rows: rows, objects: objects };
    });
  }

  global.Importer = {
    importWord: importWord,
    importExcel: importExcel
  };
})(window);
